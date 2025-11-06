import paramiko
import os
import shlex
from typing import Optional
from config import Config

class SSHManager:
    def __init__(self, host: str = None, port: int = None, username: str = None,
                 password: str = None, key_path: str = None):
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

    def create_remote_archive(self, paths: list, archive_name: str, progress_callback=None, use_fast_compression=None) -> str:
        validated_paths = []
        total_size = 0

        for path in paths:
            if not self._is_safe_path(path):
                raise ValueError(f"Invalid or potentially unsafe path: {path}")
            validated_paths.append(shlex.quote(path))

            # Estimate total size
            try:
                size_cmd = f"du -sb {shlex.quote(path)} | cut -f1"
                stdout_size, stderr_size, exit_status_size = self.execute_command(size_cmd)
                if exit_status_size == 0:
                    size_str = stdout_size.strip()
                    if size_str.isdigit():
                        total_size += int(size_str)
                else:
                    # If 'du' fails for a path, we might still want to proceed but log the issue
                    if self.logger:
                        self.logger.warning(f"Could not get size for path '{path}': {stderr_size}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Error estimating size for path '{path}': {e}")
                # Continue even if size estimation fails for one path

        paths_str = ' '.join(validated_paths)
        remote_temp_dir = '/tmp' # Default temporary directory
        remote_archive_path = f"{remote_temp_dir}/{archive_name}"

        # Use faster compression for files >= 1GB
        if use_fast_compression is None:
            use_fast_compression = total_size >= 1073741824  # 1GB

        # --fast uses gzip level 1 (faster, slightly larger files)
        # For very large files, speed is more important than size
        compression_flag = "--fast" if use_fast_compression else ""

        tar_command = f"tar {compression_flag} -czf {shlex.quote(remote_archive_path)} {paths_str}"

        if progress_callback and total_size >= 1073741824:
            progress_callback(f"Tamanho estimado: {total_size / (1024*1024):.2f} MB - usando compressão rápida")

        stdout, stderr, exit_status = self.execute_command(tar_command)

        if exit_status != 0:
            # Attempt to provide a more specific error if the path itself was the issue
            if "No such file or directory" in stderr:
                raise Exception(f"Failed to create archive: One or more specified paths do not exist on the server. Details: {stderr}")
            else:
                raise Exception(f"Failed to create archive: {stderr}")

        # Verificar o tamanho do arquivo criado
        if progress_callback:
            # Correctly quote the remote_archive_path for the stat command
            stat_command = f"stat -c%s {shlex.quote(remote_archive_path)} 2>/dev/null"
            stdout_stat, _, exit_status_stat = self.execute_command(stat_command)
            if exit_status_stat == 0:
                try:
                    archive_size = int(stdout_stat.strip())
                    progress_callback(f"Arquivo compactado criado: {self._format_bytes(archive_size)}")
                except ValueError:
                    if self.logger:
                        self.logger.warning(f"Could not parse archive size: '{stdout_stat.strip()}'")
            else:
                if self.logger:
                    self.logger.warning(f"Could not get archive size for '{remote_archive_path}'.")


        return remote_archive_path # Return the full path where the archive was created

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
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

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
            return stat.st_size
        except FileNotFoundError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}")
        except Exception as e:
            raise Exception(f"Error getting file size for {remote_path}: {str(e)}")
        finally:
            sftp.close()