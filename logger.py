import logging
import os
from datetime import datetime
from config import Config

class BackupLogger:
    def __init__(self, backup_id: int = None):
        self.backup_id = backup_id
        
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        
        log_file = os.path.join(Config.LOGS_DIR, f'backup_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)
