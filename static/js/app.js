let logsModal, hostModal, backupModal;
let currentHostId = null;

document.addEventListener('DOMContentLoaded', function() {
    logsModal = new bootstrap.Modal(document.getElementById('logsModal'));
    hostModal = new bootstrap.Modal(document.getElementById('hostModal'));
    backupModal = new bootstrap.Modal(document.getElementById('backupModal'));
    
    loadStatus();
    loadSSHHosts();
    loadBackups();
    
    setInterval(loadStatus, 5000);
    setInterval(loadSSHHosts, 15000);
    setInterval(loadBackups, 10000);
});

async function loadSSHHosts() {
    try {
        const response = await fetch('/api/ssh-hosts');
        const hosts = await response.json();
        
        const tbody = document.getElementById('sshHostsTable');
        
        if (hosts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">
                        Nenhum servidor cadastrado. Clique em "Adicionar Servidor" para começar.
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = hosts.map(host => {
            const statusBadge = host.connection_status?.startsWith('SUCCESS') 
                ? '<span class="badge bg-success">Conectado</span>' 
                : host.connection_status?.startsWith('FAILED') 
                ? '<span class="badge bg-danger">Falhou</span>' 
                : '<span class="badge bg-secondary">Não testado</span>';
            
            const authType = host.auth_type === 'password' ? 'Senha' : 'Chave SSH';
            
            return `
                <tr>
                    <td><strong>${host.name}</strong></td>
                    <td>${host.host}</td>
                    <td>${host.port}</td>
                    <td>${host.username}</td>
                    <td>${authType}</td>
                    <td><small>${host.backup_paths}</small></td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="testConnection(${host.id})" title="Testar Conexão">
                            <i class="fas fa-plug"></i>
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="showEditHostModal(${host.id})" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteHost(${host.id})" title="Excluir">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading SSH hosts:', error);
    }
}

function showAddHostModal() {
    currentHostId = null;
    document.getElementById('hostModalTitle').textContent = 'Adicionar Servidor SSH';
    document.getElementById('hostForm').reset();
    document.getElementById('hostId').value = '';
    document.getElementById('hostPort').value = '22';
    document.getElementById('hostAuthType').value = 'password';
    toggleAuthFields();
    hostModal.show();
}

async function showEditHostModal(hostId) {
    currentHostId = hostId;
    document.getElementById('hostModalTitle').textContent = 'Editar Servidor SSH';
    
    try {
        const response = await fetch(`/api/ssh-hosts`);
        const hosts = await response.json();
        const host = hosts.find(h => h.id === hostId);
        
        if (host) {
            document.getElementById('hostId').value = host.id;
            document.getElementById('hostName').value = host.name;
            document.getElementById('hostAddress').value = host.host;
            document.getElementById('hostPort').value = host.port;
            document.getElementById('hostUsername').value = host.username;
            document.getElementById('hostAuthType').value = host.auth_type;
            document.getElementById('hostBackupPaths').value = host.backup_paths;
            document.getElementById('hostPassword').value = '';
            document.getElementById('hostKeyPath').value = '';
            
            toggleAuthFields();
            hostModal.show();
        }
    } catch (error) {
        console.error('Error loading host:', error);
        alert('Erro ao carregar dados do servidor');
    }
}

async function saveHost() {
    const hostId = document.getElementById('hostId').value;
    const name = document.getElementById('hostName').value.trim();
    const host = document.getElementById('hostAddress').value.trim();
    const port = parseInt(document.getElementById('hostPort').value);
    const username = document.getElementById('hostUsername').value.trim();
    const authType = document.getElementById('hostAuthType').value;
    const password = document.getElementById('hostPassword').value;
    const keyPath = document.getElementById('hostKeyPath').value.trim();
    const backupPaths = document.getElementById('hostBackupPaths').value.trim();
    
    if (!name || !host || !username || !backupPaths) {
        alert('Por favor, preencha todos os campos obrigatórios');
        return;
    }
    
    const data = {
        name,
        host,
        port,
        username,
        auth_type: authType,
        password,
        key_path: keyPath,
        backup_paths: backupPaths
    };
    
    try {
        let response;
        if (hostId) {
            response = await fetch(`/api/ssh-hosts/${hostId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch('/api/ssh-hosts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            hostModal.hide();
            loadSSHHosts();
        } else {
            alert('Erro: ' + (result.error || 'Falha ao salvar'));
        }
    } catch (error) {
        console.error('Error saving host:', error);
        alert('Erro ao salvar servidor');
    }
}

async function deleteHost(hostId) {
    if (!confirm('Tem certeza que deseja excluir este servidor?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/ssh-hosts/${hostId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            loadSSHHosts();
        } else {
            alert('Erro: ' + (result.error || 'Falha ao excluir'));
        }
    } catch (error) {
        console.error('Error deleting host:', error);
        alert('Erro ao excluir servidor');
    }
}

async function testConnection(hostId) {
    const btn = event.target.closest('button');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    try {
        const response = await fetch(`/api/ssh-hosts/${hostId}/test`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✓ ' + result.message);
        } else {
            alert('✗ ' + result.message);
        }
        
        loadSSHHosts();
    } catch (error) {
        console.error('Error testing connection:', error);
        alert('Erro ao testar conexão');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

function toggleAuthFields() {
    const authType = document.getElementById('hostAuthType').value;
    const passwordField = document.getElementById('passwordField');
    const keyPathField = document.getElementById('keyPathField');
    
    if (authType === 'password') {
        passwordField.classList.remove('d-none');
        keyPathField.classList.add('d-none');
    } else {
        passwordField.classList.add('d-none');
        keyPathField.classList.remove('d-none');
    }
}

async function showBackupModal() {
    try {
        const response = await fetch('/api/ssh-hosts');
        const hosts = await response.json();
        
        const select = document.getElementById('backupHostSelect');
        
        if (hosts.length === 0) {
            select.innerHTML = '<option value="">Nenhum servidor cadastrado</option>';
            alert('Você precisa cadastrar um servidor SSH primeiro');
            return;
        }
        
        select.innerHTML = hosts.map(host => 
            `<option value="${host.id}">${host.name} (${host.host})</option>`
        ).join('');
        
        backupModal.show();
    } catch (error) {
        console.error('Error loading hosts for backup:', error);
        alert('Erro ao carregar servidores');
    }
}

async function startBackupWithHost() {
    const hostId = document.getElementById('backupHostSelect').value;
    
    if (!hostId) {
        alert('Por favor, selecione um servidor');
        return;
    }
    
    if (!confirm('Deseja iniciar um backup agora para o servidor selecionado?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/backup/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ host_id: parseInt(hostId) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Backup iniciado com sucesso!');
            backupModal.hide();
            loadStatus();
            setTimeout(loadBackups, 3000);
        } else {
            alert('Erro: ' + (data.error || 'Falha ao iniciar backup'));
        }
    } catch (error) {
        console.error('Error starting backup:', error);
        alert('Erro ao iniciar backup');
    }
}

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
            
            window.backupData = window.backupData || {};
            window.backupData[backup.id] = backup;
            
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
                        ${backup.status === 'SUCCESS' && backup.drive_file_id ? `
                            <button class="btn btn-sm btn-warning" onclick="restoreBackup(${backup.id})" title="Restaurar (Descriptografar)">
                                <i class="fas fa-unlock"></i> Restaurar
                            </button>
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

async function restoreBackup(backupId) {
    if (!confirm('Deseja restaurar (descriptografar) este backup? O arquivo .tar.gz será baixado para seu computador.')) {
        return;
    }
    
    const btn = event.target.closest('button');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Restaurando...';
    
    try {
        const response = await fetch(`/api/backup/${backupId}/restore`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✓ Backup descriptografado com sucesso!');
            
            // Fazer download automático
            window.location.href = result.download_path;
        } else {
            alert('✗ Erro ao restaurar backup: ' + result.error);
        }
    } catch (error) {
        console.error('Error restoring backup:', error);
        alert('Erro ao restaurar backup');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
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
