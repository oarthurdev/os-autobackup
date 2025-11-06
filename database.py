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
                drive_file_id TEXT,
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
