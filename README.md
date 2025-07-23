# MIB2ZABBIXPY
AI enhance converter  from mib files to zabbix templates for snmp


Herramienta Python para generar plantillas de Zabbix desde archivos MIB o respuestas SNMP walk. Combina las funcionalidades de `mib2zabbix` (Perl) y `SNMPWALK2ZABBIX` (Python).

## Características

- **Modo MIB**: Genera plantillas directamente desde archivos MIB
- **Modo Walk**: Genera plantillas desde respuestas SNMP walk
- Soporte completo para SNMP v1, v2c y v3
- Configuración avanzada de parámetros de items
- Detección automática de tablas y generación de discovery rules
- Compatible con Zabbix 6.0+
- Obtiene descripciones y nombres desde MIBs automáticamente

## Desarrolladores

- **Basado en trabajos originales de:**
  - Ryan Armstrong - [mib2zabbix](https://github.com/cavaliercoder/mib2zabbix)
  - Sean Bradley - [SNMPWALK2ZABBIX](https://github.com/Sean-Bradley/SNMPWALK2ZABBIX)
- **Implementación Python combinada por:** Assistant AI

## Requisitos del Sistema

### Debian/Ubuntu y derivados:

```bash
# Instalar dependencias
sudo apt update
sudo apt install python3 snmp snmp-mibs-downloader

# Opcional: instalar MIBs adicionales
sudo apt install snmp-mibs-downloader
```

### RedHat/CentOS/Rocky Linux y derivados:

```bash
# Instalar dependencias
sudo yum install python3 net-snmp net-snmp-utils

# O para sistemas con dnf (Fedora, RHEL 8+)
sudo dnf install python3 net-snmp net-snmp-utils

# Instalar MIBs adicionales (opcional)
# Nota: En RHEL/CentOS, las MIBs comerciales pueden requerir repositorios adicionales
```

## Instalación

1. **Descargar el script:**

```bash
wget https://raw.githubusercontent.com/tu-usuario/mib2zabbix-py/master/mib2zabbix-py.py
chmod +x mib2zabbix-py.py
```

2. **(Opcional) Mover a un directorio en el PATH:**

```bash
sudo mv mib2zabbix-py.py /usr/local/bin/mib2zabbix-py
```

## Uso

### Modo básico (SNMP walk):

```bash
# Modo walk - genera plantilla desde dispositivo SNMP
python3 mib2zabbix-py.py --mode walk --ip 192.168.1.1 -o .1.3.6.1.2.1 -c public
```

### Modo MIB (desde archivos MIB):

```bash
# Modo MIB - genera plantilla desde archivos MIB
python3 mib2zabbix-py.py --mode mib -o .1.3.6.1.2.1.1 -N "Mi Template"
```

## Ejemplos detallados

### Ejemplo 1: Generar template desde router usando SNMP v2c

```bash
# Verificar conectividad SNMP primero
snmpwalk -v 2c -c public 192.168.1.1 1.3.6.1.2.1

# Generar template
python3 mib2zabbix-py.py --mode walk --ip 192.168.1.1 -o .1.3.6.1.2.1 -c public -N "Router Template"
```

### Ejemplo 2: Generar template con SNMP v3

```bash
python3 mib2zabbix-py.py --mode walk -v 3 -u myuser -L authPriv -a SHA -A mypass -x AES -X mypriv --ip 192.168.1.1 -o .1.3.1.2.1
```

### Ejemplo 3: Generar template con configuración personalizada

```bash
python3 mib2zabbix-py.py --mode walk --ip 192.168.1.1 -o .1.3.6.1.2.1 \
  -c public \
  --check-delay 30 \
  --disc-delay 1800 \
  --history 30 \
  --trends 365 \
  -N "Servidor Web" \
  -G "Servidores"
```

## Opciones completas

```bash
usage: mib2zabbix-py.py [-h] [--mode {mib,walk}] -o OID [-f FILENAME] [-N NAME] [-G GROUP] [-e] [-v {1,2,3}] [-p PORT] [-c COMMUNITY] [-L {noAuthNoPriv,authNoPriv,authPriv}]
                        [-n CONTEXT] [-u USERNAME] [-a {MD5,SHA}] [-A AUTHPASS] [-x {DES,AES}] [-X PRIVPASS] [--check-delay CHECK_DELAY] [--disc-delay DISC_DELAY]
                        [--history HISTORY] [--trends TRENDS] [--ip IP]

Generate Zabbix template from MIB files or SNMP walk

optional arguments:
  -h, --help            show this help message and exit
  --mode {mib,walk}     Operation mode: mib (from MIB file) or walk (from SNMP walk)
  -o OID, --oid OID     Root OID to process (must start with . for MIB mode)
  -f FILENAME, --filename FILENAME
                        Output filename (default: stdout)
  -N NAME, --name NAME  Template name (default: auto-generated)
  -G GROUP, --group GROUP
                        Template group (default: Templates)
  -e, --enable-items    Enable all template items (default: disabled)
  -v {1,2,3}, --snmpver {1,2,3}
                        SNMP version (default: 2)
  -p PORT, --port PORT  SNMP UDP port number (default: 161)
  -c COMMUNITY, --community COMMUNITY
                        SNMP community string (default: public)
  -L {noAuthNoPriv,authNoPriv,authPriv}, --level {noAuthNoPriv,authNoPriv,authPriv}
                        Security level
  -n CONTEXT, --context CONTEXT
                        Context name
  -u USERNAME, --username USERNAME
                        Security name
  -a {MD5,SHA}, --auth {MD5,SHA}
                        Authentication protocol
  -A AUTHPASS, --authpass AUTHPASS
                        Authentication passphrase
  -x {DES,AES}, --privacy {DES,AES}
                        Privacy protocol
  -X PRIVPASS, --privpass PRIVPASS
                        Privacy passphrase
  --check-delay CHECK_DELAY
                        Check interval in seconds (default: 60)
  --disc-delay DISC_DELAY
                        Discovery interval in seconds (default: 3600)
  --history HISTORY     History retention in days (default: 7)
  --trends TRENDS       Trends retention in days (default: 365)
  --ip IP               IP address for SNMP walk mode
```

## Notas importantes

1. **Los items se generan deshabilitados por defecto** para prevenir sobrecarga del servidor Zabbix
2. **Es recomendable revisar y editar el template generado** antes de importarlo
3. **Asegúrate de que el servidor Zabbix puede acceder al dispositivo SNMP**
4. **Para MIBs propietarias**, colócalas en `/usr/share/snmp/mibs/` o el directorio correspondiente

## Importar template en Zabbix

1. Accede a la interfaz web de Zabbix
2. Ve a **Configuration** → **Templates** → **Import**
3. Selecciona el archivo XML generado
4. Revisa y ajusta los items según sea necesario
5. Habilita los items que requieras monitorear

## Licencia

Este programa es software libre: puedes redistribuirlo y/o modificarlo bajo los términos de la Licencia Pública General GNU publicada por la Free Software Foundation, ya sea la versión 2 de la Licencia, o (a tu elección) cualquier versión posterior.

Este programa se distribuye con la esperanza de que sea útil, pero SIN NINGUNA GARANTÍA; incluso sin la garantía implícita de COMERCIALIZACIÓN o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Ver la Licencia Pública General GNU para más detalles.

---

**Nota:** Este script NO crea automáticamente templates perfectos para todas las necesidades. El template resultante puede ser muy grande y contener muchos items innecesarios. Es tu responsabilidad revisar y editar el resultado según tus necesidades específicas.
