@echo off
setlocal enabledelayedexpansion

REM Script de instalacion de dependencias
title Instalando Banco de Alimentos

cd /d "%~dp0"

echo ================================================
echo Banco de Alimentos - Instalador
echo ================================================
echo.

REM Crear venv
if not exist "venv\" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo Error: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
)

REM Activar venv
call venv\Scripts\activate.bat

REM Instalar dependencias
echo.
echo Instalando dependencias Python...
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

REM Crear carpeta screenshots
if not exist "screenshots\" (
    mkdir screenshots
)

echo.
echo ================================================
echo Instalacion completada correctamente
echo ================================================
echo.
echo Puedes ejecutar run.bat para iniciar la aplicacion
echo.
pause
