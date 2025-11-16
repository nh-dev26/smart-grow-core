let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth(); // 0-11
let currentLayerId = 1;
let imagesByDate = {}; // 日付ごとの画像データ
let allImages = []; // 全画像データ
let currentModalDate = null; // 現在モーダルで表示中の日付
let imageModalInstance = null; // モーダルインスタンス（再利用）

// 月の変更
function changeMonth(delta) {
    currentMonth += delta;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    } else if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    loadGallery();
}

// ギャラリー読み込み
function loadGallery() {
    currentLayerId = parseInt(document.getElementById('layer-select').value);
    
    // 月表示を更新
    const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    document.getElementById('current-month-text').textContent = `${currentYear}年 ${monthNames[currentMonth]}`;
    
    // 画像一覧を取得
    fetch(`/api/images?layer_id=${currentLayerId}&limit=1000`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                allImages = result.images;
                processImages();
                renderCalendar();
                renderTimeline();
            } else {
                console.error('Failed to load images:', result.error);
            }
        })
        .catch(error => {
            console.error('Error fetching images:', error);
        });
}

// 画像データを日付ごとに整理
function processImages() {
    imagesByDate = {};
    
    allImages.forEach(img => {
        // ファイル名から日付を抽出: 20250910_100000.jpg -> 2025-09-10
        const filename = img.image_path.split('/').pop();
        const match = filename.match(/^(\d{4})(\d{2})(\d{2})_/);
        
        if (match) {
            const dateStr = `${match[1]}-${match[2]}-${match[3]}`;
            
            if (!imagesByDate[dateStr]) {
                imagesByDate[dateStr] = [];
            }
            
            imagesByDate[dateStr].push({
                path: img.image_path,
                timestamp: img.timestamp,
                date: dateStr
            });
        }
    });
}

// カレンダーをレンダリング
function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';
    
    // 今月の1日
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    
    // 曜日のオフセット
    const startDayOfWeek = firstDay.getDay();
    
    // 今日の日付
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    
    let hasImages = false;
    
    // 空白セルを追加
    for (let i = 0; i < startDayOfWeek; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'calendar-day empty';
        grid.appendChild(emptyCell);
    }
    
    // 日付セルを追加
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const images = imagesByDate[dateStr] || [];
        
        const cell = document.createElement('div');
        cell.className = 'calendar-day';
        
        if (dateStr === todayStr) {
            cell.classList.add('today');
        }
        
        if (images.length > 0) {
            cell.classList.add('has-images');
            hasImages = true;
            cell.onclick = () => openModal(dateStr);
        }
        
        const dayNum = document.createElement('div');
        dayNum.className = 'day-number';
        dayNum.textContent = day;
        cell.appendChild(dayNum);
        
        if (images.length > 0) {
            const count = document.createElement('div');
            count.className = 'image-count';
            count.innerHTML = `<i class="fas fa-camera"></i> ${images.length}`;
            cell.appendChild(count);
        }
        
        grid.appendChild(cell);
    }
    
    // 画像なしメッセージの表示切り替え
    document.getElementById('no-images-message').style.display = hasImages ? 'none' : 'block';
}

// モーダルを開く
function openModal(dateStr) {
    currentModalDate = dateStr;
    
    // モーダルの内容を更新
    updateModalContent(dateStr);
    
    // モーダルが既に開いている場合は何もしない、開いていない場合のみ開く
    if (!imageModalInstance) {
        imageModalInstance = new bootstrap.Modal(document.getElementById('imageModal'));
        // モーダルが閉じられたらインスタンスをリセット
        document.getElementById('imageModal').addEventListener('hidden.bs.modal', function () {
            imageModalInstance = null;
        });
    }
    
    imageModalInstance.show();
}

