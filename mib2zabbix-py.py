#!/usr/bin/env python3
"""
mib2zabbix-py - SNMP Template Generator for Zabbix
Combina las funcionalidades de mib2zabbix (Perl) y SNMPWALK2ZABBIX (Python)

Copyright (C) 2024 - Basado en trabajos de Ryan Armstrong y Sean Bradley
"""

import sys
import os
import re
import uuid
import argparse
import subprocess
from xml.etree import ElementTree as ET
from xml.dom import minidom

# Mapeo de tipos de datos
DATATYPES = {
    "STRING": "CHAR",
    "OID": "CHAR", 
    "TIMETICKS": "FLOAT",
    "BITS": "TEXT",
    "COUNTER": "FLOAT",
    "COUNTER32": "FLOAT",
    "COUNTER64": "FLOAT",
    "GAUGE": "FLOAT",
    "GAUGE32": "FLOAT",
    "INTEGER": "FLOAT",
    "INTEGER32": "FLOAT",
    "IPADDR": "TEXT",
    "IPADDRESS": "TEXT",
    "NETADDDR": "TEXT",
    "NOTIF": "LOG",
    "TRAP": "LOG",
    "OBJECTID": "TEXT",
    "OCTETSTR": "TEXT",
    "OPAQUE": "TEXT",
    "TICKS": "FLOAT",
    "UNSIGNED32": "FLOAT",
    "WRONG TYPE (SHOULD BE GAUGE32 OR UNSIGNED32)": "TEXT",
    "\"\"": "TEXT",
    "HEX-STRING": "TEXT",
}

class MIBProcessor:
    def __init__(self):
        self.items = []
        self.discovery_rules = {}
        self.value_maps = {}
        self.last_part_10 = ""
        
    def get_data_type(self, snmp_type):
        """Obtiene el tipo de dato Zabbix correspondiente"""
        data_type = DATATYPES.get(snmp_type.upper(), "TEXT")
        if data_type == snmp_type.upper():
            print(f"Unhandled data type [{snmp_type}] so assigning TEXT")
        return data_type if data_type != "" else None
        
    def get_mib_info(self, oid):
        """Obtiene información MIB para un OID"""
        try:
            # Nombre completo
            full_name = subprocess.check_output(['snmptranslate', '-Tz', oid.strip()], 
                                              stderr=subprocess.DEVNULL, text=True).strip()
            # Descripción
            description_raw = subprocess.check_output(['snmptranslate', '-Td', oid.strip()], 
                                                    stderr=subprocess.DEVNULL, text=True)
            # Extraer descripción
            desc_match = re.search(r'DESCRIPTION\s+"([^"]*)"', description_raw)
            description = desc_match.group(1) if desc_match else ""
            description = description.replace('\n', '&#13;').replace('<', '<').replace('>', '>')
            description = re.sub(r"\s\s+", " ", description)
            
            # OID formateado
            formatted_oid = subprocess.check_output(['snmptranslate', '-Of', oid.strip()], 
                                                  stderr=subprocess.DEVNULL, text=True).strip()
            
            return full_name, description, formatted_oid
        except subprocess.CalledProcessError:
            return oid.strip(), "", oid.strip()

