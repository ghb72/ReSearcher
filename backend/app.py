from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
from pathlib import Path
import sys

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
    Obtiene información de un artículo basado en su DOI o URL sin descargarlo
    """
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'success': False, 'error': 'No se proporcionó una consulta'})
    
    try:
        paper_info, error = get_paper_info(query)
        
        if error or not paper_info:
            return jsonify({'success': False, 'error': error or 'No se pudo obtener información del artículo'})
        
        return jsonify({'success': True, 'info': paper_info})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/search', methods=['POST'])
def search():
    """
    Busca y descarga un artículo basado en su DOI o URL
    """
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'success': False, 'error': 'No se proporcionó una consulta'})
    
    try:
        result, error = search_and_download_paper(query, DOWNLOAD_DIR)
        
        if error or not result:
            return jsonify({'success': False, 'error': error or 'No se pudo descargar el artículo'})
        
        return jsonify({
            'success': True, 
            'results': [result]  # Mantenemos compatibilidad con el formato anterior
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