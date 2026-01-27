"""
CONFIGURACIÓN CENTRALIZADA
===========================

Archivo para almacenar todas las variables de configuración.
Modifica aquí los IDs, rangos y URLs cuando necesites cambiar de archivos.

Actualizado: 14 de enero de 2026
"""

# ════════════════════════════════════════════════════════════════
# LISTA B - ALIADOS (La lista de nombres a buscar)
# ════════════════════════════════════════════════════════════════

# ID del Google Sheet con la lista de aliados
DOCUMENT_B_URL = 'https://docs.google.com/spreadsheets/d/1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4/edit?gid=1132855930#gid=1132855930'
LIST_B_ID = "1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4"

# Nombre de la hoja (sheet) dentro del Google Sheet
# NOTA: Si tiene espacios o caracteres especiales, se ponen entre comillas simples
LIST_B_SHEET_NAME = "'Razón Social'"  # CON COMILLAS porque tiene acentos

# Rango de celdas donde están los nombres
# Usa el formato exacto de Google Sheets API
LIST_B_RANGE = "abastos!A2:A"  # Cámbialo a tu nombre de hoja real

# ════════════════════════════════════════════════════════════════
# LISTA A - DOCUMENTO SAT (Donde buscar)
# ════════════════════════════════════════════════════════════════

# URL completa del documento donde buscar
# Puede ser Google Sheets, Google Docs, o cualquier URL
DOCUMENT_A_URL = "https://docs.google.com/spreadsheets/d/1caM1BHP1yhiihKtjXdGBrKs0YiwawiIQ1w26xRpsZlU/edit?gid=36637328#gid=36637328"

# ID del Google Sheet (se extrae automáticamente de la URL si lo necesitas)
DOCUMENT_A_ID = "1caM1BHP1yhiihKtjXdGBrKs0YiwawiIQ1w26xRpsZlU"
# ════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CAPTURAS (Screenshots)
# ════════════════════════════════════════════════════════════════

# Directorio donde guardar las screenshots
SCREENSHOTS_DIR = "screenshots"

# ════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL API
# ════════════════════════════════════════════════════════════════

# Host y puerto del servidor Flask
API_HOST = "127.0.0.1"
API_PORT = 5000
API_DEBUG = True

# ════════════════════════════════════════════════════════════════
# CREDENCIALES
# ════════════════════════════════════════════════════════════════

from pathlib import Path
import os

# Carpeta de datos del usuario (fuera del código, resistente a actualizaciones)
USER_DATA_DIR = Path.home() / ".banco-alimentos"
USER_DATA_DIR.mkdir(exist_ok=True)

# Rutas a los archivos de credenciales (en carpeta de datos)
CREDENTIALS_FILE = USER_DATA_DIR / "credentials.json"
SHEETS_TOKEN_FILE = USER_DATA_DIR / "token.json"
DRIVE_TOKEN_FILE = USER_DATA_DIR / "token_drive.json"

# ════════════════════════════════════════════════════════════════
# GOOGLE DRIVE - ESTRUCTURA DE CARPETAS
# ════════════════════════════════════════════════════════════════

# Carpeta raíz del Banco de Alimentos en Drive
# Obtén el ID de la URL: https://drive.google.com/drive/folders/AQUI_ESTA_EL_ID
BANCO_ALIMENTOS_FOLDER_ID = "1_f_RkuvXo41ahx4lQ_F1YD5LG5LCgOtu"

# La estructura será:
# BANCO_ALIMENTOS/
#   ├── abastos/
#   │   ├── ALIADO_1/
#   │   │   ├── lista_a_20260125.png
#   │   │   ├── lista_b_20260125.png
#   │   │   └── lista_c_20260125.png
#   │   └── ALIADO_2/
#   ├── campo/
#   ├── pymes/
#   └── ...

# ════════════════════════════════════════════════════════════════
# NAVEGADOR
# ════════════════════════════════════════════════════════════════

# Tipo de navegador para Selenium (Safari, Chrome, Firefox)
BROWSER_TYPE = "Chrome"  # Chrome es más fácil de usar con Selenium

# Tamaño de ventana (fijo para evitar problemas con monitores ultrawide)
BROWSER_WIDTH = 1280
BROWSER_HEIGHT = 800

# Timeout para cargar páginas (segundos)
BROWSER_TIMEOUT = 30

# Pausa después de búsqueda (segundos)
SEARCH_PAUSE = 4

# Tiempo de espera para autenticación manual (segundos)
# Aumenta esto si necesitas más tiempo para loguearte en Google
AUTH_WAIT_SECONDS = 20  # 15 segundos es suficiente para loguearse

# ════════════════════════════════════════════════════════════════
# LOGGING
# ════════════════════════════════════════════════════════════════

# Nivel de log (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# ════════════════════════════════════════════════════════════════
# EJEMPLOS DE CÓMO CAMBIAR CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════

"""
SI CAMBIAS DE LISTA DE ALIADOS:
═══════════════════════════════

1. Abre el nuevo Google Sheet de aliados
2. Copia su ID de la URL: https://docs.google.com/spreadsheets/d/AQUI_ESTA_EL_ID/edit
3. Reemplaza LIST_B_ID con el nuevo ID
4. Ajusta LIST_B_SHEET_NAME y LIST_B_RANGE si es necesario

IMPORTANTE: Si el nombre de la hoja tiene:
  - Espacios           → Envuelve en comillas simples: 'Mis Datos'
  - Acentos (á, é, í)  → Envuelve en comillas simples: 'Razón Social'
  - Caracteres especiales → Envuelve en comillas simples: 'Mi@Hoja!'
  
Sin espacios ni caracteres especiales → Sin comillas: MiDatos


SI CAMBIAS EL DOCUMENTO DONDE BUSCAR:
════════════════════════════════════

1. Abre el Google Sheet del SAT
2. Copia la URL completa de la dirección
3. Reemplaza DOCUMENT_A_URL con la nueva URL


EJEMPLO DE CAMBIO COMPLETO:
═══════════════════════════

# Antes:
LIST_B_ID = "1soOnhLz6X4opy0de2r6Z6aomKTxY51VxzbUFfn6XeQA"
LIST_B_SHEET_NAME = "'Razón Social'"
LIST_B_RANGE = "'Razón Social'!A2:A"

# Después (con otro archivo):
LIST_B_ID = "1NUEVO_ID_AQUI_1234567890"
LIST_B_SHEET_NAME = "'Nombres de Aliados'"  # Si se llama diferente
LIST_B_RANGE = "'Nombres de Aliados'!A1:A"  # Si el rango es diferente
"""
