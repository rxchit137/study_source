const pdfjsLib = window['pdfjs-dist/build/pdf'];
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

let pdfDoc = null, pageNum = 1, pageRendering = false, pageNumPending = null, scale = 1.5,
    canvas = document.getElementById('pdf-render'), ctx = canvas.getContext('2d');

let uploadedFiles = [];

function renderPage(num) {
    pageRendering = true;
    pdfDoc.getPage(num).then((page) => {
        let viewport = page.getViewport({ scale: scale });
        canvas.height = viewport.height; canvas.width = viewport.width;
        let renderContext = { canvasContext: ctx, viewport: viewport };
        let renderTask = page.render(renderContext);
        renderTask.promise.then(() => {
            pageRendering = false;
            if (pageNumPending !== null) { renderPage(pageNumPending); pageNumPending = null; }
        });
    });
    document.getElementById('page-num').textContent = num;
}

function queueRenderPage(num) { if (pageRendering) { pageNumPending = num; } else { renderPage(num); } }

document.getElementById('prev-page').addEventListener('click', () => { if (pageNum <= 1) return; pageNum--; queueRenderPage(pageNum); });
document.getElementById('next-page').addEventListener('click', () => { if (pageNum >= pdfDoc.numPages) return; pageNum++; queueRenderPage(pageNum); });

function loadPDF(url) {
    document.getElementById('pdf-render').classList.remove('hidden');
    document.getElementById('txt-viewer').classList.add('hidden');
    pdfjsLib.getDocument(url).promise.then((pdfDoc_) => {
        pdfDoc = pdfDoc_;
        document.getElementById('page-count').textContent = pdfDoc.numPages;
        pageNum = 1; renderPage(pageNum);
    });
}

function loadTXT(url) {
    document.getElementById('pdf-render').classList.add('hidden');
    document.getElementById('txt-viewer').classList.remove('hidden');
    fetch(url).then(res => res.text()).then(text => {
        document.getElementById('txt-viewer').textContent = text;
        document.getElementById('page-num').textContent = 1;
        document.getElementById('page-count').textContent = 1;
    });
}

function updateFileList(files) {
    const listContainer = document.getElementById('file-list');
    listContainer.innerHTML = '';
    files.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.textContent = file.name;
        item.onclick = () => {
            const url = URL.createObjectURL(file);
            if (file.name.endsWith('.pdf')) { loadPDF(url); } else { loadTXT(url); }
            document.querySelectorAll('.file-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
        };
        if (index === 0) item.classList.add('active');
        listContainer.appendChild(item);
    });
}

const chatMessages = document.getElementById('chat-messages');
function addMessage(text, isUser = false, sources = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    msgDiv.textContent = text;
    if (sources.length > 0) {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'sources';
        sourceDiv.textContent = 'Sources: ' + [...new Set(sources.map(s => `${s.source} (p. ${s.page})`))].join(', ');
        msgDiv.appendChild(sourceDiv);
    }
    chatMessages.appendChild(msgDiv); chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.getElementById('upload-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('file-upload');
    if (fileInput.files.length === 0) return;
    uploadedFiles = Array.from(fileInput.files);
    updateFileList(uploadedFiles);
    const formData = new FormData();
    for (let file of fileInput.files) { formData.append('files', file); }
    addMessage('Uploading and indexing documents...', false);
    const response = await fetch('/upload', { method: 'POST', body: formData });
    const result = await response.json();
    addMessage(result.message, false);
    const firstFile = fileInput.files[0];
    const url = URL.createObjectURL(firstFile);
    if (firstFile.name.endsWith('.pdf')) { loadPDF(url); } else { loadTXT(url); }
});

document.getElementById('send-btn').addEventListener('click', async () => {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    const mode = document.getElementById('mode').value;
    if (!query) return;
    addMessage(query, true); input.value = '';
    const formData = new FormData();
    formData.append('query', query); formData.append('mode', mode);
    const endpoint = mode === 'summary' ? '/summary' : '/chat';
    const response = await fetch(endpoint, { method: 'POST', body: formData });
    const result = await response.json();
    addMessage(result.answer, false, result.sources || []);
});
