"""
Servicio para interactuar con Google Drive API.
"""
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from config import CREDENTIALS_FILE, DRIVE_TOKEN_FILE


class GoogleDriveService:
    """Servicio para crear carpetas y subir archivos a Google Drive."""
    
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        """
        Inicializa el servicio de Google Drive.
        
        Args:
            credentials_path: Ruta al archivo de credenciales OAuth2
            token_path: Ruta donde se guardará el token de autenticación
        """
        self.credentials_path = credentials_path or str(CREDENTIALS_FILE)
        self.token_path = token_path or str(DRIVE_TOKEN_FILE)
        self.service = None
        
        # Solo autenticar si credenciales existen
        if Path(self.credentials_path).exists():
            self._authenticate()
        else:
            print(f"⚠️  Credenciales no encontradas en {self.credentials_path}")
            print("Cárgalas desde Streamlit (pestaña Configuración)")
    
    def _authenticate(self) -> None:
        """Autentica con Google Drive API y crea el servicio."""
        creds = None
        
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        
        self.service = build("drive", "v3", credentials=creds)
    
    @staticmethod
    def extract_folder_id(url_or_id: str) -> str:
        """
        Extrae el ID de carpeta desde una URL de Google Drive o retorna el ID si ya lo es.
        
        Args:
            url_or_id: URL completa de Google Drive o ID de la carpeta
            
        Returns:
            ID de la carpeta
            
        Examples:
            >>> extract_folder_id("https://drive.google.com/drive/folders/1_f_RkuvXo41ahx4lQ_F1YD5LG5LCgOtu")
            '1_f_RkuvXo41ahx4lQ_F1YD5LG5LCgOtu'
            
            >>> extract_folder_id("1_f_RkuvXo41ahx4lQ_F1YD5LG5LCgOtu")
            '1_f_RkuvXo41ahx4lQ_F1YD5LG5LCgOtu'
        """
        # Si es una URL, extraer el ID usando regex
        if 'drive.google.com' in url_or_id:
            # Pattern: /folders/{FOLDER_ID}
            match = re.search(r'/folders/([a-zA-Z0-9-_]+)', url_or_id)
            if match:
                return match.group(1)
            # Pattern alternativo: ?id={FOLDER_ID}
            match = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', url_or_id)
            if match:
                return match.group(1)
            raise ValueError(f"No se pudo extraer el ID de carpeta de la URL: {url_or_id}")
        
        # Si no contiene la URL, asumir que ya es un ID
        return url_or_id
    
    def get_folder_info(self, folder_id: str) -> Dict[str, Any]:
        """
        Obtiene información de una carpeta de Drive.
        
        Args:
            folder_id: ID o URL de la carpeta
            
        Returns:
            Diccionario con información de la carpeta (id, name, webViewLink)
        """
        folder_id = self.extract_folder_id(folder_id)
        
        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields='id, name, webViewLink, parents'
            ).execute()
            
            return folder
        
        except HttpError as err:
            print(f"Error al obtener info de carpeta: {err}")
            raise
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Crea una carpeta en Google Drive.
        
        Args:
            folder_name: Nombre de la carpeta a crear
            parent_folder_id: ID o URL de la carpeta padre (opcional)
            
        Returns:
            ID de la carpeta creada
            
        Raises:
            HttpError: Si hay un error al acceder a la API
        """
        # Extraer ID si se proporciona URL
        if parent_folder_id:
            parent_folder_id = self.extract_folder_id(parent_folder_id)
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            print(f"✓ Carpeta '{folder_name}' creada con ID: {folder.get('id')}")
            return folder.get('id')
        
        except HttpError as err:
            print(f"Error al crear carpeta: {err}")
            raise

    def find_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Busca una carpeta por nombre en Google Drive.
        
        Args:
            folder_name: Nombre de la carpeta a buscar
            parent_folder_id: ID o URL de la carpeta padre donde buscar (opcional)
            
        Returns:
            ID de la carpeta si existe, None si no se encuentra
        """
        # Extraer ID si se proporciona URL
        if parent_folder_id:
            parent_folder_id = self.extract_folder_id(parent_folder_id)
        
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            return None
        
        except HttpError as err:
            print(f"Error al buscar carpeta: {err}")
            raise
    
    def get_or_create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Obtiene el ID de una carpeta existente o la crea si no existe.
        
        Args:
            folder_name: Nombre de la carpeta
            parent_folder_id: ID o URL de la carpeta padre (opcional)
            
        Returns:
            ID de la carpeta
        """
        # extract_folder_id se llama dentro de find_folder y create_folder
        folder_id = self.find_folder(folder_name, parent_folder_id)
        
        if folder_id:
            print(f"✓ Carpeta '{folder_name}' encontrada con ID: {folder_id}")
            return folder_id
        
        return self.create_folder(folder_name, parent_folder_id)
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None, file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Sube un archivo a Google Drive.
        
        Args:
            file_path: Ruta local del archivo a subir
            folder_id: ID o URL de la carpeta destino (opcional)
            file_name: Nombre del archivo en Drive (opcional, usa el nombre original si no se especifica)
            
        Returns:
            Diccionario con información del archivo subido (id, name, webViewLink)
            
        Raises:
            HttpError: Si hay un error al acceder a la API
            FileNotFoundError: Si el archivo no existe
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Extraer ID si se proporciona URL
        if folder_id:
            folder_id = self.extract_folder_id(folder_id)
        
        try:
            if file_name is None:
                file_name = os.path.basename(file_path)
            
            file_metadata = {'name': file_name}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            print(f"✓ Archivo '{file_name}' subido con ID: {file.get('id')}")
            return file
        
        except HttpError as err:
            print(f"Error al subir archivo: {err}")
            raise
