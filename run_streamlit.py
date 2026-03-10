import sys
import os


def get_base_path() -> str:
    """Retorna la ruta base correcta tanto en desarrollo como en exe compilado."""
    if getattr(sys, 'frozen', False):
        # Corriendo como exe de PyInstaller: archivos extraídos en _MEIPASS
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    base_path = get_base_path()
    app_script = os.path.join(base_path, 'streamlit_app.py')

    # Cambiar al directorio base para que los imports relativos funcionen
    os.chdir(base_path)

    # En modo empaquetado, Streamlit detecta developmentMode=true porque
    # no encuentra su config habitual. Forzar a false antes de importar.
    if getattr(sys, 'frozen', False):
        os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    from streamlit.web import cli as stcli
    sys.argv = [
        "streamlit", "run", app_script,
        "--server.port=8501",
        "--server.headless=true",
        "--server.fileWatcherType=none",
    ]
    sys.exit(stcli.main())
