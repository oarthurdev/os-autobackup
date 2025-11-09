import os
import time
from datetime import datetime
from typing import Optional
from ssh_manager import SSHManager
from supabase_storage_manager import SupabaseStorageManager
from database import Database
from logger import BackupLogger
from config import Config
from ssh_host_manager import SSHHostManager

class BackupEngine:
    def __init__(self):
        self.db = Database()
        self.logger = None
        self.ssh_host_manager = SSHHostManager()

        # Peso relativo de cada etapa (baseado em experiência com arquivos grandes)
        self.step_weights = {
            1: 1,   # Iniciando backup
            2: 2,   # Conectando ao servidor
            3: 40,  # Criando arquivo ZIP (compressão) - MAIS DEMORADO
            4: 30,  # Download
            5: 5,   # Limpeza remota
            6: 20,  # Upload para Supabase Storage
            7: 2    # Finalização
        }

        self.total_weight = sum(self.step_weights.values())

        self.progress = {
            'status': 'idle',
            'current_step': '',
            'percentage': 0,
            'total_steps': 7,
            'current_step_number': 0,
            'start_time': None,
            'estimated_time_remaining': None,
            'estimated_file_size': None,
            'step_start_times': {}
        }

        os.makedirs(Config.TEMP_DIR, exist_ok=True)

    def update_progress(self, step_number: int, step_name: str, estimated_size_mb: Optional[float] = None):
        self.progress['current_step_number'] = step_number
        self.progress['current_step'] = step_name

        # Registrar tempo de início da etapa
        self.progress['step_start_times'][step_number] = time.time()

        # Calcular porcentagem baseada em pesos
        completed_weight = sum(self.step_weights[i] for i in range(1, step_number))
        self.progress['percentage'] = int((completed_weight / self.total_weight) * 100)
        self.progress['status'] = 'in_progress'

        # Armazenar tamanho estimado do arquivo
        if estimated_size_mb:
            self.progress['estimated_file_size'] = estimated_size_mb

        # Calcular tempo estimado total restante (englobando todas as etapas)
        if self.progress['start_time'] and step_number > 1:
            elapsed_time = time.time() - self.progress['start_time']

            # Peso completado até agora
            completed_weight = sum(self.step_weights[i] for i in range(1, step_number))

            # Peso restante
            remaining_weight = self.total_weight - completed_weight

            if completed_weight > 0:
                # Tempo médio por unidade de peso já processada
                time_per_weight_unit = elapsed_time / completed_weight

                # Estimativa base do tempo restante
                base_estimate = time_per_weight_unit * remaining_weight

                # Ajuste fino baseado no tamanho do arquivo (mais conservador)
                if self.progress.get('estimated_file_size'):
                    size_mb = self.progress['estimated_file_size']

                    # Fator de ajuste mais realista baseado no tamanho
                    # Apenas para arquivos muito grandes e apenas nas etapas pesadas
                    if size_mb > 3000 and step_number <= 4:  # > 3GB e ainda nas etapas pesadas
                        # Pequeno ajuste incremental (máximo 30% extra)
                        size_factor = min(1 + (size_mb / 10000), 1.3)
                        base_estimate *= size_factor
                    elif size_mb > 1000 and step_number <= 4:  # > 1GB
                        # Ajuste menor (máximo 15% extra)
                        size_factor = min(1 + (size_mb / 20000), 1.15)
                        base_estimate *= size_factor

                self.progress['estimated_time_remaining'] = int(base_estimate)
            else:
                self.progress['estimated_time_remaining'] = None

    def reset_progress(self):
        self.progress = {
            'status': 'idle',
            'current_step': '',
            'percentage': 0,
            'total_steps': 7,
            'current_step_number': 0,
            'start_time': None,
            'estimated_time_remaining': None,
            'estimated_file_size': None,
            'step_start_times': {}
        }

    def get_progress(self):
        return self.progress.copy()

    def perform_backup(self, host_id: Optional[int] = None, paths: Optional[list] = None) -> dict:
        start_time = datetime.now()
        start_time_str = start_time.isoformat()

        self.reset_progress()
        self.progress['start_time'] = time.time()
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

            archive_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

            # Estimar tamanho dos diretórios antes de criar o arquivo
            estimated_size_mb = None
            try:
                total_size = ssh_manager.get_directory_size(paths)
                estimated_size_mb = total_size / (1024 * 1024)  # Converter para MB
                self.logger.info(f"Estimated backup size: {estimated_size_mb:.2f} MB")
                self.db.add_log(backup_id, 'INFO', f"Tamanho estimado: {estimated_size_mb:.2f} MB")
            except Exception as e:
                self.logger.warning(f"Could not estimate size: {e}")

            self.update_progress(3, 'Criando arquivo de backup no servidor...', estimated_size_mb)
            self.logger.info(f"Creating remote archive: {archive_name}")
            self.db.add_log(backup_id, 'INFO', f"Creating archive: {archive_name}")

            def archive_progress_callback(message):
                self.update_progress(3, f'Criando arquivo de backup: {message}', estimated_size_mb)
                if self.logger:
                    self.logger.info(message)
                self.db.add_log(backup_id, 'INFO', message)

            remote_archive = ssh_manager.create_remote_archive(paths, archive_name, progress_callback=archive_progress_callback)
            self.logger.info(f"Remote archive created: {remote_archive}")
            self.db.add_log(backup_id, 'INFO', 'Archive creation completed')

            local_archive = os.path.join(Config.TEMP_DIR, archive_name)

            self.update_progress(4, 'Baixando arquivo ZIP...')
            self.logger.info(f"Streaming download: {remote_archive}")
            self.db.add_log(backup_id, 'INFO', 'Starting download')

            file_size = ssh_manager.download_file_streaming(
                remote_archive, 
                local_archive,
                progress_callback=lambda msg: self.db.add_log(backup_id, 'INFO', msg)
            )

            self.logger.info(f"Download completed ({file_size} bytes)")
            self.db.add_log(backup_id, 'INFO', f'Downloaded {file_size} bytes')

            self.update_progress(5, 'Limpando arquivos temporários no servidor...')
            self.logger.info("Cleaning up remote archive")
            ssh_manager.remove_remote_file(remote_archive)
            ssh_manager.disconnect()

            self.update_progress(6, 'Enviando para Supabase Storage...')
            self.logger.info("Uploading to Supabase Storage...")
            self.db.add_log(backup_id, 'INFO', 'Uploading to Supabase Storage')

            storage_manager = SupabaseStorageManager()
            try:
                self.logger.info("Uploading to Supabase Storage...")
                self.update_progress(6, 'Enviando para Supabase Storage...', estimated_size_mb)
                storage_file_id = storage_manager.upload_file(local_archive, archive_name)
                self.logger.info(f"Upload completed. File: {storage_file_id}")
                self.db.add_log(backup_id, 'INFO', f'Upload completed: {storage_file_id}')
            except Exception as e:
                error_msg = f"Supabase Storage upload failed: {str(e)}"
                self.logger.error(error_msg)
                self.db.add_log(backup_id, 'ERROR', error_msg)
                storage_file_id = None
                raise

            os.remove(local_archive)

            self.update_progress(7, 'Backup concluído com sucesso!')

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.db.update_backup_record(
                backup_id=backup_id,
                status='SUCCESS',
                file_name=archive_name,
                file_size=file_size,
                drive_file_id=storage_file_id,
                end_time=end_time.isoformat(),
                duration_seconds=duration
            )

            self.logger.info(f"Backup completed successfully in {duration:.2f} seconds")
            self.db.add_log(backup_id, 'INFO', f'Backup completed ({duration:.2f}s)')

            self.progress['status'] = 'completed'

            return {
                'success': True,
                'backup_id': backup_id,
                'file_name': archive_name,
                'file_size': file_size,
                'storage_file_id': storage_file_id,
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