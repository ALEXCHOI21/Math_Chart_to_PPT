const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const resultArea = document.getElementById('result-area');
const loadingOverlay = document.getElementById('loading-overlay');
const imagePreview = document.getElementById('image-preview');
const jsonDisplay = document.getElementById('json-display');
const downloadBtn = document.getElementById('download-btn');

let currentFileId = null;

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
        const response = await fetch('/upload', {
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
            window.location.href = result.download_url;
        };

    } catch (error) {
        console.error(error);
        alert('처리 중 오류가 발생했습니다: ' + error.message);
        loadingOverlay.style.display = 'none';
    }
}
