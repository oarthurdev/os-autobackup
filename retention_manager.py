
import logging
from typing import Dict, List, Optional
from database import Database
from supabase_storage_manager import SupabaseStorageManager

class RetentionManager:
    def __init__(self):
        self.db = Database()
        self.storage_manager = SupabaseStorageManager()
        self.logger = logging.getLogger('RetentionManager')
    
    def apply_retention_policy(self) -> Dict:
        """Aplica a política de retenção e remove backups antigos"""
        try:
            policy = self.db.get_retention_policy()
            
            if not policy or not policy.get('enabled'):
                return {
                    'success': True,
                    'message': 'Política de retenção desabilitada',
                    'removed_count': 0,
                    'freed_space': 0
                }
            
            # Obter backups para remoção
            backups_to_remove = self.db.get_backups_to_cleanup(policy)
            
            if not backups_to_remove:
                return {
                    'success': True,
                    'message': 'Nenhum backup para remover',
                    'removed_count': 0,
                    'freed_space': 0
                }
            
            removed_count = 0
            freed_space = 0
            errors = []
            
            for backup in backups_to_remove:
                try:
                    # Remover do Supabase Storage
                    if backup.get('drive_file_id'):
                        self.storage_manager.delete_file(backup['drive_file_id'])
                    
                    # Marcar como removido no banco (não deletar o registro)
                    self._mark_backup_as_deleted(backup['id'])
                    
                    removed_count += 1
                    freed_space += backup.get('file_size', 0)
                    
                    self.logger.info(f"Backup #{backup['id']} removido pela política de retenção")
                    
                except Exception as e:
                    error_msg = f"Erro ao remover backup #{backup['id']}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                'success': True,
                'message': f'{removed_count} backup(s) removido(s)',
                'removed_count': removed_count,
                'freed_space': freed_space,
                'errors': errors if errors else None
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao aplicar política de retenção: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'removed_count': 0,
                'freed_space': 0
            }
    
    def _mark_backup_as_deleted(self, backup_id: int):
        """Marca backup como deletado (mantém registro histórico)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE backups
            SET drive_file_id = NULL
            WHERE id = ?
        ''', (backup_id,))
        
        conn.commit()
        conn.close()
    
    def get_retention_stats(self) -> Dict:
        """Retorna estatísticas sobre retenção de backups"""
        try:
            policy = self.db.get_retention_policy()
            all_backups = self.db.get_all_backups(limit=1000)
            
            active_backups = [b for b in all_backups if b.get('drive_file_id') and b['status'] == 'SUCCESS']
            total_size = sum(b.get('file_size', 0) for b in active_backups)
            
            if policy and policy.get('enabled'):
                backups_to_remove = self.db.get_backups_to_cleanup(policy)
                removable_size = sum(b.get('file_size', 0) for b in backups_to_remove)
            else:
                backups_to_remove = []
                removable_size = 0
            
            return {
                'total_backups': len(active_backups),
                'total_size': total_size,
                'backups_to_remove': len(backups_to_remove),
                'removable_size': removable_size,
                'policy': policy
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                'total_backups': 0,
                'total_size': 0,
                'backups_to_remove': 0,
                'removable_size': 0,
                'policy': None
            }
