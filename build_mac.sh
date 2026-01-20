#!/bin/bash

# Script para crear instalador para macOS
# Uso: bash build_mac.sh

set -e

echo "================================================"
echo "Banco de Alimentos - Build para macOS"
echo "================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ] || [ ! -f "streamlit_app.py" ]; then
    echo -e "${RED}Error: No se encontraron archivos principales${NC}"
    echo "Ejecuta este script desde la raíz del proyecto"
    exit 1
fi

# Crear directorio de build
mkdir -p build/mac
cd build/mac

echo -e "${YELLOW}1. Creando entorno virtual...${NC}"
python3 -m venv venv_build
source venv_build/bin/activate

echo -e "${YELLOW}2. Instalando dependencias...${NC}"
pip install --upgrade pip setuptools wheel
pip install -r ../../requirements.txt
pip install pyinstaller

echo -e "${YELLOW}3. Instalando PyInstaller adicionales...${NC}"
pip install pydantic

echo -e "${YELLOW}4. Creando bundle con PyInstaller...${NC}"

# Crear especificación para PyInstaller
cat > BancoDeAlimentos.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['../../app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../../config.py', '.'),
        ('../../streamlit_app.py', '.'),
        ('../../core', 'core'),
        ('../../credentials.json', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'flask',
        'flask_cors',
        'selenium',
        'google',
        'google.auth',
        'google.oauth2',
        'google.auth.transport.requests',
        'google.cloud.storage',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='banco-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='banco-api',
)

app = BUNDLE(
    coll,
    name='BancoDeAlimentos.app',
    icon_file=None,
    bundle_identifier='com.bancoalimentos.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'CFBundleShortVersionString': '1.0',
        'CFBundleVersion': '1.0.0',
    },
)
EOF

# Ejecutar PyInstaller
pyinstaller BancoDeAlimentos.spec --distpath ./dist --buildpath ./build --specpath .

echo -e "${YELLOW}5. Creando script de inicio para Streamlit...${NC}"

# Crear script wrapper que ejecute todo
cat > "dist/BancoDeAlimentos.app/Contents/MacOS/start.sh" << 'STARTSCRIPT'
#!/bin/bash
cd "$(dirname "$0")/../../.."

# Verificar si venv existe
if [ ! -d "venv_app" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv_app
fi

source venv_app/bin/activate

# Instalar dependencias si no están
pip install -q -r requirements.txt 2>/dev/null || true

# Crear carpeta screenshots si no existe
mkdir -p screenshots

# Iniciar aplicación
echo "Iniciando Banco de Alimentos..."
echo "URL: http://localhost:8501"

# Abrir navegador automáticamente
sleep 3 && open http://localhost:8501 &

# Ejecutar API + Streamlit
python app.py &
API_PID=$!

streamlit run streamlit_app.py

# Cleanup
kill $API_PID 2>/dev/null || true
STARTSCRIPT

chmod +x "dist/BancoDeAlimentos.app/Contents/MacOS/start.sh"

echo -e "${YELLOW}6. Creando script de instalación...${NC}"

# Crear script installer.sh
cat > install.sh << 'INSTALLER'
#!/bin/bash

echo "================================================"
echo "Banco de Alimentos - Instalador macOS"
echo "================================================"
echo ""

SOURCE_APP="$(pwd)/dist/BancoDeAlimentos.app"
DEST_FOLDER="$HOME/Applications/BancoDeAlimentos"
FINAL_APP="$DEST_FOLDER/BancoDeAlimentos.app"

# Crear carpeta destino
mkdir -p "$DEST_FOLDER"

echo "Copiando aplicación..."
cp -r "$SOURCE_APP" "$FINAL_APP"

echo "Creando carpeta de datos..."
mkdir -p "$DEST_FOLDER/screenshots"
mkdir -p "$DEST_FOLDER/.config"

echo "Creando acceso directo en Dock..."
# Opcional: crear alias en Dock (requiere AppleScript)

echo ""
echo "✅ Instalación completada"
echo ""
echo "Para ejecutar:"
echo "  open '$FINAL_APP'"
echo ""
echo "O haz doble clic en:"
echo "  $FINAL_APP"
INSTALLER

chmod +x install.sh

echo -e "${YELLOW}7. Creando archivo DMG (instalador)...${NC}"

# Crear DMG
mkdir -p dmg_temp
cp -r dist/BancoDeAlimentos.app dmg_temp/
cp ../../INSTALACION_MAC.md dmg_temp/README.md

hdiutil create -volname "BancoDeAlimentos" \
    -srcfolder dmg_temp \
    -ov \
    -format UDZO \
    BancoDeAlimentos.dmg

rm -rf dmg_temp

cd ../..

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Build completado exitosamente${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Archivos generados:"
echo "  📦 build/mac/BancoDeAlimentos.dmg - Instalador (drag & drop)"
echo "  📱 build/mac/dist/BancoDeAlimentos.app - Aplicación"
echo ""
echo "Para distribuir: comparte BancoDeAlimentos.dmg"
echo ""
