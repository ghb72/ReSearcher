document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    const API_BASE_URL = 'http://localhost:5000';
    let currentPaperInfo = null;
    let selectedSourceIndex = 0;
    let searchTimeout = null;

    // Elementos del DOM
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const keywordsSearchForm = document.getElementById('keywordsSearchForm');
    const keywordsInput = document.getElementById('keywordsInput');
    const resultsDiv = document.getElementById('results');
    const pdfViewer = document.getElementById('pdfViewer');
    const pdfFrame = document.getElementById('pdfFrame');
    const closePdfBtn = document.getElementById('closePdfBtn');
    const findRelatedBtn = document.getElementById('findRelatedBtn');
    const relatedArticles = document.getElementById('relatedArticles');
    const relatedResults = document.getElementById('relatedResults');

    // Manejo del formulario de búsqueda de artículos
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (!query) {
            return;
        }
        
        // Mostrar mensaje de búsqueda inicial
        resultsDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Buscando información del artículo...</div>';
        closePDF(); // Cierra cualquier visor abierto antes de nueva búsqueda
        relatedArticles.style.display = 'none';
        currentPaperInfo = null; // Resetear información del paper actual
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/info`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentPaperInfo = data.info;
                mostrarFuentesArticulo(data.info);
                
                // Actualizar la UI cuando el enlace de descarga esté disponible
                if (data.info.download_link) {
                    const downloadBtn = document.getElementById('downloadBtn');
                    if (downloadBtn) {
                        downloadBtn.disabled = false;
                    }
                }
            } else {
                resultsDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle me-2"></i>Error: ' + (data.error || 'No se encontró información del artículo') + '</div>';
            }
        } catch (error) {
            resultsDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle me-2"></i>Error: ' + error.message + '</div>';
        }
    });

    // Búsqueda de artículos por palabras clave
    keywordsSearchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = keywordsInput.value.trim();
        if (!query) return;
        
        // Mostrar mensaje de búsqueda inicial
        resultsDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Buscando artículos que coincidan con las palabras clave...</div>';
        closePDF(); // Cierra cualquier visor abierto antes de nueva búsqueda
        relatedArticles.style.display = 'none';
        
        // Limpiar cualquier timeout previo
        if (searchTimeout) {
            clearTimeout(searchTimeout);
            searchTimeout = null;
        }
        
        // Simular actualizaciones de estado para mejorar la experiencia de usuario
        searchTimeout = setTimeout(() => {
            resultsDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Consultando múltiples fuentes académicas en paralelo...</div>';
        }, 1500);
        
        try {
            // Realizar la búsqueda por palabras clave
            const response = await fetch(`${API_BASE_URL}/api/search_keywords`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: query,
                    max_results: 15
                })
            });
            
            // Limpiar timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
                searchTimeout = null;
            }
            
            const data = await response.json();
            
            if (!data.success) {
                resultsDiv.innerHTML = `
                    <div class='alert alert-danger'>
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>Error</h5>
                        <p>${data.error || 'No se encontraron artículos que coincidan con la búsqueda'}</p>
                    </div>`;
                return;
            }
            
            // Mostrar los resultados de la búsqueda
            mostrarResultadosBusquedaPorPalabras(data.results);
            
        } catch (error) {
            // Limpiar timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
                searchTimeout = null;
            }
            
            resultsDiv.innerHTML = `
                <div class='alert alert-danger'>
                    <h5><i class="fas fa-exclamation-triangle me-2"></i>Error de conexión</h5>
                    <p>${error.message}</p>
                    <p>Compruebe que el servidor backend está en funcionamiento.</p>
                </div>`;
        }
    });

    // Mostrar las fuentes disponibles del artículo
    function mostrarFuentesArticulo(info) {
        if (!info || !info.sources || info.sources.length === 0) {
            resultsDiv.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-circle me-2"></i>No se encontró información del artículo.</div>';
            return;
        }
        
        // Crear los tabs para las diferentes fuentes
        let tabsHTML = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-database me-2"></i>Fuentes de Información</h5>
                </div>
                <div class="card-body">
                    <p class="card-text">Se encontró información en ${info.sources.length} fuente(s). Seleccione una fuente para ver más detalles:</p>
                    
                    <ul class="nav nav-tabs" id="sourceTabs" role="tablist">
        `;
        
        info.sources.forEach((source, index) => {
            const sourceId = `source-${index}`;
            const sourceIcon = source.source === "Crossref" ? "fas fa-book" : "fas fa-graduation-cap";
            
            tabsHTML += `
                <li class="nav-item" role="presentation">
                    <button class="nav-link ${index === selectedSourceIndex ? 'active' : ''}" 
                            id="${sourceId}-tab" 
                            data-bs-toggle="tab" 
                            data-bs-target="#${sourceId}" 
                            type="button" 
                            role="tab" 
                            aria-controls="${sourceId}" 
                            aria-selected="${index === selectedSourceIndex ? 'true' : 'false'}"
                            onclick="cambiarFuente(${index})">
                        <i class="${sourceIcon} me-1"></i> ${source.source}
                    </button>
                </li>
            `;
        });
        
        tabsHTML += `
                    </ul>
                </div>
            </div>
        `;
        
        // Mostrar la información del artículo según la fuente seleccionada
        resultsDiv.innerHTML = tabsHTML + '<div id="sourceContent"></div>';
        
        // Mostrar el contenido de la fuente seleccionada
        mostrarInformacionArticulo(info.sources[selectedSourceIndex]);
    }

    // Función para cambiar entre fuentes
    window.cambiarFuente = function(index) {
        selectedSourceIndex = index;
        
        // Actualizar la clase active en las pestañas
        const tabs = document.querySelectorAll('#sourceTabs .nav-link');
        tabs.forEach((tab, idx) => {
            if (idx === index) {
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');
            } else {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            }
        });
        
        // Mostrar la información de la fuente seleccionada
        mostrarInformacionArticulo(currentPaperInfo.sources[index]);
    };

    // Mostrar información del artículo
    function mostrarInformacionArticulo(info) {
        if (!info) {
            document.getElementById('sourceContent').innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-circle me-2"></i>No se encontró información del artículo.</div>';
            return;
        }
        
        // Crear HTML para mostrar información del artículo
        const title = info.title || 'Sin título';
        
        // Manejar autores, asegurando que sea un array antes de unirlo
        let authors = 'Autores desconocidos';
        if (info.authors) {
            if (Array.isArray(info.authors)) {
                authors = info.authors.join(', ');
            } else if (typeof info.authors === 'string') {
                authors = info.authors;
            }
        }
        
        const year = info.year || '';
        const journal = info.jurnal || '';
        const abstract = info.abstract || 'No hay resumen disponible';
        const doi = info.doi || '';
        const cites = info.cites_num ? `<span class="badge bg-secondary">${info.cites_num} citas</span>` : '';
        const source = info.source || '';
        const sourceIcon = source === "Crossref" ? "fas fa-book" : "fas fa-graduation-cap";
        
        const infoHTML = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-file-alt me-2"></i>Información del Artículo</h5>
                    <div>
                        <span class="badge bg-info me-2"><i class="${sourceIcon} me-1"></i> Fuente: ${source}</span>
                        <span class="badge bg-light text-dark">DOI: ${doi}</span>
                    </div>
                </div>
                <div class="card-body">
                    <h4 class="card-title">${title}</h4>
                    <h6 class="card-subtitle mb-3 text-muted">${authors}</h6>
                    
                    <div class="d-flex mb-3 flex-wrap">
                        ${journal ? `<span class="badge bg-secondary me-2">${journal}</span>` : ''}
                        ${year ? `<span class="badge bg-info text-dark me-2">${year}</span>` : ''}
                        ${cites}
                    </div>
                    
                    <div class="card mb-3">
                        <div class="card-header">Resumen</div>
                        <div class="card-body">
                            <p class="card-text">${abstract}</p>
                        </div>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <button id="downloadBtn" class="btn btn-success" onclick="descargarArticulo('${doi}')" disabled>
                            <i class="fas fa-download me-2"></i>Descargar PDF
                        </button>
                        
                        <button class="btn btn-outline-secondary" onclick="mostrarBibtex('${encodeURIComponent(info.bibtex || '')}', '${doi}', '${encodeURIComponent(title)}', '${encodeURIComponent(authors)}', '${year}', '${encodeURIComponent(journal)}')">
                            <i class="fas fa-quote-right me-2"></i>Citar
                        </button>
                    </div>
                </div>
            </div>
            
            <div id="bibtexContainer" class="card mb-4" style="display: none;">
                <div class="card-header bg-secondary text-white">
                    <h5 class="mb-0"><i class="fas fa-quote-right me-2"></i>Referencia BibTeX</h5>
                </div>
                <div class="card-body">
                    <pre id="bibtexContent" class="bg-light p-3 rounded"></pre>
                    <button class="btn btn-sm btn-primary mt-2" onclick="copiarBibtex()">
                        <i class="fas fa-copy me-2"></i>Copiar al portapapeles
                    </button>
                </div>
            </div>
            
            <div id="downloadStatus"></div>
        `;
        
        document.getElementById('sourceContent').innerHTML = infoHTML;
    }

    // Función para mostrar el BibTeX
    window.mostrarBibtex = function(bibtexEncoded, doi, titleEncoded, authorsEncoded, year, journalEncoded) {
        const title = decodeURIComponent(titleEncoded);
        const authors = decodeURIComponent(authorsEncoded);
        const journal = decodeURIComponent(journalEncoded);
        
        const bibtex = decodeURIComponent(bibtexEncoded) || 
            `@article{${doi.replace('/', '_')},
    title = {${title}},
    author = {${authors}},
    journal = {${journal || 'Unknown'}},
    year = {${year || 'Unknown'}},
    doi = {${doi}}
}`;
        
        const bibtexContainer = document.getElementById('bibtexContainer');
        const bibtexContent = document.getElementById('bibtexContent');
        
        bibtexContent.textContent = bibtex;
        bibtexContainer.style.display = 'block';
        bibtexContainer.scrollIntoView({ behavior: 'smooth' });
    };

    // Función para copiar BibTeX al portapapeles
    window.copiarBibtex = function() {
        const bibtexContent = document.getElementById('bibtexContent');
        const textArea = document.createElement('textarea');
        textArea.value = bibtexContent.textContent;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        // Mostrar mensaje de confirmación
        const btn = document.querySelector('#bibtexContainer .btn-primary');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check me-2"></i>¡Copiado!';
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    };

    // Función para descargar el artículo
    window.descargarArticulo = async function(doi) {
        const downloadBtn = document.getElementById('downloadBtn');
        const downloadStatus = document.getElementById('downloadStatus');
        
        if (!currentPaperInfo || !currentPaperInfo.download_link) {
            downloadStatus.innerHTML = '<div class="alert alert-warning">No hay enlace de descarga disponible todavía. Por favor, espere unos momentos...</div>';
            return;
        }
        
        // Deshabilitar el botón de descarga
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Descargando...';
        
        // Mostrar mensaje de descarga
        downloadStatus.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Descargando PDF, esto puede tardar unos momentos...</div>';
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    doi: doi,
                    download_link: currentPaperInfo.download_link
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Descargar PDF';
                mostrarPDF(data.pdf_url, doi, currentPaperInfo.sources[selectedSourceIndex].title);
            } else {
                downloadStatus.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle me-2"></i>Error al descargar el PDF: ' + (data.error || 'Error desconocido') + '</div>';
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Reintentar descarga';
            }
        } catch (error) {
            downloadStatus.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-circle me-2"></i>Error al descargar el PDF: ' + error.message + '</div>';
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Reintentar descarga';
        }
        
        // Simular actualizaciones de estado para mejorar la experiencia de usuario
        searchTimeout = setTimeout(() => {
            downloadStatus.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Consultando repositorios académicos...</div>';
            
            searchTimeout = setTimeout(() => {
                downloadStatus.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Procesando archivo PDF...</div>';
            }, 3000);
        }, 2000);
        
        // Realizar la solicitud de descarga
        fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: doi })
        })
        .then(response => response.json())
        .then(data => {
            // Limpiar timeouts
            if (searchTimeout) {
                clearTimeout(searchTimeout);
                searchTimeout = null;
            }
            
            if (!data.success) {
                let errorMsg = data.error;
                if (errorMsg.includes("No se pudo descargar el PDF")) {
                    errorMsg = "No se pudo descargar el PDF del artículo. Esto puede deberse a restricciones de acceso o problemas con los servidores de descarga. Por favor, intente más tarde o con otro DOI.";
                }
                downloadStatus.innerHTML = `
                    <div class='alert alert-danger'>
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>Error</h5>
                        <p>${errorMsg}</p>
                    </div>`;
                    
                // Restaurar botón de descarga
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Reintentar Descarga';
                return;
            }
            
            // Mostrar mensaje de éxito
            downloadStatus.innerHTML = '<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>¡PDF descargado con éxito!</div>';
            
            // Mostrar el PDF
            if (data.results && data.results.length > 0) {
                const result = data.results[0];
                mostrarPDF(result.pdf_url, result.doi, encodeURIComponent(result.title));
            }
        })
        .catch(error => {
            // Limpiar timeouts
            if (searchTimeout) {
                clearTimeout(searchTimeout);
                searchTimeout = null;
            }
            
            downloadStatus.innerHTML = `
                <div class='alert alert-danger'>
                    <h5><i class="fas fa-exclamation-triangle me-2"></i>Error de conexión</h5>
                    <p>${error.message}</p>
                    <p>Compruebe que el servidor backend está en funcionamiento.</p>
                </div>`;
                
            // Restaurar botón de descarga
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Reintentar Descarga';
        });
    };

    // Mostrar resultados de búsqueda
    function mostrarResultados(results) {
        if (!results || !results.length) {
            resultsDiv.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-circle me-2"></i>No se encontraron artículos.</div>';
            return;
        }
        
        const resultItems = results.map((r, i) => {
            const title = r.title || 'Sin título';
            
            // Manejar autores, asegurando que sea un array antes de unirlo
            let authors = 'Autores desconocidos';
            if (r.authors) {
                if (Array.isArray(r.authors)) {
                    authors = r.authors.join(', ');
                } else if (typeof r.authors === 'string') {
                    authors = r.authors;
                }
            }
            
            const year = r.year || '';
            const jurnal = r.jurnal ? `<span class="badge bg-secondary">${r.jurnal}</span> ` : '';
            
            return `<div class="card mb-3">
                <div class="card-body" style="cursor:pointer;" onclick="mostrarPDF('${r.pdf_url || ''}', '${r.doi}', '${encodeURIComponent(title)}')">
                    <h5 class="card-title">${title}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">${authors}</h6>
                    <p class="card-text">
                        ${jurnal}
                        ${year ? `<span class="badge bg-info text-dark">${year}</span>` : ''}
                        <span class="badge bg-success">PDF disponible</span>
                    </p>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-primary"><i class="fas fa-file-pdf me-2"></i>Ver PDF</button>
                        <small class="text-muted ms-2">DOI: ${r.doi}</small>
                    </div>
                </div>
            </div>`;
        }).join('');
        
        resultsDiv.innerHTML = resultItems;
    }

    // Mostrar PDF en el visor
    window.mostrarPDF = function(pdf_url, doi, title) {
        if (pdf_url && pdf_url !== 'null') {
            resultsDiv.scrollIntoView({ behavior: 'smooth' });
            resultsDiv.innerHTML += '<div class="alert alert-info mt-3 mb-3"><i class="fas fa-spinner fa-spin me-2"></i>Cargando PDF en el visor...</div>';
            
            pdfFrame.src = `${API_BASE_URL}${pdf_url}`;
            pdfViewer.style.display = 'block';
            currentDOI = doi;
            currentPaperTitle = decodeURIComponent(title);
            
            // Hacer scroll hacia el visor cuando se cargue el PDF
            pdfFrame.onload = function() {
                // Quitar el mensaje de carga
                const loadingAlert = document.querySelector('.alert.alert-info.mt-3');
                if (loadingAlert) {
                    loadingAlert.remove();
                }
                // Hacer scroll al visor
                pdfViewer.scrollIntoView({ behavior: 'smooth' });
            };
            
            // Manejar errores de carga del PDF
            pdfFrame.onerror = function() {
                const loadingAlert = document.querySelector('.alert.alert-info.mt-3');
                if (loadingAlert) {
                    loadingAlert.innerHTML = 
                        '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Error al cargar el PDF. Intente de nuevo.</div>';
                }
            };
        } else {
            pdfViewer.style.display = 'none';
            alert('No hay PDF disponible para este artículo.');
        }
    }

    // Cerrar PDF y programar eliminación
    closePdfBtn.addEventListener('click', closePDF);

    async function closePDF() {
        pdfFrame.src = '';
        pdfViewer.style.display = 'none';
        
        if (currentDOI) {
            try {
                await fetch(`${API_BASE_URL}/api/close_pdf`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ doi: currentDOI })
                });
            } catch (error) {
                console.error('Error al notificar cierre de PDF:', error);
            }
            
            currentDOI = null;
            currentPaperTitle = null;
        }
    }

    // Búsqueda de artículos relacionados
    findRelatedBtn.addEventListener('click', async () => {
        if (!currentDOI) {
            alert('No hay un artículo seleccionado');
            return;
        }
        
        relatedResults.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Buscando artículos relacionados...</div>';
        relatedArticles.style.display = 'block';
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/find_related`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    paper_id: currentDOI,
                    context: currentPaperTitle || '',
                    model: 'tfidf'
                })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                relatedResults.innerHTML = `
                    <div class="alert alert-danger">
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>Error</h5>
                        <p>${data.error || 'Error al buscar artículos relacionados'}</p>
                    </div>`;
                return;
            }
            
            mostrarArticulosRelacionados(data.results);
        } catch (error) {
            relatedResults.innerHTML = `
                <div class="alert alert-danger">
                    <h5><i class="fas fa-exclamation-triangle me-2"></i>Error de conexión</h5>
                    <p>${error.message}</p>
                </div>`;
        }
        
        // Hacer scroll hacia los resultados relacionados
        relatedArticles.scrollIntoView({ behavior: 'smooth' });
    });

    // Mostrar artículos relacionados
    function mostrarArticulosRelacionados(results) {
        if (!results || !results.length) {
            relatedResults.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-circle me-2"></i>No se encontraron artículos relacionados.</div>';
            return;
        }
        
        const resultItems = results.map((r, i) => {
            const title = r.title || 'Sin título';
            
            // Manejar autores, asegurando que sea un array antes de unirlo
            let authors = 'Autores desconocidos';
            if (r.authors) {
                if (Array.isArray(r.authors)) {
                    authors = r.authors.join(', ');
                } else if (typeof r.authors === 'string') {
                    authors = r.authors;
                }
            }
            
            const year = r.year || '';
            const similarity = r.similarity_score ? Math.round(r.similarity_score * 100) : 0;
            
            return `<div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title">${title}</h5>
                        <span class="badge bg-success">${similarity}% similar</span>
                    </div>
                    <h6 class="card-subtitle mb-2 text-muted">${authors}</h6>
                    <p class="card-text">
                        ${year ? `<span class="badge bg-info text-dark">${year}</span>` : ''}
                        ${r.cites_num ? `<span class="badge bg-secondary">${r.cites_num} citas</span>` : ''}
                    </p>
                    ${r.abstract ? `<p class="card-text small">${r.abstract.substring(0, 200)}...</p>` : ''}
                    ${r.doi ? `<a href="#" class="btn btn-sm btn-primary" onclick="buscarPorDOI('${r.doi}'); return false;"><i class="fas fa-search me-1"></i>Ver artículo</a>` : ''}
                </div>
            </div>`;
        }).join('');
        
        relatedResults.innerHTML = resultItems;
    }

    // Buscar por DOI (para artículos relacionados)
    window.buscarPorDOI = function(doi) {
        searchInput.value = `https://doi.org/${doi}`;
        searchForm.dispatchEvent(new Event('submit'));
    }

    // Mostrar resultados de búsqueda por palabras clave
    function mostrarResultadosBusquedaPorPalabras(results) {
        if (!results || !results.length) {
            resultsDiv.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-circle me-2"></i>No se encontraron artículos que coincidan con la búsqueda.</div>';
            return;
        }
        
        // Crear el encabezado de resultados
        let resultsHTML = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-search me-2"></i>Resultados de la Búsqueda (${results.length})</h5>
                </div>
                <div class="card-body">
                    <div class="list-group">
        `;
        
        // Crear los elementos de resultados
        results.forEach((paper, index) => {
            const title = paper.title || 'Sin título';
            
            // Manejar autores
            let authors = 'Autores desconocidos';
            if (paper.authors) {
                if (Array.isArray(paper.authors)) {
                    authors = paper.authors.join(', ');
                } else if (typeof paper.authors === 'string') {
                    authors = paper.authors;
                }
            }
            
            // Extraer información adicional
            const year = paper.year || '';
            const journal = paper.jurnal || '';
            const abstract = paper.abstract || 'No hay resumen disponible';
            const doi = paper.doi || '';
            const source = paper.source || '';
            const sourceIcon = source === "Crossref" ? "fas fa-book" : "fas fa-graduation-cap";
            const cites = paper.cites_num ? `<span class="badge bg-secondary">${paper.cites_num} citas</span>` : '';
            
            resultsHTML += `
                <div class="list-group-item list-group-item-action">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="mb-1">${title}</h5>
                        <span class="badge bg-info text-dark"><i class="${sourceIcon} me-1"></i> ${source}</span>
                    </div>
                    <p class="mb-1 text-muted">${authors}</p>
                    <div class="d-flex mb-2 flex-wrap">
                        ${journal ? `<span class="badge bg-secondary me-2">${journal}</span>` : ''}
                        ${year ? `<span class="badge bg-info text-dark me-2">${year}</span>` : ''}
                        ${cites}
                    </div>
                    <div class="mb-2 small">
                        ${abstract.length > 300 ? abstract.substring(0, 300) + '...' : abstract}
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            ${doi ? `<small class="text-muted">DOI: ${doi}</small>` : ''}
                        </div>
                        <div>
                            ${doi ? `<button class="btn btn-sm btn-primary me-2" onclick="buscarPorDOI('${doi}')">
                                <i class="fas fa-info-circle me-1"></i>Ver detalles
                            </button>` : ''}
                            ${paper.url ? `<a href="${paper.url}" target="_blank" class="btn btn-sm btn-outline-secondary">
                                <i class="fas fa-external-link-alt me-1"></i>Ver fuente
                            </a>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        resultsHTML += `
                    </div>
                </div>
            </div>
        `;
        
        resultsDiv.innerHTML = resultsHTML;
        
        // Hacer scroll hacia los resultados
        resultsDiv.scrollIntoView({ behavior: 'smooth' });
    }
});