// モーダルの内容を更新（日付変更時に使用）
function updateModalContent(dateStr) {
    const images = imagesByDate[dateStr] || [];
    
    currentModalDate = dateStr;
    
    // 日付表示
    const date = new Date(dateStr);
    document.getElementById('modal-date').textContent = 
        `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
    
    // AI解析レポートセクションを非表示にする（日付が変わったら一旦隠す）
    document.getElementById('ai-report-section').style.display = 'none';
    
    // 画像がある場合は表示、ない場合はメッセージ表示
    if (images.length > 0) {
        showImage(images[0], images);
    } else {
        showNoImageMessage();
    }
}

// 画像を表示
function showImage(imageData, allDayImages) {
    const modalImage = document.getElementById('modal-image');
    modalImage.src = '/' + imageData.path;
    modalImage.style.display = 'block';
    modalImage.parentElement.querySelector('.no-image-message')?.remove();
    
    // センサーデータを取得（画像のタイムスタンプに近いデータ）
    fetchSensorData(imageData.timestamp);
    
    // AI解析レポートを取得
    fetchAIReportForImage(imageData.path);
    
    // センサー情報を表示
    document.getElementById('sensor-info').style.display = 'flex';
    
    // 同じ日の他の画像
    if (allDayImages.length > 1) {
        document.getElementById('same-day-images').style.display = 'block';
        document.getElementById('same-day-count').textContent = allDayImages.length;
        
        const thumbnailsContainer = document.getElementById('same-day-thumbnails');
        thumbnailsContainer.innerHTML = '';
        
        allDayImages.forEach(img => {
            const col = document.createElement('div');
            col.className = 'col-4';
            col.innerHTML = `<img src="/${img.path}" class="img-fluid thumbnail-img" onclick="showImage(${JSON.stringify(img).replace(/"/g, '&quot;')}, ${JSON.stringify(allDayImages).replace(/"/g, '&quot;')})">`;
            thumbnailsContainer.appendChild(col);
        });
    } else {
        document.getElementById('same-day-images').style.display = 'none';
    }
}

// 画像なしメッセージを表示
function showNoImageMessage() {
    const modalImage = document.getElementById('modal-image');
    modalImage.style.display = 'none';
    
    // 既存のメッセージを削除
    modalImage.parentElement.querySelector('.no-image-message')?.remove();
    
    // メッセージを追加
    const noImageDiv = document.createElement('div');
    noImageDiv.className = 'no-image-message text-center py-5';
    noImageDiv.innerHTML = `
        <i class="fas fa-image fa-3x text-muted mb-3"></i>
        <h5 class="text-muted">この日は画像がありません</h5>
        <p class="text-muted mb-0">前後の日の画像を確認してください</p>
    `;
    modalImage.parentElement.appendChild(noImageDiv);
    
    // センサー情報を非表示
    document.getElementById('sensor-info').style.display = 'none';
    
    // 同じ日の他の画像を非表示
    document.getElementById('same-day-images').style.display = 'none';
}

// センサーデータを取得
function fetchSensorData(timestamp) {
    // タイムスタンプに近いセンサーデータを取得
    fetch(`/api/dashboard-data`)
        .then(response => response.json())
        .then(result => {
            if (result.success && result.sensor_data) {
                const data = result.sensor_data;
                document.getElementById('modal-temp').textContent = 
                    data.temperature !== null ? `${data.temperature}℃` : 'N/A';
                document.getElementById('modal-humidity').textContent = 
                    data.humidity !== null ? `${data.humidity}%` : 'N/A';
            }
        })
        .catch(error => {
            console.error('Error fetching sensor data:', error);
        });
}

// AI解析レポートを取得
function fetchAIReportForImage(imagePath) {
    const reportSection = document.getElementById('ai-report-section');
    const reportContent = document.getElementById('gallery-ai-report-content');
    
    // API経由で画像に対応するAI解析レポートを取得
    fetch(`/api/ai-report-by-image?image_path=${encodeURIComponent(imagePath)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.report) {
                const report = data.report;
                const stars = getGalleryStarRating(report.growth_rate);
                const timestamp = new Date(report.timestamp).toLocaleString('ja-JP');
                
                reportContent.innerHTML = `
                    <div class="d-flex align-items-center mb-3">
                        <div class="me-3">
                            <div style="font-size: 2rem;">${stars}</div>
                        </div>
                        <div>
                            <h5 class="mb-1">成長率: ${report.growth_rate}%</h5>
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> ${timestamp}
                            </small>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <h6 class="text-muted">状態サマリー</h6>
                        <p class="mb-0">${report.ai_summary || 'データなし'}</p>
                    </div>
                    
                    ${report.ai_advice ? `
                    <div class="mb-2">
                        <h6 class="text-muted"><i class="fas fa-lightbulb text-warning"></i> アドバイス</h6>
                        <div class="alert alert-info py-2 mb-0">
                            <small>${formatGalleryAdvice(report.ai_advice)}</small>
                        </div>
                    </div>
                    ` : ''}
                `;
                
                reportSection.style.display = 'block';
            } else {
                // AI解析レポートがない場合は非表示
                reportSection.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error fetching AI report:', error);
            reportSection.style.display = 'none';
        });
}

