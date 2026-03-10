"""
Módulo centralizado de autenticación con Google OAuth2.
Un solo token con los scopes necesarios.
"""
import os
import shutil
import subprocess
import webbrowser
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import CREDENTIALS_FILE, TOKEN_FILE, USER_DATA_DIR

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

# Singleton: una sola instancia de credenciales compartida
_cached_creds: Optional[Credentials] = None


def _find_chrome_executable() -> Optional[str]:
    """Busca el ejecutable de Chrome en el sistema."""
    exe = shutil.which("chrome") or shutil.which("google-chrome")
    if exe:
        return exe

    # Rutas habituales en Windows
    win_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in win_paths:
        if os.path.isfile(p):
            return p

    return None


def _open_auth_url_in_chrome(url: str):
    """Abre la URL de autenticación en un perfil persistente de Chrome.

    Usa un perfil dedicado (chrome-auth-profile) para que, si el usuario ya
    se autenticó antes, vea su cuenta y solo necesite dar clic en 'Continuar'.
    Si Chrome no se encuentra, cae a webbrowser.open() como respaldo.
    """
    chrome_auth_dir = str(USER_DATA_DIR / "chrome-auth-profile")
    os.makedirs(chrome_auth_dir, exist_ok=True)

    chrome_exe = _find_chrome_executable()

    if chrome_exe:
        try:
            subprocess.Popen([
                chrome_exe,
                f"--user-data-dir={chrome_auth_dir}",
                "--profile-directory=Default",
                "--no-first-run",
                "--no-default-browser-check",
                url,
            ])
            return
        except Exception:
            pass

    webbrowser.open(url)


def get_credentials() -> Credentials:
    """
    Obtiene credenciales válidas de Google OAuth2.
    Reutiliza las credenciales en memoria si ya existen y son válidas.
    Solo abre el navegador una vez por ejecución.
    """
    global _cached_creds

    if _cached_creds and _cached_creds.valid:
        return _cached_creds

    creds = None
    token_path = str(TOKEN_FILE)
    credentials_path = str(CREDENTIALS_FILE)

    # 1. Intentar cargar token existente del disco
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Token corrupto o inválido ({e}), eliminando...")
            clean_tokens()
            creds = None

    # 2. Si el token existe pero expiró, intentar refrescar
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"No se pudo refrescar el token ({e}), solicitando nuevo...")
            clean_tokens()
            creds = None

    # 3. Si no hay credenciales válidas, iniciar flujo OAuth
    if not creds or not creds.valid:
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Credenciales no encontradas en {credentials_path}. "
                "Cárgalas desde Streamlit (pestaña Configuración)."
            )
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)

        # Reemplazar webbrowser.open temporalmente para que la URL de
        # autenticación se abra en un Chrome con perfil persistente,
        # no en el perfil default que puede no tener la cuenta correcta.
        original_open = webbrowser.open
        webbrowser.open = _open_auth_url_in_chrome
        try:
            creds = flow.run_local_server(port=0)
        finally:
            webbrowser.open = original_open

    # 4. Guardar token actualizado
    with open(token_path, "w") as f:
        f.write(creds.to_json())

    _cached_creds = creds
    return creds


def clean_tokens() -> None:
    """Elimina el token para forzar re-autenticación en el siguiente uso."""
    global _cached_creds
    _cached_creds = None
    token_path = str(TOKEN_FILE)
    if os.path.exists(token_path):
        os.remove(token_path)
        print(f"Token eliminado: {token_path}")


def invalidate_cache() -> None:
    """Invalida las credenciales en memoria sin borrar el archivo."""
    global _cached_creds
    _cached_creds = None
