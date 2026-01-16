#!/usr/bin/env python3
"""
Script de prueba para el endpoint /api/search-in-document
Uso: python test_search_endpoint.py

NOTA: Los parámetros se cargan automáticamente de config.py
"""
import requests
import json
from datetime import datetime
from config import (
    API_HOST, 
    API_PORT, 
    LIST_B_ID, 
    LIST_B_RANGE, 
    DOCUMENT_A_URL
)

# URL del API local (construida desde config)
API_URL = f"http://{API_HOST}:{API_PORT}"


def test_search_endpoint():
    """Prueba el endpoint de búsqueda."""
    
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL ENDPOINT /api/search-in-document")
    print("="*60 + "\n")
    
    # Preparar payload
    payload = {
        "list_b_id": LIST_B_ID,
        "list_b_range": LIST_B_RANGE,
        "document_a_url": DOCUMENT_A_URL
    }
    
    print("📤 Enviando request...")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        # Hacer request
        response = requests.post(
            f"{API_URL}/api/search-in-document",
            json=payload,
            timeout=600  # 10 minutos de timeout (porque toma screenshots)
        )
        
        # Mostrar resultado
        print(f"Status Code: {response.status_code}\n")
        
        result = response.json()
        
        print("📊 RESULTADO:")
        print(json.dumps(result, indent=2))
        
        # Resumen
        if result.get('status') == 'completed':
            print("\n" + "="*60)
            print("✅ ÉXITO")
            print("="*60)
            print(f"Total procesados: {result.get('successful', 0)} / {result.get('total_names', 0)}")
            
            if result.get('results'):
                print("\n📸 Screenshots generadas:")
                for name, data in result['results'].items():
                    if data.get('status') == 'success':
                        print(f"  ✓ {name}: {data.get('screenshot_path')}")
                    else:
                        print(f"  ✗ {name}: {data.get('error', 'Error desconocido')}")
        else:
            print("\n⚠️  Error en la respuesta")
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor")
        print(f"   Asegúrate de que la API está corriendo en {API_URL}")
        print("   Ejecuta: python app.py")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_search_endpoint()
