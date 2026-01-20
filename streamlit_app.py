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
# INICIALIZAR ESTADO DE SESIÓN
# ════════════════════════════════════════════════════════════════
if 'list_b_id' not in st.session_state:
    st.session_state.list_b_id = ""

if 'list_b_range' not in st.session_state:
    st.session_state.list_b_range = ""

if 'document_a_url' not in st.session_state:
    st.session_state.document_a_url = ""

if 'searching' not in st.session_state:
    st.session_state.searching = False

if 'auth_wait_seconds' not in st.session_state:
    st.session_state.auth_wait_seconds = 15

if 'last_result' not in st.session_state:
    st.session_state.last_result = None

if 'last_timestamp' not in st.session_state:
    st.session_state.last_timestamp = None

if 'stop_signal' not in st.session_state:
    st.session_state.stop_signal = False

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
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("🏪 Banco de Alimentos")
st.markdown("**Sistema de Búsqueda de Aliados en Documentos**")
st.divider()

# Barra lateral - Configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    api_host = st.text_input(
        "Host del API",
        value="127.0.0.1",
        help="IP o dominio del servidor API"
    )
    
    api_port = st.number_input(
        "Puerto del API",
        value=5000,
        min_value=1000,
        max_value=65535,
        help="Puerto donde corre el servidor API"
    )
    
    api_url = f"http://{api_host}:{api_port}"
    
    st.info(f"📍 API URL: `{api_url}`")
    
    # Botón para probar conexión
    if st.button("🔗 Probar conexión"):
        try:
            response = requests.get(f"{api_url}/", timeout=5)
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
    
    # Mostrar estado actual
    if st.session_state.searching:
        st.warning("⏳ Búsqueda en progreso...")
        if st.button("🔴 Detener Búsqueda Actual", use_container_width=True):
            st.session_state.searching = False
            st.session_state.stop_signal = True
            st.warning("⏸️ Búsqueda cancelada")
            st.rerun()
    else:
        st.success("✅ Listo para buscar")
        st.caption("No hay búsqueda activa")
        st.info("ℹ️ No hay búsqueda en progreso")

