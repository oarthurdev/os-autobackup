from database import Database
from credentials_manager import CredentialsManager
from ssh_manager import SSHManager
from typing import List, Dict, Optional

class SSHHostManager:
    def __init__(self):
        self.db = Database()
        self.creds_manager = CredentialsManager()
    
    def add_host(self, name: str, host: str, port: int, username: str,
                 auth_type: str, password: str = '', key_path: str = '',
                 backup_paths: str = '/home') -> int:
        encrypted_password = self.creds_manager.encrypt(password) if password else ''
        encrypted_key_path = self.creds_manager.encrypt(key_path) if key_path else ''
        
        host_id = self.db.create_ssh_host(
            name=name,
            host=host,
            port=port,
            username=username,
            auth_type=auth_type,
            encrypted_password=encrypted_password,
            encrypted_key_path=encrypted_key_path,
            backup_paths=backup_paths
        )
        
        return host_id
    
    def update_host(self, host_id: int, name: str, host: str, port: int,
                   username: str, auth_type: str, password: str = '',
                   key_path: str = '', backup_paths: str = '/home'):
        current_host = self.db.get_ssh_host(host_id)
        
        if not current_host:
            raise Exception(f"Host with ID {host_id} not found")
        
        if password:
            encrypted_password = self.creds_manager.encrypt(password)
        else:
            encrypted_password = current_host['encrypted_password']
        
        if key_path:
            encrypted_key_path = self.creds_manager.encrypt(key_path)
        else:
            encrypted_key_path = current_host['encrypted_key_path']
        
        self.db.update_ssh_host(
            host_id=host_id,
            name=name,
            host=host,
            port=port,
            username=username,
            auth_type=auth_type,
            encrypted_password=encrypted_password,
            encrypted_key_path=encrypted_key_path,
            backup_paths=backup_paths
        )
    
    def delete_host(self, host_id: int):
        self.db.delete_ssh_host(host_id)
    
    def get_all_hosts(self) -> List[Dict]:
        hosts = self.db.get_all_ssh_hosts()
        
        for host in hosts:
            host.pop('encrypted_password', None)
            host.pop('encrypted_key_path', None)
        
        return hosts
    
    def get_host(self, host_id: int) -> Optional[Dict]:
        host = self.db.get_ssh_host(host_id)
        
        if host:
            host.pop('encrypted_password', None)
            host.pop('encrypted_key_path', None)
        
        return host
    
    def get_ssh_manager(self, host_id: int) -> SSHManager:
        host = self.db.get_ssh_host(host_id)
        
        if not host:
            raise Exception(f"Host with ID {host_id} not found")
        
        password = self.creds_manager.decrypt(host['encrypted_password']) if host['encrypted_password'] else ''
        key_path = self.creds_manager.decrypt(host['encrypted_key_path']) if host['encrypted_key_path'] else ''
        
        return SSHManager(
            host=host['host'],
            port=host['port'],
            username=host['username'],
            password=password,
            key_path=key_path
        )
    
    def test_connection(self, host_id: int) -> Dict:
        try:
            ssh_manager = self.get_ssh_manager(host_id)
            ssh_manager.connect()
            ssh_manager.disconnect()
            
            self.db.update_ssh_host_connection_status(host_id, 'SUCCESS')
            
            return {
                'success': True,
                'message': 'Conexão estabelecida com sucesso'
            }
        except Exception as e:
            error_msg = str(e)
            self.db.update_ssh_host_connection_status(host_id, f'FAILED: {error_msg}')
            
            return {
                'success': False,
                'message': f'Falha na conexão: {error_msg}'
            }
    
    def get_backup_paths(self, host_id: int) -> List[str]:
        host = self.db.get_ssh_host(host_id)
        
        if not host:
            raise Exception(f"Host with ID {host_id} not found")
        
        return [path.strip() for path in host['backup_paths'].split(',') if path.strip()]
