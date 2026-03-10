"""
Servicio para buscar nombres en documentos y capturar screenshots.
"""
import os
import platform
import threading
import time
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .google_sheets_service import GoogleSheetsService

# Tecla modificadora: Ctrl en Windows/Linux, Cmd en Mac
_MODIFIER_KEY = Keys.COMMAND if platform.system() == "Darwin" else Keys.CONTROL


class ComparisonService:
    """Servicio para buscar aliados en documentos y tomar screenshots."""

    def __init__(self, sheets_service: GoogleSheetsService = None,
                 screenshots_dir: str = "screenshots"):
        self.sheets_service = sheets_service or GoogleSheetsService()
        self.screenshots_dir = screenshots_dir
        self.stop_event = None

        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)

    def set_stop_event(self, event: threading.Event):
        """Establece el evento para detener la búsqueda."""
        self.stop_event = event

    def _check_stop_signal(self):
        """Verifica si se ha solicitado detener la búsqueda."""
        if self.stop_event and self.stop_event.is_set():
            raise KeyboardInterrupt("Búsqueda detenida por el usuario")

    @staticmethod
    def _clean_chrome_locks(profile_dir: str):
        """Elimina archivos de bloqueo de Chrome de ejecuciones anteriores.

        Si Chrome o Selenium no se cerraron correctamente, estos archivos
        evitan que el perfil se cargue y Chrome cae a un perfil temporal vacío.
        """
        for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
            lock_path = os.path.join(profile_dir, name)
            try:
                if os.path.exists(lock_path):
                    os.remove(lock_path)
            except OSError:
                pass

    def _create_chrome_driver(self):
        """Crea un driver de Chrome con perfil persistente para mantener la sesión."""
        from config import BROWSER_WIDTH, BROWSER_HEIGHT, USER_DATA_DIR

        chrome_profile_dir = str(USER_DATA_DIR / "chrome-profile")
        os.makedirs(chrome_profile_dir, exist_ok=True)

        # Limpiar locks de ejecuciones anteriores que no cerraron bien
        self._clean_chrome_locks(chrome_profile_dir)

        options = webdriver.ChromeOptions()
        options.add_argument(f"--window-size={BROWSER_WIDTH},{BROWSER_HEIGHT}")
        options.add_argument(f"--user-data-dir={chrome_profile_dir}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # No se fuerza user-agent: Chrome usa su versión real.
        # Un UA estático (ej. Chrome/120) no coincide con la versión instalada
        # y Google invalida la sesión al detectar la inconsistencia.

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def _is_driver_alive(self, driver) -> bool:
        """Verifica si el driver de Chrome sigue vivo."""
        try:
            _ = driver.title
            return True
        except Exception:
            return False

    def search_names_in_document(self,
                                 list_b_id: str,
                                 list_b_range: str,
                                 document_a_url: str,
                                 auth_wait_seconds: int = None,
                                 filename_prefix: str = "search") -> Dict:
        """
        Lee nombres de la lista B y busca cada uno en el documento A.
        Toma screenshot de cada búsqueda (aparezca o no el resultado).
        Mantiene el navegador abierto durante todo el proceso.

        Args:
            list_b_id: ID de Google Sheets de la lista B (aliados)
            list_b_range: Rango de la lista B (ej: 'Sheet1!A:A')
            document_a_url: URL completa del documento A donde buscar
            auth_wait_seconds: Tiempo de espera para autenticación
            filename_prefix: Prefijo para el nombre de las capturas (ej: 'sat', 'osac', 'nu')

        Returns:
            Diccionario con resultados {nombre: {screenshot_path, status}}
        """
        driver = None

        try:
            from config import AUTH_WAIT_SECONDS as DEFAULT_AUTH_WAIT
            if auth_wait_seconds is None:
                auth_wait_seconds = DEFAULT_AUTH_WAIT

            print("\n" + "="*60)
            print("INICIANDO BUSQUEDA DE ALIADOS EN DOCUMENTO")
            print("="*60 + "\n")

            # Paso 1: Leer nombres de la lista B
            print(f"Leyendo lista B desde {list_b_id}...")
            list_b_values = self.sheets_service.read_range(list_b_id, list_b_range)
            list_b_names = [row[0].strip() for row in list_b_values if row and row[0]]

            print(f"Se encontraron {len(list_b_names)} aliados para buscar\n")

            # Paso 2: Inicializar navegador con perfil persistente
            print("Iniciando navegador...")
            driver = self._create_chrome_driver()

            print("Abriendo documento para autenticación...")
            driver.get(document_a_url)

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            print(f"Esperando {auth_wait_seconds}s para autenticación...")
            time.sleep(auth_wait_seconds)

            print("Iniciando búsquedas...\n")

            results = {}

            # Paso 3: Para cada aliado, buscar en el documento A
            for idx, name in enumerate(list_b_names, 1):
                try:
                    self._check_stop_signal()

                    # Verificar que Chrome sigue vivo
                    if not self._is_driver_alive(driver):
                        print("Chrome se cerró inesperadamente. Abortando...")
                        for remaining_name in list_b_names[idx - 1:]:
                            results[remaining_name] = {
                                'status': 'error',
                                'error': 'Chrome se cerró inesperadamente',
                                'timestamp': datetime.now().isoformat()
                            }
                        break

                    print(f"\n{'='*60}")
                    print(f"[{idx}/{len(list_b_names)}] Procesando: {name}")
                    print(f"{'='*60}")

                    # Limpiar búsqueda anterior
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)

                    # Abrir diálogo de búsqueda (Ctrl+F en Windows/Linux, Cmd+F en Mac)
                    driver.find_element(By.TAG_NAME, "body").send_keys(_MODIFIER_KEY, "f")
                    time.sleep(2)

                    # Escribir nombre en el campo de búsqueda
                    print(f"Buscando: '{name}'")
                    try:
                        search_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "input[aria-label*='Buscar'], input[aria-label*='Find'], input[aria-label*='buscar'], input[aria-label*='find']")
                            )
                        )
                        search_input.clear()
                        search_input.send_keys(name)
                    except Exception:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(driver)
                        actions.send_keys(name)
                        actions.perform()

                    time.sleep(2)

                    # Tomar screenshot
                    date_stamp = datetime.now().strftime("%Y%m%d")
                    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
                    filename = f"{self.screenshots_dir}/{filename_prefix}_{safe_name}_{date_stamp}.png"

                    driver.save_screenshot(filename)
                    print(f"Screenshot guardado: {filename}")

                    results[name] = {
                        'screenshot_path': filename,
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    }

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Error procesando '{name}': {e}")
                    results[name] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    if not self._is_driver_alive(driver):
                        print("Chrome ya no responde. Abortando restantes...")
                        for remaining_name in list_b_names[idx:]:
                            results[remaining_name] = {
                                'status': 'error',
                                'error': 'Chrome se cerró inesperadamente',
                                'timestamp': datetime.now().isoformat()
                            }
                        break

            # Resumen final
            successful = sum(1 for r in results.values() if r.get('status') == 'success')
            failed = len(results) - successful

            print("\n" + "="*60)
            print("BUSQUEDA COMPLETADA")
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
            print("\nProceso cancelado por el usuario")
            return {
                'status': 'cancelled',
                'message': 'Proceso cancelado',
                'results': results if 'results' in locals() else {}
            }

        finally:
            if driver:
                print("Cerrando navegador...")
                try:
                    driver.quit()
                except Exception:
                    pass
