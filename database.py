import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os
from config import Config

class Database:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                file_name TEXT,
                file_size INTEGER,
                drive_file_id TEXT,  -- Nome mantido para compatibilidade; armazena ID do arquivo no Supabase Storage
                error_message TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_seconds REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id INTEGER,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY (backup_id) REFERENCES backups (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ssh_hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                username TEXT NOT NULL,
                auth_type TEXT NOT NULL,
                encrypted_password TEXT,
                encrypted_key_path TEXT,
                backup_paths TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_connection_test TEXT,
                connection_status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ssh_host_id INTEGER NOT NULL,
                schedule_type TEXT NOT NULL,
                schedule_value TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_run TEXT,
                next_run TEXT,
                FOREIGN KEY (ssh_host_id) REFERENCES ssh_hosts (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_backup_record(self, start_time: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO backups (timestamp, status, start_time)
            VALUES (?, ?, ?)
        ''', (start_time, 'IN_PROGRESS', start_time))
        
        backup_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return backup_id
    
    def update_backup_record(self, backup_id: int, status: str, file_name: str = None,
                            file_size: int = None, drive_file_id: str = None,
                            error_message: str = None, end_time: str = None,
                            duration_seconds: float = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE backups
            SET status = ?, file_name = ?, file_size = ?, drive_file_id = ?,
                error_message = ?, end_time = ?, duration_seconds = ?
            WHERE id = ?
        ''', (status, file_name, file_size, drive_file_id, error_message,
              end_time, duration_seconds, backup_id))
        
        conn.commit()
        conn.close()
    
    def add_log(self, backup_id: int, level: str, message: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO logs (backup_id, timestamp, level, message)
            VALUES (?, ?, ?, ?)
        ''', (backup_id, timestamp, level, message))
        
        conn.commit()
        conn.close()
    
    def get_all_backups(self, limit: int = 100) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM backups
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_backup_logs(self, backup_id: int) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM logs
            WHERE backup_id = ?
            ORDER BY timestamp ASC
        ''', (backup_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_latest_backup(self) -> Optional[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM backups
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def create_ssh_host(self, name: str, host: str, port: int, username: str,
                       auth_type: str, encrypted_password: str, encrypted_key_path: str,
                       backup_paths: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO ssh_hosts 
            (name, host, port, username, auth_type, encrypted_password, 
             encrypted_key_path, backup_paths, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, host, port, username, auth_type, encrypted_password,
              encrypted_key_path, backup_paths, now, now))
        
        host_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return host_id
    
    def update_ssh_host(self, host_id: int, name: str, host: str, port: int,
                       username: str, auth_type: str, encrypted_password: str,
                       encrypted_key_path: str, backup_paths: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE ssh_hosts
            SET name = ?, host = ?, port = ?, username = ?, auth_type = ?,
                encrypted_password = ?, encrypted_key_path = ?, backup_paths = ?,
                updated_at = ?
            WHERE id = ?
        ''', (name, host, port, username, auth_type, encrypted_password,
              encrypted_key_path, backup_paths, now, host_id))
        
        conn.commit()
        conn.close()
    
    def delete_ssh_host(self, host_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM ssh_hosts WHERE id = ?', (host_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_ssh_hosts(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ssh_hosts ORDER BY name ASC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_ssh_host(self, host_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ssh_hosts WHERE id = ?', (host_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_ssh_host_connection_status(self, host_id: int, status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE ssh_hosts
            SET connection_status = ?, last_connection_test = ?
            WHERE id = ?
        ''', (status, now, host_id))
        
        conn.commit()
        conn.close()
    
    def create_schedule(self, ssh_host_id: int, schedule_type: str, schedule_value: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO schedules (ssh_host_id, schedule_type, schedule_value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (ssh_host_id, schedule_type, schedule_value, now, now))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return schedule_id
    
    def update_schedule(self, schedule_id: int, schedule_type: str = None, 
                       schedule_value: str = None, is_active: bool = None,
                       last_run: str = None, next_run: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        updates = []
        params = []
        
        if schedule_type is not None:
            updates.append('schedule_type = ?')
            params.append(schedule_type)
        
        if schedule_value is not None:
            updates.append('schedule_value = ?')
            params.append(schedule_value)
        
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(1 if is_active else 0)
        
        if last_run is not None:
            updates.append('last_run = ?')
            params.append(last_run)
        
        if next_run is not None:
            updates.append('next_run = ?')
            params.append(next_run)
        
        updates.append('updated_at = ?')
        params.append(now)
        params.append(schedule_id)
        
        query = f"UPDATE schedules SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
    
    def delete_schedule(self, schedule_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_schedules(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, h.name as host_name, h.host as host_address
            FROM schedules s
            JOIN ssh_hosts h ON s.ssh_host_id = h.id
            ORDER BY s.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_schedule(self, schedule_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM schedules WHERE id = ?', (schedule_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_active_schedules(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, h.name as host_name, h.host as host_address
            FROM schedules s
            JOIN ssh_hosts h ON s.ssh_host_id = h.id
            WHERE s.is_active = 1
            ORDER BY s.next_run ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
