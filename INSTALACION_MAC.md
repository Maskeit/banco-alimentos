# Banco de Alimentos - Instalación en macOS

## Requisitos previos
- macOS 10.13 o superior
- Python 3.12 (incluido en la mayoría de Macs modernos)
- Libre de restricciones de seguridad

## Instalación

### Opción 1: DMG (Recomendado)
1. Descarga `BancoDeAlimentos.dmg`
2. Haz doble clic para abrir
3. Arrastra `BancoDeAlimentos.app` a la carpeta `Applications`
4. Haz doble clic en `BancoDeAlimentos.app`

### Opción 2: Desde carpeta
1. Extrae `banco-alimentos.zip`
2. Abre Terminal en la carpeta
3. Ejecuta: `bash start.sh`
4. Se abrirá automáticamente en http://localhost:8501

## Primera ejecución

**Importante:** La primera ejecución puede tardar mientras instala dependencias:
- Python creará un entorno virtual
- Se descargarán librerías necesarias (2-3 minutos)
- Se abrirá Chrome automáticamente

## Autenticación Google

La primera vez necesitarás:
1. Iniciar sesión con tu cuenta de Google
2. Autorizar acceso a Google Sheets y Drive
3. Los tokens se guardarán automáticamente

## Uso

```bash
# Abrir desde Terminal:
open /Applications/BancoDeAlimentos.app

# O desde línea de comandos:
bash start.sh
```

## Solución de problemas

### "BancoDeAlimentos no puede abrirse"
```bash
# Dar permisos:
chmod +x /Applications/BancoDeAlimentos.app/Contents/MacOS/start.sh
```

### "Python no instalado"
```bash
# Instalar con Homebrew:
brew install python@3.12
```

### "Puerto 8501 en uso"
- Cierra la aplicación anterior (Ctrl+C)
- Espera unos segundos
- Vuelve a ejecutar

### Ver logs de error
```bash
cd $HOME/Applications/BancoDeAlimentos
tail -f log.txt
```

## Desinstalar
1. Arrastra `BancoDeAlimentos.app` a Papelera
2. Elimina `~/Applications/BancoDeAlimentos/`
3. Vacía Papelera
