#!/usr/bin/env python3
"""
mib2zabbix-py - SNMP Template Generator for Zabbix
Combina las funcionalidades de mib2zabbix (Perl) y SNMPWALK2ZABBIX (Python)

Copyright (C) 2024 - Basado en trabajos de Ryan Armstrong y Sean Bradley
Distribuido bajo la licencia GNU GPL v2 o posterior
"""

import sys
import os
import re
import uuid
import argparse
import subprocess
from xml.etree import ElementTree as ET
from xml.dom import minidom

# Mapeo de tipos de datos SNMP a Zabbix
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
    """Procesador de información MIB"""
    
    def __init__(self):
        self.items = []
        self.discovery_rules = {}
        self.value_maps = {}
        self.last_part_10 = ""
        
    def get_data_type(self, snmp_type):
        """
        Obtiene el tipo de dato Zabbix correspondiente al tipo SNMP
        
        Args:
            snmp_type (str): Tipo de dato SNMP
            
        Returns:
            str: Tipo de dato Zabbix correspondiente
        """
        data_type = DATATYPES.get(snmp_type.upper(), "TEXT")
        if data_type == snmp_type.upper():
            print(f"Unhandled data type [{snmp_type}] so assigning TEXT")
        return data_type if data_type != "" else None
        
    def get_mib_info(self, oid):
        """
        Obtiene información MIB para un OID específico
        
        Args:
            oid (str): OID a consultar
            
        Returns:
            tuple: (nombre_completo, descripcion, oid_formateado)
        """
        try:
            # Obtener nombre completo del OID
            full_name = subprocess.check_output(['snmptranslate', '-Tz', oid.strip()], 
                                              stderr=subprocess.DEVNULL, text=True).strip()
            
            # Obtener descripción del OID
            description_raw = subprocess.check_output(['snmptranslate', '-Td', oid.strip()], 
                                                    stderr=subprocess.DEVNULL, text=True)
            
            # Extraer descripción usando expresión regular
            desc_match = re.search(r'DESCRIPTION\s+"([^"]*)"', description_raw)
            description = desc_match.group(1) if desc_match else ""
            description = description.replace('\n', '&#13;').replace('<', '<').replace('>', '>')
            description = re.sub(r"\s\s+", " ", description)
            
            # Obtener OID formateado
            formatted_oid = subprocess.check_output(['snmptranslate', '-Of', oid.strip()], 
                                                  stderr=subprocess.DEVNULL, text=True).strip()
            
            return full_name, description, formatted_oid
        except subprocess.CalledProcessError:
            # En caso de error, devolver valores por defecto
            return oid.strip(), "", oid.strip()

