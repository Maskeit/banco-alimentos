# Setup de Sectores en Drive

## Estructura Esperada en Google Drive

```
Banco Alimentos (Carpeta Raíz)
├── abastos/
│   ├── JUAN_RUIZ/
│   │   ├── lista_a_20260125_143052.png
│   │   ├── lista_b_20260125_145030.png
│   │   └── lista_c_20260125_150045.png
│   ├── PEDRO_LOPEZ/
│   ├── MARIA_GARCIA/
│   └── ... (más aliados)
├── campo/
│   ├── ALIADO_1/
│   └── ... (más aliados)
├── pymes/
│   ├── ALIADO_1/
│   └── ... (más aliados)
└── ... (más sectores)
```

## Usar el API para crear sectores

### 1. Crear un sector con aliados

**Endpoint:** `POST /api/drive/setup-sector`

```bash
curl -X POST http://localhost:5000/api/drive/setup-sector \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "abastos",
    "allies": [
      "JUAN_RUIZ",
      "PEDRO_LOPEZ",
      "MARIA_GARCIA",
      "CARLOS_FERNANDEZ"
    ]
  }'
```

**Response:**
```json
{
  "status": "success",
  "sector": "abastos",
  "folder_id": "1ABC123...",
  "parent_folder": "BANCO_ALIMENTOS",
  "created_allies": 4,
  "failed_aliases": []
}
```

### 2. Listar sectores creados

**Endpoint:** `GET /api/drive/sectors`

```bash
curl http://localhost:5000/api/drive/sectors
```

**Response:**
```json
{
  "status": "success",
  "total": 2,
  "sectors": [
    {
      "name": "abastos",
      "folder_id": "1ABC123...",
      "allies_count": 4
    },
    {
      "name": "campo",
      "folder_id": "1XYZ789...",
      "allies_count": 3
    }
  ]
}
```

### 3. Listar aliados de un sector

**Endpoint:** `GET /api/drive/sectors/{sector}/allies`

```bash
curl http://localhost:5000/api/drive/sectors/abastos/allies
```

**Response:**
```json
{
  "status": "success",
  "sector": "abastos",
  "total": 4,
  "allies": [
    {
      "name": "JUAN_RUIZ",
      "folder_id": "1DEF456...",
      "screenshots": []
    },
    {
      "name": "PEDRO_LOPEZ",
      "folder_id": "1GHI789...",
      "screenshots": []
    }
  ]
}
```

## Cómo usar desde Python/Streamlit

```python
import requests

API_URL = "http://localhost:5000"

# Crear sector con aliados
sector_data = {
    "sector": "abastos",
    "allies": ["JUAN_RUIZ", "PEDRO_LOPEZ", "MARIA_GARCIA"]
}

response = requests.post(
    f"{API_URL}/api/drive/setup-sector",
    json=sector_data
)

if response.status_code == 201:
    result = response.json()
    print(f"✅ Sector '{result['sector']}' creado")
    print(f"   Aliados creados: {result['created_allies']}")
    if result['failed_aliases']:
        print(f"   Fallos: {result['failed_aliases']}")
else:
    print(f"❌ Error: {response.json()['message']}")
```

## Pasos para crear todos los sectores

1. **Preparar datos:** Obtener la lista de aliados por sector (CSV o Excel)
2. **Crear sectores:** Llamar POST /api/drive/setup-sector para cada sector
3. **Verificar:** Revisar en Drive que se crearon correctamente
4. **Comenzar búsquedas:** Usar Streamlit para buscar aliados y capturar screenshots

## Metadata guardada localmente

Cuando creas un sector, se guarda metadata en: `~/.banco-alimentos/sectors_index.json`

```json
{
  "abastos": {
    "folder_id": "1ABC123...",
    "parent_folder": "BANCO_ALIMENTOS",
    "allies": {
      "JUAN_RUIZ": {
        "folder_id": null,
        "screenshots": []
      },
      "PEDRO_LOPEZ": {
        "folder_id": null,
        "screenshots": []
      }
    }
  }
}
```


