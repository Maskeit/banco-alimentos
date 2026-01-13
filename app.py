"""
API REST para el sistema Banco de Alimentos.
Expone endpoints para ser consumidos por n8n via webhooks.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.services import (
    GoogleSheetsService, 
    GoogleDriveService, 
    ComparisonService,
)

app = Flask(__name__)
CORS(app)  # Habilitar CORS para n8n

# Inicializar servicios (se reutilizan entre requests)
sheets_service = GoogleSheetsService()
drive_service = GoogleDriveService()
comparison_service = ComparisonService(sheets_service, drive_service)


@app.route('/', methods=['GET'])
def health_check():
    """Endpoint de health check."""
    return jsonify({
        'status': 'ok',
        'service': 'Banco de Alimentos API',
        'version': '1.0.0'
    })


@app.route('/api/compare-lists', methods=['POST'])
def compare_lists():
    """
    Endpoint para comparar dos listas de Google Sheets con screenshots.
    
    Request Body (JSON):
    {
        "list_a_id": "ID_o_URL_de_Google_Sheets_A",
        "list_a_range": "Sheet1!A:A",
        "list_b_id": "ID_o_URL_de_Google_Sheets_B",
        "list_b_range": "Sheet1!B:B",
        "drive_folder": "Nombre de carpeta o ID/URL de carpeta Drive (opcional)",
        "search_url_template": "https://example.com/search?q={name} (opcional)"
    }
    
    Response:
    {
        "status": "completed",
        "matches_count": 3,
        "matches": ["nombre1", "nombre2", "nombre3"],
        "successful": 3,
        "failed": 0,
        "results": {...}
    }
    """
    try:
        # Validar request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No se recibieron datos JSON'
            }), 400
        
        # Validar campos requeridos
        required_fields = ['list_a_id', 'list_a_range', 'list_b_id', 'list_b_range']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            }), 400
        
        # Extraer parámetros
        list_a_id = data['list_a_id']
        list_a_range = data['list_a_range']
        list_b_id = data['list_b_id']
        list_b_range = data['list_b_range']
        drive_folder = data.get('drive_folder', 'Banco Alimentos - Coincidencias')
        search_url_template = data.get('search_url_template', None)
        
        print(f"\n{'='*60}")
        print(f"Nueva solicitud recibida de n8n")
        print(f"Lista A: {list_a_id} - {list_a_range}")
        print(f"Lista B: {list_b_id} - {list_b_range}")
        print(f"{'='*60}\n")
        
        # Ejecutar workflow
        result = comparison_service.run_comparison_workflow(
            list_a_id=list_a_id,
            list_a_range=list_a_range,
            list_b_id=list_b_id,
            list_b_range=list_b_range,
            drive_folder=drive_folder,
            search_url_template=search_url_template
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"❌ Error en endpoint: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/read-sheet', methods=['POST'])
def read_sheet():
    """
    Endpoint para leer un rango de Google Sheets.
    
    Request Body (JSON):
    {
        "spreadsheet_id": "ID_de_Google_Sheets",
        "range": "Sheet1!A:B"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'spreadsheet_id' not in data or 'range' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Se requieren spreadsheet_id y range'
            }), 400
        
        values = sheets_service.read_range(data['spreadsheet_id'], data['range'])
        
        return jsonify({
            'status': 'success',
            'row_count': len(values),
            'values': values
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Iniciando Banco de Alimentos API")
    print("="*60)
    print("Endpoints disponibles:")
    print("  GET  /                     - Health check")
    print("  POST /api/compare-lists    - Comparar listas y procesar coincidencias")
    print("  POST /api/read-sheet       - Leer datos de Google Sheets")
    print("="*60 + "\n")
    
    # Ejecutar servidor Flask
    # Para desarrollo: host='127.0.0.1', debug=True
    # Para producción con n8n: host='0.0.0.0', debug=False
    app.run(host='127.0.0.1', port=5000, debug=True)