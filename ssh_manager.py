import paramiko
import os
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
    
    def connect(self) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
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
            raise Exception(f"SSH connection failed: {str(e)}")
    
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
    
    def create_remote_archive(self, paths: list, archive_name: str, remote_temp_dir: str = '/tmp') -> str:
        paths_str = ' '.join(paths)
        archive_path = f"{remote_temp_dir}/{archive_name}"
        
        command = f"tar -czf {archive_path} {paths_str} 2>&1"
        
        stdout, stderr, exit_status = self.execute_command(command)
        
        if exit_status != 0:
            raise Exception(f"Failed to create archive: {stderr}")
        
        return archive_path
    
    def download_file(self, remote_path: str, local_path: str):
        if not self.client:
            raise Exception("Not connected to SSH server")
        
        sftp = self.client.open_sftp()
        try:
            sftp.get(remote_path, local_path)
        finally:
            sftp.close()
    
    def remove_remote_file(self, remote_path: str):
        if not self.client:
            raise Exception("Not connected to SSH server")
        
        sftp = self.client.open_sftp()
        try:
            sftp.remove(remote_path)
        finally:
            sftp.close()
    
    def get_file_size(self, remote_path: str) -> int:
        if not self.client:
            raise Exception("Not connected to SSH server")
        
        sftp = self.client.open_sftp()
        try:
            stat = sftp.stat(remote_path)
            return stat.st_size
        finally:
            sftp.close()
