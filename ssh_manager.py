import paramiko
import os
import shlex
from typing import Optional
from config import Config

class SSHManager:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, username: Optional[str] = None,
                 password: Optional[str] = None, key_path: Optional[str] = None):
        self.host = host or Config.VPS_HOST
        self.port = port or Config.VPS_PORT
        self.username = username or Config.VPS_USERNAME
        self.password = password or Config.VPS_PASSWORD
        self.key_path = key_path or Config.VPS_KEY_PATH
        self.client = None
        self.logger = None # Assume self.logger is initialized elsewhere

    def connect(self) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()

            known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
            if os.path.exists(known_hosts_path):
                self.client.load_host_keys(known_hosts_path)

            self.client.set_missing_host_key_policy(paramiko.RejectPolicy())

            if self.key_path and os.path.exists(self.key_path):
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=30
                )
            elif self.password:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )
            else:
                raise Exception("No authentication method provided (password or key)")

            return True
        except Exception as e:
            error_msg = f"Falha na conexão SSH: {str(e)}"
            if "Name or service not known" in str(e):
                error_msg = f"Falha na conexão: Host '{self.host}' não encontrado. Verifique o endereço IP/hostname."
            elif "Authentication failed" in str(e):
                error_msg = "Falha na autenticação. Verifique usuário e senha/chave SSH."
            elif "No such file or directory" in str(e):
                error_msg = f"Caminho não encontrado no servidor: {str(e)}"

            if self.logger: # Check if logger is initialized
                self.logger.error(error_msg)
            if self.client:
                self.client.close()
            raise Exception(error_msg)

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None

    def execute_command(self, command: str) -> tuple:
        if not self.client:
            raise Exception("Not connected to SSH server")

        stdin, stdout, stderr = self.client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()

        return stdout.read().decode('utf-8'), stderr.read().decode('utf-8'), exit_status

    def get_directory_size(self, paths: list) -> int:
        """Estima o tamanho total dos diretórios a serem backupeados, excluindo diretórios virtuais."""
        try:
            # Diretórios a excluir da estimativa (mesmos que serão excluídos do backup)
            exclude_dirs = [
                'proc', 'sys', 'dev', 'run', 'tmp',
                'mnt', 'media', 'lost+found', 'snap',
                'var/cache', 'var/tmp', 'var/run', 'var/lock'
            ]
            
            # Construir exclusões para o comando du
            exclude_str = ' '.join([f'--exclude="{d}"' for d in exclude_dirs])
            
            paths_str = ' '.join([f'"{p}"' for p in paths])
            command = f'du -sb {exclude_str} {paths_str} 2>/dev/null | awk \'{{sum+=$1}} END {{print sum}}\''

            stdin, stdout, stderr = self.client.exec_command(command, timeout=60)
            output = stdout.read().decode().strip()

            return int(output) if output and output.isdigit() else 0
        except Exception as e:
            # Se falhar, retornar 0 (sem estimativa)
            return 0

    def create_remote_archive(self, paths: list, archive_name: str, progress_callback=None, use_fast_compression=None) -> str:
        validated_paths = []
        total_size = 0

        # Exclusions for virtual filesystems and unnecessary directories
        # These should be excluded especially when backing up root "/"
        exclusions = [
            '/proc/*', '/sys/*', '/dev/*', '/run/*', '/tmp/*',
            '/mnt/*', '/media/*', '/lost+found/*', '/snap/*',
            '/var/cache/*', '/var/tmp/*', '/var/run/*',
            '/var/lock/*', '/swapfile',
            '*.cache', '*.tmp', '*~', '*.swp', '*.swo',
            '__pycache__/*', '.cache/*', '.tmp/*'
        ]

        for path in paths:
            if not self._is_safe_path(path):
                raise ValueError(f"Invalid or unsafe path: {path}")
            validated_paths.append(shlex.quote(path))

        # Use the new method to estimate total size for the progress callback
        total_size = self.get_directory_size(paths)

        paths_str = ' '.join(validated_paths)
        remote_temp_dir = '/tmp'
        remote_archive_path = f"{remote_temp_dir}/{archive_name}"

        # Build exclusion string with proper zip syntax
        # zip expects: -x "pattern1" "pattern2" ...
        exclude_parts = ' '.join([f'"{e}"' for e in exclusions])
        exclude_str = f'-x {exclude_parts}' if exclusions else ''

        # Optimize compression level based on file size
        # ZIP compression levels: 0 (no compression) to 9 (best compression)
        # Level 1-3 for large files (faster), level 6 for smaller files (balanced)
        if total_size >= 5 * 1024 * 1024 * 1024:  # >5GB: minimal compression
            compression_level = "1"
            compression_info = "compressão mínima (mais rápido)"
        elif total_size >= 1 * 1024 * 1024 * 1024:  # >1GB: fast compression
            compression_level = "3"
            compression_info = "compressão rápida"
        else:
            compression_level = "6"
            compression_info = "compressão balanceada"

        # Use zip command with compression level
        zip_command = f"""
            cd / && zip -{compression_level} -r {shlex.quote(remote_archive_path)} {paths_str} {exclude_str} 2>&1
        """

        if progress_callback and total_size >= 1073741824:
            progress_callback(f"Tamanho estimado: {total_size / (1024*1024):.2f} MB - usando {compression_info}")

        stdout, stderr, exit_status = self.execute_command(zip_command)

        if exit_status != 0 and "nothing to do" not in stderr.lower():
            if "No such file or directory" in stderr:
                raise Exception(f"Failed to create archive: One or more specified paths do not exist on the server. Details: {stderr}")
            else:
                raise Exception(f"Failed to create archive: {stderr}")

        # Verificar o tamanho do arquivo criado
        if progress_callback:
            stat_command = f"stat -c%s {shlex.quote(remote_archive_path)} 2>/dev/null"
            stdout_stat, _, exit_status_stat = self.execute_command(stat_command)
            if exit_status_stat == 0:
                try:
                    archive_size = int(stdout_stat.strip())
                    progress_callback(f"Arquivo ZIP criado: {self._format_bytes(archive_size)}")
                except ValueError:
                    if self.logger:
                        self.logger.warning(f"Could not parse archive size: '{stdout_stat.strip()}'")
            else:
                if self.logger:
                    self.logger.warning(f"Could not get archive size for '{remote_archive_path}'.")

        return remote_archive_path

    def _is_safe_path(self, path: str) -> bool:
        # More robust check: disallow empty paths, paths with '..', and paths starting with '-'
        # Also ensure paths don't contain problematic characters that shlex.quote might miss
        # and check for absolute paths that might be unintended.
        cleaned_path = path.strip()
        if not cleaned_path:
            return False
        if '..' in cleaned_path:
            return False
        if cleaned_path.startswith('-'):
            return False
        # Optionally, disallow absolute paths if they are not intended for backups and should be relative to user's home
        # if cleaned_path.startswith('/'):
        #     return False
        return True

    def _format_bytes(self, bytes_size: int) -> str:
        """Formata bytes para formato legível"""
        if bytes_size < 0:
            return "Invalid size"
        size_float = float(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_float < 1024.0:
                return f"{size_float:.2f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.2f} PB"

    def download_file(self, remote_path: str, local_path: str):
        if not self.client:
            raise Exception("Not connected to SSH server")

        sftp = self.client.open_sftp()
        try:
            sftp.get(remote_path, local_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}")
        except Exception as e:
            raise Exception(f"Error downloading file {remote_path} to {local_path}: {str(e)}")
        finally:
            sftp.close()

    def remove_remote_file(self, remote_path: str):
        if not self.client:
            raise Exception("Not connected to SSH server")

        sftp = self.client.open_sftp()
        try:
            sftp.remove(remote_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}")
        except Exception as e:
            raise Exception(f"Error removing remote file {remote_path}: {str(e)}")
        finally:
            sftp.close()

    def get_file_size(self, remote_path: str) -> int:
        if not self.client:
            raise Exception("Not connected to SSH server")

        sftp = self.client.open_sftp()
        try:
            stat = sftp.stat(remote_path)
            file_size = stat.st_size
            if file_size is None:
                raise Exception(f"Could not get file size for {remote_path}")
            return file_size
        except FileNotFoundError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}")
        except Exception as e:
            raise Exception(f"Error getting file size for {remote_path}: {str(e)}")
        finally:
            sftp.close()

    def download_file_streaming(self, remote_path: str, local_path: str,
                                progress_callback=None) -> int:
        """
        Download a file from the remote server with progress tracking.

        Args:
            remote_path: Path to the file on the remote server
            local_path: Path where the file will be saved locally
            progress_callback: Optional callback function for progress updates

        Returns:
            int: Size of the downloaded file in bytes
        """
        if not self.client:
            raise Exception("Not connected to SSH server")

        sftp = self.client.open_sftp()
        total_downloaded = 0

        try:
            # Get file size for progress tracking
            file_stat = sftp.stat(remote_path)
            file_size = file_stat.st_size

            if file_size is None or file_size <= 0:
                raise Exception(f"Invalid file size for {remote_path}")
            
            # Optimize chunk size based on file size
            if file_size > 5 * 1024 * 1024 * 1024:  # > 5GB
                chunk_size = 8 * 1024 * 1024  # 8MB chunks
            elif file_size > 1 * 1024 * 1024 * 1024:  # > 1GB
                chunk_size = 4 * 1024 * 1024  # 4MB chunks
            else:
                chunk_size = 1024 * 1024  # 1MB chunks

            if progress_callback:
                progress_callback(f"Iniciando download de {self._format_bytes(file_size)} (chunks de {chunk_size // (1024*1024)}MB)")

            # Enable prefetching for better performance on large files
            if hasattr(sftp, 'get_channel'):
                channel = sftp.get_channel()
                if hasattr(channel, 'settimeout'):
                    channel.settimeout(300)  # 5 minute timeout for large files
            
            # Open remote file for reading
            with sftp.open(remote_path, 'rb') as remote_file:
                # Enable prefetching for SFTP to reduce latency
                if hasattr(remote_file, 'prefetch'):
                    remote_file.prefetch(file_size)
                
                with open(local_path, 'wb') as local_file:
                    try:
                        # Read and write in chunks
                        while True:
                            chunk = remote_file.read(chunk_size)
                            if not chunk:
                                break

                            local_file.write(chunk)
                            total_downloaded += len(chunk)

                            # Dynamic progress update frequency based on file size
                            progress_interval = 50 * 1024 * 1024 if file_size > 5 * 1024 * 1024 * 1024 else 10 * 1024 * 1024
                            if progress_callback and file_size > 0 and total_downloaded % progress_interval < chunk_size:
                                percentage = (total_downloaded / file_size) * 100
                                progress_callback(f"Baixado: {self._format_bytes(total_downloaded)} ({percentage:.1f}%)")

                        if progress_callback:
                            progress_callback(f"Download concluído: {self._format_bytes(total_downloaded)}")

                    except Exception as e:
                        # Clean up partial file on error
                        if os.path.exists(local_path):
                            os.remove(local_path)
                        raise Exception(f"Error during streaming download: {str(e)}")

            # Get the size of the downloaded file
            file_size_final = os.path.getsize(local_path)
            return file_size_final

        except FileNotFoundError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}")
        except Exception as e:
            if "streaming download" not in str(e):
                raise Exception(f"Error in streaming download: {str(e)}")
            raise
        finally:
            sftp.close()