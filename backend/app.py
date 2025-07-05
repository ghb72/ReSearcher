from flask import Flask, request, jsonify, send_from_directory, copy_current_request_context
from flask_cors import CORS
import os
import time
from pathlib import Path
import sys
from threading import Thread

# Añadir la carpeta 'backend' al sys.path para permitir importaciones relativas
backend_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from services.paper_service import get_paper_info, search_and_download_paper, search_papers_by_keywords

app = Flask(__name__)
CORS(app)

# Directorio para almacenar PDFs
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

@app.route('/api/info', methods=['POST'])
def get_info():
    """
    Obtiene información de un artículo y busca un enlace de descarga de forma asíncrona
    """
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'success': False, 'error': 'No se proporcionó una consulta'})
    
    try:
        paper_info, error = get_paper_info(query)
        
        if error or not paper_info:
            return jsonify({'success': False, 'error': error or 'No se pudo obtener información del artículo'})

        # Crear una tarea en segundo plano para buscar el enlace de descarga
        @copy_current_request_context
        def find_download_link():
            try:
                from services.paper_service import download_from_scihub
                doi = paper_info['sources'][0]['doi'] if paper_info['sources'] else None
                
                if doi:
                    # Buscar enlace de descarga sin descargar el archivo
                    download_link = download_from_scihub(doi, None, get_link_only=True)
                    if download_link:
                        paper_info['download_link'] = download_link
                        # Aquí podrías emitir un evento WebSocket o usar Server-Sent Events
                        # para notificar al frontend que el enlace está disponible
            except Exception as e:
                print(f"Error finding download link: {str(e)}")

        # Iniciar la búsqueda del enlace en segundo plano
        thread = Thread(target=find_download_link)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'info': paper_info})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download', methods=['POST'])
def download_paper():
    """
    Descarga un artículo usando la información y enlace obtenidos previamente
    """
    data = request.get_json()
    doi = data.get('doi')
    download_link = data.get('download_link')
    
    if not doi or not download_link:
        return jsonify({'success': False, 'error': 'Se requiere DOI y enlace de descarga'})
    
    try:
        # Preparar nombre de archivo
        pdf_filename = f"{doi.replace('/', '_')}.pdf"
        pdf_path = os.path.join(DOWNLOAD_DIR, pdf_filename)
        
        from services.paper_service import download_paper_from_link
        success = download_paper_from_link(download_link, pdf_path)
        
        if not success:
            return jsonify({'success': False, 'error': 'No se pudo descargar el artículo'})
        
        return jsonify({
            'success': True,
            'pdf_url': f"/pdf/{pdf_filename}"
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    """Sirve archivos PDF desde el directorio de descargas"""
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.route('/api/close_pdf', methods=['POST'])
def close_pdf():
    """
    Recibe notificación de que se ha cerrado un visor de PDF
    Esta función podría usarse para programar la eliminación del archivo
    después de un cierto tiempo, o para limpiar archivos temporales
    """
    # No eliminamos el archivo inmediatamente para permitir
    # que el usuario pueda volver a abrirlo durante la sesión
    return jsonify({'success': True})

@app.route('/api/find_related', methods=['POST'])
def find_related():
    """
    Encuentra artículos relacionados con el artículo actual
    Esta es una función de prueba que devuelve datos de ejemplo
    """
    try:
        # En una implementación real, aquí buscaríamos artículos relacionados
        # basados en el contenido, citas, etc.
        example_related = [
            {
                "title": "Deep Learning: A Comprehensive Overview",
                "authors": ["Smith, John", "Johnson, Mary"],
                "year": "2021",
                "abstract": "This paper provides a comprehensive overview of deep learning techniques and their applications in various fields.",
                "doi": "10.1234/dl.2021.001",
                "cites_num": 145,
                "similarity_score": 0.85
            },
            {
                "title": "Neural Networks in Computer Vision: A Survey",
                "authors": ["Davis, Robert", "Wilson, Lisa"],
                "year": "2020",
                "abstract": "We survey the most recent advances in neural networks applied to computer vision tasks.",
                "doi": "10.1234/nn.2020.015",
                "cites_num": 78,
                "similarity_score": 0.72
            }
        ]
        
        return jsonify({
            'success': True,
            'results': example_related
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/search_keywords', methods=['POST'])
def search_keywords():
    """
    Busca papers por título o palabras clave utilizando solicitudes paralelas a Scholar y Crossref
    """
    data = request.get_json()
    query = data.get('query', '')
    max_results = data.get('max_results', 10)
    
    if not query:
        return jsonify({'success': False, 'error': 'No se proporcionó una consulta de búsqueda'})
    
    try:
        results, error = search_papers_by_keywords(query, max_results)
        
        if error or not results:
            return jsonify({'success': False, 'error': error or 'No se encontraron papers que coincidan con la búsqueda'})
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)