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

from core.services import GoogleSheetsService, GoogleDriveService, ComparisonService
from config import API_HOST, API_PORT, API_DEBUG
from routes.drive_routes import drive_bp

app = Flask(__name__)
CORS(app)

# Registrar blueprints
app.register_blueprint(drive_bp)

# ════════════════════════════════════════════════════════════════
# FLAG GLOBAL PARA DETENER BÚSQUEDA
# ════════════════════════════════════════════════════════════════
search_stop_event = threading.Event()

sheets_service = GoogleSheetsService()
drive_service = GoogleDriveService()
comparison_service = ComparisonService(sheets_service, drive_service)
comparison_service.set_stop_event(search_stop_event)


@app.route('/', methods=['GET'])
def health_check():
    """Health check del servicio."""
    print("✅ GET /")
    return jsonify({'status': 'ok', 'service': 'Banco de Alimentos API', 'version': '1.0.0'})


@app.route('/api/search-in-document', methods=['POST'])
def search_in_document():
    """
    Busca nombres de una lista en un Google Sheet.
    Lee la lista B (aliados) y busca cada nombre en el documento A con Cmd+F.
    Toma screenshot de cada búsqueda y guarda en carpeta local.
    
    Body JSON esperado:
    {
        "list_b_id": "ID_DEL_GOOGLE_SHEET",
        "list_b_range": "nombre_hoja!A2:A",
        "document_a_url": "https://...",
        "auth_wait_seconds": 15  (opcional - segundos para loguearse)
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
        auth_wait_seconds = data.get('auth_wait_seconds', None)  # Opcional
        
        print(f"\n{'='*60}")
        print(f"Nueva solicitud de búsqueda recibida")
        print(f"Lista B: {list_b_id}")
        print(f"Rango: {list_b_range}")
        print(f"Documento A: {document_a_url[:80]}...")
        if auth_wait_seconds:
            print(f"Tiempo de autenticación: {auth_wait_seconds}s")
        print(f"{'='*60}\n")
        
        result = comparison_service.search_names_in_document(
            list_b_id=list_b_id,
            list_b_range=list_b_range,
            document_a_url=document_a_url,
            auth_wait_seconds=auth_wait_seconds
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"❌ Error en endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/read-sheet', methods=['POST'])
def read_sheet():
    """Leer un rango de Google Sheets."""
    print("\n" + "="*60)
    print("📊 Petición: POST /api/read-sheet")
    
    try:
        data = request.get_json()
        
        if not data or 'spreadsheet_id' not in data or 'range' not in data:
            print("❌ Parámetros faltantes")
            return jsonify({'status': 'error', 'message': 'Se requieren spreadsheet_id y range'}), 400
        
        print(f"ID: {data['spreadsheet_id'][:50]}...")
        print(f"Rango: {data['range']}")
        
        values = sheets_service.read_range(data['spreadsheet_id'], data['range'])
        
        print(f"✅ Éxito - {len(values)} filas leídas")
        return jsonify({'status': 'success', 'row_count': len(values), 'values': values}), 200
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/reload-credentials', methods=['POST'])
def reload_credentials():
    """Recarga las credenciales sin reiniciar la aplicación."""
    global sheets_service, drive_service, comparison_service
    
    print(f"\n{'='*60}")
    print("🔄 Petición: POST /api/reload-credentials")
    print(f"{'='*60}")
    
    try:
        sheets_service = GoogleSheetsService()
        drive_service = GoogleDriveService()
        comparison_service = ComparisonService(sheets_service, drive_service)
        comparison_service.set_stop_event(search_stop_event)
        
        print("✅ Credenciales recargadas exitosamente")
        return jsonify({'status': 'success', 'message': 'Credenciales recargadas'}), 200
    except Exception as e:
        print(f"❌ Error al recargar credenciales: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stop-search', methods=['POST'])
def stop_search():
    """Detiene la búsqueda en progreso."""
    global search_stop_event
    
    print(f"\n{'='*60}")
    print("🛑 Petición: POST /api/stop-search")
    print("Deteniendo búsqueda...")
    print(f"{'='*60}")
    
    search_stop_event.set()
    return jsonify({'status': 'success', 'message': 'Búsqueda detenida'}), 200


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Iniciando Banco de Alimentos API")
    print("="*60)
    print("Endpoints disponibles:")
    print("\n🔍 BÚSQUEDA:")
    print("  POST /api/search-in-document - Buscar aliados en documento")
    print("  POST /api/stop-search        - Detener búsqueda")
    print("\n📊 GOOGLE SHEETS:")
    print("  POST /api/read-sheet         - Leer datos de Google Sheets")
    print("  POST /api/reload-credentials - Recargar credenciales")
    print("\n💾 GOOGLE DRIVE:")
    print("  GET  /api/drive/sectors      - Listar sectores")
    print("  GET  /api/drive/sectors/<sector>/allies - Listar aliados")
    print("  POST /api/drive/setup-sector - Crear sector + aliados")
    print("  POST /api/drive/sectors/<sector>/create-allies - Agregar aliados")
    print("  POST /api/drive/sectors/<sector>/upload - Subir screenshots")
    print("="*60)
    print(f"\n📍 Servidor: http://{API_HOST}:{API_PORT}")
    print(f"🔧 Debug: {API_DEBUG}\n")
    
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)
