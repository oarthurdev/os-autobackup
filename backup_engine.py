import os
import time
from datetime import datetime
from ssh_manager import SSHManager
from encryption import Encryptor
from drive_manager import GoogleDriveManager
from database import Database
from logger import BackupLogger
from config import Config
from ssh_host_manager import SSHHostManager

class BackupEngine:
    def __init__(self):
        self.db = Database()
        self.logger = None
        self.ssh_host_manager = SSHHostManager()
        self.progress = {
            'status': 'idle',
            'current_step': '',
            'percentage': 0,
            'total_steps': 7,
            'current_step_number': 0
        }
        
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
    
    def update_progress(self, step_number: int, step_name: str):
        self.progress['current_step_number'] = step_number
        self.progress['current_step'] = step_name
        self.progress['percentage'] = int((step_number / self.progress['total_steps']) * 100)
        self.progress['status'] = 'in_progress'
    
    def reset_progress(self):
        self.progress = {
            'status': 'idle',
            'current_step': '',
            'percentage': 0,
            'total_steps': 7,
            'current_step_number': 0
        }
    
    def get_progress(self):
        return self.progress.copy()
    
    def perform_backup(self, host_id: int = None, paths: list = None) -> dict:
        start_time = datetime.now()
        start_time_str = start_time.isoformat()
        
        self.reset_progress()
        self.update_progress(1, 'Iniciando backup...')
        
        backup_id = self.db.create_backup_record(start_time_str)
        self.logger = BackupLogger(backup_id)
        
        self.logger.info(f"Starting backup process (ID: {backup_id})")
        self.db.add_log(backup_id, 'INFO', 'Backup process started')
        
        ssh_manager = None
        local_archive = None
        encrypted_archive = None
        remote_archive = None
        
        try:
            if host_id:
                ssh_manager = self.ssh_host_manager.get_ssh_manager(host_id)
                if not paths:
                    paths = self.ssh_host_manager.get_backup_paths(host_id)
                host_info = self.ssh_host_manager.get_host(host_id)
                host_name = host_info['name'] if host_info else f"Host {host_id}"
            else:
                if not paths:
                    paths = Config.BACKUP_PATHS
                ssh_manager = SSHManager()
                host_name = Config.VPS_HOST
            
            self.logger.info(f"Backup paths: {', '.join(paths)}")
            self.db.add_log(backup_id, 'INFO', f"Paths to backup: {', '.join(paths)}")
            
            self.update_progress(2, f'Conectando ao servidor {host_name}...')
            self.logger.info(f"Connecting to {host_name} via SSH...")
            self.db.add_log(backup_id, 'INFO', f"Connecting to {host_name}")
            ssh_manager.connect()
            self.logger.info("SSH connection established")
            self.db.add_log(backup_id, 'INFO', 'SSH connection successful')
            
            archive_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            self.update_progress(3, 'Criando arquivo de backup no servidor...')
            self.logger.info(f"Creating remote archive: {archive_name}")
            self.db.add_log(backup_id, 'INFO', f"Creating archive: {archive_name}")
            
            def archive_progress_callback(message):
                self.update_progress(3, f'Criando arquivo de backup: {message}')
                self.logger.info(message)
                self.db.add_log(backup_id, 'INFO', message)
            
            remote_archive = ssh_manager.create_remote_archive(paths, archive_name, progress_callback=archive_progress_callback)
            self.logger.info(f"Remote archive created: {remote_archive}")
            self.db.add_log(backup_id, 'INFO', 'Archive creation completed')
            
            local_archive = os.path.join(Config.TEMP_DIR, archive_name)
            encrypted_name = archive_name.replace('.tar.gz', '.encrypted')
            encrypted_archive = os.path.join(Config.TEMP_DIR, encrypted_name)
            
            self.update_progress(4, 'Baixando e criptografando arquivo (streaming)...')
            self.logger.info(f"Streaming download and encryption: {remote_archive}")
            self.db.add_log(backup_id, 'INFO', 'Starting streaming download and encryption')
            
            encryptor = Encryptor()
            file_size = ssh_manager.download_and_encrypt_streaming(
                remote_archive, 
                encrypted_archive,
                encryptor,
                progress_callback=lambda msg: self.db.add_log(backup_id, 'INFO', msg)
            )
            
            self.logger.info(f"Streaming completed ({file_size} bytes)")
            self.db.add_log(backup_id, 'INFO', f'Downloaded and encrypted {file_size} bytes')
            
            self.logger.info("Cleaning up remote archive")
            ssh_manager.remove_remote_file(remote_archive)
            ssh_manager.disconnect()
            
            self.update_progress(6, 'Enviando para Google Drive...')
            self.logger.info("Uploading to Google Drive...")
            self.db.add_log(backup_id, 'INFO', 'Uploading to Google Drive')
            
            drive_manager = GoogleDriveManager()
            drive_file_id = drive_manager.upload_file(encrypted_archive, encrypted_name)
            
            self.logger.info(f"Upload completed. File ID: {drive_file_id}")
            self.db.add_log(backup_id, 'INFO', f'Upload completed: {drive_file_id}')
            
            os.remove(encrypted_archive)
            
            self.update_progress(7, 'Backup concluído com sucesso!')
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.db.update_backup_record(
                backup_id=backup_id,
                status='SUCCESS',
                file_name=encrypted_name,
                file_size=file_size,
                drive_file_id=drive_file_id,
                end_time=end_time.isoformat(),
                duration_seconds=duration
            )
            
            self.logger.info(f"Backup completed successfully in {duration:.2f} seconds")
            self.db.add_log(backup_id, 'INFO', f'Backup completed ({duration:.2f}s)')
            
            self.progress['status'] = 'completed'
            
            return {
                'success': True,
                'backup_id': backup_id,
                'file_name': encrypted_name,
                'file_size': file_size,
                'drive_file_id': drive_file_id,
                'duration': duration
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Backup failed: {error_msg}")
            self.db.add_log(backup_id, 'ERROR', error_msg)
            
            self.progress['status'] = 'failed'
            self.progress['current_step'] = f'Erro: {error_msg}'
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.db.update_backup_record(
                backup_id=backup_id,
                status='FAILED',
                error_message=error_msg,
                end_time=end_time.isoformat(),
                duration_seconds=duration
            )
            
            if ssh_manager:
                try:
                    if remote_archive:
                        ssh_manager.remove_remote_file(remote_archive)
                    ssh_manager.disconnect()
                except:
                    pass
            
            if local_archive and os.path.exists(local_archive):
                os.remove(local_archive)
            if encrypted_archive and os.path.exists(encrypted_archive):
                os.remove(encrypted_archive)
            
            return {
                'success': False,
                'backup_id': backup_id,
                'error': error_msg,
                'duration': duration
            }
    
    def get_backup_history(self, limit: int = 100) -> list:
        return self.db.get_all_backups(limit)
    
    def get_backup_logs(self, backup_id: int) -> list:
        return self.db.get_backup_logs(backup_id)