class MIB2ZabbixGenerator:
    def __init__(self):
        self.processor = MIBProcessor()
        self.args = None
        
    def parse_arguments(self):
        """Parsea argumentos de línea de comandos"""
        parser = argparse.ArgumentParser(description='Generate Zabbix template from MIB files or SNMP walk')
        
        # Modo de operación
        parser.add_argument('--mode', choices=['mib', 'walk'], default='mib',
                          help='Operation mode: mib (from MIB file) or walk (from SNMP walk)')
        
        # Parámetros generales
        parser.add_argument('-o', '--oid', required=True,
                          help='Root OID to process (must start with . for MIB mode)')
        parser.add_argument('-f', '--filename', default='stdout',
                          help='Output filename (default: stdout)')
        parser.add_argument('-N', '--name', help='Template name (default: auto-generated)')
        parser.add_argument('-G', '--group', default='Templates',
                          help='Template group (default: Templates)')
        parser.add_argument('-e', '--enable-items', action='store_true',
                          help='Enable all template items (default: disabled)')
        
        # SNMP parámetros
        parser.add_argument('-v', '--snmpver', choices=['1', '2', '3'], default='2',
                          help='SNMP version (default: 2)')
        parser.add_argument('-p', '--port', default='161',
                          help='SNMP UDP port number (default: 161)')
        
        # SNMP v1/v2c específicos
        parser.add_argument('-c', '--community', default='public',
                          help='SNMP community string (default: public)')
        
        # SNMP v3 específicos
        parser.add_argument('-L', '--level', choices=['noAuthNoPriv', 'authNoPriv', 'authPriv'],
                          help='Security level')
        parser.add_argument('-n', '--context', help='Context name')
        parser.add_argument('-u', '--username', help='Security name')
        parser.add_argument('-a', '--auth', choices=['MD5', 'SHA'], help='Authentication protocol')
        parser.add_argument('-A', '--authpass', help='Authentication passphrase')
        parser.add_argument('-x', '--privacy', choices=['DES', 'AES'], help='Privacy protocol')
        parser.add_argument('-X', '--privpass', help='Privacy passphrase')
        
        # Configuración de items
        parser.add_argument('--check-delay', default='60',
                          help='Check interval in seconds (default: 60)')
        parser.add_argument('--disc-delay', default='3600',
                          help='Discovery interval in seconds (default: 3600)')
        parser.add_argument('--history', default='7',
                          help='History retention in days (default: 7)')
        parser.add_argument('--trends', default='365',
                          help='Trends retention in days (default: 365)')
        
        # Parámetros para modo walk
        parser.add_argument('--ip', help='IP address for SNMP walk mode')
        
        self.args = parser.parse_args()
        
        # Validaciones
        if self.args.mode == 'walk' and not self.args.ip:
            parser.error("--ip is required for walk mode")
            
    def process_mib_mode(self):
        """Procesa desde archivo MIB"""
        print(f"Processing MIB mode for OID: {self.args.oid}")
        # Esta sería la implementación completa del modo MIB
        # Por ahora simulamos el procesamiento básico
        self.generate_basic_template()
        
    def process_walk_mode(self):
        """Procesa desde SNMP walk"""
        print(f"Processing SNMP walk mode for {self.args.ip}")
        
        # Construir comando snmpwalk
        cmd = ['snmpwalk', '-v', self.args.snmpver, '-On', '-c', self.args.community, 
               f'{self.args.ip}:{self.args.port}', self.args.oid]
        
        try:
            result = subprocess.check_output(cmd, text=True)
            oids = result.strip().split('\n')
            print(f"Processing {len(oids)} OIDs")
            
            template_name = "SNMP Template"
            
            for oid_line in oids:
                if not oid_line or "NO MORE VARIABLES LEFT" in oid_line.upper():
                    continue
                    
                parts = oid_line.split('=', 1)
                if len(parts) < 2:
                    continue
                    
                oid = parts[0].strip()
                value_part = parts[1].strip()
                
                # Extraer tipo y valor
                if ':' in value_part:
                    type_part, value = value_part.split(':', 1)
                    snmp_type = type_part.strip()
                    value = value.strip()
                else:
                    snmp_type = "STRING"
                    value = value_part
                
                # Obtener información MIB
                mib_name, description, formatted_oid = self.processor.get_mib_info(oid)
                
                # Detectar si es tabla
                oid_parts = formatted_oid.split('.')
                if len(oid_parts) >= 9 and oid_parts[8].upper().endswith("TABLE"):
                    # Procesar como tabla
                    table_name = f"{mib_name.split('::')[0]}::{oid_parts[8]}"
                    if table_name not in self.processor.discovery_rules:
                        self.processor.discovery_rules[table_name] = []
                    
                    # Simplificación: agregar como item prototype
                    item_proto = [
                        oid_parts[10] if len(oid_parts) > 10 else "column",
                        mib_name,
                        mib_name.replace("::", "."),
                        oid,
                        self.processor.get_data_type(snmp_type),
                        description
                    ]
                    self.processor.discovery_rules[table_name].append(item_proto)
                    print(f"ITEM_PROTOTYPE -> {table_name}")
                else:
                    # Procesar como item simple
                    name = mib_name.split("::")[1] if "::" in mib_name else mib_name
                    name = name.split(".")[0]
                    key = mib_name.replace("::", ".") if "::" in mib_name else oid
                    
                    # Usar sysName como nombre de template si es el OID correspondiente
                    if oid == ".1.3.6.1.2.1.1.5.0":
                        template_name = value
                        
                    item = [name, mib_name, key, oid, self.processor.get_data_type(snmp_type), description]
                    self.processor.items.append(item)
                    print(f"ITEM -> {mib_name} -> {name}")
                    
            self.generate_template(template_name)
            
        except subprocess.CalledProcessError as e:
            print(f"Error executing snmpwalk: {e}")
            sys.exit(1)
            
    def generate_basic_template(self):
        """Genera una plantilla básica"""
        template_name = self.args.name or "Generated SNMP Template"
        self.processor.items = [
            ["sysDescr", "SNMPv2-MIB::sysDescr.0", "SNMPv2-MIB.sysDescr.0", 
             ".1.3.6.1.2.1.1.1.0", "CHAR", "System description"],
            ["sysUpTime", "SNMPv2-MIB::sysUpTime.0", "SNMPv2-MIB.sysUpTime.0", 
             ".1.3.6.1.2.1.1.3.0", "FLOAT", "System uptime"]
        ]
        self.generate_template(template_name)
        
    def generate_template(self, template_name):
        """Genera el template XML"""
        # Crear estructura XML
        root = ET.Element("zabbix_export")
        ET.SubElement(root, "version").text = "6.0"
        
        templates = ET.SubElement(root, "templates")
        template = ET.SubElement(templates, "template")
        ET.SubElement(template, "uuid").text = uuid.uuid4().hex
        ET.SubElement(template, "template").text = f"{template_name} SNMP"
        ET.SubElement(template, "name").text = f"{template_name} SNMP"
        ET.SubElement(template, "description").text = "Template generated by mib2zabbix-py"
        
        # Groups
        groups = ET.SubElement(template, "groups")
        group = ET.SubElement(groups, "group")
        ET.SubElement(group, "name").text = self.args.group
        
        # Items
        if self.processor.items:
            items = ET.SubElement(template, "items")
            for item in self.processor.items:
                item_elem = ET.SubElement(items, "item")
                ET.SubElement(item_elem, "uuid").text = uuid.uuid4().hex
                ET.SubElement(item_elem, "name").text = item[0]
                ET.SubElement(item_elem, "type").text = "SNMP_AGENT"
                ET.SubElement(item_elem, "snmp_oid").text = item[3]
                ET.SubElement(item_elem, "key").text = item[2]
                if item[4]:
                    ET.SubElement(item_elem, "value_type").text = item[4]
                ET.SubElement(item_elem, "description").text = item[5]
                ET.SubElement(item_elem, "history").text = f"{self.args.history}d"
                ET.SubElement(item_elem, "trends").text = self.args.trends
                ET.SubElement(item_elem, "status").text = "ENABLED" if self.args.enable_items else "DISABLED"
                ET.SubElement(item_elem, "delay").text = self.args.check_delay
        
        # Discovery rules
        if self.processor.discovery_rules:
            discovery_rules = ET.SubElement(template, "discovery_rules")
            for rule_name, item_prototypes in self.processor.discovery_rules.items():
                rule = ET.SubElement(discovery_rules, "discovery_rule")
                ET.SubElement(rule, "uuid").text = uuid.uuid4().hex
                ET.SubElement(rule, "name").text = rule_name.split("::")[1] if "::" in rule_name else rule_name
                ET.SubElement(rule, "delay").text = self.args.disc_delay
                ET.SubElement(rule, "key").text = rule_name.replace("::", ".")
                ET.SubElement(rule, "status").text = "DISABLED"
                ET.SubElement(rule, "type").text = "SNMP_AGENT"
                
                if item_prototypes:
                    prototypes = ET.SubElement(rule, "item_prototypes")
                    for proto in item_prototypes:
                        proto_elem = ET.SubElement(prototypes, "item_prototype")
                        ET.SubElement(proto_elem, "uuid").text = uuid.uuid4().hex
                        ET.SubElement(proto_elem, "name").text = f"{proto[0]}.{{#SNMPINDEX}}"
                        ET.SubElement(proto_elem, "type").text = "SNMP_AGENT"
                        ET.SubElement(proto_elem, "snmp_oid").text = f"{proto[3]}.{{#SNMPINDEX}}"
                        ET.SubElement(proto_elem, "key").text = f"{proto[3]}[{{#SNMPINDEX}}]"
                        if proto[4]:
                            ET.SubElement(proto_elem, "value_type").text = proto[4]
                        ET.SubElement(proto_elem, "delay").text = self.args.check_delay
                        ET.SubElement(proto_elem, "history").text = f"{self.args.history}d"
                        ET.SubElement(proto_elem, "description").text = proto[5]
        
        # Pretty print XML
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        xml_string = reparsed.toprettyxml(indent="  ")
        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip()])
        
        # Output
        if self.args.filename == 'stdout':
            print(xml_string)
        else:
            with open(self.args.filename, 'w') as f:
                f.write(xml_string)
            print(f"Template saved to {self.args.filename}")
    
    def run(self):
        """Ejecuta el generador"""
        self.parse_arguments()
        
        if self.args.mode == 'mib':
            self.process_mib_mode()
        else:
            self.process_walk_mode()

def main():
    """Función principal"""
    generator = MIB2ZabbixGenerator()
    generator.run()

if __name__ == "__main__":
    main()
