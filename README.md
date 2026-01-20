# Banco de Alimentos

API REST para automatización de procesos del Banco de Alimentos usando Google Sheets, Google Drive y Selenium.

## 🚀 Inicio Rápido

### 1. Activar entorno virtual
```bash
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales de Google
- Coloca tu archivo `credencials.json` en la raíz del proyecto, es lo que contiene un json que empieza con "installed"
- Debe ser una aplicación de escritorio (Desktop app) de Google Cloud Console
- Scopes necesarios:
  - `https://www.googleapis.com/auth/spreadsheets.readonly`
  - `https://www.googleapis.com/auth/drive.file`

### 4. Opción A: Ejecutar API solamente
```bash
python app.py
```

La API estará disponible en `http://127.0.0.1:5000`

### 4. Opción B: Ejecutar con interfaz Streamlit (RECOMENDADO)
**Terminal 1 - Inicia el API:**
```bash
python app.py
```

**Terminal 2 - Inicia Streamlit:**
```bash
streamlit run streamlit_app.py
```

Se abrirá automáticamente en `http://localhost:8501`

**Acceso remoto a Streamlit:**
Si necesitas acceder desde otra máquina:
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Luego accede desde: `http://IP_DE_TU_MAQUINA:8501`

## 🎨 Interfaz Gráfica (Streamlit)

Este proyecto incluye una interfaz web amigable construida con **Streamlit** para simplificar el uso del sistema.

### Características:
- ✅ Formulario intuitivo para configurar búsquedas
- ✅ Validación de campos en tiempo real
- ✅ Prueba de conexión al API
- ✅ Visualización de resultados en tabla
- ✅ Descarga de resultados en JSON
- ✅ Historial de búsquedas
- ✅ Panel de ayuda integrado

### Ejecutar Streamlit:
```bash
# Terminal 1: Inicia el API
python app.py

# Terminal 2: Inicia Streamlit
streamlit run streamlit_app.py
```

Luego abre: **http://localhost:8501**

### Acceso remoto (para múltiples usuarios):
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Acceso desde otro equipo: `http://IP_DE_TU_MAQUINA:8501`

---

## 📋 Endpoints

### `GET /`
Health check del servicio.

### `POST /api/search-in-document` ⭐ (PRINCIPAL - BUSCAR EN DOCUMENTO)
Lee una lista de aliados (lista B) desde un Google Sheet y busca cada nombre en un documento (documento A).
Toma screenshot de cada búsqueda con Cmd+F para generar evidencia visual.

**Casos de uso:**
- Verificar si aliados aparecen en una lista negra o documento
- Generar evidencia visual de búsquedas en documentos grandes
- Automatizar búsquedas manuales con Cmd+F
- Validar presencia de nombres en hojas de cálculo

**Parámetros (Body JSON):**
- `list_b_id` ⭐ (requerido): ID del Google Sheet con la lista de aliados
- `list_b_range` ⭐ (requerido): Rango en formato "nombre_hoja!A2:A" o "nombre_hoja!A11:A20"
- `document_a_url` ⭐ (requerido): URL completa del documento donde buscar (puede ser cualquier URL)
- `auth_wait_seconds` (opcional): Segundos para loguearse manualmente (default: 15 segundos)

**Ejemplo con curl (Terminal):**
```bash
curl -X POST http://127.0.0.1:5000/api/search-in-document \
  -H "Content-Type: application/json" \
  -d '{
    "list_b_id": "1soOnhLz6X4opy0de2r6Z6aomKTxY51VxzbUFfn6XeQA",
    "list_b_range": "abastos!A2:A",
    "document_a_url": "https://docs.google.com/spreadsheets/d/13tZWqVdIUeOeXozdk0V5R4D78bGl8YjAaqNhrrJv4eE/edit",
    "auth_wait_seconds": 20
  }'
```

**Ejemplo con Postman:**
1. Crea una nueva request POST
2. URL: `http://127.0.0.1:5000/api/search-in-document`
3. Tab **Headers**: Agrega `Content-Type: application/json`
4. Tab **Body** → Raw → JSON:
```json
{
  "list_b_id": "1soOnhLz6X4opy0de2r6Z6aomKTxY51VxzbUFfn6XeQA",
  "list_b_range": "abastos!A2:A",
  "document_a_url": "https://docs.google.com/spreadsheets/d/13tZWqVdIUeOeXozdk0V5R4D78bGl8YjAaqNhrrJv4eE/edit",
  "auth_wait_seconds": 20
}
```
5. Click **Send**

**Ejemplo con Python:**
```python
import requests

response = requests.post(
    "http://127.0.0.1:5000/api/search-in-document",
    json={
        "list_b_id": "1soOnhLz6X4opy0de2r6Z6aomKTxY51VxzbUFfn6XeQA",
        "list_b_range": "abastos!A2:A",
        "document_a_url": "https://docs.google.com/spreadsheets/d/13tZWqVdIUeOeXozdk0V5R4D78bGl8YjAaqNhrrJv4eE/edit",
        "auth_wait_seconds": 20
    },
    timeout=600
)

print(response.json())
```

