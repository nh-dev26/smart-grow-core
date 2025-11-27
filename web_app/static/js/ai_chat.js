let imageSelectModal = null;
let imagesByDate = {};
let allChatImages = [];
let selectedImageFilename = null;
let tempSelectedImage = null;
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth();

document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('imageSelectModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
        imageSelectModal = new bootstrap.Modal(modalEl);
    }

    setupEventListeners();
    loadImageList();

    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            highlight: function (code, lang) {
                try {
                    if (lang && hljs.getLanguage(lang)) {
                        return hljs.highlight(code, { language: lang }).value;
                    }
                    return hljs.highlightAuto(code).value;
                } catch (e) {
                    return code;
                }
            }
        });
    }
});

function setupEventListeners() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');

    if (chatForm) {
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            if (userInput.value.trim() !== '') {
                sendMessage(null);
            }
        });
    }

    if (userInput) {
        userInput.addEventListener('input', autoResizeTextarea);
        autoResizeTextarea(); 
        
        userInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault(); 
                
                if (this.value.trim() !== '') {
                    sendMessage(); 
                }
            }
        });
    }

    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.quick-action-btn');
        if (!btn) return;
        const question = btn.getAttribute('data-question') || '';
        const quickActionType = btn.getAttribute('data-action-type') || null;
        const input = document.getElementById('user-input');
        if (input) input.value = question;
        sendMessage(quickActionType);
    });

    const attachBtn = document.getElementById('attach-image-btn');
    if (attachBtn) attachBtn.addEventListener('click', openImageSelectModal);

    const removeBtn = document.getElementById('remove-image-btn');
    if (removeBtn) removeBtn.addEventListener('click', removeAttachedImage);

    const confirmBtn = document.getElementById('confirm-select-btn');
    if (confirmBtn) confirmBtn.addEventListener('click', confirmImageSelection);

    const thumb = document.getElementById('attached-image-thumb');
    if (thumb) {
        thumb.addEventListener('click', function () {
            if (this.src) window.open(this.src, '_blank');
        });
    }

    const quickBtn = document.getElementById('quick-question-btn');
    if (quickBtn) {
        quickBtn.addEventListener('click', async () => {
            if (!selectedImageFilename) return;
            const input = document.getElementById('user-input');
            if (input) input.value = '';
            await sendMessage('quick_image');
            quickBtn.style.display = 'none';
        });
    }
}

async function loadImageList() {
    try {
        const res = await fetch('/api/images?layer_id=1');
        if (!res.ok) throw new Error(`画像一覧取得失敗: ${res.status}`);
        const data = await res.json();
        allChatImages = Array.isArray(data.images) ? data.images : [];
        imagesByDate = {};
        allChatImages.forEach(img => {
            if (!img.timestamp || !img.filename) return;
            const date = img.timestamp.split('T')[0];
            if (!imagesByDate[date]) imagesByDate[date] = [];
            imagesByDate[date].push(img);
        });
    } catch (err) {
        console.error('loadImageList error:', err);
        allChatImages = [];
        imagesByDate = {};
    }
}

function openImageSelectModal() {
    const latestDate = (allChatImages.length > 0 && allChatImages[0].timestamp)
        ? new Date(allChatImages[0].timestamp)
        : new Date();

    currentYear = latestDate.getFullYear();
    currentMonth = latestDate.getMonth();

    renderModalCalendar(currentYear, currentMonth);
    if (imageSelectModal) imageSelectModal.show();
}

