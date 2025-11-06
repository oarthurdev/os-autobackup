let logsModal, hostModal, backupModal;
let currentHostId = null;
let backupChart = null;
let allBackups = [];

document.addEventListener('DOMContentLoaded', function() {
    logsModal = new bootstrap.Modal(document.getElementById('logsModal'));
    hostModal = new bootstrap.Modal(document.getElementById('hostModal'));
    backupModal = new bootstrap.Modal(document.getElementById('backupModal'));

    // Load theme preference
    loadTheme();

    // Initialize chart
    initializeChart();

    loadStatus();
    loadSSHHosts();
    loadBackups();

    setInterval(loadStatus, 5000);
    setInterval(loadSSHHosts, 15000);
    setInterval(loadBackups, 10000);
});

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

    // Update chart colors
    if (backupChart) {
        updateChartTheme(newTheme);
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (theme === 'dark') {
        icon.className = 'fas fa-sun';
    } else {
        icon.className = 'fas fa-moon';
    }
}

function initializeChart() {
    const ctx = document.getElementById('backupChart');
    const theme = document.documentElement.getAttribute('data-theme');
    const textColor = theme === 'dark' ? '#eaeaea' : '#212529';
    const gridColor = theme === 'dark' ? '#2d3561' : '#dee2e6';

    backupChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Tamanho do Backup (MB)',
                data: [],
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                },
                x: {
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                }
            }
        }
    });
}

function updateChartTheme(theme) {
    const textColor = theme === 'dark' ? '#eaeaea' : '#212529';
    const gridColor = theme === 'dark' ? '#2d3561' : '#dee2e6';

    backupChart.options.plugins.legend.labels.color = textColor;
    backupChart.options.scales.y.ticks.color = textColor;
    backupChart.options.scales.y.grid.color = gridColor;
    backupChart.options.scales.x.ticks.color = textColor;
    backupChart.options.scales.x.grid.color = gridColor;
    backupChart.update();
}

function updateChart(backups) {
    const successBackups = backups.filter(b => b.status === 'SUCCESS' && b.file_size).slice(0, 10).reverse();

    const labels = successBackups.map(b => {
        const date = new Date(b.timestamp);
        return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    });

    const data = successBackups.map(b => (b.file_size / (1024 * 1024)).toFixed(2));

    backupChart.data.labels = labels;
    backupChart.data.datasets[0].data = data;
    backupChart.update();
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

        // Update statistics and chart
        updateStatistics(backups);
        updateChart(backups);

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
                        ${backup.status === 'SUCCESS' && backup.drive_file_id ? `
                            <button class="btn btn-sm btn-warning" onclick="restoreBackup(${backup.id}, event)" title="Restaurar (Descriptografar)">
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

async function restoreBackup(backupId, event) {
    const confirmed = await showConfirm(
        'Restaurar Backup',
        'Deseja restaurar (descriptografar) este backup? O arquivo .tar.gz será baixado para seu computador.'
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
        const response = await fetch(`/api/backup/${backupId}/restore`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Backup descriptografado com sucesso!');
            // Fazer download automático
            window.location.href = result.download_path;
        } else {
            showError('Erro ao restaurar backup: ' + result.error);
        }
    } catch (error) {
        console.error('Error restoring backup:', error);
        showError('Erro ao restaurar backup');
    } finally {
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