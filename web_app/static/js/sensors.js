let temperatureChart = null;
let humidityChart = null;
let currentPeriod = 24; // デフォルト24時間
let updateInterval = null;

// Chart.jsの共通設定
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        intersect: false,
        mode: 'index'
    },
    plugins: {
        legend: {
            display: false
        },
        tooltip: {
            callbacks: {
                title: function(context) {
                    const date = new Date(context[0].parsed.x);
                    return date.toLocaleString('ja-JP');
                }
            }
        }
    },
    scales: {
        x: {
            type: 'time',
            time: {
                unit: 'hour',
                stepSize: 1,
                displayFormats: {
                    hour: 'MM/dd HH:mm'
                }
            },
            ticks: {
                maxTicksLimit: 24,
                autoSkip: true
            },
            grid: {
                display: false
            }
        },
        y: {
            beginAtZero: false,
            grid: {
                color: 'rgba(0, 0, 0, 0.05)'
            }
        }
    }
};

// 期間変更
function changePeriod(hours) {
    currentPeriod = hours;
    
    // ボタンのアクティブ状態を更新
    document.querySelectorAll('.btn-group button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-hours') == hours) {
            btn.classList.add('active');
        }
    });
    
    // X軸の表示単位を変更
    if (hours <= 24) {
        temperatureChart.options.scales.x.time.unit = 'hour';
        temperatureChart.options.scales.x.time.stepSize = 2;
        temperatureChart.options.scales.x.ticks.maxTicksLimit = 12;
        humidityChart.options.scales.x.time.unit = 'hour';
        humidityChart.options.scales.x.time.stepSize = 2;
        humidityChart.options.scales.x.ticks.maxTicksLimit = 12;
    } else if (hours <= 168) {
        temperatureChart.options.scales.x.time.unit = 'day';
        temperatureChart.options.scales.x.time.stepSize = 1;
        temperatureChart.options.scales.x.ticks.maxTicksLimit = 7;
        humidityChart.options.scales.x.time.unit = 'day';
        humidityChart.options.scales.x.time.stepSize = 1;
        humidityChart.options.scales.x.ticks.maxTicksLimit = 7;
    } else {
        temperatureChart.options.scales.x.time.unit = 'day';
        temperatureChart.options.scales.x.time.stepSize = 2;
        temperatureChart.options.scales.x.ticks.maxTicksLimit = 15;
        humidityChart.options.scales.x.time.unit = 'day';
        humidityChart.options.scales.x.time.stepSize = 2;
        humidityChart.options.scales.x.ticks.maxTicksLimit = 15;
    }
    
    // データ更新
    updateSensorData();
}