# Función para obtener screenshots
def get_screenshots_files():
    """Obtiene lista de screenshots actuales"""
    screenshots_dir = Path("screenshots")
    if screenshots_dir.exists():
        files = sorted(screenshots_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
        return files
    return []

# Pestañas principales
tab1, tab2 = st.tabs([
    "🔍 Buscar Aliados",
    "❓ Ayuda"
])

# Tab 1: Buscar Aliados
with tab1:
    st.header("Buscar Aliados en Documento")
    
    col1, col2 = st.columns([2, 1])
    
    # Columna izquierda - Formulario
    with col1:
        st.subheader("📊 Datos de Entrada")
        
        list_b_id = st.text_input(
            "ID del Google Sheet (Lista B)",
            value=st.session_state.list_b_id,
            placeholder="Ejemplo: 1soOnhLz6X4opy0de2r6Z6aomKTxY51VxzbUFfn6XeQA",
            help="ID de Google Sheets que contiene la lista de aliados",
            key="input_list_b_id"
        )
        st.session_state.list_b_id = list_b_id
        
        list_b_range = st.text_input(
            "Rango de celdas (Lista B)",
            value=st.session_state.list_b_range,
            placeholder="Ejemplo: abastos!A2:A",
            help="Formato: nombre_hoja!A2:A (incluye el rango de filas del que quieres hacer la busqueda)",
            key="input_list_b_range"
        )
        st.session_state.list_b_range = list_b_range
        
        document_a_url = st.text_area(
            "URL del Documento (Lista A)",
            value=st.session_state.document_a_url,
            placeholder="https://docs.google.com/...",
            help="URL completa del documento donde buscar a los aliados",
            height=100,
            key="input_document_a_url"
        )
        st.session_state.document_a_url = document_a_url
        
        st.subheader("⏱️ Configuración")
        
        auth_wait_seconds = st.slider(
            "Tiempo para autenticarse (segundos)",
            min_value=5,
            max_value=120,
            value=st.session_state.auth_wait_seconds,
            step=5,
            help="Cuánto tiempo esperar para que te logues en Google",
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
            st.success("✅ Campos limpiados")
            st.rerun()
        
        st.info(f"""
        **Configuración actual:**
        - Tiempo de espera: {auth_wait_seconds}s
        - Host: {api_host}
        - Puerto: {api_port}
        """)
        
        st.divider()
        
        # Botón para ejecutar búsqueda
        if st.button("🚀 Iniciar Búsqueda", use_container_width=True, type="primary", key="search_button"):
            
            # Validar campos
            if not list_b_id.strip():
                st.error("❌ Ingresa el ID del Google Sheet")
            elif not list_b_range.strip():
                st.error("❌ Ingresa el rango de celdas")
            elif not document_a_url.strip():
                st.error("❌ Ingresa la URL del documento donde se buscararán a los aliados")
            else:
                # Marcar que está buscando
                st.session_state.searching = True
                
                # Contenedor para mostrar progreso
                progress_container = st.container()
                
                # Enviar solicitud al API
                with progress_container:
                    with st.spinner(f"⏳ Ejecutando búsqueda... Se abrirá Chrome en {auth_wait_seconds}s"):
                        try:
                            payload = {
                                "list_b_id": list_b_id.strip(),
                                "list_b_range": list_b_range.strip(),
                                "document_a_url": document_a_url.strip(),
                                "auth_wait_seconds": auth_wait_seconds
                            }
                            
                            response = requests.post(
                                f"{api_url}/api/search-in-document",
                                json=payload,
                                timeout=600  # 10 minutos máximo
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                # Mostrar resumen
                                st.success("✅ Búsqueda completada")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Total", result.get('total_names', 0))
                                with col2:
                                    st.metric("Exitosos", result.get('successful', 0), delta="green")
                                with col3:
                                    st.metric("Fallidos", result.get('failed', 0), delta="red" if result.get('failed', 0) > 0 else None)
                                with col4:
                                    status = "Cancelado" if result.get('cancelled') else "Completado"
                                    st.metric("Estado", status)
                                
                                st.divider()
                                
                                # Mostrar resultados en tabla
                                st.subheader("📸 Resultados de Búsqueda")
                                
                                if result.get('results'):
                                    results_list = []
                                    for name, data in result['results'].items():
                                        results_list.append({
                                            "Nombre": name,
                                            "Estado": data.get('status', 'unknown'),
                                            "Screenshot": data.get('screenshot_path', 'N/A'),
                                            "Timestamp": data.get('timestamp', 'N/A')
                                        })
                                    
                                    # Mostrar tabla
                                    st.dataframe(results_list, use_container_width=True)
                                    
                                    # Guardar en historial
                                    st.session_state.last_result = result
                                    st.session_state.last_timestamp = datetime.now()
                                
                                # Botón para descargar resultados
                                st.divider()
                                col1, col2 = st.columns(2)
                                with col1:
                                    json_str = json.dumps(result, indent=2, ensure_ascii=False)
                                    st.download_button(
                                        label="📥 Descargar JSON",
                                        data=json_str,
                                        file_name=f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                        mime="application/json",
                                        use_container_width=True
                                    )
                            else:
                                st.error(f"❌ Error: {response.status_code}")
                                st.error(response.text)
                        
                        except requests.exceptions.Timeout:
                            st.error("❌ Error: La solicitud tardó demasiado (timeout)")
                        except requests.exceptions.ConnectionError:
                            st.error(f"❌ Error: No se puede conectar al API en {api_url}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                        finally:
                            st.session_state.searching = False
    
    # Columna derecha - Monitoreo en tiempo real
    with col2:
        st.subheader("📊 Monitoreo en Tiempo Real")
        
        # Contenedor para refrescar automáticamente
        monitor_container = st.container(border=True)
        
        with monitor_container:
            # Mostrar carpeta de screenshots
            st.markdown("**📂 Carpeta de Screenshots**")
            
            screenshots_path = Path("screenshots").resolve()
            st.caption(f"Ruta: `{screenshots_path}`")
            
            # Botón para abrir carpeta
            if st.button("📁 Abrir carpeta", use_container_width=True):
                import subprocess
                import platform
                
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", str(screenshots_path)])
                    elif platform.system() == "Windows":
                        subprocess.run(["explorer", str(screenshots_path)])
                    elif platform.system() == "Linux":
                        subprocess.run(["xdg-open", str(screenshots_path)])
                    st.success("✅ Carpeta abierta")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            st.divider()
            
            # Auto-refresh cuando está buscando
            if st.session_state.searching:
                st.info("🔄 Actualizando cada 2 segundos...")
                # Placeholder para forzar refresh
                placeholder = st.empty()
            
            # Lista de screenshots actuales
            st.markdown("**📸 Archivos Generados**")
            
            screenshots = get_screenshots_files()
            
            if screenshots:
                st.success(f"✅ {len(screenshots)} archivo(s) encontrado(s)")
                
                # Mostrar últimos 10 archivos
                for i, file in enumerate(screenshots[:10], 1):
                    size_kb = file.stat().st_size / 1024
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(f"{i}. {file.name}")
                        st.text(f"   📅 {mod_time.strftime('%H:%M:%S')}")
                    with col2:
                        st.caption(f"{size_kb:.1f} KB")
                
                if len(screenshots) > 10:
                    st.info(f"📦 +{len(screenshots) - 10} archivo(s) más")
            else:
                st.info("📭 No hay screenshots aún")
            
            st.divider()
            
            # Estadísticas
            st.markdown("**📊 Estadísticas**")
            
            if screenshots:
                total_size = sum(f.stat().st_size for f in screenshots) / (1024 * 1024)
                st.metric("Tamaño total", f"{total_size:.2f} MB")
                st.metric("Cantidad", len(screenshots))
            else:
                st.metric("Cantidad", 0)
        
        # Auto-refresh cuando está buscando
        if st.session_state.searching:
            time.sleep(2)
            st.rerun()


# Tab 2: Ayuda
with tab2:
    st.header("❓ Ayuda y Documentación")
    
    st.subheader("¿Cómo funciona?")
    st.markdown("""
    1. **Ingresa el Google Sheet** con la lista de aliados a buscar
    2. **Define el rango** de celdas donde están los nombres (ej: abastos!A2:A)
    3. **Proporciona la URL** del documento donde buscar
    4. **Ajusta el tiempo** de autenticación si es necesario
    5. **Haz clic en "Iniciar Búsqueda"**
    
    El sistema:
    - Abrirá Chrome automáticamente
    - Te pedirá que te logues en Google (si no estás logueado)
    - Buscará cada nombre usando Cmd+F
    - Tomará screenshots de cada búsqueda
    - Guardará los resultados en la carpeta `screenshots/`
    """)
    
    st.divider()
    
    st.subheader("📖 Rangos de Google Sheets")
    st.markdown("""
    **Ejemplos válidos:**
    - `abastos!A2:A` - Desde la fila 2 hasta el final de la columna A
    - `abastos!A2:A50` - Desde la fila 2 hasta la fila 50
    - `Aliados!B1:B100` - Columna B, filas 1 a 100
    
    **Parámetros:**
    - `nombre_hoja!` - El nombre exacto de la hoja en Google Sheets
    - `A2:A` - Columna A desde fila 2 hasta el final
    """)
    
    st.divider()
    
    st.subheader("⏱️ Tiempo de Autenticación")
    st.markdown("""
    - **5-15 segundos**: Si ya estás logueado en Google
    - **20-30 segundos**: Si necesitas hacer login
    - **60+ segundos**: Si tienes autenticación de dos factores
    
    Puedes ajustar este tiempo en el panel derecho.
    """)
    
    st.divider()
    
    st.subheader("🔧 Requisitos")
    st.markdown(f"""
    - ✅ Chrome instalado (se abre automáticamente)
    - ✅ Conexión a Internet
    - ✅ API corriendo en `{api_url}`
    - ✅ Credenciales de Google configuradas
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.85rem; margin-top: 2rem;'>
    <p>🏪 Banco de Alimentos v1.0 | Streamlit App</p>
    <p>Última actualización: 20 de enero de 2026</p>
</div>
""", unsafe_allow_html=True)
