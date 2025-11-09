from flask import Flask, render_template, jsonify, request
import threading
from datetime import datetime
from backup_engine import BackupEngine
from database import Database
from ssh_host_manager import SSHHostManager
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY

backup_engine = BackupEngine()
db = Database()
ssh_host_manager = SSHHostManager()

backup_in_progress = False
backup_lock = threading.Lock()

from scheduler import get_scheduler
scheduler = get_scheduler()

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
                from supabase_storage_manager import SupabaseStorageManager
                storage_manager = SupabaseStorageManager()
                backup['download_link'] = storage_manager.get_file_url(backup['drive_file_id'])
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
    progress = backup_engine.get_progress() if backup_in_progress else None
    return jsonify({
        'in_progress': backup_in_progress,
        'latest_backup': latest,
        'progress': progress
    })

@app.route('/api/backup/start', methods=['POST'])
def start_backup():
    global backup_in_progress
    
    if not backup_lock.acquire(blocking=False):
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
            backup_lock.release()
    
    thread = threading.Thread(target=run_backup)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Backup started', 'success': True})

def execute_scheduled_backup(ssh_host_id, schedule_id):
    global backup_in_progress
    
    if not backup_lock.acquire(blocking=False):
        return {'success': False, 'error': 'Backup already in progress'}
    
    try:
        backup_in_progress = True
        now = datetime.now().isoformat()
        
        backup_engine.perform_backup(host_id=ssh_host_id)
        
        db.update_schedule(schedule_id, last_run=now)
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        backup_in_progress = False
        backup_lock.release()

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

@app.route('/api/schedules')
def get_schedules():
    schedules = db.get_all_schedules()
    return jsonify(schedules)

@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    from scheduler import get_scheduler
    
    data = request.get_json()
    
    try:
        schedule_id = db.create_schedule(
            ssh_host_id=data['ssh_host_id'],
            schedule_type=data['schedule_type'],
            schedule_value=data['schedule_value']
        )
        
        scheduler = get_scheduler()
        scheduler.reload_schedule(schedule_id)
        
        return jsonify({
            'success': True,
            'schedule_id': schedule_id,
            'message': 'Agendamento criado com sucesso'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    from scheduler import get_scheduler
    
    data = request.get_json()
    
    try:
        db.update_schedule(
            schedule_id=schedule_id,
            schedule_type=data.get('schedule_type'),
            schedule_value=data.get('schedule_value'),
            is_active=data.get('is_active')
        )
        
        scheduler = get_scheduler()
        scheduler.reload_schedule(schedule_id)
        
        return jsonify({'success': True, 'message': 'Agendamento atualizado com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    from scheduler import get_scheduler
    
    try:
        scheduler = get_scheduler()
        scheduler.remove_schedule(schedule_id)
        
        db.delete_schedule(schedule_id)
        
        return jsonify({'success': True, 'message': 'Agendamento removido com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/schedules/<int:schedule_id>/toggle', methods=['POST'])
def toggle_schedule(schedule_id):
    from scheduler import get_scheduler
    
    try:
        schedule = db.get_schedule(schedule_id)
        if not schedule:
            return jsonify({'success': False, 'error': 'Agendamento não encontrado'}), 404
        
        new_status = not bool(schedule['is_active'])
        db.update_schedule(schedule_id, is_active=new_status)
        
        scheduler = get_scheduler()
        scheduler.reload_schedule(schedule_id)
        
        return jsonify({
            'success': True,
            'is_active': new_status,
            'message': f"Agendamento {'ativado' if new_status else 'desativado'} com sucesso"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/scheduler/status')
def scheduler_status():
    from scheduler import get_scheduler
    
    try:
        scheduler = get_scheduler()
        status = scheduler.get_scheduler_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/<int:backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    try:
        from supabase_storage_manager import SupabaseStorageManager
        from config import Config
        import os
        
        # Buscar informações do backup
        backups = db.get_all_backups(limit=1000)
        backup = next((b for b in backups if b['id'] == backup_id), None)
        
        if not backup:
            return jsonify({'success': False, 'error': 'Backup não encontrado'}), 404
        
        if not backup.get('drive_file_id'):
            return jsonify({'success': False, 'error': 'Arquivo não disponível no Supabase Storage'}), 400
        
        # Iniciar processo em background
        def restore_process():
            try:
                # Download do arquivo do Supabase Storage
                storage_manager = SupabaseStorageManager()
                restored_file = os.path.join(Config.TEMP_DIR, f"restore_{backup['file_name']}")
                
                # Baixar arquivo
                storage_manager.download_file(backup['drive_file_id'], restored_file)
                
            except Exception as e:
                print(f"Erro ao restaurar backup: {e}")
        
        # Iniciar thread
        thread = threading.Thread(target=restore_process)
        thread.daemon = True
        thread.start()
        
        # Retornar imediatamente com informação
        restored_filename = backup['file_name']
        
        return jsonify({
            'success': True,
            'message': 'Restauração iniciada! O arquivo será baixado automaticamente quando estiver pronto.',
            'file_name': restored_filename,
            'backup_id': backup_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backup/<int:backup_id>/restore/status')
def restore_status(backup_id):
    from config import Config
    import os
    
    # Buscar informações do backup
    backups = db.get_all_backups(limit=1000)
    backup = next((b for b in backups if b['id'] == backup_id), None)
    
    if not backup:
        return jsonify({'ready': False, 'error': 'Backup não encontrado'})
    
    # Verificar se arquivo restaurado existe
    restored_filename = f"restore_{backup['file_name']}"
    file_path = os.path.join(Config.TEMP_DIR, restored_filename)
    
    if os.path.exists(file_path):
        return jsonify({
            'ready': True,
            'download_path': f"/download/{restored_filename}",
            'file_name': restored_filename
        })
    else:
        return jsonify({'ready': False, 'message': 'Ainda processando...'})

@app.route('/download/<filename>')
def download_file(filename):
    from flask import send_from_directory
    from config import Config
    import os
    
    # Verificar se o arquivo existe
    file_path = os.path.join(Config.TEMP_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    return send_from_directory(
        Config.TEMP_DIR, 
        filename, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/zip'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
