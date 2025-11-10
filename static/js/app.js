let logsModal, hostModal, backupModal, scheduleModal, emailConfigModal, retentionModal;
let currentHostId = null;
let currentScheduleId = null;
let allBackups = [];
let allSchedules = [];

document.addEventListener('DOMContentLoaded', function() {
    logsModal = new bootstrap.Modal(document.getElementById('logsModal'));
    hostModal = new bootstrap.Modal(document.getElementById('hostModal'));
    backupModal = new bootstrap.Modal(document.getElementById('backupModal'));
    scheduleModal = new bootstrap.Modal(document.getElementById('scheduleModal'));
    emailConfigModal = new bootstrap.Modal(document.getElementById('emailConfigModal'));
    retentionModal = new bootstrap.Modal(document.getElementById('retentionModal'));

    // Load theme preference
    loadTheme();

    loadStatus();
    loadSSHHosts();
    loadBackups();
    loadSchedules();
    loadRetentionStats();

    setInterval(loadStatus, 5000);
    setInterval(loadSSHHosts, 15000);
    setInterval(loadBackups, 10000);
    setInterval(loadSchedules, 15000);
    setInterval(loadRetentionStats, 30000);
});

async function loadRetentionStats() {
    try {
        const response = await fetch('/api/retention-policy/stats');
        const stats = await response.json();
        
        const container = document.getElementById('retentionStats');
        
        if (!stats.policy) {
            container.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="fas fa-cog fa-2x mb-2"></i>
                    <p>Nenhuma política configurada</p>
                    <button class="action-btn action-btn-primary" onclick="showRetentionModal()">
                        <i class="fas fa-plus"></i> Configurar Política
                    </button>
                </div>
            `;
            return;
        }
        
        const policy = stats.policy;
        const policyText = policy.policy_type === 'count' 
            ? `Manter ${policy.retention_count} backups mais recentes`
            : `Manter backups de ${policy.retention_days} dias`;
        
        container.innerHTML = `
            <div class="retention-info">
                <div class="retention-stat-grid">
                    <div class="retention-stat-item">
                        <div class="retention-stat-icon">
                            <i class="fas fa-database"></i>
                        </div>
                        <div class="retention-stat-info">
                            <div class="retention-stat-label">Backups Ativos</div>
                            <div class="retention-stat-value">${stats.total_backups}</div>
                        </div>
                    </div>
                    
                    <div class="retention-stat-item">
                        <div class="retention-stat-icon retention-icon-size">
                            <i class="fas fa-hdd"></i>
                        </div>
                        <div class="retention-stat-info">
                            <div class="retention-stat-label">Espaço Usado</div>
                            <div class="retention-stat-value">${formatBytes(stats.total_size)}</div>
                        </div>
                    </div>
                    
                    <div class="retention-stat-item">
                        <div class="retention-stat-icon retention-icon-remove">
                            <i class="fas fa-trash"></i>
                        </div>
                        <div class="retention-stat-info">
                            <div class="retention-stat-label">A Remover</div>
                            <div class="retention-stat-value">${stats.backups_to_remove}</div>
                        </div>
                    </div>
                    
                    <div class="retention-stat-item">
                        <div class="retention-stat-icon retention-icon-free">
                            <i class="fas fa-arrow-down"></i>
                        </div>
                        <div class="retention-stat-info">
                            <div class="retention-stat-label">Espaço Liberável</div>
                            <div class="retention-stat-value">${formatBytes(stats.removable_size)}</div>
                        </div>
                    </div>
                </div>
                
                <div class="retention-policy-info">
                    <div class="alert alert-info mb-3">
                        <i class="fas fa-info-circle"></i>
                        <strong>Política Ativa:</strong> ${policyText}
                        ${policy.auto_cleanup ? ' (Limpeza automática habilitada)' : ''}
                    </div>
                    
                    ${stats.backups_to_remove > 0 ? `
                        <button class="action-btn action-btn-danger w-100" onclick="applyRetentionNow()">
                            <i class="fas fa-trash-alt"></i> Remover ${stats.backups_to_remove} Backup(s) Agora
                        </button>
                    ` : `
                        <div class="text-center text-muted">
                            <i class="fas fa-check-circle"></i> Nenhum backup para remover
                        </div>
                    `}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading retention stats:', error);
    }
}

async function showRetentionModal() {
    try {
        const response = await fetch('/api/retention-policy');
        const policy = await response.json();
        
        document.getElementById('retentionEnabled').checked = policy.enabled !== 0;
        document.getElementById('policyType').value = policy.policy_type || 'count';
        document.getElementById('retentionCount').value = policy.retention_count || 10;
        document.getElementById('retentionDays').value = policy.retention_days || 30;
        document.getElementById('autoCleanup').checked = policy.auto_cleanup !== 0;
        
        toggleRetentionFields();
        retentionModal.show();
    } catch (error) {
        console.error('Error loading retention policy:', error);
        retentionModal.show();
    }
}

function toggleRetentionFields() {
    const policyType = document.getElementById('policyType').value;
    const countField = document.getElementById('countField');
    const daysField = document.getElementById('daysField');
    
    if (policyType === 'count') {
        countField.classList.remove('d-none');
        daysField.classList.add('d-none');
    } else {
        countField.classList.add('d-none');
        daysField.classList.remove('d-none');
    }
}

// Adicionar listener ao select de tipo de política
document.addEventListener('DOMContentLoaded', function() {
    const policyTypeSelect = document.getElementById('policyType');
    if (policyTypeSelect) {
        policyTypeSelect.addEventListener('change', toggleRetentionFields);
    }
});

async function saveRetentionPolicy() {
    const policy = {
        enabled: document.getElementById('retentionEnabled').checked,
        policy_type: document.getElementById('policyType').value,
        retention_count: parseInt(document.getElementById('retentionCount').value),
        retention_days: parseInt(document.getElementById('retentionDays').value),
        auto_cleanup: document.getElementById('autoCleanup').checked
    };
    
    try {
        const response = await fetch('/api/retention-policy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(policy)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Política de retenção salva com sucesso!');
            retentionModal.hide();
            loadRetentionStats();
        } else {
            showError('Erro ao salvar: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving retention policy:', error);
        showError('Erro ao salvar política');
    }
}

async function applyRetentionNow() {
    const confirmed = await showConfirm(
        'Aplicar Política de Retenção',
        'Deseja remover os backups antigos agora? Esta ação não pode ser desfeita.'
    );
    
    if (!confirmed) return;
    
    showInfo('Aplicando política de retenção...');
    
    try {
        const response = await fetch('/api/retention-policy/apply', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess(`${result.removed_count} backup(s) removido(s). ${formatBytes(result.freed_space)} liberados!`);
            loadRetentionStats();
            loadBackups();
        } else {
            showError('Erro ao aplicar política: ' + result.error);
        }
    } catch (error) {
        console.error('Error applying retention:', error);
        showError('Erro ao aplicar política de retenção');
    }
}

// Custom Toast Notification System
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const titles = {
        success: 'Sucesso',
        error: 'Erro',
        warning: 'Atenção',
        info: 'Informação'
    };

    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${icons[type]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${titles[type]}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="removeToast(this)">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(toast);

    // Auto remove after duration
    setTimeout(() => {
        removeToast(toast);
    }, duration);

    return toast;
}

function removeToast(element) {
    const toast = element.classList ? element : element.parentElement.parentElement;
    toast.classList.add('toast-removing');
    setTimeout(() => {
        toast.remove();
    }, 300);
}

// Convenience functions
function showSuccess(message, duration = 4000) {
    return showToast(message, 'success', duration);
}

function showError(message, duration = 5000) {
    return showToast(message, 'error', duration);
}

function showWarning(message, duration = 4500) {
    return showToast(message, 'warning', duration);
}

function showInfo(message, duration = 4000) {
    return showToast(message, 'info', duration);
}

// Custom Confirm Dialog System
function showConfirm(title, message, onConfirm, onCancel) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';
        
        overlay.innerHTML = `
            <div class="confirm-modal">
                <div class="confirm-icon">
                    <i class="fas fa-question-circle"></i>
                </div>
                <div class="confirm-content">
                    <h3 class="confirm-title">${title}</h3>
                    <p class="confirm-message">${message}</p>
                </div>
                <div class="confirm-actions">
                    <button class="btn-confirm-cancel">
                        <i class="fas fa-times"></i> Cancelar
                    </button>
                    <button class="btn-confirm-ok">
                        <i class="fas fa-check"></i> OK
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Trigger animation
        setTimeout(() => overlay.classList.add('show'), 10);
        
        const cancelBtn = overlay.querySelector('.btn-confirm-cancel');
        const okBtn = overlay.querySelector('.btn-confirm-ok');
        
        const closeModal = (confirmed) => {
            overlay.classList.remove('show');
            setTimeout(() => {
                overlay.remove();
                resolve(confirmed);
                if (confirmed && onConfirm) onConfirm();
                if (!confirmed && onCancel) onCancel();
            }, 300);
        };
        
        cancelBtn.onclick = () => closeModal(false);
        okBtn.onclick = () => closeModal(true);
        
        // Close on overlay click
        overlay.onclick = (e) => {
            if (e.target === overlay) closeModal(false);
        };
        
        // Close on ESC key
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal(false);
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    });
}

function loadTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (theme === 'dark') {
        icon.className = 'fas fa-sun';
    } else {
        icon.className = 'fas fa-moon';
    }
}

function updateActivityTimeline(backups, schedules) {
    const timeline = document.getElementById('activityTimeline');
    
    // Get recent backups (last 5)
    const recentBackups = backups.slice(0, 5);
    
    if (recentBackups.length === 0) {
        timeline.innerHTML = `
            <div class="timeline-empty">
                <i class="fas fa-inbox"></i>
                <p>Nenhuma atividade recente</p>
            </div>
        `;
        return;
    }
    
    timeline.innerHTML = recentBackups.map(backup => {
        const date = new Date(backup.timestamp);
        const timeAgo = getTimeAgo(date);
        const statusClass = backup.status === 'SUCCESS' ? 'success' : 'failed';
        const statusText = backup.status === 'SUCCESS' ? 'Sucesso' : 'Falha';
        const sizeText = backup.file_size ? formatBytes(backup.file_size) : 'N/A';
        const durationText = backup.duration_seconds ? `${backup.duration_seconds.toFixed(0)}s` : 'N/A';
        
        return `
            <div class="timeline-item">
                <div class="timeline-indicator ${statusClass}"></div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <div class="timeline-title">${backup.file_name || 'Backup #' + backup.id}</div>
                        <div class="timeline-time">${timeAgo}</div>
                    </div>
                    <div class="timeline-details">
                        <span class="timeline-detail-item">
                            <i class="fas fa-circle-${statusClass === 'success' ? 'check' : 'xmark'}"></i>
                            ${statusText}
                        </span>
                        <span class="timeline-detail-item">
                            <i class="fas fa-file-archive"></i>
                            ${sizeText}
                        </span>
                        <span class="timeline-detail-item">
                            <i class="fas fa-clock"></i>
                            ${durationText}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Update quick metrics
    updateQuickMetrics(backups, schedules);
}

