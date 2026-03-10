"""
Aplicación Streamlit para Banco de Alimentos
Interface gráfica para buscar aliados en documentos
"""

import streamlit as st
import requests
import json
from datetime import datetime
import os
import time
import threading
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Banco de Alimentos",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════
# ARCHIVO DE ESTADO PERSISTENTE
# (sobrevive recargas de página y mantiene el monitoreo visible)
# ════════════════════════════════════════════════════════════════
from config import USER_DATA_DIR

STATE_FILE = USER_DATA_DIR / "search_state.json"


def _read_persistent_state() -> dict:
    """Lee el estado persistente del disco."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _write_persistent_state(state: dict):
    """Escribe el estado persistente al disco."""
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False))


def _mark_search_running():
    _write_persistent_state({"running": True, "started_at": datetime.now().isoformat()})


def _mark_search_stopped():
    _write_persistent_state({"running": False})


def _is_search_running() -> bool:
    return _read_persistent_state().get("running", False)


# ════════════════════════════════════════════════════════════════
# INICIALIZAR ESTADO DE SESIÓN
# ════════════════════════════════════════════════════════════════
if 'list_b_id' not in st.session_state:
    st.session_state.list_b_id = ""

if 'list_b_range' not in st.session_state:
    st.session_state.list_b_range = ""

if 'document_a_url' not in st.session_state:
    st.session_state.document_a_url = ""

if 'searching' not in st.session_state:
    # Restaurar estado desde disco (por si se recargó la página)
    st.session_state.searching = _is_search_running()

if 'auth_wait_seconds' not in st.session_state:
    st.session_state.auth_wait_seconds = 15

if 'last_result' not in st.session_state:
    st.session_state.last_result = None

if 'last_timestamp' not in st.session_state:
    st.session_state.last_timestamp = None

if 'filename_prefix' not in st.session_state:
    st.session_state.filename_prefix = "sat"

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        font-size: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL
# ════════════════════════════════════════════════════════════════
API_HOST = "127.0.0.1"
API_PORT = 5000
API_URL = f"http://{API_HOST}:{API_PORT}"

# Título principal
st.title("🏪 Banco de Alimentos")
st.markdown("**Sistema de Búsqueda de Aliados en Documentos**")
st.divider()

# Barra lateral - Configuración
with st.sidebar:
    st.header("⚙️ Configuración")

    api_host = st.text_input(
        "Host del API",
        value=API_HOST,
        help="IP o dominio del servidor API"
    )

    api_port = st.number_input(
        "Puerto del API",
        value=API_PORT,
        min_value=1000,
        max_value=65535,
        help="Puerto donde corre el servidor API"
    )

    # Actualizar URL global si cambia
    if api_host != API_HOST or api_port != API_PORT:
        API_URL_LOCAL = f"http://{api_host}:{api_port}"
    else:
        API_URL_LOCAL = API_URL

    st.info(f"📍 API URL: `{API_URL_LOCAL}`")

    # Botón para probar conexión
    if st.button("🔗 Probar conexión"):
        try:
            response = requests.get(f"{API_URL_LOCAL}/", timeout=5)
            if response.status_code == 200:
                st.success("✅ Conexión exitosa")
            else:
                st.error(f"❌ Error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ No se puede conectar al API")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    st.divider()
    st.subheader("🛑 Control de Procesos")

    # Sincronizar con estado persistente (recupera estado tras recarga)
    is_running = _is_search_running()
    if is_running:
        st.warning("⏳ Búsqueda en progreso...")
        if st.button("🔴 Detener Búsqueda Actual", use_container_width=True):
            try:
                response = requests.post(f"{API_URL_LOCAL}/api/stop-search", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Señal de detención enviada")
                else:
                    st.error(f"❌ Error: {response.status_code}")
            except Exception as e:
                st.error(f"❌ No se pudo detener: {str(e)}")

            _mark_search_stopped()
            st.session_state.searching = False
            st.rerun()
    else:
        st.success("✅ Listo para buscar")


# Función para obtener screenshots
def get_screenshots_files():
    """Obtiene lista de screenshots actuales"""
    screenshots_dir = Path("screenshots")
    if screenshots_dir.exists():
        files = sorted(screenshots_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
        return files
    return []


# Pestañas principales
tab1, tab2, tab3 = st.tabs([
    "🔍 Buscar Aliados",
    "⚙️ Configuración",
    "❓ Ayuda"
])

# Tab 1: Buscar Aliados
with tab1:
    st.header("Buscar Aliados en Documento")

    col1, col2 = st.columns([2, 1])

    # Columna izquierda - Formulario
    with col1:
        st.subheader("📋 Listado B - Aliados a buscar")
        st.caption("El Google Sheet que contiene los nombres que quieres buscar (ej. listado de asociados).")

        list_b_input = st.text_input(
            "URL o ID del Google Sheet",
            value=st.session_state.list_b_id,
            placeholder="https://docs.google.com/spreadsheets/d/1soOnhLz.../ o solo el ID",
            help="Pega la URL completa o solo el ID del Google Sheet con los nombres a buscar.",
            key="input_list_b_id"
        )

        # Extraer ID de URL si es necesario
        def extract_sheet_id(input_str):
            """Extrae el ID de un URL de Google Sheets o retorna el mismo string si ya es un ID."""
            if 'docs.google.com/spreadsheets' in input_str:
                import re
                match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', input_str)
                if match:
                    return match.group(1)
                return input_str.strip()
            return input_str.strip()

        list_b_id = extract_sheet_id(list_b_input)
        st.session_state.list_b_id = list_b_id

        list_b_range = st.text_input(
            "Rango de celdas con los nombres",
            value=st.session_state.list_b_range,
            placeholder="Ejemplo: abastos!A2:A",
            help="Formato: nombre_hoja!columna_inicio:columna_fin. Ej: abastos!A2:A lee la columna A desde la fila 2.",
            key="input_list_b_range"
        )
        st.session_state.list_b_range = list_b_range

        st.divider()

        st.subheader("📄 Listado A - Documento donde buscar")
        st.caption("La URL del documento donde se buscara cada nombre del Listado B (ej. listado de contribuyentes del SAT, OSAC, etc).")

        document_a_url = st.text_area(
            "URL del documento",
            value=st.session_state.document_a_url,
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="URL completa del documento. Se abrira en Chrome y se usara Ctrl+F para buscar cada nombre.",
            height=80,
            key="input_document_a_url"
        )
        st.session_state.document_a_url = document_a_url

        st.divider()

        st.subheader("⚙️ Opciones de ejecucion")

        col_opt1, col_opt2 = st.columns(2)

        with col_opt1:
            prefix_options = {
                "sat": "SAT - Servicio de Administración Tributaria",
                "osac": "OSAC - Overseas Security Advisory Council",
                "nu": "NU - Naciones Unidas",
            }
            filename_prefix = st.selectbox(
                "Prefijo para nombre de capturas",
                options=list(prefix_options.keys()),
                format_func=lambda x: prefix_options[x],
                index=list(prefix_options.keys()).index(st.session_state.filename_prefix),
                help="Cada captura se guardara como: prefijo_NOMBRE_FECHA.png",
                key="input_prefix"
            )
            st.session_state.filename_prefix = filename_prefix
            st.caption(f"Ejemplo: `{filename_prefix}_AGRICOLA SANTA VENERANDA_{datetime.now().strftime('%Y%m%d')}.png`")

        with col_opt2:
            auth_wait_seconds = st.slider(
                "Tiempo para autenticarse (seg)",
                min_value=5,
                max_value=120,
                value=st.session_state.auth_wait_seconds,
                step=5,
                help="Segundos de espera para que inicies sesion en Google dentro de Chrome.",
                key="input_auth_wait"
            )
            st.session_state.auth_wait_seconds = auth_wait_seconds

        # Botón limpiar campos
        st.divider()
        if st.button("🗑️ Limpiar Campos", use_container_width=True):
            st.session_state.list_b_id = ""
            st.session_state.list_b_range = ""
            st.session_state.document_a_url = ""
            st.session_state.auth_wait_seconds = 15
            st.session_state.filename_prefix = "sat"
            st.rerun()

        st.divider()

        # ════════════════════════════════════════════════════════════════
        # BOTÓN DE BÚSQUEDA
        # ════════════════════════════════════════════════════════════════
        search_disabled = _is_search_running()

        if search_disabled:
            st.warning("⏳ Ya hay una búsqueda en progreso. Detenla desde la barra lateral para iniciar otra.")

        if st.button("🚀 Iniciar Búsqueda", use_container_width=True, type="primary",
                     key="search_button", disabled=search_disabled):

            # Validar campos
            if not list_b_id.strip():
                st.error("❌ Ingresa el ID del Google Sheet (Listado B)")
            elif not list_b_range.strip():
                st.error("❌ Ingresa el rango de celdas (Listado B)")
            elif not document_a_url.strip():
                st.error("❌ Ingresa la URL del documento donde buscar (Listado A)")
            else:
                # Marcar que está buscando (persistente)
                st.session_state.searching = True
                _mark_search_running()
                st.rerun()

        # ════════════════════════════════════════════════════════════════
        # EJECUCIÓN DE BÚSQUEDA (en el mismo rerun)
        # ════════════════════════════════════════════════════════════════
        if st.session_state.searching and _is_search_running():
            # Solo ejecutar si tenemos datos válidos
            if list_b_id.strip() and list_b_range.strip() and document_a_url.strip():
                with st.spinner(f"⏳ Ejecutando búsqueda... Chrome se abrira, tienes {auth_wait_seconds}s para autenticarte."):
                    try:
                        payload = {
                            "list_b_id": list_b_id.strip(),
                            "list_b_range": list_b_range.strip(),
                            "document_a_url": document_a_url.strip(),
                            "auth_wait_seconds": auth_wait_seconds,
                            "filename_prefix": filename_prefix
                        }

                        response = requests.post(
                            f"{API_URL_LOCAL}/api/search-in-document",
                            json=payload,
                            timeout=3600  # 1 hora max
                        )

                        if response.status_code == 200:
                            result = response.json()

                            st.success("✅ Búsqueda completada")

                            mc1, mc2, mc3, mc4 = st.columns(4)
                            with mc1:
                                st.metric("Total", result.get('total_names', 0))
                            with mc2:
                                st.metric("Exitosos", result.get('successful', 0))
                            with mc3:
                                st.metric("Fallidos", result.get('failed', 0))
                            with mc4:
                                status = "Cancelado" if result.get('status') == 'cancelled' else "Completado"
                                st.metric("Estado", status)

                            st.divider()

                            if result.get('results'):
                                st.subheader("📸 Resultados de Búsqueda")
                                results_list = []
                                for name, data in result['results'].items():
                                    results_list.append({
                                        "Nombre": name,
                                        "Estado": data.get('status', 'unknown'),
                                        "Screenshot": data.get('screenshot_path', 'N/A'),
                                    })
                                st.dataframe(results_list, use_container_width=True)

                                st.session_state.last_result = result
                                st.session_state.last_timestamp = datetime.now()

                            st.divider()
                            json_str = json.dumps(result, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="📥 Descargar resultados JSON",
                                data=json_str,
                                file_name=f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        else:
                            st.error(f"❌ Error: {response.status_code}")
                            st.error(response.text)

                    except requests.exceptions.Timeout:
                        st.error("❌ La solicitud superó el tiempo máximo")
                    except requests.exceptions.ConnectionError:
                        st.error(f"❌ No se puede conectar al API en {API_URL_LOCAL}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                    finally:
                        _mark_search_stopped()
                        st.session_state.searching = False

    # ════════════════════════════════════════════════════════════════
    # Columna derecha - Monitoreo en tiempo real
    # ════════════════════════════════════════════════════════════════
    with col2:
        st.subheader("📊 Monitoreo")

        monitor_container = st.container(border=True)

        with monitor_container:
            # Estado de búsqueda (siempre visible, sobrevive recargas)
            if _is_search_running():
                state_data = _read_persistent_state()
                started = state_data.get("started_at", "")
                st.error("🔴 BÚSQUEDA EN CURSO")
                if started:
                    st.caption(f"Iniciada: {started[:19]}")
            else:
                st.success("🟢 Sin búsqueda activa")

            st.divider()

            # Carpeta de screenshots
            st.markdown("**📂 Carpeta de Screenshots**")

            screenshots_path = Path("screenshots").resolve()
            st.caption(f"`{screenshots_path}`")

            if st.button("📁 Abrir carpeta", use_container_width=True):
                import subprocess
                import platform

                try:
                    if platform.system() == "Darwin":
                        subprocess.run(["open", str(screenshots_path)])
                    elif platform.system() == "Windows":
                        subprocess.run(["explorer", str(screenshots_path)])
                    elif platform.system() == "Linux":
                        subprocess.run(["xdg-open", str(screenshots_path)])
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            st.divider()

            # Lista de screenshots actuales
            st.markdown("**📸 Archivos Generados**")

            screenshots = get_screenshots_files()

            if screenshots:
                st.success(f"{len(screenshots)} archivo(s)")

                for i, file in enumerate(screenshots[:15], 1):
                    size_kb = file.stat().st_size / 1024
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)

                    fc1, fc2 = st.columns([3, 1])
                    with fc1:
                        st.caption(f"{i}. {file.name}")
                    with fc2:
                        st.caption(f"{size_kb:.0f} KB")

                if len(screenshots) > 15:
                    st.info(f"+{len(screenshots) - 15} archivo(s) más")
            else:
                st.info("📭 No hay screenshots aún")

            st.divider()

            # Estadísticas
            if screenshots:
                total_size = sum(f.stat().st_size for f in screenshots) / (1024 * 1024)
                st.metric("Tamaño total", f"{total_size:.2f} MB")
                st.metric("Cantidad", len(screenshots))
            else:
                st.metric("Cantidad", 0)

        # Auto-refresh cada 3 segundos cuando hay búsqueda activa
        if _is_search_running():
            time.sleep(3)
            st.rerun()

# Tab 2: Configuración
with tab2:
    st.header("⚙️ Configuración")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔐 Credenciales Google")

        from config import CREDENTIALS_FILE, TOKEN_FILE
        creds_path = Path(CREDENTIALS_FILE)
        token_path = Path(TOKEN_FILE)

        if creds_path.exists():
            st.success("✅ Credenciales configuradas")
            st.info(f"📂 Ubicación: `{creds_path}`")

            st.subheader("Opciones:")
            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("🔄 Recargar desde archivo", use_container_width=True):
                    try:
                        response = requests.post(f"{API_URL_LOCAL}/api/reload-credentials", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ Credenciales recargadas")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ No se puede conectar al API: {str(e)}")

            with col_b:
                if st.button("🗑️ Eliminar y cargar otras", use_container_width=True):
                    try:
                        creds_path.unlink()
                        if token_path.exists():
                            token_path.unlink()
                        st.success("✅ Credenciales eliminadas. Recarga la página para cargar nuevas.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al eliminar: {str(e)}")

        else:
            st.warning("⚠️ Credenciales no configuradas")
            st.markdown("""
            Necesitas cargar tu archivo `credentials.json` para autenticarte con Google Sheets.
            """)

        st.divider()
        st.markdown("**📥 Cargar nuevas credenciales:**")

        uploaded_file = st.file_uploader(
            "Selecciona credentials.json",
            type="json",
            help="Archivo descargado desde Google Cloud Console",
            key="creds_uploader"
        )

        if uploaded_file is not None:
            try:
                creds_data = json.loads(uploaded_file.read().decode())

                if "installed" in creds_data or "web" in creds_data:
                    creds_path.parent.mkdir(parents=True, exist_ok=True)
                    creds_path.write_text(json.dumps(creds_data, indent=2))

                    st.success("✅ Credenciales cargadas correctamente")
                    st.info(f"📂 Guardadas en: `{creds_path}`")

                    if token_path.exists():
                        token_path.unlink()

                    st.info("🔄 Token antiguo limpiado")

                    try:
                        response = requests.post(f"{API_URL_LOCAL}/api/reload-credentials", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ API reconfigurada automáticamente")
                        else:
                            st.warning(f"⚠️ Error en API: {response.status_code}")
                    except Exception as e:
                        st.warning(f"⚠️ API no disponible: {str(e)}")
                else:
                    st.error("❌ Formato inválido. Debe tener estructura 'installed' o 'web'")
            except json.JSONDecodeError:
                st.error("❌ El archivo no es un JSON válido")
            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")

    with col2:
        st.subheader("🔄 Token y Sesión")

        st.markdown("""
        El token se genera automáticamente en el primer login.
        Si la sesión expira o algo funciona mal, limpia el token.
        """)

        st.divider()
        st.subheader("📊 Estado Actual:")

        if creds_path.exists():
            st.success("✅ Credenciales")
        else:
            st.error("❌ Credenciales")

        if token_path.exists():
            st.success("✅ Token (Sheets)")
        else:
            st.warning("⚠️ Token no generado")

        st.divider()
        st.subheader("🧹 Limpiar Token:")

        if st.button("🗑️ Limpiar token", use_container_width=True, type="secondary"):
            try:
                if token_path.exists():
                    token_path.unlink()

                st.success("✅ Token eliminado")
                st.info("ℹ️ Se pedirá nueva autenticación al siguiente uso")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al limpiar token: {str(e)}")

# Tab 3: Ayuda
with tab3:
    st.header("❓ Ayuda y Documentación")

    st.subheader("¿Cómo funciona?")
    st.markdown("""
    1. **Configura el Listado B** (Google Sheet con los nombres de aliados a buscar)
    2. **Define el rango** de celdas donde están los nombres (ej: `abastos!A2:A`)
    3. **Proporciona la URL del Listado A** (documento donde se va a buscar, ej. listado SAT)
    4. **Elige el prefijo** para las capturas (sat, osac, nu)
    5. **Ajusta el tiempo** de autenticación si es necesario
    6. **Haz clic en "Iniciar Búsqueda"**

    El sistema:
    - Abrirá Chrome automáticamente
    - Te pedirá que inicies sesión en Google (si no estás logueado)
    - Buscará cada nombre usando Ctrl+F
    - Tomará screenshot de cada búsqueda
    - Guardará las capturas como `prefijo_NOMBRE_FECHA.png`
    """)

    st.divider()

    st.subheader("📖 Rangos de Google Sheets")
    st.markdown("""
    **Ejemplos válidos:**
    - `abastos!A2:A` - Columna A desde la fila 2 hasta el final
    - `abastos!A2:A50` - Columna A, filas 2 a 50
    - `Aliados!B1:B100` - Columna B, filas 1 a 100

    **Formato:** `nombre_hoja!columna_inicio:columna_fin`
    """)

    st.divider()

    st.subheader("📸 Nombres de capturas")
    st.markdown("""
    Las capturas se guardan con el formato:

    `prefijo_NOMBRE_FECHA.png`

    **Ejemplo:** `sat_AGRICOLA SANTA VENERANDA_20260308.png`

    El prefijo se elige en la sección de opciones antes de iniciar la búsqueda.
    """)

    st.divider()

    st.subheader("⏱️ Tiempo de Autenticación")
    st.markdown("""
    - **5-15 segundos**: Si ya estás logueado en Google
    - **20-30 segundos**: Si necesitas hacer login
    - **60+ segundos**: Si tienes autenticación de dos factores
    """)

    st.divider()

    st.subheader("🔧 Requisitos")
    st.markdown(f"""
    - Chrome instalado
    - Conexión a Internet
    - API corriendo en `{API_URL_LOCAL}`
    - Credenciales de Google configuradas (pestaña Configuración)
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.85rem; margin-top: 2rem;'>
    <p>🏪 Banco de Alimentos v1.0 | Streamlit App</p>
</div>
""", unsafe_allow_html=True)