// 【修正箇所】引数 year と month を受け取る
function renderModalCalendar(year, month) {
    const container = document.getElementById('modal-calendar');
    if (!container) return;
    
    // 【変更部分】ヘッダーをボタン付きに修正
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <button class="btn btn-sm btn-outline-secondary" onclick="goToPreviousMonth()">＜</button>
            <strong>${year}年${month+1}月</strong>
            <button class="btn btn-sm btn-outline-secondary" onclick="goToNextMonth()">＞</button>
        </div>
        <div class="mini-calendar-grid">`;
    
    // 曜日のヘッダー
    ['日','月','火','水','木','金','土'].forEach(day => {
        html += `<div class="mini-cal-header">${day}</div>`;
    });

    // カレンダーの残りのロジックはほぼそのまま使用可能
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDayOfWeek = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    for (let i=0;i<startDayOfWeek;i++) html += `<div class="mini-cal-day empty"></div>`;
    for (let day=1; day<=daysInMonth; day++) {
        const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
        const hasImage = imagesByDate[dateStr] && imagesByDate[dateStr].length>0;
        const isToday = dateStr === new Date().toISOString().split('T')[0];
        let className = 'mini-cal-day';
        if (hasImage) className += ' has-image';
        if (isToday) className += ' today';
        html += `<div class="${className}" data-date="${dateStr}">${day}</div>`;
    }
    html += `</div>`;
    container.innerHTML = html;

    // ... （後略：日付選択のイベントリスナー設定ロジックはそのまま）
    container.querySelectorAll('.mini-cal-day').forEach(el=>{
        const date = el.getAttribute('data-date');
        if(!date) return;
        if(imagesByDate[date] && imagesByDate[date].length>0){
            el.classList.add('clickable');
            el.addEventListener('click',function(ev){
                selectDateInModal(date, ev.currentTarget);
            });
        } else el.classList.remove('clickable');
    });

    const preview = document.getElementById('modal-image-preview');
    if(preview) preview.style.display='none';
    const confirmBtn = document.getElementById('confirm-select-btn');
    if(confirmBtn) confirmBtn.disabled=true;
    tempSelectedImage = null;
}

function goToPreviousMonth() {
    currentMonth--;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    renderModalCalendar(currentYear, currentMonth);
}

function goToNextMonth() {
    currentMonth++;
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    renderModalCalendar(currentYear, currentMonth);
}

function selectDateInModal(dateStr, clickedEl) {
    const images = imagesByDate[dateStr];
    if(!images || images.length===0) return;
    tempSelectedImage = images[0];

    const preview = document.getElementById('modal-image-preview');
    const previewImg = document.getElementById('modal-preview-image');
    const dateDisplay = document.getElementById('modal-preview-date');
    if(previewImg) previewImg.src = `/plant_images/layer_1/${tempSelectedImage.filename}`;
    if(dateDisplay) dateDisplay.textContent = new Date(tempSelectedImage.timestamp).toLocaleDateString('ja-JP');
    if(preview) preview.style.display='block';

    const confirmBtn = document.getElementById('confirm-select-btn');
    if(confirmBtn) confirmBtn.disabled=false;

    const container = document.getElementById('modal-calendar');
    if(container){
        container.querySelectorAll('.mini-cal-day').forEach(el=>el.classList.remove('selected'));
    }
    if(clickedEl) clickedEl.classList.add('selected');
}

function removeAttachedImage() {
    selectedImageFilename = null;

    const preview = document.getElementById('attached-image-preview');
    const thumb = document.getElementById('attached-image-thumb');
    if (thumb) thumb.src = '';
    if (preview) preview.style.display = 'none';

    const quickActions = document.getElementById('quick-action-container');
    if (quickActions) quickActions.classList.add('d-none');
}

function addUserMessage(message, imagePath) {
    const chatContainer = document.getElementById('chat-container');
    if(!chatContainer) return;

    const displayMessage = nl2br(escapeHtml(message)); 

    const messageDiv = document.createElement('div');
    messageDiv.className='message user-message';
    let imageHTML='';
    if(imagePath){
        const fullPath=`/plant_images/layer_1/${imagePath}`;
        imageHTML=`<img src="${fullPath}" class="attached-image" alt="添付画像" onclick="showAttachedImage('${fullPath}')">`;
    }
    messageDiv.innerHTML=`
        <div class="message-avatar"><i class="fas fa-user"></i></div>
        <div class="message-bubble user-bubble">
            <div class="message-content"><p class="mb-0">${displayMessage}</p>${imageHTML}</div>
        </div>`;
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function addAIMessage(message){
    const chatContainer = document.getElementById('chat-container');
    if(!chatContainer) return;
    const messageDiv=document.createElement('div');
    messageDiv.className='message ai-message';
    let htmlContent='';
    if(typeof marked!=='undefined'){
        try{htmlContent=marked.parse(message||'');}catch(e){htmlContent=escapeHtml(message||'');}
    }else htmlContent=escapeHtml(message||'');
    messageDiv.innerHTML=`
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-bubble ai-bubble">
            <div class="message-content markdown-body">${htmlContent}</div>
        </div>`;
    chatContainer.appendChild(messageDiv);
    try{messageDiv.querySelectorAll('pre code').forEach((block)=>{if(typeof hljs!=='undefined') hljs.highlightElement(block);});}catch(e){}
    scrollToBottom();
}

async function sendMessage(quickActionType=null){
    const input=document.getElementById('user-input');
    const message=input?input.value.trim():'';
    if(!message && !quickActionType) return; 
    
    const sendBtn=document.getElementById('send-btn');
    if(sendBtn){
        sendBtn.disabled=true; 
        // 修正: 送信ボタンをローディングアイコンのみにする
        sendBtn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
    }

    addUserMessage(message, selectedImageFilename);
    if(input) input.value='';
    
    autoResizeTextarea();

    try{
        showTypingIndicator();
        const requestData={
            message:message,
            image_filename:selectedImageFilename||null,
            sensor_data:null,
            quick_action_type:quickActionType
        };
        const response=await fetch('/api/ai-chat',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(requestData)
        });
        removeTypingIndicator();
        if(!response.ok){
            const text=await response.text().catch(()=>'');
            addAIMessage(`⚠️ **エラー**\n\nAPI Error: ${response.status}\n${escapeHtml(text)}`);
            return;
        }
        const data=await response.json();
        if(data.error) addAIMessage(`⚠️ **エラー**\n\n${escapeHtml(data.error)}`);
        else addAIMessage(data.response||'（AIからの応答がありません）');
    }catch(err){
        console.error('sendMessage error:', err);
        removeTypingIndicator();
        addAIMessage('⚠️ **エラー**\n\n通信中にエラーが発生しました。');
    }finally{
        removeAttachedImage();
        // 修正: 送信完了後、送信ボタンを飛行機アイコンのみに戻す
        if(sendBtn){sendBtn.disabled=false; sendBtn.innerHTML='<i class="fas fa-paper-plane"></i>';}
    }
}

function showAttachedImage(imagePath){if(!imagePath) return; window.open(imagePath,'_blank');}

function escapeHtml(text){
    if(text===undefined||text===null) return''; 
    const map={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}; 
    return String(text).replace(/[&<>"']/g,m=>map[m]);
}

function nl2br(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/\n/g, '<br>');
}

function autoResizeTextarea() {
    const userInput = document.getElementById('user-input');
    if (!userInput) return;
    
    userInput.style.height = 'auto';
    
    const newHeight = userInput.scrollHeight;
    userInput.style.height = `${newHeight}px`;
}

function scrollToBottom(){const chatContainer=document.getElementById('chat-container'); if(!chatContainer) return; chatContainer.scrollTop=chatContainer.scrollHeight;}
function showTypingIndicator(){const chatContainer=document.getElementById('chat-container'); if(!chatContainer) return; if(document.getElementById('typing-indicator')) return; const indicatorDiv=document.createElement('div'); indicatorDiv.className='message ai-message'; indicatorDiv.id='typing-indicator'; indicatorDiv.innerHTML=`
    <div class="message-avatar"><i class="fas fa-robot"></i></div>
    <div class="message-bubble ai-bubble">
        <div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>
    </div>`; chatContainer.appendChild(indicatorDiv); scrollToBottom();}
function removeTypingIndicator(){const indicator=document.getElementById('typing-indicator'); if(indicator) indicator.remove();}

function confirmImageSelection() {
    if (!tempSelectedImage) return;

    selectedImageFilename = tempSelectedImage.filename;

    const preview = document.getElementById('attached-image-preview');
    const thumb = document.getElementById('attached-image-thumb');
    const dateDisplay = document.getElementById('attached-image-date');
    const quickActions = document.getElementById('quick-action-container');

    if (thumb) thumb.src = `/plant_images/layer_1/${selectedImageFilename}`;
    if (dateDisplay) dateDisplay.textContent = new Date(tempSelectedImage.timestamp).toLocaleDateString('ja-JP');
    if (preview) preview.style.display = 'block';

    if (quickActions) quickActions.classList.remove('d-none');

    if (imageSelectModal) imageSelectModal.hide();
    tempSelectedImage = null;
}