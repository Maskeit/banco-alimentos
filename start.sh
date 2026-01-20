#!/bin/bash
# Script para iniciar tanto el API como Streamlit

echo "🏪 Iniciando Banco de Alimentos..."
echo "================================================"

# Activar entorno virtual
source venv/bin/activate

echo "✅ Entorno virtual activado"
echo ""
echo "Abriendo dos terminales..."
echo ""

# Iniciar API en background
echo "🚀 Terminal 1: Iniciando API Flask en puerto 5000..."
python app.py &
API_PID=$!

# Esperar a que el API esté listo
sleep 3

# Iniciar Streamlit
echo "🎨 Terminal 2: Iniciando Streamlit en puerto 8501..."
echo ""
echo "La interfaz se abrirá automáticamente en: http://localhost:8501"
echo "API disponible en: http://127.0.0.1:5000"
echo ""
echo "Para detener, presiona Ctrl+C"
echo ""

streamlit run streamlit_app.py

# Cleanup
kill $API_PID 2>/dev/null
