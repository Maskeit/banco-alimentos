"""
Servicio para interactuar con Google Sheets API.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import CREDENTIALS_FILE, SHEETS_TOKEN_FILE


class GoogleSheetsService:
    """Servicio para leer y escribir en Google Sheets."""
    
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        """
        Inicializa el servicio de Google Sheets.
        
        Args:
            credentials_path: Ruta al archivo de credenciales OAuth2
            token_path: Ruta donde se guardará el token de autenticación
        """
        self.credentials_path = credentials_path or str(CREDENTIALS_FILE)
        self.token_path = token_path or str(SHEETS_TOKEN_FILE)
        self.service = None
        
        # Solo autenticar si credenciales existen
        if Path(self.credentials_path).exists():
            self._authenticate()
        else:
            print(f"⚠️  Credenciales no encontradas en {self.credentials_path}")
            print("Cárgalas desde Streamlit (pestaña Configuración)")
    
    def _authenticate(self) -> None:
        """Autentica con Google Sheets API y crea el servicio."""
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
        
        self.service = build("sheets", "v4", credentials=creds)
    
    @staticmethod
    def extract_spreadsheet_id(url_or_id: str) -> str:
        """
        Extrae el ID del spreadsheet desde una URL de Google Sheets o retorna el ID si ya lo es.
        
        Args:
            url_or_id: URL completa de Google Sheets o ID del spreadsheet
            
        Returns:
            ID del spreadsheet
            
        Examples:
            >>> extract_spreadsheet_id("https://docs.google.com/spreadsheets/d/1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4/edit")
            '1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4'
            
            >>> extract_spreadsheet_id("1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4")
            '1z29BSwk_n3b-27XAhPME30LTslnYO6xiOoTo3c9yX-4'
        """
        # Si es una URL, extraer el ID usando regex
        if 'docs.google.com' in url_or_id or 'drive.google.com' in url_or_id:
            # Pattern: /d/{SPREADSHEET_ID}/
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_or_id)
            if match:
                return match.group(1)
            else:
                raise ValueError(f"No se pudo extraer el ID del spreadsheet de la URL: {url_or_id}")
        
        # Si no contiene la URL, asumir que ya es un ID
        return url_or_id
    
    def read_range(self, spreadsheet_id: str, range_name: str) -> List[List[str]]:
        """
        Lee un rango de celdas de una hoja de cálculo.
        
        Args:
            spreadsheet_id: ID del spreadsheet o URL completa de Google Sheets
            range_name: Rango a leer (ej: 'Sheet1!A1:B10')
            
        Returns:
            Lista de listas con los valores de las celdas
            
        Raises:
            HttpError: Si hay un error al acceder a la API
        """
        # Extraer ID si se proporciona URL
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_id)
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return values
        
        except HttpError as err:
            print(f"Error al leer Google Sheets: {err}")
            raise
    
    def read_column(self, spreadsheet_id: str, sheet_name: str, column: str) -> List[str]:
        """
        Lee una columna completa de una hoja.
        
        Args:
            spreadsheet_id: ID del spreadsheet o URL completa de Google Sheets
            sheet_name: Nombre de la hoja
            column: Letra de la columna (ej: 'A', 'B')
            
        Returns:
            Lista con los valores de la columna (sin valores vacíos)
        """
        # extract_spreadsheet_id se llama dentro de read_range
        range_name = f"{sheet_name}!{column}:{column}"
        values = self.read_range(spreadsheet_id, range_name)
        
        # Aplanar la lista y remover valores vacíos
        column_values = [row[0] for row in values if row and row[0]]
        return column_values
    
    def get_sheet_metadata(self, spreadsheet_id: str) -> Dict[str, Any]:
        """
        Obtiene metadatos de la hoja de cálculo.
        
        Args:
            spreadsheet_id: ID del spreadsheet o URL completa de Google Sheets
            
        Returns:
            Diccionario con información de la hoja
        """
        # Extraer ID si se proporciona URL
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_id)
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.get(spreadsheetId=spreadsheet_id).execute()
            return result
        
        except HttpError as err:
            print(f"Error al obtener metadatos: {err}")
            raise
