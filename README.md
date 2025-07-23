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

## Uso con Visual Studio Code en Windows

### Requisitos previos

1. **Instalar Python 3**:
   - Descarga Python desde [python.org](https://www.python.org/downloads/)
   - Durante la instalación, marca "Add Python to PATH"

2. **Instalar Visual Studio Code**:
   - Descarga VS Code desde [code.visualstudio.com](https://code.visualstudio.com/)

3. **Instalar extensiones recomendadas en VS Code**:
   - Python (por Microsoft)
   - Pylint (para análisis de código)

4. **Instalar Net-SNMP para Windows**:
   - Descarga Net-SNMP desde [sourceforge.net/projects/net-snmp](https://sourceforge.net/projects/net-snmp/)
   - Durante la instalación, selecciona agregar al PATH
   - Asegúrate de que los MIBs estén correctamente configurados

### Configuración del entorno

1. **Abrir VS Code** y crear una nueva carpeta para el proyecto

2. **Crear un entorno virtual** (opcional pero recomendado):
   ```bash
   python -m venv snmp_env
   # En Windows PowerShell:
   .\snmp_env\Scripts\Activate.ps1
   # En Símbolo del sistema:
   snmp_env\Scripts\activate.bat
   ```

3. **Descargar el script**:
   ```bash
   # Usando curl (si está disponible)
   curl -O https://raw.githubusercontent.com/tu-usuario/mib2zabbix-py/master/mib2zabbix-py.py
   
   # O copia el código directamente en un nuevo archivo llamado mib2zabbix-py.py
   ```

4. **Verificar instalación de SNMP**:
   ```bash
   snmpwalk -V
   ```

### Ejecución en VS Code

1. **Abrir el terminal en VS Code**:
   - `Terminal` → `New Terminal`

2. **Ejecutar el script**:
   ```bash
   # Modo walk básico
   python mib2zabbix-py.py --mode walk --ip 192.168.1.1 -o .1.3.6.1.2.1 -c public

   # Con opciones personalizadas
   python mib2zabbix-py.py --mode walk --ip 192.168.1.1 -o .1.3.6.1.2.1 -c public -N "Mi Router" --check-delay 30
   ```

### Configuración de depuración en VS Code

1. **Crear archivo `.vscode/launch.json`**:
   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Generar Template SNMP",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/mib2zabbix-py.py",
               "args": [
                   "--mode", "walk",
                   "--ip", "192.168.1.1",
                   "-o", ".1.3.6.1.2.1",
                   "-c", "public"
               ],
               "console": "integratedTerminal"
           }
       ]
   }
   ```

2. **Ejecutar con depuración**:
   - Presiona `F5` o ve a `Run` → `Start Debugging`

### Notas importantes para Windows

- **Permisos de red**: Asegúrate de que Windows Firewall no bloquee las conexiones SNMP
- **Formato de rutas**: Usa barras diagonales `/` o doble barra invertida `\\` en las rutas
- **Codificación**: Guarda los archivos con codificación UTF-8
- **MIBs personalizados**: Colócalos en `C:\usr\share\snmp\mibs\` o configura la variable de entorno `MIBDIRS`

### Solución de problemas comunes

**Error: "snmpwalk is not recognized"**
- Verifica que Net-SNMP esté en el PATH
- Reinicia VS Code después de instalar Net-SNMP

**Error: "No MIBs found"**
- Verifica que las MIBs estén en el directorio correcto
- Ejecuta `snmptranslate -D YOUR_OID` para diagnosticar problemas de MIB

**Error de codificación**
- En el terminal de VS Code, ejecuta: `chcp 65001` para establecer UTF-8

¡Claro! Aquí tienes una **sección adicional para tu `README.md`** que explica cómo usar el script `snmpwalk2zabbix.py` desde **Visual Studio Code (VSCode)** en un entorno **Windows**, incluyendo la instalación de dependencias, configuración del entorno y ejecución paso a paso.

---

## ✅ Uso con Visual Studio Code en Windows modo 2

### 🛠 Requisitos previos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

- [Python 3.x](https://www.python.org/downloads/)
- [Git for Windows](https://git-scm.com/download/win) *(opcional, pero útil para clonar repositorios)*
- [Visual Studio Code](https://code.visualstudio.com/) con las extensiones recomendadas:
  - Python (por Microsoft)
  - Pylance
  - Jupyter (si planeas ejecutar celdas interactivas)

---

### 🔧 Configuración del entorno

1. **Instalar Python en Windows:**

   - Descarga e instala Python desde [python.org](https://www.python.org/downloads/).
   - Durante la instalación, **asegúrate de marcar la opción "Add Python to PATH"**.
   - Verifica la instalación abriendo un terminal (CMD o PowerShell) y ejecutando:
     ```bash
     python --version
     ```

2. **Instalar `net-snmp-utils` para Windows:**

   Este paquete contiene las herramientas necesarias como `snmpwalk` y `snmptranslate`.

   - Puedes instalarlo usando [Chocolatey](https://chocolatey.org/install):
     ```bash
     choco install net-snmp
     ```
   - O bien, descarga manualmente desde [Net-SNMP for Windows](https://sourceforge.net/projects/net-snmp/files/).

3. **Configurar MIBs (opcional pero recomendado):**

   Si planeas obtener descripciones legibles de los OID, debes tener las MIBs descargadas.

   - Instala `snmp-mibs-downloader` (requiere Git y Python):
     ```bash
     pip install snmp-mibs-downloader
     mibs download
     ```
   - Asegúrate de que la variable de entorno `MIBS` apunte al directorio donde se guardaron las MIBs.

---

### 📁 Clonar el proyecto en VSCode

1. Abre Visual Studio Code.
2. Ve a **File > Open Folder** y crea un nuevo directorio para el proyecto.
3. Abre el **Terminal integrado** (`Ctrl + ``) y clona el repositorio:
   ```bash
   git clone https://github.com/tu-repo/snmpwalk2zabbix.git
   cd snmpwalk2zabbix
   ```

