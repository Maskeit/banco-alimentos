"""
API REST para el sistema Banco de Alimentos.
Expone endpoints para buscar aliados en documentos y leer Google Sheets.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.services import GoogleSheetsService, ComparisonService, clean_tokens
from config import API_HOST, API_PORT, API_DEBUG

app = Flask(__name__)
CORS(app)

# ════════════════════════════════════════════════════════════════
# FLAG GLOBAL PARA DETENER BÚSQUEDA
# ════════════════════════════════════════════════════════════════
search_stop_event = threading.Event()

sheets_service = GoogleSheetsService()
comparison_service = ComparisonService(sheets_service)
comparison_service.set_stop_event(search_stop_event)


@app.route('/', methods=['GET'])
def health_check():
    """Health check del servicio."""
    return jsonify({'status': 'ok', 'service': 'Banco de Alimentos API', 'version': '1.0.0'})


@app.route('/api/search-in-document', methods=['POST'])
def search_in_document():
    """
    Busca nombres de una lista en un Google Sheet.
    Lee la lista B (aliados) y busca cada nombre en el documento A con Ctrl+F.
    Toma screenshot de cada búsqueda y guarda en carpeta local.

    Body JSON esperado:
    {
        "list_b_id": "ID_DEL_GOOGLE_SHEET",
        "list_b_range": "nombre_hoja!A2:A",
        "document_a_url": "https://...",
        "auth_wait_seconds": 15,
        "filename_prefix": "sat"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'status': 'error', 'message': 'No se recibieron datos JSON'}), 400

        required_fields = ['list_b_id', 'list_b_range', 'document_a_url']
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            return jsonify({'status': 'error', 'message': f'Campos faltantes: {", ".join(missing_fields)}'}), 400

        list_b_id = data['list_b_id']
        list_b_range = data['list_b_range']
        document_a_url = data['document_a_url']
        auth_wait_seconds = data.get('auth_wait_seconds', None)

        print(f"\n{'='*60}")
        print(f"Nueva solicitud de búsqueda recibida")
        print(f"Lista B: {list_b_id}")
        print(f"Rango: {list_b_range}")
        print(f"Documento A: {document_a_url[:80]}...")
        if auth_wait_seconds:
            print(f"Tiempo de autenticación: {auth_wait_seconds}s")
        print(f"{'='*60}\n")

        # Limpiar stop_event antes de iniciar nueva búsqueda
        search_stop_event.clear()

        result = comparison_service.search_names_in_document(
            list_b_id=list_b_id,
            list_b_range=list_b_range,
            document_a_url=document_a_url,
            auth_wait_seconds=auth_wait_seconds,
            filename_prefix=data.get('filename_prefix', 'search')
        )

        return jsonify(result), 200

    except Exception as e:
        print(f"Error en endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/read-sheet', methods=['POST'])
def read_sheet():
    """Leer un rango de Google Sheets."""
    try:
        data = request.get_json()

        if not data or 'spreadsheet_id' not in data or 'range' not in data:
            return jsonify({'status': 'error', 'message': 'Se requieren spreadsheet_id y range'}), 400

        values = sheets_service.read_range(data['spreadsheet_id'], data['range'])

        return jsonify({'status': 'success', 'row_count': len(values), 'values': values}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/reload-credentials', methods=['POST'])
def reload_credentials():
    """Recarga las credenciales limpiando el token y recreando servicios."""
    global sheets_service, comparison_service

    print(f"\n{'='*60}")
    print("Peticion: POST /api/reload-credentials")
    print(f"{'='*60}")

    try:
        clean_tokens()
        print("Token limpiado")

        sheets_service = GoogleSheetsService()
        comparison_service = ComparisonService(sheets_service)
        comparison_service.set_stop_event(search_stop_event)

        print("Credenciales recargadas exitosamente")
        return jsonify({'status': 'success', 'message': 'Credenciales recargadas'}), 200
    except Exception as e:
        print(f"Error al recargar credenciales: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stop-search', methods=['POST'])
def stop_search():
    """Detiene la búsqueda en progreso."""
    search_stop_event.set()
    return jsonify({'status': 'success', 'message': 'Búsqueda detenida'}), 200


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Iniciando Banco de Alimentos API")
    print("="*60)
    print("Endpoints disponibles:")
    print("  GET  /                        - Health check")
    print("  POST /api/search-in-document  - Buscar aliados en documento")
    print("  POST /api/stop-search         - Detener búsqueda")
    print("  POST /api/read-sheet          - Leer datos de Google Sheets")
    print("  POST /api/reload-credentials  - Recargar credenciales")
    print("="*60)
    print(f"\nServidor: http://{API_HOST}:{API_PORT}")
    print(f"Debug: {API_DEBUG}\n")

    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)