// 成長率から星評価を生成（ギャラリー用）
function getGalleryStarRating(growthRate) {
    const starCount = Math.ceil(growthRate / 20);
    const fullStars = '⭐'.repeat(Math.min(starCount, 5));
    const emptyStars = '☆'.repeat(Math.max(0, 5 - starCount));
    return fullStars + emptyStars;
}

// アドバイステキストをフォーマット（ギャラリー用）
function formatGalleryAdvice(advice) {
    if (!advice) return 'アドバイスなし';
    
    const lines = advice.split('\n');
    let formatted = '';
    lines.forEach(line => {
        line = line.trim();
        if (line.startsWith('•') || line.startsWith('-') || line.startsWith('*')) {
            formatted += line.substring(1).trim() + '<br>';
        } else if (line) {
            formatted += line + '<br>';
        }
    });
    
    return formatted || advice;
}

// 前後の日へ移動
function navigateDay(delta) {
    if (!currentModalDate) return;
    
    const currentDate = new Date(currentModalDate);
    currentDate.setDate(currentDate.getDate() + delta);
    
    const newDateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(currentDate.getDate()).padStart(2, '0')}`;
    
    // モーダルの内容のみを更新（新しくモーダルを開かない）
    updateModalContent(newDateStr);
}

// 表示切替
function toggleView(view) {
    if (view === 'timeline') {
        document.getElementById('timeline-view').style.display = 'block';
        document.getElementById('calendar-view').style.display = 'none';
        renderTimeline(); // タイムラインを描画
    } else {
        document.getElementById('timeline-view').style.display = 'none';
        document.getElementById('calendar-view').style.display = 'block';
        renderCalendar(); // カレンダーを描画
    }
}

// タイムラインのレンダリング
function renderTimeline() {
    const timelineContainer = document.getElementById('timeline-view');
    timelineContainer.innerHTML = '<div class="timeline"></div>'; // Reset
    const timeline = timelineContainer.querySelector('.timeline');

    if (allImages.length === 0) {
        timeline.innerHTML = '<p class="text-muted text-center">表示できる画像がありません。</p>';
        return;
    }

    // 日付ごとにグループ化
    const imagesByDay = {};
    allImages.forEach(img => {
        const date = new Date(img.timestamp).toLocaleDateString('ja-JP');
        if (!imagesByDay[date]) {
            imagesByDay[date] = [];
        }
        imagesByDay[date].push(img);
    });

    for (const date in imagesByDay) {
        const dayImages = imagesByDay[date];
        const firstImage = dayImages[0];

        const timelineItem = document.createElement('div');
        timelineItem.className = 'timeline-item';

        timelineItem.innerHTML = `
            <div class="timeline-icon">
                <i class="fas fa-camera"></i>
            </div>
            <div class="card border-0 shadow-sm">
                <div class="card-header">
                    <strong>${date}</strong>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <img src="/${firstImage.image_path}" class="img-fluid rounded" style="cursor: pointer;" onclick="openModal('${firstImage.date}')">
                        </div>
                        <div class="col-md-8" id="report-${firstImage.date}">
                            <p class="text-muted">AI解析レポートを読み込み中...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        timeline.appendChild(timelineItem);
        fetchAIReportForTimeline(firstImage.image_path, `report-${firstImage.date}`);
    }
}

// タイムライン用のAIレポート取得
function fetchAIReportForTimeline(imagePath, elementId) {
    const reportContainer = document.getElementById(elementId);
    fetch(`/api/ai-report-by-image?image_path=${encodeURIComponent(imagePath)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.report) {
                const report = data.report;
                reportContainer.innerHTML = `
                    <h5>${report.ai_summary}</h5>
                    <p class="text-muted">${report.ai_advice}</p>
                    <button class="btn btn-sm btn-outline-success" onclick="openModal('${new Date(report.timestamp).toISOString().split('T')[0]}')">
                        詳細を見る
                    </button>
                `;
            } else {
                reportContainer.innerHTML = '<p class="text-muted">この画像のAI解析レポートはありません。</p>';
            }
        });
}


// 初期化
document.addEventListener('DOMContentLoaded', function() {
    loadGallery();
});