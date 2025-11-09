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
    
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
    SUPABASE_BUCKET_NAME = os.getenv('SUPABASE_BUCKET_NAME', 'backups')
    
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    DATABASE_PATH = 'backups.db'
    LOGS_DIR = 'logs'
    TEMP_DIR = 'temp_backups'
    
    # Performance settings for large files
    STREAMING_CHUNK_SIZE = int(os.getenv('STREAMING_CHUNK_SIZE', 8388608))  # 8MB default
    LARGE_FILE_THRESHOLD = int(os.getenv('LARGE_FILE_THRESHOLD', 1073741824))  # 1GB
    USE_FAST_COMPRESSION = os.getenv('USE_FAST_COMPRESSION', 'true').lower() == 'true'
