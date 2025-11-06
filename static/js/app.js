let logsModal;

document.addEventListener('DOMContentLoaded', function() {
    logsModal = new bootstrap.Modal(document.getElementById('logsModal'));
    loadStatus();
    loadBackups();
    
    setInterval(loadStatus, 5000);
    setInterval(loadBackups, 10000);
});

async function loadStatus() {
    try {
        const response = await fetch('/api/backup/status');
        const data = await response.json();
        
        const statusDiv = document.getElementById('currentStatus');
        
        if (data.in_progress) {
            statusDiv.innerHTML = `
                <p><strong>Status:</strong> <span class="badge status-in-progress">
                    <span class="spinner-border spinner-border-sm"></span> Backup em Andamento
                </span></p>
            `;
        } else if (data.latest_backup) {
            const latest = data.latest_backup;
            const statusClass = latest.status === 'SUCCESS' ? 'status-success' : 
                               latest.status === 'FAILED' ? 'status-failed' : 'status-in-progress';
            const statusText = latest.status === 'SUCCESS' ? 'Sucesso' :
                              latest.status === 'FAILED' ? 'Falhou' : 'Em Progresso';
            
            statusDiv.innerHTML = `
                <p><strong>Último Backup:</strong> ${formatDate(latest.timestamp)}</p>
                <p><strong>Status:</strong> <span class="badge ${statusClass}">${statusText}</span></p>
                ${latest.file_name ? `<p><strong>Arquivo:</strong> ${latest.file_name}</p>` : ''}
                ${latest.file_size ? `<p><strong>Tamanho:</strong> ${formatBytes(latest.file_size)}</p>` : ''}
                ${latest.error_message ? `<p class="text-danger"><strong>Erro:</strong> ${latest.error_message}</p>` : ''}
            `;
        } else {
            statusDiv.innerHTML = '<p class="text-muted">Nenhum backup realizado ainda.</p>';
        }
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

async function loadBackups() {
    try {
        const response = await fetch('/api/backups?limit=50');
        const backups = await response.json();
        
        const tbody = document.getElementById('backupsTable');
        
        if (backups.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        Nenhum backup encontrado.
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = backups.map(backup => {
            const statusClass = backup.status === 'SUCCESS' ? 'status-success' : 
                               backup.status === 'FAILED' ? 'status-failed' : 'status-in-progress';
            const statusText = backup.status === 'SUCCESS' ? 'Sucesso' :
                              backup.status === 'FAILED' ? 'Falhou' : 'Em Progresso';
            
            return `
                <tr>
                    <td>${backup.id}</td>
                    <td>${formatDate(backup.timestamp)}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                    <td>${backup.file_name || 'N/A'}</td>
                    <td>${backup.file_size ? formatBytes(backup.file_size) : 'N/A'}</td>
                    <td>${backup.duration_seconds ? backup.duration_seconds.toFixed(2) + 's' : 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="viewLogs(${backup.id})">
                            <i class="fas fa-file-alt"></i> Logs
                        </button>
                        ${backup.download_link ? `
                            <a href="${backup.download_link}" target="_blank" class="btn btn-sm btn-success">
                                <i class="fas fa-download"></i> Download
                            </a>
                        ` : ''}
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading backups:', error);
    }
}

async function viewLogs(backupId) {
    try {
        const response = await fetch(`/api/backup/${backupId}/logs`);
        const logs = await response.json();
        
        const logsContent = document.getElementById('logsContent');
        
        if (logs.length === 0) {
            logsContent.innerHTML = '<p class="text-muted">Nenhum log encontrado.</p>';
        } else {
            logsContent.innerHTML = logs.map(log => {
                return `
                    <div class="log-entry log-${log.level}">
                        <small>${formatDate(log.timestamp)}</small>
                        <strong>[${log.level}]</strong>
                        ${log.message}
                    </div>
                `;
            }).join('');
        }
        
        logsModal.show();
    } catch (error) {
        console.error('Error loading logs:', error);
        alert('Erro ao carregar logs');
    }
}

async function forceBackup() {
    const btn = document.getElementById('forceBackupBtn');
    
    if (!confirm('Deseja iniciar um backup agora?')) {
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Iniciando...';
    
    try {
        const response = await fetch('/api/backup/start', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Backup iniciado com sucesso!');
            loadStatus();
            setTimeout(loadBackups, 3000);
        } else {
            alert('Erro: ' + (data.error || 'Falha ao iniciar backup'));
        }
    } catch (error) {
        console.error('Error starting backup:', error);
        alert('Erro ao iniciar backup');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-play"></i> Forçar Backup Agora';
    }
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR');
}

function formatBytes(bytes) {
    if (!bytes) return 'N/A';
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
