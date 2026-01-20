# Banco de Alimentos - Instalación en Windows

## Requisitos previos
- Windows 10/11
- Python 3.12 instalado (descarga desde https://www.python.org/downloads/)
  - **Importante**: Marca "Add Python to PATH" durante la instalación

## Opción 1: Instalador (Recomendado)

1. Descarga el archivo `BancoDeAlimentos-Setup.exe`
2. Haz doble clic para ejecutar
3. Sigue las instrucciones del instalador
4. Se creará un acceso directo en el escritorio
5. Ejecuta el acceso directo para iniciar la app

## Opción 2: Manual (Portable)

1. Extrae la carpeta `banco-alimentos` en tu computadora
2. Haz doble clic en `run.bat`
3. Se abrirá automáticamente en http://localhost:8501

## Primeras credenciales

**Importante**: La primera vez que ejecutes, necesitarás autenticarte con Google:
- Se abrirá Chrome automáticamente
- Inicia sesión con tu cuenta de Google
- Autoriza el acceso a Google Sheets y Drive
- Los tokens se guardarán automáticamente

## Solución de problemas

### "Python no está instalado"
- Instala Python 3.12 desde https://www.python.org/downloads/
- Marca "Add Python to PATH"
- Reinicia Windows
- Vuelve a ejecutar el instalador

### "Puerto 8501 en uso"
- Cierra la aplicación anterior (presiona Ctrl+C en la terminal)
- Espera unos segundos
- Ejecuta `run.bat` nuevamente

### "ModuleNotFoundError"
- Haz doble clic en `install.bat` para reinstalar dependencias
- Luego ejecuta `run.bat`

## Contacto
Para problemas técnicos, contacta al equipo de desarrollo.
