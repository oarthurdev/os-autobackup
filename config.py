import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    VPS_HOST = os.getenv('VPS_HOST', 'localhost')
    VPS_PORT = int(os.getenv('VPS_PORT', 22))
    VPS_USERNAME = os.getenv('VPS_USERNAME', 'root')
    VPS_PASSWORD = os.getenv('VPS_PASSWORD', '')
    VPS_KEY_PATH = os.getenv('VPS_KEY_PATH', '')
    
    BACKUP_PATHS = os.getenv('BACKUP_PATHS', '/home').split(',')
    
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
    
    GOOGLE_DRIVE_CREDENTIALS_FILE = os.getenv('GOOGLE_DRIVE_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_DRIVE_TOKEN_FILE = os.getenv('GOOGLE_DRIVE_TOKEN_FILE', 'token.json')
    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
    
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    DATABASE_PATH = 'backups.db'
    LOGS_DIR = 'logs'
    TEMP_DIR = 'temp_backups'
