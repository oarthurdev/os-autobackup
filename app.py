from flask import Flask, render_template, jsonify, request
import threading
from backup_engine import BackupEngine
from database import Database
from drive_manager import GoogleDriveManager
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY

backup_engine = BackupEngine()
db = Database()

backup_in_progress = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/backups')
def get_backups():
    limit = request.args.get('limit', 100, type=int)
    backups = backup_engine.get_backup_history(limit)
    
    for backup in backups:
        if backup['drive_file_id']:
            try:
                drive_manager = GoogleDriveManager()
                backup['download_link'] = drive_manager.get_file_link(backup['drive_file_id'])
            except:
                backup['download_link'] = None
    
    return jsonify(backups)

@app.route('/api/backup/<int:backup_id>/logs')
def get_backup_logs(backup_id):
    logs = backup_engine.get_backup_logs(backup_id)
    return jsonify(logs)

@app.route('/api/backup/status')
def backup_status():
    latest = db.get_latest_backup()
    return jsonify({
        'in_progress': backup_in_progress,
        'latest_backup': latest
    })

@app.route('/api/backup/start', methods=['POST'])
def start_backup():
    global backup_in_progress
    
    if backup_in_progress:
        return jsonify({'error': 'Backup already in progress'}), 400
    
    def run_backup():
        global backup_in_progress
        backup_in_progress = True
        try:
            backup_engine.perform_backup()
        finally:
            backup_in_progress = False
    
    thread = threading.Thread(target=run_backup)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Backup started', 'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
