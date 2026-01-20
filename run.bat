@echo off
setlocal enabledelayedexpansion

REM Script para ejecutar Banco de Alimentos en Windows
title Banco de Alimentos

REM Cambiar a directorio de la app
cd /d "%~dp0"

REM Verificar si venv existe
if not exist "venv\" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo Error: No se pudo crear el entorno virtual
        echo Verifica que Python esté instalado correctamente
        pause
        exit /b 1
    )
)

REM Activar venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

REM Instalar dependencias si requirements.txt existe
if exist "requirements.txt" (
    echo Verificando dependencias...
    pip install -q -r requirements.txt
)

REM Verificar que la carpeta screenshots existe
if not exist "screenshots\" (
    mkdir screenshots
)

REM Iniciar la app
echo.
echo ================================================
echo Iniciando Banco de Alimentos...
echo ================================================
echo.
echo URL: http://localhost:8501
echo.
echo Abriendo navegador en 5 segundos...
echo Presiona Ctrl+C para detener
echo.
timeout /t 5

REM Abrir navegador
start http://localhost:8501

REM Ejecutar Flask + Streamlit
start "API Flask" cmd /c python app.py
timeout /t 3
streamlit run streamlit_app.py

pause
