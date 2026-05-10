const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const resultArea = document.getElementById('result-area');
const loadingOverlay = document.getElementById('loading-overlay');
const imagePreview = document.getElementById('image-preview');
const jsonDisplay = document.getElementById('json-display');
const downloadBtn = document.getElementById('download-btn');

let currentFileId = null;

// API 베이스 URL (환경에 따라 동적 설정)
const API_BASE_URL = (() => {
    // 로컬 개발: localhost:8000
    if (window.location.hostname === 'localhost') {
        return 'http://localhost:8000';
    }
    // GitHub Pages 또는 Render 배포: 같은 도메인 사용
    return 'https://math-chart-to-ppt.onrender.com';
})();

console.log('🚀 API_BASE_URL:', API_BASE_URL);

// Drag and Drop Logic
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--accent-primary)';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--glass-border)';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

async function handleFileUpload(file) {
    if (!file.type.startsWith('image/')) {
        alert('이미지 파일만 업로드 가능합니다.');
        return;
    }

    // Preview local image
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);

    // Show loading
    loadingOverlay.style.display = 'flex';

    const formData = new FormData();
    formData.append('file', file);

    try {
        console.log('📤 Uploading to:', `${API_BASE_URL}/upload`);
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('서버 처리 오류');

        const result = await response.json();

        // Update UI with results
        currentFileId = result.file_id;
        jsonDisplay.textContent = JSON.stringify(result.data, null, 2);

        loadingOverlay.style.display = 'none';
        dropZone.parentElement.style.display = 'none';
        resultArea.style.display = 'block';

        downloadBtn.onclick = () => {
            const downloadUrl = `${API_BASE_URL}${result.download_url}`;
            console.log('📥 Downloading from:', downloadUrl);
            window.location.href = downloadUrl;
        };

    } catch (error) {
        console.error('❌ Error:', error);
        alert('처리 중 오류가 발생했습니다: ' + error.message);
        loadingOverlay.style.display = 'none';
    }
}

// Gallery Loading Logic
async function loadGallery() {
    const galleryGrid = document.getElementById('gallery-grid');
    if (!galleryGrid) return;

    try {
        const response = await fetch('results.json');
        if (!response.ok) {
            console.log('No gallery data found yet.');
            return;
        }
        
        const results = await response.json();
        if (results.length === 0) return;

        galleryGrid.innerHTML = ''; // Clear placeholder

        results.forEach(item => {
            const card = document.createElement('div');
            card.className = 'gallery-item';
            card.innerHTML = `
                <div class="gallery-preview">
                    <img src="${item.result_png}" alt="Result Preview">
                </div>
                <div class="gallery-info">
                    <h4>${item.original} 변환 결과</h4>
                    <p>분석 일시: ${item.date}</p>
                </div>
                <div class="gallery-actions">
                    <a href="${item.result_png}" target="_blank" class="gallery-btn view">크게 보기</a>
                    <a href="${item.result_pptx}" download class="gallery-btn download">PPT 다운로드</a>
                </div>
            `;
            galleryGrid.appendChild(card);
        });
    } catch (error) {
        console.error('Gallery Error:', error);
        galleryGrid.innerHTML = '<p>갤러리를 불러오지 못했습니다.</p>';
    }
}

// Initial Load
document.addEventListener('DOMContentLoaded', loadGallery);