// センサーデータの更新
function updateSensorData() {
    fetch(`/api/sensor-history?hours=${currentPeriod}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                updateCharts(result.data);
                updateTankStatus();
                
                // 最終更新時刻
                const now = new Date();
                document.getElementById('last-update').textContent = now.toLocaleTimeString('ja-JP');
            } else {
                console.error('Error fetching sensor data:', result.error);
            }
        })
        .catch(error => {
            console.error('Failed to fetch sensor data:', error);
        });
}

// グラフの更新
function updateCharts(data) {
    // データの準備
    const timestamps = data.map(d => new Date(d.timestamp));
    const temperatures = data.map(d => d.temperature);
    const humidities = data.map(d => d.humidity);
    
    // 温度グラフ更新
    temperatureChart.data.labels = timestamps;
    temperatureChart.data.datasets[0].data = temperatures;
    temperatureChart.update('none'); // アニメーションなしで更新
    
    // 湿度グラフ更新
    humidityChart.data.labels = timestamps;
    humidityChart.data.datasets[0].data = humidities;
    humidityChart.update('none');
}

// タンク状態の更新
function updateTankStatus() {
    fetch('/api/dashboard-data')
        .then(response => response.json())
        .then(result => {
            if (result.success && result.sensor_data) {
                const data = result.sensor_data;
                
                // 給水タンク
                if (data.supply_pressure !== null) {
                    updateSupplyTank(data.supply_pressure, 90.0); // 閾値90.0
                }
                
                // 排水タンク
                if (data.drain_pressure !== null) {
                    updateDrainTank(data.drain_pressure, 150.0); // 閾値150.0
                }
            }
        })
        .catch(error => {
            console.error('Failed to fetch tank status:', error);
        });
}

// 給水タンク更新
function updateSupplyTank(pressure, threshold) {
    const valueElement = document.getElementById('supply-value');
    const progressElement = document.getElementById('supply-progress');
    const alertElement = document.getElementById('supply-alert');
    
    valueElement.textContent = `${pressure} kPa`;
    
    // プログレスバー（70-110 kPaの範囲を0-100%にマップ）
    const minPressure = 70;
    const maxPressure = 110;
    const percentage = Math.max(0, Math.min(100, ((pressure - minPressure) / (maxPressure - minPressure)) * 100));
    progressElement.style.width = `${percentage}%`;
    
    // 色とステータス
    if (pressure < threshold) {
        progressElement.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
        alertElement.className = 'alert alert-danger mb-0';
        alertElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> <strong>警告:</strong> 水圧が低下しています。給水が必要です！';
    } else if (pressure < threshold + 5) {
        progressElement.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
        alertElement.className = 'alert alert-warning mb-0';
        alertElement.innerHTML = '<i class="fas fa-exclamation-circle"></i> <strong>注意:</strong> 水圧がやや低下しています。';
    } else {
        progressElement.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
        alertElement.className = 'alert alert-success mb-0';
        alertElement.innerHTML = '<i class="fas fa-check-circle"></i> <strong>正常:</strong> 水圧は適正範囲内です。';
    }
}

// 排水タンク更新
function updateDrainTank(pressure, threshold) {
    const valueElement = document.getElementById('drain-value');
    const progressElement = document.getElementById('drain-progress');
    const alertElement = document.getElementById('drain-alert');
    
    valueElement.textContent = `${pressure} kPa`;
    
    // プログレスバー（80-160 kPaの範囲を0-100%にマップ）
    const minPressure = 80;
    const maxPressure = 160;
    const percentage = Math.max(0, Math.min(100, ((pressure - minPressure) / (maxPressure - minPressure)) * 100));
    progressElement.style.width = `${percentage}%`;
    
    // 色とステータス
    if (pressure > threshold) {
        progressElement.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
        alertElement.className = 'alert alert-danger mb-0';
        alertElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> <strong>警告:</strong> 水圧が高すぎます。排水が必要です！';
    } else if (pressure > threshold - 10) {
        progressElement.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
        alertElement.className = 'alert alert-warning mb-0';
        alertElement.innerHTML = '<i class="fas fa-exclamation-circle"></i> <strong>注意:</strong> 水圧がやや高くなっています。';
    } else {
        progressElement.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
        alertElement.className = 'alert alert-success mb-0';
        alertElement.innerHTML = '<i class="fas fa-check-circle"></i> <strong>正常:</strong> 水圧は適正範囲内です。';
    }
}

// Chart.jsの初期化
document.addEventListener('DOMContentLoaded', function() {
    // 温度グラフ
    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    temperatureChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '温度 (℃)',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                borderWidth: 2,
                pointRadius: 0,  // データポイント非表示
                pointHoverRadius: 5,  // ホバー時は表示
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: '温度 (℃)'
                    }
                }
            }
        }
    });
    
    // 湿度グラフ
    const humCtx = document.getElementById('humidityChart').getContext('2d');
    humidityChart = new Chart(humCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '湿度 (%)',
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                borderWidth: 2,
                pointRadius: 0,  // データポイント非表示
                pointHoverRadius: 5,  // ホバー時は表示
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: {
                    ...chartOptions.scales.y,
                    title: {
                        display: true,
                        text: '湿度 (%)'
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
    
    // 初回データ読み込み
    updateSensorData();
    
    // 30秒ごとに自動更新
    updateInterval = setInterval(updateSensorData, 30000);
});

// ページを離れるときにインターバルをクリア
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
