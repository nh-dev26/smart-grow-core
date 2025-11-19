// static/js/settings.js

// APIエンドポイントの定義
const API_URLS = {
    fetch: '/api/system-config',                     // GET: 全設定取得
    updateThreshold: '/api/settings/thresholds',        // POST: 制御・閾値設定の更新
    resetThreshold: '/api/settings/thresholds/reset',   // POST: 制御・閾値設定のリセット
    updateIntegration: '/api/settings/integrations',    // POST: 連携設定の更新
    resetIntegration: '/api/settings/integrations/reset'// POST: 連携設定のリセット
};

// ------------------------------------------
// 1. 初期設定値の読み込み
// ------------------------------------------
async function loadSettings() {
    try {
        const response = await fetch(API_URLS.fetch);
        if (!response.ok) throw new Error('設定データの取得に失敗しました。');
        
        const settings_json = await response.json();
        settings = settings_json.config || {};
        console.log(settings)
        
        // 制御・閾値設定をセット
        document.getElementById('water_duration').value = settings.water_duration_sec || 0;
        document.getElementById('temp_max').value = settings.temp_high_threshold || 0;
        document.getElementById('temp_min').value = settings.temp_low_threshold || 0;
        document.getElementById('supply_low').value = settings.supply_low_threshold || 0;
        document.getElementById('drain_high').value = settings.drain_high_threshold || 0;

        // 連携設定をセット
        document.getElementById('llm_model').value = settings.llm_model_name || '';
        
        console.log('設定データを読み込みました。', settings);

    } catch (error) {
        console.error('設定の読み込みエラー:', error);
        displayMessage('現在の設定の読み込み中にエラーが発生しました。', 'alert-danger');
    }
}

// ------------------------------------------
// 2. 制御・閾値設定の送信処理
// ------------------------------------------
async function handleThresholdSubmit(e) {
    e.preventDefault(); 
    
    const data = {
        water_duration_sec: parseInt(document.getElementById('water_duration').value),
        temp_high_threshold: parseFloat(document.getElementById('temp_max').value),
        temp_low_threshold: parseFloat(document.getElementById('temp_min').value),
        supply_low_threshold: parseFloat(document.getElementById('supply_low').value),
        drain_high_threshold: parseFloat(document.getElementById('drain_high').value)
    };
    
    await saveSettings(API_URLS.updateThreshold, data, '制御・閾値設定');
}

// ------------------------------------------
// 3. 連携設定の送信処理
// ------------------------------------------
async function handleIntegrationSubmit(e) {
    e.preventDefault();
    
    const data = {
        llm_model_name: document.getElementById('llm_model').value
    };

    await saveSettings(API_URLS.updateIntegration, data, '連携設定');
}

// ------------------------------------------
// 4. 設定保存の共通ロジック
// ------------------------------------------
async function saveSettings(apiUrl, data, settingName) {
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            displayMessage(`${settingName}を正常に保存しました。`, 'alert-success');
        } else {
            const errorData = await response.json();
            displayMessage(`${settingName}の保存に失敗しました: ${errorData.error || response.statusText}`, 'alert-warning');
        }
        
    } catch (error) {
        console.error(`${settingName}の保存中にエラーが発生しました:`, error);
        displayMessage('ネットワークエラーにより設定を保存できませんでした。', 'alert-danger');
    }
}

// ------------------------------------------
// 5. デフォルト設定に戻す処理 (共通)
// ------------------------------------------
async function handleReset(apiUrl, settingName) {
    if (!confirm(`本当に${settingName}をデフォルトに戻しますか？`)) return;

    try {
        const response = await fetch(apiUrl, { method: 'POST' });

        if (response.ok) {
            displayMessage(`${settingName}がデフォルトに戻されました。`, 'alert-success');
            loadSettings(); // デフォルト値が適用された後、フォームを再読み込み
        } else {
            const errorData = await response.json();
            displayMessage(`リセットに失敗しました: ${errorData.error || response.statusText}`, 'alert-warning');
        }

    } catch (error) {
        console.error('リセット中にエラーが発生しました:', error);
        displayMessage('リセット中にネットワークエラーが発生しました。', 'alert-danger');
    }
}

// ------------------------------------------
// 6. メッセージ表示ヘルパー関数
// ------------------------------------------
function displayMessage(message, className) {
    const container = document.getElementById('message-area');
    // ... (前回のメッセージ表示ロジックと同じ) ...
    container.innerHTML = `
        <div class="alert ${className} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    setTimeout(() => {
        const alertElement = container.querySelector('.alert');
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement); 
            bsAlert.close();
        }
    }, 3000);
}


// ------------------------------------------
// 7. イベントリスナーのセットアップ
// ------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // 制御・閾値フォーム
    document.getElementById('threshold-form').addEventListener('submit', handleThresholdSubmit);
    document.getElementById('reset-threshold-btn').addEventListener('click', () => {
        handleReset(API_URLS.resetThreshold, '制御・閾値設定');
    });

    // 連携フォーム
    document.getElementById('integration-form').addEventListener('submit', handleIntegrationSubmit);
    document.getElementById('reset-integration-btn').addEventListener('click', () => {
        handleReset(API_URLS.resetIntegration, '連携設定');
    });
    
    // ページの初期化
    loadSettings();
});