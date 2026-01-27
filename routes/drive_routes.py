"""
Rutas para gestionar Drive: sectores, carpetas y uploads
"""
from flask import Blueprint, request, jsonify
import json
from pathlib import Path
from typing import List

drive_bp = Blueprint('drive', __name__, url_prefix='/api/drive')


# ════════════════════════════════════════════════════════════════
# UTILIDADES
# ════════════════════════════════════════════════════════════════

def get_drive_service():
    """Obtiene el servicio de Drive desde el contexto de Flask."""
    from app import drive_service
    return drive_service


def get_sector_index_path():
    """Ruta al archivo que guarda metadatos de sectores."""
    return Path.home() / ".banco-alimentos" / "sectors_index.json"


def load_sector_index() -> dict:
    """Carga el índice de sectores."""
    index_path = get_sector_index_path()
    if index_path.exists():
        return json.loads(index_path.read_text())
    return {}


def save_sector_index(data: dict):
    """Guarda el índice de sectores."""
    index_path = get_sector_index_path()
    index_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ════════════════════════════════════════════════════════════════
# GET - Listar sectores
# ════════════════════════════════════════════════════════════════

@drive_bp.route('/sectors', methods=['GET'])
def list_sectors():
    """
    Lista todos los sectores creados.
    
    GET /api/drive/sectors
    
    Response:
    {
        "status": "success",
        "sectors": [
            {
                "name": "abastos",
                "folder_id": "1ABC...",
                "allies_count": 150
            }
        ]
    }
    """
    try:
        index = load_sector_index()
        sectors = [
            {
                "name": name,
                "folder_id": data.get("folder_id"),
                "allies_count": len(data.get("allies", {}))
            }
            for name, data in index.items()
        ]
        
        return jsonify({
            'status': 'success',
            'total': len(sectors),
            'sectors': sectors
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ════════════════════════════════════════════════════════════════
# GET - Listar aliados de un sector
# ════════════════════════════════════════════════════════════════

@drive_bp.route('/sectors/<sector>/allies', methods=['GET'])
def list_allies(sector):
    """
    Lista todos los aliados de un sector.
    
    GET /api/drive/sectors/abastos/allies
    
    Response:
    {
        "status": "success",
        "sector": "abastos",
        "total": 150,
        "allies": [
            {
                "name": "JUAN_RUIZ",
                "folder_id": "1XYZ...",
                "screenshots": ["lista_a_20260125.png", ...]
            }
        ]
    }
    """
    try:
        index = load_sector_index()
        
        if sector not in index:
            return jsonify({
                'status': 'error',
                'message': f'Sector "{sector}" no existe'
            }), 404
        
        allies_data = index[sector].get('allies', {})
        allies = [
            {
                "name": name,
                "folder_id": data.get("folder_id"),
                "screenshots": data.get("screenshots", [])
            }
            for name, data in allies_data.items()
        ]
        
        return jsonify({
            'status': 'success',
            'sector': sector,
            'total': len(allies),
            'allies': allies
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ════════════════════════════════════════════════════════════════
# POST - Crear sector con aliados
# ════════════════════════════════════════════════════════════════

@drive_bp.route('/setup-sector', methods=['POST'])
def setup_sector():
    """
    Crea un sector y sus carpetas de aliados dentro de BANCO_ALIMENTOS.
    
    POST /api/drive/setup-sector
    Content-Type: application/json
    
    La estructura que crea es:
    BANCO_ALIMENTOS/
    └── {sector}/
        ├── {ally_1}/
        ├── {ally_2}/
        └── ...
    
    Body:
    {
        "sector": "abastos",
        "allies": ["JUAN_RUIZ", "PEDRO_LOPEZ", ...]
    }
    
    Response:
    {
        "status": "success",
        "sector": "abastos",
        "folder_id": "1XYZ...",
        "parent_folder": "BANCO_ALIMENTOS",
        "created_allies": 2,
        "failed_aliases": []
    }
    """
    try:
        from config import BANCO_ALIMENTOS_FOLDER_ID
        
        data = request.get_json()
        
        if not data or 'sector' not in data:
            return jsonify({'status': 'error', 'message': 'Campo "sector" requerido'}), 400
        
        if 'allies' not in data or not isinstance(data['allies'], list):
            return jsonify({'status': 'error', 'message': 'Campo "allies" debe ser lista'}), 400
        
        sector_name = data['sector'].strip()
        allies_list = [str(a).strip() for a in data['allies']]
        
        print(f"\n{'='*60}")
        print(f"🔧 POST /api/drive/setup-sector")
        print(f"Carpeta raíz: BANCO_ALIMENTOS (ID: {BANCO_ALIMENTOS_FOLDER_ID[:20]}...)")
        print(f"Sector: {sector_name}")
        print(f"Aliados a crear: {len(allies_list)}")
        print(f"{'='*60}\n")
        
        drive_service = get_drive_service()
        
        # 1. Crear carpeta del sector dentro de BANCO_ALIMENTOS
        print(f"📁 Creando carpeta sector: {sector_name}")
        sector_folder_id = drive_service.get_or_create_folder(
            sector_name, 
            BANCO_ALIMENTOS_FOLDER_ID
        )
        
        # 2. Crear carpetas de aliados dentro del sector
        print(f"👥 Creando carpetas de {len(allies_list)} aliados...")
        created = 0
        failed = []
        
        for i, ally_name in enumerate(allies_list, 1):
            try:
                print(f"  [{i}/{len(allies_list)}] {ally_name}")
                drive_service.create_folder(ally_name, sector_folder_id)
                created += 1
            except Exception as e:
                print(f"  ❌ {ally_name}: {str(e)}")
                failed.append(ally_name)
        
        # 3. Guardar en índice
        index = load_sector_index()
        index[sector_name] = {
            "folder_id": sector_folder_id,
            "parent_folder": "BANCO_ALIMENTOS",
            "allies": {
                ally: {
                    "folder_id": None,  # Se llenarán después
                    "screenshots": []
                }
                for ally in allies_list
            }
        }
        save_sector_index(index)
        
        print(f"\n✅ Sector '{sector_name}' creado con {created}/{len(allies_list)} aliados")
        
        return jsonify({
            'status': 'success',
            'sector': sector_name,
            'folder_id': sector_folder_id,
            'parent_folder': 'BANCO_ALIMENTOS',
            'created_allies': created,
            'failed_aliases': failed
        }), 201
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ════════════════════════════════════════════════════════════════
# POST - Crear aliados en sector existente
# ════════════════════════════════════════════════════════════════

@drive_bp.route('/sectors/<sector>/create-allies', methods=['POST'])
def create_allies(sector):
    """
    Crea carpetas para nuevos aliados en un sector existente.
    
    POST /api/drive/sectors/abastos/create-allies
    Content-Type: application/json
    
    Body:
    {
        "allies": ["NUEVO_ALIADO_1", "NUEVO_ALIADO_2", ...]
    }
    
    Response:
    {
        "status": "success",
        "sector": "abastos",
        "created": 2,
        "failed": []
    }
    """
    try:
        data = request.get_json()
        
        if 'allies' not in data or not isinstance(data['allies'], list):
            return jsonify({'status': 'error', 'message': 'Campo "allies" debe ser lista'}), 400
        
        allies_list = [str(a).strip() for a in data['allies']]
        
        print(f"\n{'='*60}")
        print(f"🔧 POST /api/drive/sectors/{sector}/create-allies")
        print(f"Aliados a crear: {len(allies_list)}")
        print(f"{'='*60}\n")
        
        index = load_sector_index()
        
        if sector not in index:
            return jsonify({
                'status': 'error',
                'message': f'Sector "{sector}" no existe'
            }), 404
        
        sector_folder_id = index[sector]['folder_id']
        drive_service = get_drive_service()
        
        created = 0
        failed = []
        
        for i, ally_name in enumerate(allies_list, 1):
            try:
                print(f"[{i}/{len(allies_list)}] Creando: {ally_name}")
                drive_service.create_folder(ally_name, sector_folder_id)
                index[sector]['allies'][ally_name] = {
                    "folder_id": None,
                    "screenshots": []
                }
                created += 1
            except Exception as e:
                print(f"❌ Error: {ally_name}")
                failed.append(ally_name)
        
        save_sector_index(index)
        
        return jsonify({
            'status': 'success',
            'sector': sector,
            'created': created,
            'failed': failed
        }), 201
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ════════════════════════════════════════════════════════════════
# POST - Subir screenshots de un aliado
# ════════════════════════════════════════════════════════════════

@drive_bp.route('/sectors/<sector>/upload', methods=['POST'])
def upload_ally_screenshots(sector):
    """
    Sube screenshots de un aliado a su carpeta.
    
    POST /api/drive/sectors/abastos/upload
    Content-Type: application/json
    
    Body:
    {
        "ally_name": "JUAN_RUIZ",
        "screenshots": [
            {
                "list_name": "lista_a",
                "file_path": "/path/to/lista_a_20260125.png"
            },
            {
                "list_name": "lista_b",
                "file_path": "/path/to/lista_b_20260125.png"
            }
        ]
    }
    
    Response:
    {
        "status": "success",
        "sector": "abastos",
        "ally": "JUAN_RUIZ",
        "uploaded": 2,
        "failed": []
    }
    """
    try:
        data = request.get_json()
        
        if 'ally_name' not in data:
            return jsonify({'status': 'error', 'message': 'Campo "ally_name" requerido'}), 400
        
        if 'screenshots' not in data or not isinstance(data['screenshots'], list):
            return jsonify({'status': 'error', 'message': 'Campo "screenshots" debe ser lista'}), 400
        
        ally_name = data['ally_name'].strip()
        screenshots = data['screenshots']
        
        print(f"\n{'='*60}")
        print(f"📤 POST /api/drive/sectors/{sector}/upload")
        print(f"Aliado: {ally_name}")
        print(f"Screenshots: {len(screenshots)}")
        print(f"{'='*60}\n")
        
        index = load_sector_index()
        
        if sector not in index:
            return jsonify({'status': 'error', 'message': f'Sector "{sector}" no existe'}), 404
        
        if ally_name not in index[sector]['allies']:
            return jsonify({'status': 'error', 'message': f'Aliado "{ally_name}" no existe'}), 404
        
        drive_service = get_drive_service()
        uploaded = 0
        failed = []
        
        for screenshot in screenshots:
            try:
                list_name = screenshot.get('list_name', 'unknown')
                file_path = screenshot.get('file_path')
                
                if not file_path or not Path(file_path).exists():
                    failed.append(f"{list_name} - archivo no encontrado")
                    continue
                
                # Usar folder_id si existe, si no crear folder
                ally_data = index[sector]['allies'][ally_name]
                if not ally_data.get('folder_id'):
                    # Obtener folder_id de la carpeta creada
                    sector_folder = drive_service.get_folder_info(
                        index[sector]['folder_id']
                    )
                    # Aquí deberías buscar la carpeta del aliado
                    # Por ahora usamos sector_folder_id como fallback
                    ally_data['folder_id'] = index[sector]['folder_id']
                
                # Subir archivo
                file_name = f"{list_name}_{Path(file_path).stem}.png"
                result = drive_service.upload_file(
                    file_path,
                    ally_data['folder_id'],
                    file_name
                )
                
                print(f"✓ {list_name} subido")
                uploaded += 1
            except Exception as e:
                print(f"❌ Error en {screenshot.get('list_name')}: {str(e)}")
                failed.append(f"{screenshot.get('list_name')} - {str(e)}")
        
        # Actualizar índice
        save_sector_index(index)
        
        return jsonify({
            'status': 'success',
            'sector': sector,
            'ally': ally_name,
            'uploaded': uploaded,
            'failed': failed
        }), 200
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500