function updateQuickMetrics(backups, schedules) {
    // Success rate (last 10 backups)
    const recent = backups.slice(0, 10);
    const successRate = recent.length > 0 
        ? ((recent.filter(b => b.status === 'SUCCESS').length / recent.length) * 100).toFixed(0)
        : 0;
    document.getElementById('successRate').textContent = successRate + '%';
    
    // Last backup time
    if (backups.length > 0) {
        const lastBackup = backups[0];
        const date = new Date(lastBackup.timestamp);
        const timeAgo = getTimeAgo(date);
        document.getElementById('lastBackupTime').textContent = timeAgo;
    } else {
        document.getElementById('lastBackupTime').textContent = 'Nunca';
    }
    
    // Next scheduled backup
    const activeSchedules = schedules.filter(s => s.is_active);
    if (activeSchedules.length > 0) {
        // Find the earliest next run
        const nextSchedule = activeSchedules.reduce((earliest, current) => {
            const currentNext = current.next_run ? new Date(current.next_run) : new Date(8640000000000000); // Max date
            const earliestNext = earliest.next_run ? new Date(earliest.next_run) : new Date(8640000000000000);
            return currentNext < earliestNext ? current : earliest;
        });
        
        if (nextSchedule.next_run) {
            const nextDate = new Date(nextSchedule.next_run);
            const timeUntil = getTimeUntil(nextDate);
            document.getElementById('nextScheduled').textContent = timeUntil;
        } else {
            document.getElementById('nextScheduled').textContent = 'Em breve';
        }
    } else {
        document.getElementById('nextScheduled').textContent = 'Nenhum';
    }
}

