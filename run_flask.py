import sys
import os

# Asegurar que el directorio del .exe (o del script) esté en sys.path
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

try:
    from app import app
except Exception as e:
    raise SystemExit(f"Error importing Flask app: {e}")

if __name__ == '__main__':
    from config import API_HOST, API_PORT

    # Desactivar debug en modo compilado: el reloader de Flask intenta
    # relanzar el proceso y falla dentro de un .exe empaquetado.
    use_debug = False if getattr(sys, 'frozen', False) else True

    app.run(host=API_HOST, port=API_PORT, debug=use_debug)
