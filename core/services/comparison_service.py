"""
Servicio para comparar listas de nombres entre dos Google Sheets 
y capturar screenshots de coincidencias.
"""
import os
from datetime import datetime
from typing import List, Dict, Set, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .google_sheets_service import GoogleSheetsService
from .google_drive_service import GoogleDriveService


class ComparisonService:
    """Servicio para comparar listas y gestionar screenshots de coincidencias."""
    
    def __init__(self, sheets_service: GoogleSheetsService = None, 
                 drive_service: GoogleDriveService = None,
                 screenshots_dir: str = "screenshots"):
        """
        Inicializa el servicio de comparación.
        
        Args:
            sheets_service: Instancia de GoogleSheetsService
            drive_service: Instancia de GoogleDriveService
            screenshots_dir: Directorio local para guardar screenshots
        """
        self.sheets_service = sheets_service or GoogleSheetsService()
        self.drive_service = drive_service or GoogleDriveService()
        self.screenshots_dir = screenshots_dir
        
        # Crear directorio de screenshots si no existe
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
    
    def compare_lists(self, 
                     list_a_id: str, 
                     list_a_range: str,
                     list_b_id: str, 
                     list_b_range: str) -> List[str]:
        """
        Compara dos listas de Google Sheets y retorna las coincidencias.
        
        Args:
            list_a_id: ID de la hoja de cálculo de la lista A
            list_a_range: Rango de la lista A (ej: 'Sheet1!A:A')
            list_b_id: ID de la hoja de cálculo de la lista B
            list_b_range: Rango de la lista B (ej: 'Sheet1!B:B')
            
        Returns:
            Lista de nombres que aparecen en ambas listas
        """
        print(f"📊 Leyendo lista A desde {list_a_id}...")
        list_a_values = self.sheets_service.read_range(list_a_id, list_a_range)
        list_a = {row[0].strip().lower() for row in list_a_values if row and row[0]}
        
        print(f"📊 Leyendo lista B desde {list_b_id}...")
        list_b_values = self.sheets_service.read_range(list_b_id, list_b_range)
        list_b = {row[0].strip().lower() for row in list_b_values if row and row[0]}
        
        # Encontrar coincidencias
        matches = list_a.intersection(list_b)
        
        print(f"✓ Se encontraron {len(matches)} coincidencias")
        return sorted(list(matches))
    
    def take_screenshot(self, name: str, search_url: str = None) -> str:
        """
        Toma una captura de pantalla para un nombre específico.
        
        Args:
            name: Nombre de la persona/item para el screenshot
            search_url: URL donde buscar (opcional, por defecto busca en Google)
            
        Returns:
            Ruta del archivo de screenshot guardado
        """
        driver = None
        try:
            # Inicializar navegador
            driver = webdriver.Safari()
            driver.set_window_size(1920, 1080)
            
            # URL de búsqueda (por defecto Google)
            if search_url is None:
                search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}"
            
            print(f"🔍 Buscando: {name}")
            driver.get(search_url)
            
            # Esperar a que cargue la página
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{self.screenshots_dir}/match_{safe_name}_{timestamp}.png"
            
            # Tomar screenshot
            driver.save_screenshot(filename)
            print(f"✓ Screenshot guardado: {filename}")
            
            return filename
        
        except Exception as e:
            print(f"❌ Error al tomar screenshot para '{name}': {e}")
            raise
        
        finally:
            if driver:
                driver.quit()
    
    def process_matches(self, 
                       matches: List[str],
                       drive_parent_folder: str = None,
                       search_url_template: str = None) -> Dict[str, Dict]:
        """
        Procesa todas las coincidencias: toma screenshots y los sube a Drive.
        
        Args:
            matches: Lista de nombres con coincidencias
            drive_parent_folder: Nombre de la carpeta padre en Drive
            search_url_template: Template de URL para buscar (usa {name} como placeholder)
            
        Returns:
            Diccionario con resultados {nombre: {screenshot_path, drive_id, drive_url}}
        """
        results = {}
        
        # Crear/obtener carpeta padre en Drive
        parent_folder_id = None
        if drive_parent_folder:
            parent_folder_id = self.drive_service.get_or_create_folder(drive_parent_folder)
        
        for name in matches:
            try:
                print(f"\n{'='*60}")
                print(f"Procesando: {name}")
                print(f"{'='*60}")
                
                # Preparar URL de búsqueda
                search_url = None
                if search_url_template:
                    search_url = search_url_template.format(name=name.replace(' ', '+'))
                
                # Tomar screenshot
                screenshot_path = self.take_screenshot(name, search_url)
                
                # Crear carpeta individual para este nombre en Drive
                name_folder_id = self.drive_service.get_or_create_folder(
                    name, 
                    parent_folder_id
                )
                
                # Subir screenshot a Drive
                drive_file = self.drive_service.upload_file(
                    screenshot_path,
                    folder_id=name_folder_id
                )
                
                results[name] = {
                    'screenshot_path': screenshot_path,
                    'drive_folder_id': name_folder_id,
                    'drive_file_id': drive_file.get('id'),
                    'drive_url': drive_file.get('webViewLink'),
                    'status': 'success'
                }
                
                print(f"✓ Completado para: {name}")
            
            except Exception as e:
                print(f"❌ Error procesando '{name}': {e}")
                results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def run_comparison_workflow(self,
                               list_a_id: str,
                               list_a_range: str,
                               list_b_id: str,
                               list_b_range: str,
                               drive_folder: str = "Banco Alimentos - Coincidencias",
                               search_url_template: str = None) -> Dict:
        """
        Ejecuta el workflow completo: compara listas, toma screenshots y sube a Drive.
        
        Args:
            list_a_id: ID de Google Sheets de la lista A
            list_a_range: Rango de la lista A
            list_b_id: ID de Google Sheets de la lista B
            list_b_range: Rango de la lista B
            drive_folder: Nombre de carpeta en Drive para guardar resultados
            search_url_template: Template de URL para búsquedas
            
        Returns:
            Diccionario con resumen de resultados
        """
        print("\n" + "="*60)
        print("INICIANDO WORKFLOW DE COMPARACIÓN")
        print("="*60 + "\n")
        
        # Paso 1: Comparar listas
        matches = self.compare_lists(list_a_id, list_a_range, list_b_id, list_b_range)
        
        if not matches:
            print("\n⚠️  No se encontraron coincidencias")
            return {
                'status': 'completed',
                'matches_count': 0,
                'matches': [],
                'results': {}
            }
        
        print(f"\n📋 Coincidencias encontradas: {', '.join(matches)}\n")
        
        # Paso 2: Procesar coincidencias
        results = self.process_matches(matches, drive_folder, search_url_template)
        
        # Resumen final
        successful = sum(1 for r in results.values() if r.get('status') == 'success')
        failed = len(results) - successful
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETADO")
        print("="*60)
        print(f"Total de coincidencias: {len(matches)}")
        print(f"Procesados exitosamente: {successful}")
        print(f"Fallidos: {failed}")
        print("="*60 + "\n")
        
        return {
            'status': 'completed',
            'matches_count': len(matches),
            'matches': matches,
            'successful': successful,
            'failed': failed,
            'results': results
        }
