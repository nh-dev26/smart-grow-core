let allLogs = [];
let filteredLogs = [];
let displayedCount = 0;
const LOGS_PER_PAGE = 20;
let updateInterval = null;

// ジョブ種別判定
function getJobType(message) {
    if (!message) return 'system';
    
    const msg = message.toLowerCase();
    
    if (msg.includes('camera') || msg.includes('カメラ') || msg.includes('photo')) {
        return 'camera';
    }
    
    if (msg.includes('sensor') || msg.includes('センサー') || 
        msg.includes('temperature') || msg.includes('温度') ||
        msg.includes('humidity') || msg.includes('湿度') ||
        msg.includes('pressure') || msg.includes('圧')) {
        return 'sensor';
    }
    
    if (msg.includes('pump') || msg.includes('ポンプ') || 
        msg.includes('water') || msg.includes('水やり')) {
        return 'water';
    }
    
    return 'system';
}

// ジョブアイコン取得
function getJobIcon(jobType) {
    const icons = {
        'camera': '📷',
        'sensor': '📊',
        'water': '💧',
        'system': '🔧'
    };
    return icons[jobType] || '🔧';
}

// ジョブラベル取得
function getJobLabel(jobType) {
    const labels = {
        'camera': 'カメラ',
        'sensor': 'センサー',
        'water': '水やり',
        'system': 'システム'
    };
    return labels[jobType] || 'システム';
}

// ログレベルのバッジクラス
function getLogLevelBadge(level) {
    const badges = {
        'CRITICAL': 'bg-danger',
        'ERROR': 'bg-danger',
        'WARNING': 'bg-warning text-dark',
        'INFO': 'bg-info text-dark'
    };
    return badges[level] || 'bg-secondary';
}

// ログレベルのアイコン
function getLogLevelIcon(level) {
    const icons = {
        'CRITICAL': '⚠️',
        'ERROR': '❌',
        'WARNING': '⚠️',
        'INFO': 'ℹ️'
    };
    return icons[level] || 'ℹ️';
}

// ログ読み込み
function loadLogs() {
    // 全件取得してフロントエンドでフィルター（より柔軟）
    fetch('/api/logs-list?limit=500')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                allLogs = result.logs.map(log => ({
                    ...log,
                    jobType: getJobType(log.message)
                }));
                applyFilters();
                
                // 最終更新時刻
                const now = new Date();
                document.getElementById('last-update').textContent = now.toLocaleTimeString('ja-JP');
            } else {
                console.error('Failed to load logs:', result.error);
            }
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
        });
}

// フィルター適用
function applyFilters() {
    const levelFilter = document.getElementById('level-filter').value;
    const layerFilter = document.getElementById('layer-filter').value;
    const jobFilter = document.getElementById('job-filter').value;
    const searchText = document.getElementById('search-input').value.toLowerCase();
    
    filteredLogs = allLogs.filter(log => {
        // ログレベルフィルター
        if (levelFilter && log.log_level !== levelFilter) {
            return false;
        }
        
        // レイヤーフィルター
        if (layerFilter && log.layer_id.toString() !== layerFilter) {
            return false;
        }
        
        // ジョブ種別フィルター
        if (jobFilter && log.jobType !== jobFilter) {
            return false;
        }
        
        // 検索フィルター
        if (searchText) {
            const searchable = (log.message + ' ' + (log.details || '')).toLowerCase();
            if (!searchable.includes(searchText)) {
                return false;
            }
        }
        
        return true;
    });
    
    // 結果件数表示
    document.getElementById('result-count').textContent = filteredLogs.length;
    
    // 表示をリセット
    displayedCount = 0;
    renderLogs();
}

// ログをレンダリング
function renderLogs(append = false) {
    const container = document.getElementById('logs-container');
    
    if (!append) {
        container.innerHTML = '';
    }
    
    if (filteredLogs.length === 0) {
        document.getElementById('no-logs-message').style.display = 'block';
        document.getElementById('load-more-container').style.display = 'none';
        return;
    }
    
    document.getElementById('no-logs-message').style.display = 'none';
    
    // 表示するログ
    const endIndex = Math.min(displayedCount + LOGS_PER_PAGE, filteredLogs.length);
    const logsToDisplay = filteredLogs.slice(displayedCount, endIndex);
    
    // DocumentFragmentを使用してパフォーマンス改善
    const fragment = document.createDocumentFragment();
    logsToDisplay.forEach(log => {
        const card = createLogCard(log);
        fragment.appendChild(card);
    });
    container.appendChild(fragment);
    
    displayedCount = endIndex;
    
    // もっと読み込むボタン
    if (displayedCount < filteredLogs.length) {
        document.getElementById('load-more-container').style.display = 'block';
    } else {
        document.getElementById('load-more-container').style.display = 'none';
    }
}

// ログカードを作成
function createLogCard(log) {
    const card = document.createElement('div');
    card.className = 'card mb-2 shadow-sm log-card';
    card.style.cursor = 'pointer';
    card.style.border = '1px solid #e0e0e0';
    card.style.borderLeft = 'none';
    card.onclick = () => openLogModal(log);
    
    const levelBadge = getLogLevelBadge(log.log_level);
    const levelIcon = getLogLevelIcon(log.log_level);
    const jobIcon = getJobIcon(log.jobType);
    const jobLabel = getJobLabel(log.jobType);
    
    const timestamp = new Date(log.timestamp);
    const timeStr = timestamp.toLocaleString('ja-JP', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    card.innerHTML = `
        <div class="card-body py-2">
            <div class="row align-items-center">
                <div class="col-auto">
                    <span class="badge ${levelBadge}">${log.log_level}</span>
                </div>
                <div class="col-auto">
                    <small class="text-muted">${timeStr}</small>
                </div>
                <div class="col-auto">
                    <small class="text-muted">Layer ${log.layer_id}</small>
                </div>
                <div class="col-auto">
                    <small>${jobIcon} ${jobLabel}</small>
                </div>
                <div class="col">
                    <strong>${log.message}</strong>
                    ${log.details ? `<br><small class="text-muted">${log.details.substring(0, 50)}...</small>` : ''}
                </div>
            </div>
        </div>
    `;
    
    return card;
}

// さらに読み込む
function loadMoreLogs() {
    renderLogs(true);
}

// ログ詳細モーダルを開く
function openLogModal(log) {
    const timestamp = new Date(log.timestamp);
    document.getElementById('modal-timestamp').textContent = timestamp.toLocaleString('ja-JP');
    document.getElementById('modal-level').innerHTML = `<span class="badge ${getLogLevelBadge(log.log_level)}">${log.log_level}</span>`;
    document.getElementById('modal-layer').textContent = `Layer ${log.layer_id}`;
    document.getElementById('modal-message').textContent = log.message;
    
    // 詳細情報
    if (log.details) {
        document.getElementById('modal-details-section').style.display = 'block';
        document.getElementById('modal-details').textContent = log.details;
    } else {
        document.getElementById('modal-details-section').style.display = 'none';
    }
    
    // ジョブ種別
    const jobIcon = getJobIcon(log.jobType);
    const jobLabel = getJobLabel(log.jobType);
    document.getElementById('modal-job-type').innerHTML = `
        <div class="alert alert-light mb-0">
            <small><strong>${jobIcon} ${jobLabel}</strong></small>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('logModal'));
    modal.show();
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    loadLogs();
    
    // 30秒ごとに自動更新
    updateInterval = setInterval(loadLogs, 30000);
});

// ページを離れるときにインターバルをクリア
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
