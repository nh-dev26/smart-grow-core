const API_URLS = {
    fetch: '/api/system-config', 
    updateThreshold: '/api/settings/thresholds',
    // 全体リセット用（全体をデフォルトに戻す）
    resetThresholds: '/api/settings/thresholds/reset', 
    resetIntegrations: '/api/settings/integrations/reset', 
    // 個別リセット用（単一キーをデフォルトに戻す）
    resetSingle: '/api/settings/reset', 
    updateIntegration: '/api/settings/integrations'
};

// 1. 初期設定値の読み込み
async function loadSettings() {
    try {
        const response = await fetch(API_URLS.fetch);
        if (!response.ok) throw new Error('設定データの取得に失敗しました。');
        
        const settings_json = await response.json();
        settings = settings_json.config || {};
        console.log(settings)
        
        document.getElementById('water_duration_sec').value = settings.water_duration_sec || 0;
        document.getElementById('temp_high_threshold').value = settings.temp_high_threshold || 0;
        document.getElementById('temp_low_threshold').value = settings.temp_low_threshold || 0;
        document.getElementById('supply_low_threshold').value = settings.supply_low_threshold || 0;
        document.getElementById('drain_high_threshold').value = settings.drain_high_threshold || 0;
        document.getElementById('pump_gpio_sig').value = settings.pump_gpio_sig || 0;
        document.getElementById('i2c_bus_num').value = settings.i2c_bus_num || 0;
        document.getElementById('llm_model_name').value = settings.llm_model_name || '';
        
        console.log('設定データを読み込みました。', settings);

    } catch (error) {
        console.error('設定の読み込みエラー:', error);
        displayMessage('現在の設定の読み込み中にエラーが発生しました。', 'alert-danger');
    }
}

// 2. 制御・閾値設定の送信処理
async function handleThresholdSubmit(e) {
    e.preventDefault(); 
    
    const data = {
        water_duration_sec: parseInt(document.getElementById('water_duration_sec').value),
        temp_high_threshold: parseFloat(document.getElementById('temp_high_threshold').value),
        temp_low_threshold: parseFloat(document.getElementById('temp_low_threshold').value),
        supply_low_threshold: parseFloat(document.getElementById('supply_low_threshold').value),
        drain_high_threshold: parseFloat(document.getElementById('drain_high_threshold').value),
        pump_gpio_sig: parseInt(document.getElementById('pump_gpio_sig').value),
        i2c_bus_num: parseInt(document.getElementById('i2c_bus_num').value)
    };
    
    await saveSettings(API_URLS.updateThreshold, data, '制御・閾値設定');
}

// 3. 連携設定の送信処理
async function handleIntegrationSubmit(e) {
    e.preventDefault();
    
    const data = {
        llm_model_name: document.getElementById('llm_model_name').value
    };

    await saveSettings(API_URLS.updateIntegration, data, '連携設定');
}

// 4. 設定保存の共通ロジック
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


// 5.a. デフォルト設定に戻す処理 （個別）
async function handleSingleReset(key) {
    const inputId = key; 
    const settingName = key; // 表示名はここではキー名をそのまま利用（またはHTMLから取得）

    if (!confirm(`本当に${settingName}をデフォルトに戻しますか？`)) return;

    try {
        // API_URLS.resetSingle を使用
        const response = await fetch(API_URLS.resetSingle, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: key }) 
        });

        // ... (以下は変更なし) ...
        if (response.ok) {
            const data = await response.json();
            document.getElementById(inputId).value = data.default_value; 
            displayMessage(`${settingName}がデフォルト値 (${data.default_value}) に戻されました。`, 'alert-success');
        } else {
            const errorData = await response.json();
            displayMessage(`リセットに失敗しました: ${errorData.error || response.statusText}`, 'alert-warning');
        }
    } catch (error) {
        console.error('リセット中にネットワークエラーが発生しました:', error);
        displayMessage('リセット中にネットワークエラーが発生しました。', 'alert-danger');
    }
}

// 5.b. 全体設定を一括でデフォルトに戻す処理
async function handleOverallReset(apiUrl, settingName) {
    if (!confirm(`本当に${settingName}の全ての設定をデフォルトに戻しますか？\nこの操作は元に戻せません。`)) return;

    try {
        // 全体リセットAPIには、キーを渡さずPOSTリクエストを送る (API側で全体リセットと判断)
        const response = await fetch(apiUrl, { method: 'POST' }); 

        if (response.ok) {
            // 全体リセットが成功したら、設定値を全て再読み込み
            displayMessage(`${settingName}の全ての設定がデフォルトに戻されました。`, 'alert-success');
            loadSettings(); 
        } else {
            const errorData = await response.json();
            displayMessage(`全体リセットに失敗しました: ${errorData.error || response.statusText}`, 'alert-warning');
        }
    } catch (error) {
        console.error('全体リセット中にエラーが発生しました:', error);
        displayMessage('ネットワークエラーにより全体リセットできませんでした。', 'alert-danger');
    }
}

// 6. メッセージ表示ヘルパー関数
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


// 7. イベントリスナーのセットアップ (修正)
document.addEventListener('DOMContentLoaded', () => {
    // 制御・閾値フォーム
    document.getElementById('threshold-form').addEventListener('submit', handleThresholdSubmit);
    // 連携フォーム
    document.getElementById('integration-form').addEventListener('submit', handleIntegrationSubmit);

    // 👇 制御・閾値 全体リセットボタンのバインド
    document.getElementById('reset-tresholds-btn').addEventListener('click', () => {
        handleOverallReset(API_URLS.resetThresholds, '制御・閾値設定');
    });

    // 👇 連携 全体リセットボタンのバインド
    document.getElementById('reset-integrations-btn').addEventListener('click', () => {
        handleOverallReset(API_URLS.resetIntegrations, 'LLM設定'); // API_URLS.resetIntegrations は統合・連携リセット用
    });
    
    // ページの初期化
    loadSettings();
});