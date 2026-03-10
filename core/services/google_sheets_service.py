"""
Servicio para interactuar con Google Sheets API.
"""
import re
from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .google_auth import get_credentials


class GoogleSheetsService:
    """Servicio para leer y escribir en Google Sheets."""

    def __init__(self):
        self.service = None

    def _get_service(self):
        """Obtiene el servicio de Sheets, autenticando solo cuando se necesita."""
        if self.service is None:
            creds = get_credentials()
            self.service = build("sheets", "v4", credentials=creds)
        return self.service

    @staticmethod
    def extract_spreadsheet_id(url_or_id: str) -> str:
        """
        Extrae el ID del spreadsheet desde una URL de Google Sheets o retorna el ID si ya lo es.

        Args:
            url_or_id: URL completa de Google Sheets o ID del spreadsheet

        Returns:
            ID del spreadsheet
        """
        if 'docs.google.com' in url_or_id or 'drive.google.com' in url_or_id:
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_or_id)
            if match:
                return match.group(1)
            else:
                raise ValueError(f"No se pudo extraer el ID del spreadsheet de la URL: {url_or_id}")
        return url_or_id

    def read_range(self, spreadsheet_id: str, range_name: str) -> List[List[str]]:
        """
        Lee un rango de celdas de una hoja de cálculo.

        Args:
            spreadsheet_id: ID del spreadsheet o URL completa de Google Sheets
            range_name: Rango a leer (ej: 'Sheet1!A1:B10')

        Returns:
            Lista de listas con los valores de las celdas
        """
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_id)

        try:
            service = self._get_service()
            sheet = service.spreadsheets()
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
        range_name = f"{sheet_name}!{column}:{column}"
        values = self.read_range(spreadsheet_id, range_name)
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
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_id)

        try:
            service = self._get_service()
            sheet = service.spreadsheets()
            result = sheet.get(spreadsheetId=spreadsheet_id).execute()
            return result

        except HttpError as err:
            print(f"Error al obtener metadatos: {err}")
            raise