function getTimeAgo(date) {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds
    
    if (diff < 60) return 'agora mesmo';
    if (diff < 3600) return `${Math.floor(diff / 60)} min atrás`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d atrás`;
    
    return date.toLocaleDateString('pt-BR');
}

function getTimeUntil(date) {
    const now = new Date();
    const diff = Math.floor((date - now) / 1000); // seconds
    
    if (diff < 0) return 'Atrasado';
    if (diff < 60) return 'Em instantes';
    if (diff < 3600) return `Em ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `Em ${Math.floor(diff / 3600)}h`;
    if (diff < 604800) return `Em ${Math.floor(diff / 86400)}d`;
    
    return date.toLocaleDateString('pt-BR');
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function updateStatistics(backups) {
    const total = backups.length;
    const success = backups.filter(b => b.status === 'SUCCESS').length;
    const failed = backups.filter(b => b.status === 'FAILED').length;
    const totalSize = backups.reduce((sum, b) => sum + (b.file_size || 0), 0);

    animateValue('totalBackups', 0, total, 1000);
    animateValue('successBackups', 0, success, 1000);
    animateValue('failedBackups', 0, failed, 1000);

    const sizeGB = (totalSize / (1024 * 1024 * 1024)).toFixed(2);
    document.getElementById('totalSize').textContent = sizeGB + ' GB';
}

function animateValue(id, start, end, duration) {
    const element = document.getElementById(id);
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

async function loadSSHHosts() {
    try {
        const response = await fetch('/api/ssh-hosts');
        const hosts = await response.json();

        const treeContainer = document.getElementById('sshHostsTree');

        if (hosts.length === 0) {
            treeContainer.innerHTML = `
                <div class="tree-empty">
                    <i class="fas fa-server"></i>
                    <p>Nenhum servidor cadastrado</p>
                    <p>Clique em "Adicionar Servidor" para começar</p>
                </div>
            `;
            return;
        }

        treeContainer.innerHTML = hosts.map(host => {
            const statusClass = host.connection_status?.startsWith('SUCCESS') 
                ? 'status-connected' 
                : host.connection_status?.startsWith('FAILED') 
                ? 'status-failed' 
                : 'status-unknown';

            const statusText = host.connection_status?.startsWith('SUCCESS') 
                ? 'Conectado' 
                : host.connection_status?.startsWith('FAILED') 
                ? 'Falhou' 
                : 'Não testado';

            const authType = host.auth_type === 'password' ? 'Senha' : 'Chave SSH';
            const paths = host.backup_paths.split(',').map(p => p.trim()).filter(p => p);

            return `
                <div class="tree-node">
                    <div class="tree-node-item">
                        <div class="tree-node-content" onclick="toggleTreeNode(this)">
                            <i class="fas fa-chevron-down tree-node-icon"></i>
                            <div class="tree-node-info">
                                <div class="tree-node-title">
                                    <i class="fas fa-server"></i>
                                    ${host.name}
                                </div>
                                <div class="tree-node-subtitle">
                                    ${host.username}@${host.host}:${host.port} • ${authType}
                                </div>
                            </div>
                            <span class="tree-node-status ${statusClass}">${statusText}</span>
                            <div class="tree-node-actions" onclick="event.stopPropagation()">
                                <button class="btn-test" onclick="testConnection(${host.id})" title="Testar Conexão">
                                    <i class="fas fa-plug"></i> Testar
                                </button>
                                <button class="btn-edit" onclick="showEditHostModal(${host.id})" title="Editar">
                                    <i class="fas fa-edit"></i> Editar
                                </button>
                                <button class="btn-delete" onclick="deleteHost(${host.id})" title="Excluir">
                                    <i class="fas fa-trash"></i> Excluir
                                </button>
                            </div>
                        </div>
                        <div class="tree-node-children">
                            <div class="tree-child-item">
                                <i class="fas fa-info-circle"></i>
                                <strong>Detalhes de Conexão</strong>
                            </div>
                            <div class="tree-child-item">
                                <i class="fas fa-globe"></i>
                                Host: ${host.host}
                            </div>
                            <div class="tree-child-item">
                                <i class="fas fa-ethernet"></i>
                                Porta: ${host.port}
                            </div>
                            <div class="tree-child-item">
                                <i class="fas fa-user"></i>
                                Usuário: ${host.username}
                            </div>
                            <div class="tree-child-item">
                                <i class="fas fa-key"></i>
                                Autenticação: ${authType}
                            </div>
                            ${paths.length > 0 ? `
                                <div class="tree-child-item">
                                    <i class="fas fa-folder"></i>
                                    <strong>Caminhos de Backup (${paths.length})</strong>
                                </div>
                                ${paths.map(path => `
                                    <div class="tree-child-item" style="padding-left: 36px">
                                        <i class="fas fa-folder-open"></i>
                                        ${path}
                                    </div>
                                `).join('')}
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading SSH hosts:', error);
    }
}

function toggleTreeNode(element) {
    const nodeItem = element.closest('.tree-node-item');
    nodeItem.classList.toggle('tree-node-collapsed');
}

function showAddHostModal() {
    currentHostId = null;
    document.getElementById('hostModalTitle').textContent = 'Adicionar Servidor SSH';
    document.getElementById('hostForm').reset();
    document.getElementById('hostId').value = '';
    document.getElementById('hostPort').value = '22';
    document.getElementById('hostAuthType').value = 'password';
    document.getElementById('hostBackupPaths').value = '';
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
        showError('Erro ao carregar dados do servidor');
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
        showWarning('Por favor, preencha todos os campos obrigatórios');
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
            showSuccess(result.message);
            hostModal.hide();
            loadSSHHosts();
        } else {
            showError('Erro: ' + (result.error || 'Falha ao salvar'));
        }
    } catch (error) {
        console.error('Error saving host:', error);
        showError('Erro ao salvar servidor');
    }
}

async function deleteHost(hostId) {
    const confirmed = await showConfirm(
        'Confirmar Exclusão',
        'Tem certeza que deseja excluir este servidor?'
    );

    if (!confirmed) return;

    try {
        const response = await fetch(`/api/ssh-hosts/${hostId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showSuccess(result.message);
            loadSSHHosts();
        } else {
            showError('Erro: ' + (result.error || 'Falha ao excluir'));
        }
    } catch (error) {
        console.error('Error deleting host:', error);
        showError('Erro ao excluir servidor');
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
            showSuccess(result.message);
        } else {
            showError(result.message);
        }

        loadSSHHosts();
    } catch (error) {
        console.error('Error testing connection:', error);
        showError('Erro ao testar conexão');
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
            showWarning('Você precisa cadastrar um servidor SSH primeiro');
            return;
        }

        select.innerHTML = hosts.map(host => 
            `<option value="${host.id}">${host.name} (${host.host})</option>`
        ).join('');

        backupModal.show();
    } catch (error) {
        console.error('Error loading hosts for backup:', error);
        showError('Erro ao carregar servidores');
    }
}

// Nova função para exibir modal de confirmação de backup
async function confirmBackup() {
    const hostId = document.getElementById('backupHostSelect').value;

    if (!hostId) {
        showWarning('Por favor, selecione um servidor');
        return;
    }

    const confirmed = await showConfirm(
        'localhost:5000 diz',
        'Deseja iniciar um backup agora para o servidor selecionado?'
    );

    if (confirmed) {
        startBackupNow(hostId);
    }
}

async function startBackupWithHost() {
    await confirmBackup();
}

async function startBackupNow(hostId) {
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
            showSuccess('Backup iniciado com sucesso!');
            backupModal.hide();
            loadStatus();
            setTimeout(loadBackups, 3000);
        } else {
            showError('Erro: ' + (data.error || 'Falha ao iniciar backup'));
        }
    } catch (error) {
        console.error('Error starting backup:', error);
        showError('Erro ao iniciar backup');
    }
}

async function loadStatus() {
    try {
        const response = await fetch('/api/backup/status');
        const data = await response.json();

        const statusDiv = document.getElementById('currentStatus');
        const progressSection = document.getElementById('progressSection');
        const progressContent = document.getElementById('progressContent');

        if (data.in_progress && data.progress) {
            const progress = data.progress;

            // Show progress section
            progressSection.style.display = 'block';
            const timeRemainingHTML = progress.estimated_time_remaining 
                ? `<div class="alert alert-warning mb-2">
                       <i class="fas fa-clock"></i> <strong>Tempo estimado restante:</strong> ${formatTime(progress.estimated_time_remaining)}
                   </div>`
                : '';
            
            progressContent.innerHTML = `
                <div class="d-flex justify-content-between mb-3">
                    <h6 class="mb-0">
                        <i class="fas fa-tasks"></i> Etapa ${progress.current_step_number} de ${progress.total_steps}
                    </h6>
                    <span class="badge bg-warning">${progress.percentage}%</span>
                </div>
                <div class="progress mb-3" style="height: 30px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" 
                         style="width: ${progress.percentage}%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);"
                         aria-valuenow="${progress.percentage}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        ${progress.percentage}%
                    </div>
                </div>
                ${timeRemainingHTML}
                <div class="alert alert-info mb-0">
                    <i class="fas fa-info-circle"></i> <strong>${progress.current_step}</strong>
                </div>
            `;

            statusDiv.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h6>Backup em Andamento</h6>
                    <p class="text-muted mb-0">Acompanhe o progresso acima</p>
                </div>
            `;
        } else {
            progressSection.style.display = 'none';

            if (data.latest_backup) {
                const latest = data.latest_backup;
                const statusClass = latest.status === 'SUCCESS' ? 'status-success' : 
                                   latest.status === 'FAILED' ? 'status-failed' : 'status-in-progress';
                const statusText = latest.status === 'SUCCESS' ? 'Sucesso' :
                                  latest.status === 'FAILED' ? 'Falhou' : 'Em Progresso';
                const statusIcon = latest.status === 'SUCCESS' ? 'fa-check-circle' :
                                  latest.status === 'FAILED' ? 'fa-times-circle' : 'fa-spinner fa-spin';

                const iconColor = latest.status === 'SUCCESS' ? 'text-success' :
                              latest.status === 'FAILED' ? 'text-danger' : 'text-warning';

                statusDiv.innerHTML = `
                    <div class="mb-3 pb-3 border-bottom">
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas ${statusIcon} ${iconColor} me-2" style="font-size: 1.5rem;"></i>
                            <h6 class="mb-0">Último Backup</h6>
                        </div>
                        <span class="badge ${statusClass}">${statusText}</span>
                    </div>
                    <div class="info-list">
                        <div class="info-item">
                            <i class="fas fa-calendar text-primary"></i>
                            <span>${formatDate(latest.timestamp)}</span>
                        </div>
                        ${latest.file_name ? `
                        <div class="info-item">
                            <i class="fas fa-file text-info"></i>
                            <span>${latest.file_name}</span>
                        </div>
                        ` : ''}
                        ${latest.file_size ? `
                        <div class="info-item">
                            <i class="fas fa-hdd text-success"></i>
                            <span>${formatBytes(latest.file_size)}</span>
                        </div>
                        ` : ''}
                        ${latest.duration_seconds ? `
                        <div class="info-item">
                            <i class="fas fa-clock text-warning"></i>
                            <span>${latest.duration_seconds.toFixed(2)}s</span>
                        </div>
                        ` : ''}
                    </div>
                    ${latest.error_message ? `
                        <div class="alert alert-danger mt-3 mb-0">
                            <i class="fas fa-exclamation-triangle"></i> ${latest.error_message}
                        </div>
                    ` : ''}
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="text-center text-muted">
                        <i class="fas fa-inbox fa-3x mb-3"></i>
                        <p>Nenhum backup realizado ainda.</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

async function loadBackups() {
    try {
        const response = await fetch('/api/backups?limit=50');
        const backups = await response.json();
        allBackups = backups;

        // Update statistics and activity timeline
        updateStatistics(backups);
        updateActivityTimeline(backups, allSchedules);

        const tbody = document.getElementById('backupsTable');

        if (backups.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-inbox fa-3x mb-3 d-block"></i>
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

async function restoreBackup(backupId, event) {
    const confirmed = await showConfirm(
        'Restaurar Backup',
        'Deseja restaurar (descriptografar) este backup? O processo pode demorar alguns minutos. O arquivo .tar.gz será baixado automaticamente quando estiver pronto.'
    );

    if (!confirmed) return;

    let btn = null;
    let originalContent = '';
    
    if (event && event.target) {
        btn = event.target.closest('button');
        if (btn) {
            originalContent = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Restaurando...';
        }
    }

    try {
        // Iniciar processo de restauração
        const response = await fetch(`/api/backup/${backupId}/restore`, {
            method: 'POST'
        });

        const result = await response.json();

        if (!result.success) {
            showError('Erro ao iniciar restauração: ' + result.error);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
            return;
        }

        showInfo('Restauração iniciada! Aguarde enquanto o arquivo é preparado...', 5000);

        // Polling para verificar quando o arquivo está pronto
        const checkInterval = setInterval(async () => {
            try {
                const statusResponse = await fetch(`/api/backup/${backupId}/restore/status`);
                const status = await statusResponse.json();

                if (status.ready) {
                    clearInterval(checkInterval);
                    
                    showSuccess('Backup pronto! Iniciando download...');
                    
                    // Fazer download automático
                    const downloadLink = document.createElement('a');
                    downloadLink.href = status.download_path;
                    downloadLink.download = status.file_name;
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                    
                    setTimeout(() => {
                        showInfo('Se o download não iniciar, <a href="' + status.download_path + '" download>clique aqui</a>', 8000);
                    }, 2000);

                    if (btn) {
                        btn.disabled = false;
                        btn.innerHTML = originalContent;
                    }
                }
            } catch (error) {
                console.error('Erro ao verificar status:', error);
            }
        }, 2000); // Verificar a cada 2 segundos

        // Timeout de 5 minutos
        setTimeout(() => {
            clearInterval(checkInterval);
            if (btn && btn.disabled) {
                showWarning('A restauração está demorando mais do que o esperado. Tente novamente mais tarde.');
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        }, 300000); // 5 minutos

    } catch (error) {
        console.error('Error restoring backup:', error);
        showError('Erro ao restaurar backup');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalContent;
        }
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

function formatTime(seconds) {
    if (!seconds || seconds < 0) return 'Calculando...';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

async function loadSchedules() {
    try {
        const response = await fetch('/api/schedules');
        const schedules = await response.json();
        allSchedules = schedules;
        
        // Update activity timeline with schedules
        updateActivityTimeline(allBackups, schedules);
        
        const schedulesTable = document.getElementById('schedulesTable');
        
        if (schedules.length === 0) {
            schedulesTable.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-calendar fa-3x mb-3 d-block"></i>
                        Nenhum agendamento configurado
                    </td>
                </tr>
            `;
            return;
        }
        
        schedulesTable.innerHTML = schedules.map(schedule => {
            const scheduleTypeLabels = {
                'daily': 'Diário',
                'weekly': 'Semanal',
                'interval_hours': 'Intervalo (Horas)',
                'interval_days': 'Intervalo (Dias)'
            };
            
            const isActive = schedule.is_active === 1;
            
            return `
                <tr>
                    <td><strong>${schedule.host_name}</strong></td>
                    <td><span class="badge bg-info">${scheduleTypeLabels[schedule.schedule_type] || schedule.schedule_type}</span></td>
                    <td>${formatScheduleValue(schedule.schedule_type, schedule.schedule_value)}</td>
                    <td>${schedule.last_run ? formatDate(schedule.last_run) : '<span class="text-muted">Nunca executado</span>'}</td>
                    <td>${schedule.next_run ? formatDate(schedule.next_run) : '<span class="text-muted">N/A</span>'}</td>
                    <td>
                        <span class="badge ${isActive ? 'bg-success' : 'bg-secondary'}">
                            ${isActive ? 'Ativo' : 'Inativo'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm ${isActive ? 'btn-warning' : 'btn-success'}" onclick="toggleSchedule(${schedule.id})" title="${isActive ? 'Desativar' : 'Ativar'}">
                            <i class="fas fa-${isActive ? 'pause' : 'play'}"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteSchedule(${schedule.id})" title="Excluir">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading schedules:', error);
    }
}

function formatScheduleValue(type, value) {
    switch (type) {
        case 'daily':
            return `Todos os dias às ${value}`;
        case 'weekly':
            const [day, time] = value.split(' ');
            const days = {
                'mon': 'Segunda', 'tue': 'Terça', 'wed': 'Quarta',
                'thu': 'Quinta', 'fri': 'Sexta', 'sat': 'Sábado', 'sun': 'Domingo'
            };
            return `Toda ${days[day]} às ${time}`;
        case 'interval_hours':
            return `A cada ${value} hora(s)`;
        case 'interval_days':
            return `A cada ${value} dia(s)`;
        default:
            return value;
    }
}

function showAddScheduleModal() {
    currentScheduleId = null;
    document.getElementById('scheduleModalTitle').innerHTML = '<i class="fas fa-clock"></i> Adicionar Agendamento';
    document.getElementById('scheduleForm').reset();
    document.getElementById('scheduleId').value = '';
    
    loadHostsForSchedule();
    scheduleModal.show();
}

async function loadHostsForSchedule() {
    try {
        const response = await fetch('/api/ssh-hosts');
        const hosts = await response.json();
        
        const select = document.getElementById('scheduleHostSelect');
        select.innerHTML = '<option value="">Selecione um servidor...</option>' +
            hosts.map(host => `<option value="${host.id}">${host.name} (${host.host})</option>`).join('');
    } catch (error) {
        console.error('Error loading hosts:', error);
    }
}

function updateScheduleValueField() {
    const scheduleType = document.getElementById('scheduleType').value;
    const scheduleValue = document.getElementById('scheduleValue');
    const scheduleValueHelp = document.getElementById('scheduleValueHelp');
    
    switch (scheduleType) {
        case 'daily':
            scheduleValue.type = 'time';
            scheduleValue.placeholder = '';
            scheduleValueHelp.textContent = 'Horário em que o backup será executado todos os dias';
            break;
        case 'weekly':
            scheduleValue.type = 'text';
            scheduleValue.placeholder = 'mon 14:00';
            scheduleValueHelp.textContent = 'Formato: dia hora (ex: mon 14:00, tue 09:30). Dias: mon, tue, wed, thu, fri, sat, sun';
            break;
        case 'interval_hours':
            scheduleValue.type = 'number';
            scheduleValue.placeholder = '6';
            scheduleValue.min = '1';
            scheduleValue.max = '24';
            scheduleValueHelp.textContent = 'Intervalo em horas (1-24)';
            break;
        case 'interval_days':
            scheduleValue.type = 'number';
            scheduleValue.placeholder = '1';
            scheduleValue.min = '1';
            scheduleValue.max = '30';
            scheduleValueHelp.textContent = 'Intervalo em dias (1-30)';
            break;
        default:
            scheduleValue.type = 'text';
            scheduleValue.placeholder = 'Selecione o tipo primeiro';
            scheduleValueHelp.textContent = '';
    }
}

async function saveSchedule() {
    const hostId = document.getElementById('scheduleHostSelect').value;
    const scheduleType = document.getElementById('scheduleType').value;
    let scheduleValue = document.getElementById('scheduleValue').value;
    
    if (!hostId || !scheduleType || !scheduleValue) {
        showError('Por favor, preencha todos os campos obrigatórios');
        return;
    }
    
    if (scheduleType === 'daily' && scheduleValue.length === 5) {
        const parts = scheduleValue.split(':');
        scheduleValue = `${parts[0]}:${parts[1]}`;
    }
    
    try {
        const response = await fetch('/api/schedules', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                ssh_host_id: parseInt(hostId),
                schedule_type: scheduleType,
                schedule_value: scheduleValue
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Agendamento criado com sucesso!');
            scheduleModal.hide();
            loadSchedules();
        } else {
            showError('Erro ao criar agendamento: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving schedule:', error);
        showError('Erro ao salvar agendamento');
    }
}

async function toggleSchedule(scheduleId) {
    try {
        const response = await fetch(`/api/schedules/${scheduleId}/toggle`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess(result.message);
            loadSchedules();
        } else {
            showError('Erro: ' + result.error);
        }
    } catch (error) {
        console.error('Error toggling schedule:', error);
        showError('Erro ao alterar status do agendamento');
    }
}

async function deleteSchedule(scheduleId) {
    const confirmed = await showConfirm(
        'Excluir Agendamento',
        'Tem certeza que deseja excluir este agendamento? Esta ação não pode ser desfeita.'
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/schedules/${scheduleId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Agendamento excluído com sucesso!');
            loadSchedules();
        } else {
            showError('Erro ao excluir agendamento: ' + result.error);
        }
    } catch (error) {
        console.error('Error deleting schedule:', error);
        showError('Erro ao excluir agendamento');
    }
}

async function showEmailConfigModal() {
    try {
        const response = await fetch('/api/email-config');
        const config = await response.json();
        
        document.getElementById('emailEnabled').checked = config.enabled || false;
        document.getElementById('smtpServer').value = config.smtp_server || '';
        document.getElementById('smtpPort').value = config.smtp_port || 587;
        document.getElementById('smtpUseTls').checked = config.smtp_use_tls !== 0;
        document.getElementById('smtpUsername').value = config.smtp_username || '';
        document.getElementById('smtpPassword').value = '';
        document.getElementById('smtpFrom').value = config.smtp_from || '';
        document.getElementById('notifyEmail').value = config.notify_email || '';
        document.getElementById('notifyOnSuccess').checked = config.notify_on_success !== 0;
        document.getElementById('notifyOnFailure').checked = config.notify_on_failure !== 0;
        document.getElementById('notifySchedules').checked = config.notify_schedules !== 0;
        
        emailConfigModal.show();
    } catch (error) {
        console.error('Error loading email config:', error);
        showError('Erro ao carregar configurações de email');
    }
}

async function saveEmailConfig() {
    const config = {
        enabled: document.getElementById('emailEnabled').checked,
        smtp_server: document.getElementById('smtpServer').value.trim(),
        smtp_port: parseInt(document.getElementById('smtpPort').value),
        smtp_use_tls: document.getElementById('smtpUseTls').checked,
        smtp_username: document.getElementById('smtpUsername').value.trim(),
        smtp_password: document.getElementById('smtpPassword').value,
        smtp_from: document.getElementById('smtpFrom').value.trim(),
        notify_email: document.getElementById('notifyEmail').value.trim(),
        notify_on_success: document.getElementById('notifyOnSuccess').checked,
        notify_on_failure: document.getElementById('notifyOnFailure').checked,
        notify_schedules: document.getElementById('notifySchedules').checked
    };
    
    if (config.enabled && (!config.smtp_server || !config.smtp_from || !config.notify_email)) {
        showWarning('Preencha os campos obrigatórios (Servidor SMTP, Email Remetente e Destinatário)');
        return;
    }
    
    try {
        const response = await fetch('/api/email-config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Configurações salvas com sucesso!');
            emailConfigModal.hide();
        } else {
            showError('Erro ao salvar: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving email config:', error);
        showError('Erro ao salvar configurações');
    }
}

async function testEmailConfig() {
    const config = {
        smtp_server: document.getElementById('smtpServer').value.trim(),
        smtp_port: parseInt(document.getElementById('smtpPort').value),
        smtp_use_tls: document.getElementById('smtpUseTls').checked,
        smtp_username: document.getElementById('smtpUsername').value.trim(),
        smtp_password: document.getElementById('smtpPassword').value,
        smtp_from: document.getElementById('smtpFrom').value.trim(),
        notify_email: document.getElementById('notifyEmail').value.trim()
    };
    
    if (!config.smtp_server || !config.smtp_from || !config.notify_email) {
        showWarning('Preencha os campos obrigatórios primeiro');
        return;
    }
    
    showInfo('Enviando email de teste...');
    
    try {
        const response = await fetch('/api/email-config/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Email de teste enviado! Verifique sua caixa de entrada.');
        } else {
            showError('Falha ao enviar: ' + result.error);
        }
    } catch (error) {
        console.error('Error testing email:', error);
        showError('Erro ao testar email');
    }
}