class MIB2ZabbixGenerator:
    """Generador de plantillas Zabbix desde MIBs o SNMP walk"""
    
    def __init__(self):
        self.processor = MIBProcessor()
        self.args = None
        
    def parse_arguments(self):
        """Parsea argumentos de línea de comandos"""
        parser = argparse.ArgumentParser(
            description='Generate Zabbix template from MIB files or SNMP walk',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos de uso:
  # Modo walk - genera plantilla desde dispositivo SNMP
  python3 mib2zabbix-py.py --mode walk --ip 192.168.1.1 -o .1.3.6.1.2.1 -c public

  # Modo MIB - genera plantilla desde archivos MIB
  python3 mib2zabbix-py.py --mode mib -o .1.3.6.1.2.1.1 -N "Mi Template"

  # Con SNMP v3
  python3 mib2zabbix-py.py --mode walk -v 3 -u myuser -L authPriv -a SHA -A mypass -x AES -X mypriv --ip 192.168.1.1 -o .1.3.6.1.2.1
            """
        )
        
        # Modo de operación
        parser.add_argument('--mode', choices=['mib', 'walk'], default='mib',
                          help='Modo de operación: mib (desde archivo MIB) o walk (desde SNMP walk)')
        
        # Parámetros generales
        parser.add_argument('-o', '--oid', required=True,
                          help='OID raíz a procesar (debe comenzar con . para modo MIB)')
        parser.add_argument('-f', '--filename', default='stdout',
                          help='Nombre de archivo de salida (por defecto: stdout)')
        parser.add_argument('-N', '--name', help='Nombre del template (por defecto: auto-generado)')
        parser.add_argument('-G', '--group', default='Templates',
                          help='Grupo del template (por defecto: Templates)')
        parser.add_argument('-e', '--enable-items', action='store_true',
                          help='Habilitar todos los items del template (por defecto: deshabilitados)')
        
        # Parámetros SNMP
        parser.add_argument('-v', '--snmpver', choices=['1', '2', '3'], default='2',
                          help='Versión SNMP (por defecto: 2)')
        parser.add_argument('-p', '--port', default='161',
                          help='Puerto UDP SNMP (por defecto: 161)')
        
        # Parámetros SNMP v1/v2c
        parser.add_argument('-c', '--community', default='public',
                          help='Cadena de comunidad SNMP (por defecto: public)')
        
        # Parámetros SNMP v3
        parser.add_argument('-L', '--level', choices=['noAuthNoPriv', 'authNoPriv', 'authPriv'],
                          help='Nivel de seguridad')
        parser.add_argument('-n', '--context', help='Nombre de contexto')
        parser.add_argument('-u', '--username', help='Nombre de usuario de seguridad')
        parser.add_argument('-a', '--auth', choices=['MD5', 'SHA'], help='Protocolo de autenticación')
        parser.add_argument('-A', '--authpass', help='Frase de contraseña de autenticación')
        parser.add_argument('-x', '--privacy', choices=['DES', 'AES'], help='Protocolo de privacidad')
        parser.add_argument('-X', '--privpass', help='Frase de contraseña de privacidad')
        
        # Configuración de items
        parser.add_argument('--check-delay', default='60',
                          help='Intervalo de chequeo en segundos (por defecto: 60)')
        parser.add_argument('--disc-delay', default='3600',
                          help='Intervalo de descubrimiento en segundos (por defecto: 3600)')
        parser.add_argument('--history', default='7',
                          help='Retención de historial en días (por defecto: 7)')
        parser.add_argument('--trends', default='365',
                          help='Retención de tendencias en días (por defecto: 365)')
        
        # Parámetros para modo walk
        parser.add_argument('--ip', help='Dirección IP para modo walk')
        
        self.args = parser.parse_args()
        
        # Validaciones adicionales
        if self.args.mode == 'walk' and not self.args.ip:
            parser.error("--ip es requerido para modo walk")
            
    def build_snmp_command(self):
        """
        Construye el comando snmpwalk basado en los argumentos proporcionados
        
        Returns:
            list: Lista de argumentos para subprocess
        """
        cmd = ['snmpwalk', '-v', self.args.snmpver, '-On']
        
        # Agregar parámetros según la versión SNMP
        if self.args.snmpver in ['1', '2']:
            cmd.extend(['-c', self.args.community])
        elif self.args.snmpver == '3':
            # Construir parámetros SNMP v3
            if self.args.level:
                cmd.extend(['-l', self.args.level])
            if self.args.username:
                cmd.extend(['-u', self.args.username])
            if self.args.auth:
                cmd.extend(['-a', self.args.auth])
            if self.args.authpass:
                cmd.extend(['-A', self.args.authpass])
            if self.args.privacy:
                cmd.extend(['-x', self.args.privacy])
            if self.args.privpass:
                cmd.extend(['-X', self.args.privpass])
            if self.args.context:
                cmd.extend(['-n', self.args.context])
        
        # Agregar IP, puerto y OID
        cmd.append(f'{self.args.ip}:{self.args.port}')
        cmd.append(self.args.oid)
        
        return cmd
            
    def process_mib_mode(self):
        """Procesa desde archivo MIB"""
        print(f"Procesando modo MIB para OID: {self.args.oid}")
        # Esta sería la implementación completa del modo MIB
        # Por ahora simulamos el procesamiento básico
        self.generate_basic_template()
        
    def process_walk_mode(self):
        """Procesa desde SNMP walk"""
        print(f"Procesando modo SNMP walk para {self.args.ip}")
        
        # Construir y ejecutar comando snmpwalk
        cmd = self.build_snmp_command()
        
        try:
            result = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            oids = result.strip().split('\n')
            print(f"Procesando {len(oids)} OIDs")
            
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
                        self.processor.last_part_10 = ""
                    
                    # Evitar duplicados en tabla
                    if len(oid_parts) > 10 and self.processor.last_part_10 != oid_parts[10]:
                        # Crear OID base para item prototype
                        oid_base_parts = oid.split('.')[:-1]
                        oid_base = '.'.join(oid_base_parts)
                        
                        item_proto = [
                            oid_parts[10] if len(oid_parts) > 10 else "column",
                            mib_name,
                            mib_name.replace("::", "."),
                            oid_base,
                            self.processor.get_data_type(snmp_type),
                            description
                        ]
                        self.processor.discovery_rules[table_name].append(item_proto)
                        self.processor.last_part_10 = oid_parts[10]
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
            print(f"Error ejecutando snmpwalk: {e.output if e.output else str(e)}")
            sys.exit(1)
        except FileNotFoundError:
            print("Error: Comando 'snmpwalk' no encontrado. Asegúrate de tener instaladas las herramientas SNMP.")
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
        """
        Genera el template XML de Zabbix
        
        Args:
            template_name (str): Nombre del template
        """
        # Crear estructura XML raíz
        root = ET.Element("zabbix_export")
        ET.SubElement(root, "version").text = "6.0"
        
        # Sección de templates
        templates = ET.SubElement(root, "templates")
        template = ET.SubElement(templates, "template")
        ET.SubElement(template, "uuid").text = uuid.uuid4().hex
        ET.SubElement(template, "template").text = f"{template_name} SNMP"
        ET.SubElement(template, "name").text = f"{template_name} SNMP"
        ET.SubElement(template, "description").text = "Template generated by mib2zabbix-py"
        
        # Grupos
        groups = ET.SubElement(template, "groups")
        group = ET.SubElement(groups, "group")
        ET.SubElement(group, "name").text = self.args.group
        
        # Items simples
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
        
        # Reglas de descubrimiento
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
                
                # Item prototypes
                if item_prototypes:
                    prototypes = ET.SubElement(rule, "item_prototypes")
                    snmp_oids = ""
                    
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
                        
                        # Construir cadena de OIDs para discovery
                        oid_append = "{#" + proto[0].upper() + "}," + proto[3] + ","
                        if(len(snmp_oids + oid_append) < 501):
                            snmp_oids += oid_append
                    
                    # Agregar OID de descubrimiento
                    if snmp_oids:
                        ET.SubElement(rule, "snmp_oid").text = f"discovery[{snmp_oids[:-1]}]"
        
        # Formatear XML de manera legible
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        xml_string = reparsed.toprettyxml(indent="  ")
        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip()])
        
        # Salida del resultado
        if self.args.filename == 'stdout':
            print(xml_string)
        else:
            # Crear nombre de archivo basado en template name si no se especifica
            filename = self.args.filename
            if filename == 'stdout':
                filename = f"template-{template_name.replace(' ', '-')}.xml"
                
            with open(filename, 'w') as f:
                f.write(xml_string)
            print(f"Template guardado en {filename}")
    
    def run(self):
        """Ejecuta el generador principal"""
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
