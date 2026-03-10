@echo off
title Banco de Alimentos - Launcher
cd /d "%~dp0"

echo Iniciando Banco de Alimentos...
echo.

REM Iniciar Flask API en ventana minimizada
start /min "Banco - API Flask" "%~dp0dist\BancoFlask\BancoFlask.exe"

REM Esperar a que Flask arranque antes de lanzar Streamlit
echo Esperando a que la API inicie...
timeout /t 3 /nobreak >nul

REM Iniciar Streamlit UI en ventana minimizada
start /min "Banco - Streamlit" "%~dp0dist\BancoStreamlit\BancoStreamlit.exe"

REM Esperar a que Streamlit arranque
echo Esperando a que la interfaz inicie...
timeout /t 5 /nobreak >nul

REM Abrir navegador
echo Abriendo navegador...
start "" "http://localhost:8501"

echo.
echo Banco de Alimentos esta corriendo.
echo Cierra esta ventana para detener la aplicacion.
echo.

REM Mantener viva esta ventana; al cerrarla se cierran las hijas
pause >nul
