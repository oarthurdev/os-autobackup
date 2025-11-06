import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import Config

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveManager:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        creds = None
        
        if os.path.exists(Config.GOOGLE_DRIVE_TOKEN_FILE):
            with open(Config.GOOGLE_DRIVE_TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(Config.GOOGLE_DRIVE_CREDENTIALS_FILE):
                    raise Exception(
                        f"Google Drive credentials file not found: {Config.GOOGLE_DRIVE_CREDENTIALS_FILE}\n"
                        "Please download credentials.json from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.GOOGLE_DRIVE_CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(Config.GOOGLE_DRIVE_TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def upload_file(self, file_path: str, file_name: str = None, folder_id: str = None) -> str:
        if not file_name:
            file_name = os.path.basename(file_path)
        
        file_metadata = {'name': file_name}
        
        if folder_id or Config.GOOGLE_DRIVE_FOLDER_ID:
            file_metadata['parents'] = [folder_id or Config.GOOGLE_DRIVE_FOLDER_ID]
        
        media = MediaFileUpload(file_path, resumable=True)
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return file.get('id')
    
    def get_file_link(self, file_id: str) -> str:
        file = self.service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        
        return file.get('webViewLink', '')
    
    def delete_file(self, file_id: str):
        self.service.files().delete(fileId=file_id).execute()
    
    def list_files(self, folder_id: str = None, max_results: int = 100) -> list:
        query = f"'{folder_id or Config.GOOGLE_DRIVE_FOLDER_ID}' in parents" if (folder_id or Config.GOOGLE_DRIVE_FOLDER_ID) else None
        
        results = self.service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, createdTime, size, webViewLink)"
        ).execute()
        
        return results.get('files', [])
