from flask import Flask, render_template, jsonify, request
import threading
from backup_engine import BackupEngine
from database import Database
from drive_manager import GoogleDriveManager
from ssh_host_manager import SSHHostManager
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY

backup_engine = BackupEngine()
db = Database()
ssh_host_manager = SSHHostManager()

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
    
    data = request.get_json() or {}
    host_id = data.get('host_id')
    
    def run_backup():
        global backup_in_progress
        backup_in_progress = True
        try:
            backup_engine.perform_backup(host_id=host_id)
        finally:
            backup_in_progress = False
    
    thread = threading.Thread(target=run_backup)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Backup started', 'success': True})

@app.route('/api/ssh-hosts')
def get_ssh_hosts():
    hosts = ssh_host_manager.get_all_hosts()
    return jsonify(hosts)

@app.route('/api/ssh-hosts', methods=['POST'])
def create_ssh_host():
    data = request.get_json()
    
    try:
        host_id = ssh_host_manager.add_host(
            name=data.get('name'),
            host=data.get('host'),
            port=data.get('port', 22),
            username=data.get('username'),
            auth_type=data.get('auth_type'),
            password=data.get('password', ''),
            key_path=data.get('key_path', ''),
            backup_paths=data.get('backup_paths', '/home')
        )
        
        return jsonify({'success': True, 'host_id': host_id, 'message': 'Host adicionado com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/ssh-hosts/<int:host_id>', methods=['PUT'])
def update_ssh_host(host_id):
    data = request.get_json()
    
    try:
        ssh_host_manager.update_host(
            host_id=host_id,
            name=data.get('name'),
            host=data.get('host'),
            port=data.get('port', 22),
            username=data.get('username'),
            auth_type=data.get('auth_type'),
            password=data.get('password', ''),
            key_path=data.get('key_path', ''),
            backup_paths=data.get('backup_paths', '/home')
        )
        
        return jsonify({'success': True, 'message': 'Host atualizado com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/ssh-hosts/<int:host_id>', methods=['DELETE'])
def delete_ssh_host(host_id):
    try:
        ssh_host_manager.delete_host(host_id)
        return jsonify({'success': True, 'message': 'Host removido com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/ssh-hosts/<int:host_id>/test', methods=['POST'])
def test_ssh_host(host_id):
    result = ssh_host_manager.test_connection(host_id)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
