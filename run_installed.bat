@echo off
REM Launcher for installed (PyInstaller) executables
cd /d "%~dp0"
REM Start Flask API (packaged)
start "API Flask" "%~dp0dist\BancoFlask\BancoFlask.exe"
REM Start Streamlit UI (packaged)
start "UI Streamlit" "%~dp0dist\BancoStreamlit\BancoStreamlit.exe"
timeout /t 2 /nobreak >nul
start "" "http://localhost:8501"
exit /b 0
