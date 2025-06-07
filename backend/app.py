from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
import threading
import time
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'PyPaperBot'))
from __main__ import start as pypaperbot_start

app = Flask(__name__)
CORS(app)

TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp_pdfs')
os.makedirs(TEMP_DIR, exist_ok=True)

DOI_REGEX = r"10.\d{4,9}/[-._;()/:A-Z0-9]+"

pdf_delete_timers = {}

def extract_doi(query):
    print(f"[extract_doi] Extrayendo DOI de la consulta: {query}")
    match = re.search(DOI_REGEX, query, re.I)
    doi = match.group(0) if match else None
    print(f"[extract_doi] DOI extraído: {doi}")
    return doi

def download_pdf_with_pypaperbot(doi):
    print(f"[download_pdf_with_pypaperbot] Iniciando descarga para DOI: {doi}")
    pypaperbot_start(
        query=None,
        scholar_results=1,
        scholar_pages=1,
        dwn_dir=TEMP_DIR,
        proxy=None,
        min_date=None,
        num_limit=None,
        num_limit_type=None,
        filter_jurnal_file=None,
        restrict=1,
        DOIs=[doi],
        SciHub_URL=None,
        chrome_version=None,
        cites=None,
        use_doi_as_filename=True,
        SciDB_URL=None,
        skip_words=None
    )
    print(f"[download_pdf_with_pypaperbot] Descarga finalizada para DOI: {doi}")

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    print(f"[search] Recibida búsqueda: {query}")
    doi = extract_doi(query)
    if not doi:
        print("[search] No se encontró un DOI válido.")
        return jsonify({'success': False, 'error': 'No se encontró un DOI válido en la búsqueda.'})
    pdf_filename = f"{doi}.pdf"
    pdf_path = os.path.join(TEMP_DIR, pdf_filename)
    print(f"[search] Ruta esperada del PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        try:
            print(f"[search] El PDF no existe, intentando descargar...")
            download_pdf_with_pypaperbot(doi)
        except Exception as e:
            print(f"[search] Error al intentar descargar el PDF: {e}")
            return jsonify({'success': False, 'error': f'Error al intentar descargar el PDF: {str(e)}'})
    else:
        print(f"[search] El PDF ya existe en el sistema.")
    pdf_url = f"/pdf/{pdf_filename}" if os.path.exists(pdf_path) else None
    result = {
        'title': doi,
        'authors': [],
        'year': '',
        'doi': doi,
        'pdf_url': pdf_url,
        'url': ''
    }
    print(f"[search] Resultado enviado al frontend: {result}")
    return jsonify({'success': True, 'results': [result]})

@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(TEMP_DIR, filename)

@app.route('/api/close_pdf', methods=['POST'])
def close_pdf():
    data = request.json
    doi = data.get('doi')
    if not doi:
        return jsonify({'success': False, 'error': 'No DOI provided'})
    pdf_filename = f"{doi}.pdf"
    pdf_path = os.path.join(TEMP_DIR, pdf_filename)
    if doi in pdf_delete_timers:
        pdf_delete_timers[doi].cancel()
    def delete_pdf():
        time.sleep(300)
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass
        pdf_delete_timers.pop(doi, None)
    t = threading.Thread(target=delete_pdf)
    t.daemon = True
    pdf_delete_timers[doi] = t
    t.start()
    return jsonify({'success': True, 'message': 'El PDF se eliminará en 5 minutos.'})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 