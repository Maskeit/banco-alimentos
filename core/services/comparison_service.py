"""
Servicio para comparar listas de nombres entre dos Google Sheets 
y capturar screenshots de coincidencias.
"""
import os
import threading
from datetime import datetime
from typing import List, Dict, Set, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
        self.stop_event = None  # Threading event para detener búsqueda
        
        # Crear directorio de screenshots si no existe
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
    
    def set_stop_event(self, event: threading.Event):
        """Establece el evento para detener la búsqueda."""
        self.stop_event = event
    
    def _check_stop_signal(self):
        """Verifica si se ha solicitado detener la búsqueda."""
        if self.stop_event and self.stop_event.is_set():
            raise KeyboardInterrupt("Búsqueda detenida por el usuario")
    
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
        (Método heredado - usar take_screenshot_in_document para búsquedas en Google Sheets)
        
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
    
    def search_names_in_document(self,
                                 list_b_id: str,
                                 list_b_range: str,
                                 document_a_url: str,
                                 auth_wait_seconds: int = None) -> Dict:
        """
        Lee nombres de la lista B y busca cada uno en el documento A.
        Toma screenshot de cada búsqueda (aparezca o no el resultado).
        Mantiene el navegador abierto durante todo el proceso.
        
        Args:
            list_b_id: ID de Google Sheets de la lista B (aliados)
            list_b_range: Rango de la lista B (ej: 'Sheet1!A:A')
            document_a_url: URL completa del documento A donde buscar
            
        Returns:
            Diccionario con resultados {nombre: {screenshot_path, status}}
        """
        driver = None
        
        try:
            from config import AUTH_WAIT_SECONDS as DEFAULT_AUTH_WAIT
            if auth_wait_seconds is None:
                auth_wait_seconds = DEFAULT_AUTH_WAIT
            
            print("\n" + "="*60)
            print("INICIANDO BÚSQUEDA DE ALIADOS EN DOCUMENTO")
            print("="*60 + "\n")
            
            # Paso 1: Leer nombres de la lista B
            print(f"📖 Leyendo lista B desde {list_b_id}...")
            list_b_values = self.sheets_service.read_range(list_b_id, list_b_range)
            list_b_names = [row[0].strip() for row in list_b_values if row and row[0]]
            
            print(f"✓ Se encontraron {len(list_b_names)} aliados para buscar\n")
            
            # Paso 2: Inicializar navegador UNA SOLA VEZ
            print("🚀 Iniciando navegador...")
            from config import BROWSER_WIDTH, BROWSER_HEIGHT
            
            options = webdriver.ChromeOptions()
            options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            print("🔓 Abriendo documento para autenticación...")
            driver.get(document_a_url)
            
            # Esperar a que cargue
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print("⏳ Esperando autenticación... (presiona Ctrl+C para cancelar)")
            import time
            time.sleep(auth_wait_seconds)
            
            print("✓ Iniciando búsquedas...\n")
            
            results = {}
            
            # Paso 3: Para cada aliado, buscar en el documento A (mismo navegador)
            for idx, name in enumerate(list_b_names, 1):
                try:
                    # Checkear si se solicitó detener
                    self._check_stop_signal()
                    
                    print(f"\n{'='*60}")
                    print(f"[{idx}/{len(list_b_names)}] Procesando: {name}")
                    print(f"{'='*60}")
                    
                    # Limpiar búsqueda anterior
                    from selenium.webdriver.common.keys import Keys
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                    
                    # Nueva búsqueda con Cmd+F
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.COMMAND, "f")
                    time.sleep(2)  # Esperar a que aparezca la caja de búsqueda
                    
                    # Buscar y hacer click en el input de búsqueda
                    print(f"🔎 Buscando: '{name}'")
                    try:
                        search_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='Buscar']"))
                        )
                        search_input.clear()
                        search_input.send_keys(name)
                    except:
                        # Si no encuentra el input, escribir directamente en el body
                        driver.find_element(By.TAG_NAME, "body").send_keys(name)
                    
                    time.sleep(2)
                    
                    # Tomar screenshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
                    filename = f"{self.screenshots_dir}/search_{safe_name}_{timestamp}.png"
                    
                    driver.save_screenshot(filename)
                    print(f"✓ Screenshot guardado: {filename}")
                    
                    results[name] = {
                        'screenshot_path': filename,
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    print(f"❌ Error procesando '{name}': {e}")
                    results[name] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Resumen final
            successful = sum(1 for r in results.values() if r.get('status') == 'success')
            failed = len(results) - successful
            
            print("\n" + "="*60)
            print("BÚSQUEDA COMPLETADA")
            print("="*60)
            print(f"Total de aliados: {len(list_b_names)}")
            print(f"Screenshots exitosos: {successful}")
            print(f"Fallidos: {failed}")
            print(f"Carpeta local: {self.screenshots_dir}")
            print("="*60 + "\n")
            
            return {
                'status': 'completed',
                'total_names': len(list_b_names),
                'successful': successful,
                'failed': failed,
                'results': results
            }
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Proceso cancelado por el usuario (Ctrl+C)")
            return {
                'status': 'cancelled',
                'message': 'Proceso cancelado',
                'results': results if 'results' in locals() else {}
            }
        
        finally:
            if driver:
                print("Cerrando navegador...")
                driver.quit()

    
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
