// Manejo del formulario de búsqueda de artículos
const searchForm = document.getElementById('searchForm');
const searchInput = document.getElementById('searchInput');
const resultsDiv = document.getElementById('results');
const pdfViewer = document.getElementById('pdfViewer');
const pdfFrame = document.getElementById('pdfFrame');

let currentDOI = null;

searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (!query) return;
    resultsDiv.innerHTML = 'Buscando...';
    closePDF(); // Cierra cualquier visor abierto antes de nueva búsqueda
    const response = await fetch('http://localhost:5000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });
    const data = await response.json();
    if (!data.success) {
        resultsDiv.innerHTML = `<div class='alert alert-danger'>${data.error}</div>`;
        return;
    }
    mostrarResultados(data.results);
});

function mostrarResultados(results) {
    if (!results.length) {
        resultsDiv.innerHTML = '<div class="alert alert-warning">No se encontraron artículos.</div>';
        return;
    }
    resultsDiv.innerHTML = '<ul class="list-group">' +
        results.map((r, i) =>
            `<li class="list-group-item list-group-item-action" style="cursor:pointer;" onclick="mostrarPDF('${r.pdf_url || ''}', '${r.doi}')">
                <strong>${r.title}</strong><br>
                <span>${r.authors.join(', ')}</span><br>
                <span>${r.year || ''}</span>
            </li>`
        ).join('') + '</ul>';
}

window.mostrarPDF = function(pdf_url, doi) {
    if (pdf_url && pdf_url !== 'null') {
        pdfFrame.src = pdf_url;
        pdfViewer.style.display = 'block';
        currentDOI = doi;
        if (!document.getElementById('closePdfBtn')) {
            const btn = document.createElement('button');
            btn.id = 'closePdfBtn';
            btn.className = 'btn btn-danger mt-2';
            btn.textContent = 'Cerrar visor PDF';
            btn.onclick = closePDF;
            pdfViewer.appendChild(btn);
        }
    } else {
        pdfViewer.style.display = 'none';
        alert('No hay PDF disponible para este artículo.');
    }
}

async function closePDF() {
    pdfFrame.src = '';
    pdfViewer.style.display = 'none';
    if (currentDOI) {
        await fetch('http://localhost:5000/api/close_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ doi: currentDOI })
        });
        currentDOI = null;
    }
    const btn = document.getElementById('closePdfBtn');
    if (btn) btn.remove();
}

// Manejo del formulario de análisis de documentos
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const summaryModel = document.getElementById('summaryModel');

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', summaryModel.value);
    const response = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();
    mostrarResumen(data);
});

function mostrarResumen(data) {
    document.getElementById('objective').textContent = data.objective || '';
    document.getElementById('methodology').textContent = data.methodology || '';
    document.getElementById('analysis').textContent = data.analysis || '';
    document.getElementById('conclusions').textContent = data.conclusions || '';
}

// Manejo de búsqueda de artículos relacionados
const contextInput = document.getElementById('contextInput');
const relatedModel = document.getElementById('relatedModel');
const relatedPapers = document.getElementById('relatedPapers');

contextInput.addEventListener('change', buscarRelacionados);
relatedModel.addEventListener('change', buscarRelacionados);

async function buscarRelacionados() {
    const context = contextInput.value;
    const model = relatedModel.value;
    if (!context) return;
    const response = await fetch('http://localhost:5000/api/related', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context, model })
    });
    const data = await response.json();
    mostrarRelacionados(data);
}

function mostrarRelacionados(data) {
    relatedPapers.innerHTML = '';
    if (data && data.papers) {
        data.papers.forEach(paper => {
            const div = document.createElement('div');
            div.className = 'mb-2';
            div.textContent = paper.title || JSON.stringify(paper);
            relatedPapers.appendChild(div);
        });
    } else {
        relatedPapers.textContent = 'No se encontraron artículos relacionados.';
    }
} 