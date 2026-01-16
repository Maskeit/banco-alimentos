#!/bin/bash
# Script para probar el endpoint /api/search-in-document

echo "🚀 Probando endpoint /api/search-in-document"
echo "================================================"
echo ""

# Python hace la petición directamente (evita problemas con bash/curl/comillas)
python3 << 'EOF'
import sys
import json
import requests
sys.path.insert(0, '.')
from config import LIST_B_ID, LIST_B_RANGE, DOCUMENT_A_URL

print("Datos a enviar:")
print(f"  • LIST_B_ID: {LIST_B_ID}")
print(f"  • LIST_B_RANGE: {LIST_B_RANGE}")
print(f"  • DOCUMENT_A_URL: {DOCUMENT_A_URL[:60]}...\n")

try:
    response = requests.post(
        "http://127.0.0.1:5000/api/search-in-document",
        json={
            "list_b_id": LIST_B_ID,
            "list_b_range": LIST_B_RANGE,
            "document_a_url": DOCUMENT_A_URL
        },
        timeout=600
    )
    
    print(f"Status: {response.status_code}\n")
    print("Respuesta:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.ConnectionError:
    print("❌ Error: No se puede conectar al servidor")
    print("   Asegúrate de ejecutar: python app.py")
except Exception as e:
    print(f"❌ Error: {e}")
EOF

echo ""
echo "================================================"
echo "✓ Request completado"
echo "Las screenshots se guardarán en: screenshots/"


