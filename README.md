# Banco de Alimentos

API REST para automatización de procesos del Banco de Alimentos usando Google Sheets, Google Drive y Selenium.

## 🚀 Inicio Rápido

### 1. Activar entorno virtual
```bash
source selenium/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales de Google
- Coloca tu archivo `credencials.json` en la raíz del proyecto
- Debe ser una aplicación de escritorio (Desktop app) de Google Cloud Console
- Scopes necesarios:
  - `https://www.googleapis.com/auth/spreadsheets.readonly`
  - `https://www.googleapis.com/auth/drive.file`

### 4. Ejecutar API
```bash
python app.py
```

La API estará disponible en `http://127.0.0.1:5000`

## 📋 Endpoints

### `GET /`
Health check del servicio.

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
- Este proyecto usa Safari WebDriver (macOS)
- Para otros navegadores, instala el driver correspondiente (ChromeDriver, GeckoDriver)