**Response (Ejemplo):**
```json
{
  "status": "completed",
  "total_names": 49,
  "successful": 49,
  "failed": 0,
  "cancelled": false,
  "results": {
    "ADAN DE JESUS SERVIN": {
      "screenshot_path": "screenshots/search_ADAN_DE_JESUS_SERVIN_20260115_143020.png",
      "status": "success",
      "timestamp": "2026-01-15T14:30:20.123456"
    },
    "ADRIAN JESUS MUNOZ": {
      "screenshot_path": "screenshots/search_ADRIAN_JESUS_MUNOZ_20260115_143045.png",
      "status": "success",
      "timestamp": "2026-01-15T14:30:45.789012"
    }
  }
}
```

**Flujo de ejecución:**
1. Se abre Chrome automáticamente y carga el documento
2. Espera X segundos para que te logues manualmente en Google (configurable con `auth_wait_seconds`)
3. Para cada nombre en la lista:
   - Presiona Escape para limpiar búsqueda anterior
   - Presiona Cmd+F para abrir cuadro de búsqueda
   - Escribe el nombre
   - Espera 2 segundos
   - Toma screenshot (aparezca o no el resultado)
   - Guarda en carpeta `screenshots/`
4. Al terminar, cierra el navegador y retorna el resumen

**Notas importantes:**
- Las screenshots se guardan en la carpeta `screenshots/` (se crea automáticamente)
- Cada screenshot incluye timestamp para identificar cuándo se tomó
- Si cancelas con Ctrl+C, el estado retornará `"cancelled": true`
- El tiempo de autenticación es configurable si necesitas más tiempo para loguearte

### `POST /api/compare-lists`
Compara dos listas de Google Sheets, encuentra coincidencias, toma screenshots y los sube a Google Drive.

**Request Body:**
```json
{
  "list_a_id": "1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4",
  "list_a_range": "Sheet1!A:A",
  "list_b_id": "1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4",
  "list_b_range": "Sheet1!B:B",
  "drive_folder": "Coincidencias 2025",
  "search_url_template": "https://www.google.com/search?q={name}"
}
```

**Response:**
```json
{
  "status": "completed",
  "matches_count": 3,
  "matches": ["Juan Pérez", "María García"],
  "successful": 2,
  "failed": 0,
  "results": {
    "Juan Pérez": {
      "screenshot_path": "screenshots/match_Juan_Perez_20251125_143022.png",
      "drive_folder_id": "abc123",
      "drive_file_id": "def456",
      "drive_url": "https://drive.google.com/file/d/...",
      "status": "success"
    }
  }
}
```

### `POST /api/read-sheet`
Lee un rango específico de Google Sheets.

**Request Body:**
```json
{
  "spreadsheet_id": "1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4",
  "range": "Sheet1!A1:B10"
}
```

## 🏗️ Arquitectura

```
banco-alimentos/
├── app.py                          # API REST Flask (entry point)
├── core/
│   ├── quickstart.py              # Script de prueba para Google Sheets
│   └── services/
│       ├── __init__.py
│       ├── google_sheets_service.py   # Leer Google Sheets
│       ├── google_drive_service.py    # Gestión de Drive
│       └── comparison_service.py      # Lógica de comparación
├── screenshots/                    # Screenshots locales (temporal)
├── credencials.json               # Credenciales OAuth2 de Google
└── requirements.txt               # Dependencias Python
```

## 🔧 Servicios

### GoogleSheetsService
- Lee rangos de celdas de Google Sheets
- Obtiene columnas completas
- Accede a metadatos de hojas

### GoogleDriveService
- Crea carpetas en Drive
- Busca carpetas existentes
- Sube archivos (screenshots)

### ComparisonService
- Compara dos listas de Google Sheets
- Toma screenshots con Selenium
- Organiza resultados en Drive por carpetas

## 🔌 Integración con n8n

Desde n8n, usa el nodo **HTTP Request** con:

- **Method**: POST
- **URL**: `http://TU_IP:5000/api/compare-lists`
- **Body Content Type**: JSON
- **Body**:
```json
{
  "list_a_id": "{{ $json.list_a_id }}",
  "list_a_range": "Sheet1!A:A",
  "list_b_id": "{{ $json.list_b_id }}",
  "list_b_range": "Sheet1!B:B",
  "drive_folder": "Resultados {{ $now.format('YYYY-MM-DD') }}"
}
```

## 🔐 Autenticación

La primera vez que ejecutes cualquier servicio que use Google APIs:
1. Se abrirá tu navegador para autorizar la aplicación
2. Asegúrate de usar la cuenta agregada como "test user" en Google Cloud Console
3. Los tokens se guardarán en `core/token.json` y `core/token_drive.json`

Para renovar credenciales, elimina los archivos de token:
```bash
rm core/token*.json
```

## 🐛 Troubleshooting

### Error: "access_denied"
- Agrega tu email como usuario de prueba en Google Cloud Console → OAuth consent screen

### Error: "redirect_uri_mismatch"
- Asegúrate de usar credenciales tipo "Desktop app", no "Web application"

### Error: ModuleNotFoundError
- Activa el entorno virtual: `source selenium/bin/activate`
- Instala dependencias: `pip install -r requirements.txt`

### Selenium no encuentra el navegador
- Este proyecto usa **Chrome WebDriver** (instalado automáticamente con webdriver-manager)
- Chrome se abre automáticamente cuando ejecutas `/api/search-in-document`
- Si tienes problemas, actualiza Chrome a la versión más reciente