4. Abre el archivo `snmpwalk2zabbix.py` en el editor.

---

### 🧪 Ejecutar el script en VSCode

1. Asegúrate de que el entorno tiene acceso a las herramientas SNMP:
   ```bash
   snmpwalk -v 2c -c public 127.0.0.1 .1.3.6.1.2.1
   ```
   Esto verificará si `snmpwalk` está disponible.

2. Ejecuta el script directamente desde el terminal integrado:
   ```bash
   python snmpwalk2zabbix.py public 192.168.1.1 1.3.6.1.2.1
   ```

   Donde:
   - `public`: comunidad SNMP.
   - `192.168.1.1`: dirección IP del dispositivo SNMP.
   - `1.3.6.1.2.1`: OID base (puedes ajustarlo según tus necesidades).

3. El script generará un archivo XML en el mismo directorio, por ejemplo:
   ```
   template-my-template.xml
   ```

---

### 📤 Importar el Template a Zabbix

1. Inicia sesión en la interfaz web de Zabbix.
2. Ve a **Configuration > Templates > Import**.
3. Selecciona el archivo `.xml` generado.
4. Revisa los items y discovery rules y habilita solo los que necesitas.
5. ¡Listo! Ya puedes usar el template con tus dispositivos.

---

### 💡 Consejos Adicionales

- Usa la extensión **Python** de VSCode para obtener soporte de autocompletado y depuración.
- Puedes crear un **script de lote (.bat)** para automatizar llamadas frecuentes al script.
- Si trabajas con dispositivos SNMP v3, agrega parámetros adicionales como `-u`, `-L`, `-a`, etc., como se muestra en el ejemplo:
  ```bash
  python snmpwalk2zabbix.py -u myuser -L authPriv -a SHA -A mypass -x AES -X mypriv 192.168.1.1 1.3.6.1.2.1
  ```

---

### ❗ Nota Final

Este script es una herramienta de ayuda, no genera automáticamente templates perfectos. Es importante revisar y personalizar los items y reglas de descubrimiento antes de importarlos a Zabbix.

¿Quieres que te ayude también a crear un script de lote (`.bat`) para facilitar su uso en Windows?

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
