#!/usr/bin/env python3
"""
mib2template.py - Genera plantillas de Zabbix desde archivos MIB

Basado en el trabajo original de mib2zabbix por Ryan Armstrong
y extendido con funcionalidades adicionales.

Copyright (C) 2024 - Basado en trabajos de Ryan Armstrong
Licencia: GNU General Public License v2.0
"""

import sys
import os
import re
import uuid
import argparse
import subprocess
from xml.etree import ElementTree as ET
from xml.dom import minidom

class MIBTemplateGenerator:
    def __init__(self):
        self.items = []
        self.discovery_rules = {}
        self.value_maps = {}
        self.args = None
        
    def parse_arguments(self):
        """Parsea los argumentos de línea de comandos"""
        parser = argparse.ArgumentParser(description='Generate Zabbix template from MIB file')
        
        parser.add_argument('-f', '--mib-file', required=True,
                          help='Path to MIB file')
        parser.add_argument('-m', '--module', required=True,
                          help='MIB module name')
        parser.add_argument('-o', '--output', default='stdout',
                          help='Output filename (default: stdout)')
        parser.add_argument('-N', '--template-name',
                          help='Template name (default: module name)')
        parser.add_argument('-G', '--group', default='Templates',
                          help='Template group (default: Templates)')
        parser.add_argument('-e', '--enable-items', action='store_true',
                          help='Enable all template items (default: disabled)')
        
        # SNMP parameters
        parser.add_argument('-v', '--snmp-version', choices=['1', '2', '3'], default='2',
                          help='SNMP version (default: 2)')
        parser.add_argument('-p', '--port', default='161',
                          help='SNMP port (default: 161)')
        
        # SNMP v1/v2c
        parser.add_argument('-c', '--community', default='public',
                          help='SNMP community (default: public)')
        
        # SNMP v3
        parser.add_argument('-L', '--sec-level', choices=['noAuthNoPriv', 'authNoPriv', 'authPriv'],
                          help='Security level')
        parser.add_argument('-u', '--username', help='Security name')
        parser.add_argument('-a', '--auth-proto', choices=['MD5', 'SHA'], help='Authentication protocol')
        parser.add_argument('-A', '--auth-pass', help='Authentication passphrase')
        parser.add_argument('-x', '--priv-proto', choices=['DES', 'AES'], help='Privacy protocol')
        parser.add_argument('-X', '--priv-pass', help='Privacy passphrase')
        
        # Item configuration
        parser.add_argument('--check-delay', default='60',
                          help='Check interval in seconds (default: 60)')
        parser.add_argument('--disc-delay', default='3600',
                          help='Discovery interval in seconds (default: 3600)')
        parser.add_argument('--history', default='7',
                          help='History retention in days (default: 7)')
        parser.add_argument('--trends', default='365',
                          help='Trends retention in days (default: 365)')
        
        self.args = parser.parse_args()
        
    def load_mib(self):
        """Carga el MIB y verifica su disponibilidad"""
        try:
            # Verificar que el MIB puede ser cargado
            result = subprocess.run(['snmptranslate', '-T', 'o', '-m', self.args.mib_file, self.args.module], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error cargando MIB: {result.stderr}")
                return False
            return True
        except FileNotFoundError:
            print("Error: snmptranslate no encontrado. Asegúrate de tener net-snmp instalado.")
            return False
            
    def get_mib_symbols(self):
        """Obtiene todos los símbolos del MIB"""
        try:
            # Obtener todos los objetos del MIB
            result = subprocess.run([
                'snmptranslate', '-T', 'l', '-m', self.args.mib_file, self.args.module
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error obteniendo símbolos del MIB: {result.stderr}")
                return []
                
            symbols = result.stdout.strip().split('\n')
            # Filtrar símbolos vacíos y comentarios
            symbols = [s.strip() for s in symbols if s.strip() and not s.startswith('#')]
            return symbols
        except Exception as e:
            print(f"Error procesando MIB symbols: {e}")
            return []
            
    def process_symbol(self, symbol):
        """Procesa un símbolo individual del MIB"""
        try:
            # Obtener OID
            oid_result = subprocess.run(['snmptranslate', '-On', '-m', self.args.mib_file, symbol], 
                                      capture_output=True, text=True)
            if oid_result.returncode != 0:
                return None
                
            oid = oid_result.stdout.strip()
            
            # Obtener nombre completo
            full_name_result = subprocess.run(['snmptranslate', '-Tz', '-m', self.args.mib_file, symbol], 
                                            capture_output=True, text=True)
            full_name = full_name_result.stdout.strip() if full_name_result.returncode == 0 else symbol
            
            # Obtener descripción
            desc_result = subprocess.run(['snmptranslate', '-Td', '-m', self.args.mib_file, symbol], 
                                       capture_output=True, text=True)
            description = ""
            if desc_result.returncode == 0:
                desc_match = re.search(r'DESCRIPTION\s+"([^"]*)"', desc_result.stdout)
                if desc_match:
                    description = desc_match.group(1).replace('\n', ' ').replace('<', '<').replace('>', '>')
                    description = re.sub(r'\s+', ' ', description).strip()
            
            # Obtener sintaxis/tipo
            syntax_result = subprocess.run(['snmptranslate', '-Ts', '-m', self.args.mib_file, symbol], 
                                         capture_output=True, text=True)
            syntax = ""
            if syntax_result.returncode == 0:
                syntax = syntax_result.stdout.strip()
                
            # Determinar tipo de dato Zabbix
            zabbix_type = self.get_zabbix_type(syntax)
            
            # Verificar si es tabla
            is_table = self.is_table_symbol(symbol, syntax)
            
            return {
                'symbol': symbol,
                'oid': oid,
                'full_name': full_name,
                'description': description,
                'syntax': syntax,
                'zabbix_type': zabbix_type,
                'is_table': is_table
            }
        except Exception as e:
            print(f"Error procesando símbolo {symbol}: {e}")
            return None
            
    def get_zabbix_type(self, syntax):
        """Mapea tipos SNMP a tipos Zabbix"""
        type_mapping = {
            'INTEGER': 'FLOAT',
            'Integer32': 'FLOAT',
            'Unsigned32': 'FLOAT',
            'Counter32': 'FLOAT',
            'Counter64': 'FLOAT',
            'Gauge32': 'FLOAT',
            'TimeTicks': 'FLOAT',
            'OCTET STRING': 'CHAR',
            'OBJECT IDENTIFIER': 'CHAR',
            'IpAddress': 'TEXT',
            'BITS': 'TEXT',
            'Opaque': 'TEXT'
        }
        
        for snmp_type, zabbix_type in type_mapping.items():
            if snmp_type in syntax:
                return zabbix_type
                
        # Tipos por defecto
        if 'INTEGER' in syntax:
            return 'FLOAT'
        elif 'STRING' in syntax:
            return 'CHAR'
        else:
            return 'TEXT'
            
    def is_table_symbol(self, symbol, syntax):
        """Determina si un símbolo es una tabla"""
        return '.1' in symbol or 'Table' in symbol or 'Entry' in symbol or 'Table' in syntax
        
    def process_mib_symbols(self):
        """Procesa todos los símbolos del MIB"""
        print(f"Procesando MIB: {self.args.module}")
        symbols = self.get_mib_symbols()
        print(f"Encontrados {len(symbols)} símbolos")
        
        tables = {}
        scalars = []
        
        for symbol in symbols:
            if '::' not in symbol:
                continue
                
            symbol_info = self.process_symbol(symbol)
            if not symbol_info:
                continue
                
            if symbol_info['is_table']:
                # Procesar tabla
                table_name = symbol_info['symbol'].split('::')[0] + '::' + symbol_info['symbol'].split('::')[1].split('.')[0]
                if table_name not in tables:
                    tables[table_name] = []
                tables[table_name].append(symbol_info)
                print(f"TABLA: {symbol_info['full_name']}")
            else:
                # Procesar scalar
                scalars.append(symbol_info)
                print(f"ITEM: {symbol_info['full_name']}")
                
        # Convertir a formato de template
        self.convert_to_template_format(tables, scalars)
        
    def convert_to_template_format(self, tables, scalars):
        """Convierte los datos procesados al formato de template"""
        # Procesar items escalares
        for scalar in scalars:
            name = scalar['full_name'].split('::')[1] if '::' in scalar['full_name'] else scalar['full_name']
            key = scalar['full_name'].replace('::', '.') if '::' in scalar['full_name'] else scalar['oid']
            
            item = [
                name,
                scalar['full_name'],
                key,
                scalar['oid'],
                scalar['zabbix_type'],
                scalar['description']
            ]
            self.items.append(item)
            
        # Procesar tablas
        for table_name, columns in tables.items():
            if table_name not in self.discovery_rules:
                self.discovery_rules[table_name] = []
                
            for column in columns:
                # Solo procesar columnas de tabla (no la entrada de tabla en sí)
                if '.1' in column['symbol']:
                    name = column['full_name'].split('::')[1].split('.')[0] if '::' in column['full_name'] else column['full_name']
                    key = column['full_name'].replace('::', '.') if '::' in column['full_name'] else column['oid']
                    
                    item_proto = [
                        name,
                        column['full_name'],
                        key,
                        column['oid'],
                        column['zabbix_type'],
                        column['description']
                    ]
                    self.discovery_rules[table_name].append(item_proto)
                    
    def generate_template(self):
        """Genera el template XML"""
        template_name = self.args.template_name or self.args.module
        
        # Crear estructura XML
        root = ET.Element("zabbix_export")
        ET.SubElement(root, "version").text = "6.0"
        
        templates = ET.SubElement(root, "templates")
        template = ET.SubElement(templates, "template")
        ET.SubElement(template, "uuid").text = str(uuid.uuid4())
        ET.SubElement(template, "template").text = f"{template_name} SNMP"
        ET.SubElement(template, "name").text = f"{template_name} SNMP"
        ET.SubElement(template, "description").text = f"Template generated from MIB {self.args.module}"
        
        # Groups
        groups = ET.SubElement(template, "groups")
        group = ET.SubElement(groups, "group")
        ET.SubElement(group, "name").text = self.args.group
        
        # Items
        if self.items:
            items = ET.SubElement(template, "items")
            for item in self.items:
                item_elem = ET.SubElement(items, "item")
                ET.SubElement(item_elem, "uuid").text = str(uuid.uuid4())
                ET.SubElement(item_elem, "name").text = item[0]
                ET.SubElement(item_elem, "type").text = "SNMP_AGENT"
                ET.SubElement(item_elem, "snmp_oid").text = item[3]
                ET.SubElement(item_elem, "key").text = item[2]
                if item[4]:
                    ET.SubElement(item_elem, "value_type").text = item[4]
                ET.SubElement(item_elem, "description").text = item[5]
                ET.SubElement(item_elem, "history").text = f"{self.args.history}d"
                ET.SubElement(item_elem, "trends").text = f"{self.args.trends}d"
                ET.SubElement(item_elem, "status").text = "ENABLED" if self.args.enable_items else "DISABLED"
                ET.SubElement(item_elem, "delay").text = self.args.check_delay
        
        # Discovery rules
        if self.discovery_rules:
            discovery_rules = ET.SubElement(template, "discovery_rules")
            for rule_name, item_prototypes in self.discovery_rules.items():
                rule = ET.SubElement(discovery_rules, "discovery_rule")
                ET.SubElement(rule, "uuid").text = str(uuid.uuid4())
                ET.SubElement(rule, "name").text = rule_name.split("::")[1] if "::" in rule_name else rule_name
                ET.SubElement(rule, "delay").text = self.args.disc_delay
                ET.SubElement(rule, "key").text = rule_name.replace("::", ".")
                ET.SubElement(rule, "status").text = "DISABLED"
                ET.SubElement(rule, "type").text = "SNMP_AGENT"
                
                if item_prototypes:
                    prototypes = ET.SubElement(rule, "item_prototypes")
                    for proto in item_prototypes:
                        proto_elem = ET.SubElement(prototypes, "item_prototype")
                        ET.SubElement(proto_elem, "uuid").text = str(uuid.uuid4())
                        ET.SubElement(proto_elem, "name").text = f"{proto[0]}.{{#SNMPINDEX}}"
                        ET.SubElement(proto_elem, "type").text = "SNMP_AGENT"
                        ET.SubElement(proto_elem, "snmp_oid").text = f"{proto[3]}.{{#SNMPINDEX}}"
                        ET.SubElement(proto_elem, "key").text = f"{proto[3]}[{{#SNMPINDEX}}]"
                        if proto[4]:
                            ET.SubElement(proto_elem, "value_type").text = proto[4]
                        ET.SubElement(proto_elem, "delay").text = self.args.check_delay
                        ET.SubElement(proto_elem, "history").text = f"{self.args.history}d"
                        ET.SubElement(proto_elem, "trends").text = f"{self.args.trends}d"
                        ET.SubElement(proto_elem, "description").text = proto[5]
                        ET.SubElement(proto_elem, "status").text = "DISABLED"
        
        # Pretty print XML
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        xml_string = reparsed.toprettyxml(indent="  ")
        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip()])
        
        # Output
        if self.args.output == 'stdout':
            print(xml_string)
        else:
            with open(self.args.output, 'w') as f:
                f.write(xml_string)
            print(f"Template guardado en: {self.args.output}")
            
    def run(self):
        """Ejecuta el generador de templates"""
        self.parse_arguments()
        
        if not self.load_mib():
            sys.exit(1)
            
        self.process_mib_symbols()
        self.generate_template()

def main():
    """Función principal"""
    generator = MIBTemplateGenerator()
    generator.run()

if __name__ == "__main__":
    main()
