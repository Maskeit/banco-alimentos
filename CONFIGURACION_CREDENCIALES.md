# 🔐 Guía de Configuración de Credenciales

## Estructura de Archivos

Tu proyecto usa **dos tipos de archivos** para Google:

```
banco-alimentos/
├── credencials.json          ← OAuth2 CLIENT SECRET (en la raíz)
├── core/
│   └── services/
│       ├── token.json        ← Token de Sheets (generado automático)
│       └── token_drive.json  ← Token de Drive (generado automático)
└── ...
```

## ¿Qué es cada archivo?

### 1. `credencials.json` (LA RAÍZ - OBLIGATORIO)
**¿Qué es?**
- El archivo JSON que descargaste de Google Cloud Console
- Contiene: `client_id`, `client_secret`, `auth_uri`, etc.
- Comienza con: `{ "installed": { ... } }`

**¿Dónde va?**
- **Raíz del proyecto**: `/Users/malejandre/Documents/developer/banco-alimentos/credencials.json`
- ✅ Está en la posición correcta

**¿Es sensible?**
- SÍ, es un secreto. Está en `.gitignore` para no subirse a GitHub
- No lo compartas con nadie

### 2. `token.json` (core/services/ - GENERADO AUTOMÁTICO)
**¿Qué es?**
- Token de acceso generado por la app la primera vez que se autentica
- Específico para Google Sheets API
- La app lo usa para acceder sin pedir contraseña de nuevo

**¿Dónde va?**
- `core/services/token.json`
- Se crea automáticamente cuando ejecutas la app por primera vez
- **No lo edites manualmente**

### 3. `token_drive.json` (core/services/ - GENERADO AUTOMÁTICO)
**¿Qué es?**
- Token de acceso para Google Drive API
- Generado la primera vez que se usa Google Drive
- La app lo usa para subir archivos y crear carpetas

**¿Dónde va?**
- `core/services/token_drive.json`
- Se crea automáticamente cuando uses funciones de Drive
- **No lo edites manualmente**

## 🔄 Flujo de Autenticación (Primera vez)

```
1. Ejecutas: python app.py

2. La app busca credencials.json en la raíz
   └─ Si no existe → ERROR

3. La app busca token.json en core/services/
   └─ Si no existe → Abre navegador con Google Login

4. Tú das permisos en Google
   └─ Google retorna un token

5. La app guarda el token automáticamente en token.json
   └─ Próximas veces usa el token (sin pedir login)

6. Mismo proceso para Drive con token_drive.json
```

## ✅ Checklist: ¿Está todo configurado?

- [ ] `credencials.json` en la raíz (`/banco-alimentos/credencials.json`)
- [ ] Contiene `"installed"` al abrirlo
- [ ] `.gitignore` tiene `*credencials.json` y `*token*.json`
- [ ] Carpeta `screenshots/` existe en la raíz
- [ ] Virtual environment activado: `source venv/bin/activate`
- [ ] Dependencias instaladas: `pip install -r requirements.txt`

## 🚀 Para ejecutar por primera vez

```bash
# 1. Activar entorno
source venv/bin/activate

# 2. Ejecutar app
python app.py

# 3. Un navegador se abrirá automáticamente
#    Inicia sesión con tu cuenta de Google
#    Dale permisos a la app

# 4. Cierra el navegador cuando vea el mensaje de éxito
#    Los tokens se guardan automáticamente

# ✓ Listo! Los tokens se generarán en:
#   - core/services/token.json
#   - core/services/token_drive.json
```

## 🔄 Cambiar de cuenta Google

Si necesitas usar otra cuenta Google:

```bash
# 1. Borra los tokens
rm core/services/token.json
rm core/services/token_drive.json

# 2. Ejecuta la app de nuevo
python app.py

# 3. Inicia sesión con la nueva cuenta
```

## ⚠️ Problemas Comunes

### "FileNotFoundError: credencials.json"
- **Problema**: El archivo no está en la raíz del proyecto
- **Solución**: Colócalo en `/Users/malejandre/Documents/developer/banco-alimentos/credencials.json`

### "Error: invalid_grant"
- **Problema**: El token expiró o es inválido
- **Solución**: Borra los tokens y vuelve a ejecutar la app
  ```bash
  rm core/services/token*.json
  python app.py
  ```

### "Permission denied: Sheets"
- **Problema**: El cliente secret no tiene los scopes correctos
- **Solución**: Descarga nuevamente de Google Cloud Console asegurándote que sea una app de Desktop

### "No module named 'selenium'"
- **Problema**: Falta instalar las dependencias
- **Solución**: 
  ```bash
  pip install -r requirements.txt
  ```

## 📚 Archivos Generados (NO editar)

Después de la primera ejecución, verás:

```
core/services/
├── token.json          ← NO EDITAR, NO SUBIR A GITHUB
├── token_drive.json    ← NO EDITAR, NO SUBIR A GITHUB
└── __pycache__/        ← NO EDITAR, NO SUBIR A GITHUB
```

Estos están en `.gitignore` por seguridad.

## 🔒 Seguridad

**NUNCA hagas esto:**
- ❌ Subir `credencials.json` a GitHub
- ❌ Compartir `token.json` o `credencials.json` por email
- ❌ Usar credenciales de producción para desarrollo
- ❌ Commitear archivos `.json` que NO estén en `.gitignore`

**SÍ haz esto:**
- ✅ Mantener `.gitignore` actualizado
- ✅ Usar `.gitignore` para secretos
- ✅ Rotar tokens si sospechas que fueron comprometidos
- ✅ Usar variables de entorno para datos sensibles en producción
