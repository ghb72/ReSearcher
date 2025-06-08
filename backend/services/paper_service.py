import os
import re
from urllib.parse import urlparse
import tempfile
import shutil
import requests
from .Crossref import getPapersInfoFromDOIs
import time
import random
from .Scholar import ScholarPapersInfo
from .ScholarExtractor import ScholarExtractor

def extract_doi_from_url(url):
    """Extrae el DOI de una URL o devuelve el DOI directo si se proporcionó uno"""
    if not url:
        return None, "No se proporcionó una consulta válida"
    
    # Comprueba si es una URL de DOI
    if url.startswith("https://doi.org/") or url.startswith("http://doi.org/"):
        doi = url.replace("https://doi.org/", "").replace("http://doi.org/", "")
        return doi, None
    
    # Comprueba si es directamente un DOI (formato 10.XXXX/XXXXX)
    doi_pattern = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'
    if re.match(doi_pattern, url, re.IGNORECASE):
        return url, None
    
    # Si no es un DOI válido, devolver error
    return None, "No se pudo identificar un DOI válido en la consulta"

def format_paper_info(paper_info, doi, source):
    """
    Formatea la información del paper en un formato estándar
    
    Args:
        paper_info: Objeto con información del paper
        doi: DOI del artículo
        source: Fuente de la información (Crossref o Scholar)
    
    Returns:
        dict: Información formateada del paper
    """
    # Manejo de autores para asegurar que siempre sea un array
    authors = getattr(paper_info, 'authors', ["Autores desconocidos"])
    if isinstance(authors, str):
        # Si es un string, convertirlo a lista dividiendo por la coma
        authors = [author.strip() for author in authors.split('and') if author.strip()]
        if not authors:  # Si después de dividir no hay autores válidos
            authors = [a.strip() for a in paper_info.authors.split(',') if a.strip()]
        if not authors:  # Si aún no hay autores válidos
            authors = [paper_info.authors]

    return {
        "doi": doi,
        "title": paper_info.title if hasattr(paper_info, 'title') and paper_info.title else "Sin título",
        "authors": authors,
        "year": paper_info.year if hasattr(paper_info, 'year') else None,
        "jurnal": paper_info.jurnal if hasattr(paper_info, 'jurnal') else None,
        "abstract": getattr(paper_info, 'abstract', ''),
        "url": getattr(paper_info, 'url', f"https://doi.org/{doi}"),
        "cites_num": getattr(paper_info, 'cites_num', None),
        "bibtex": getattr(paper_info, 'bibtex', ''),
        "source": source
    }

def get_paper_info(query):
    """
    Busca información de un artículo basado en su DOI o URL sin descargarlo,
    consultando tanto Crossref como Google Scholar
    
    Args:
        query: DOI o URL completa del artículo
        
    Returns:
        tuple: (resultados_dict, error_mensaje)
    """
    # Extraer DOI de la URL o query
    doi, error = extract_doi_from_url(query)
    
    if error or not doi:
        return None, error or "DOI no válido o no encontrado"
    
    try:
        results = []
        errors = []
        
        # 1. Obtener información de Crossref
        try:
            crossref_info = getPapersInfoFromDOIs(doi, restrict=None)
            if crossref_info and crossref_info.DOI:
                results.append(format_paper_info(crossref_info, doi, "Crossref"))
        except Exception as e:
            errors.append(f"Error en Crossref: {str(e)}")
        
        # 2. Obtener información de Google Scholar
        try:
            # Buscar en Google Scholar usando el DOI
            scholar_papers = ScholarPapersInfo(
                query=f'"{doi}"', 
                scholar_pages=range(1, 2),  # Solo la primera página
                restrict=None, 
                scholar_results=1  # Solo el primer resultado
            )
            
            if scholar_papers and len(scholar_papers) > 0:
                scholar_info = scholar_papers[0]
                if hasattr(scholar_info, 'DOI') and scholar_info.DOI:
                    results.append(format_paper_info(scholar_info, doi, "Google Scholar"))
        except Exception as e:
            errors.append(f"Error en Google Scholar: {str(e)}")
        
        # Si no se encontró información en ninguna fuente
        if not results:
            error_msg = "No se encontró información para el DOI proporcionado"
            if errors:
                error_msg += ": " + "; ".join(errors)
            return None, error_msg
        
        # 3. Intentar obtener abstract y más información desde Google Scholar
        try:
            scholar_extractor = ScholarExtractor()
            for i in range(len(results)):
                # Intentar enriquecer con abstract y otros datos que puedan faltar
                results[i] = scholar_extractor.enrich_paper_info(results[i])
        except Exception as e:
            errors.append(f"Error al enriquecer información: {str(e)}")
            # No fallamos aquí, continuamos con la información que tengamos
        
        # Preparar la respuesta con los resultados de ambas fuentes
        print(results)
        return {
            "sources": results,
            "doi": doi
        }, None
        
    except Exception as e:
        return None, f"Error al procesar la solicitud: {str(e)}"

def download_from_scihub(doi, output_path):
    """
    Intenta descargar un artículo desde Sci-Hub
    
    Args:
        doi: DOI del artículo
        output_path: Ruta donde guardar el PDF
    
    Returns:
        bool: True si se descargó correctamente, False en caso contrario
    """
    # Lista de espejos de Sci-Hub a probar
    mirrors = [
        "https://sci-hub.ee",
        "https://sci-hub.se",
        "https://sci-hub.st",
        "https://sci-hub.ru",
        "https://sci-hub.cat",
        "https://sci-hub.wf",
        "https://sci-hub.ren",
        "https://sci-hub.mksa.top"
    ]
    
    # Aleatorizar el orden de los espejos para distribuir la carga
    random.shuffle(mirrors)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    print(f"Searching paper 1 of 1 with DOI {doi}")
    print("Searching for a sci-hub mirror")
    
    for mirror in mirrors:
        try:
            print(f"Trying with {mirror}...")
            url = f"{mirror}/{doi}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Buscar diferentes patrones de iframe o enlaces de descarga en la respuesta HTML
                patterns = [
                    r'<iframe[^>]*src="([^"]+)"[^>]*id="pdf"',  # Patrón estándar de iframe
                    r'<iframe[^>]*src="([^"]+\.pdf)"',  # Cualquier iframe con PDF
                    r'<a[^>]*href="([^"]+\.pdf)"[^>]*>',  # Enlaces directos a PDF
                    r'location.href\s*=\s*[\'"]([^\'"]+\.pdf)[\'"]',  # Redirecciones JavaScript
                ]
                
                pdf_link = None
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        pdf_link = match.group(1)
                        break
                
                if pdf_link:
                    # Normalizar la URL del PDF
                    if pdf_link.startswith('//'):
                        pdf_link = 'https:' + pdf_link
                    elif not pdf_link.startswith('http'):
                        # URL relativa
                        if pdf_link.startswith('/'):
                            pdf_link = f"{mirror}{pdf_link}"
                        else:
                            pdf_link = f"{mirror}/{pdf_link}"
                    
                    print(f"Using Sci-Hub mirror {mirror}")
                    print(f"Found PDF link: {pdf_link}")
                    
                    # Agregar un retraso para evitar detección
                    time.sleep(random.uniform(1, 3))
                    
                    # Descargar el PDF
                    pdf_response = requests.get(pdf_link, headers=headers, timeout=30, stream=True)
                    
                    # Verificar que la respuesta es un PDF o al menos contenido binario
                    content_type = pdf_response.headers.get('Content-Type', '')
                    if pdf_response.status_code == 200 and (
                        content_type.startswith('application/pdf') or 
                        content_type.startswith('application/octet-stream') or
                        content_type.startswith('binary/octet-stream')
                    ):
                        with open(output_path, 'wb') as f:
                            for chunk in pdf_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Verificar que el archivo es un PDF válido
                        if os.path.getsize(output_path) > 1000:  # Mínimo 1KB para ser un PDF válido
                            with open(output_path, 'rb') as f:
                                header = f.read(8)
                                if b'%PDF' in header:  # Comprobar firma de archivo PDF
                                    print(f"Download 1 of 1 -> {os.path.basename(output_path)}")
                                    return True
                                else:
                                    print("Archivo descargado no es un PDF válido")
                        else:
                            print("Archivo PDF descargado es demasiado pequeño")
        except Exception as e:
            print(f"Error with {mirror}: {str(e)}")
        
        # Agregar un retraso entre intentos para evitar detección
        time.sleep(random.uniform(2, 5))
    
    # Intentar con Annas-Archive como último recurso
    try:
        print("Using Sci-DB mirror https://annas-archive.se/scidb/")
        url = f"https://annas-archive.se/scidb/{doi}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Buscar enlace de descarga
            download_patterns = [
                r'href="(/scidb/[^"]+)".*?Download',
                r'href="(/dl/[^"]+)".*?Download',
                r'href="(/md5/[^"]+)".*?Download',
            ]
            
            for pattern in download_patterns:
                download_link_match = re.search(pattern, response.text)
                if download_link_match:
                    download_link = "https://annas-archive.se" + download_link_match.group(1)
                    print(f"Found download link: {download_link}")
                    
                    # Agregar un retraso para evitar detección
                    time.sleep(random.uniform(1, 3))
                    
                    pdf_response = requests.get(download_link, headers=headers, timeout=30, stream=True)
                    
                    if pdf_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            for chunk in pdf_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Verificar que el archivo es un PDF válido
                        if os.path.getsize(output_path) > 1000:
                            with open(output_path, 'rb') as f:
                                header = f.read(8)
                                if b'%PDF' in header:
                                    print(f"Download 1 of 1 -> {os.path.basename(output_path)}")
                                    return True
                    break
    except Exception as e:
        print(f"Error with Annas-Archive: {str(e)}")
    
    # Si todos los intentos fallan, intentar con API libre de Unpaywall
    try:
        print("Trying with Unpaywall API...")
        unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email=app@example.org"
        response = requests.get(unpaywall_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('is_oa') and data.get('best_oa_location') and data['best_oa_location'].get('url_for_pdf'):
                pdf_url = data['best_oa_location']['url_for_pdf']
                print(f"Found PDF at Unpaywall: {pdf_url}")
                
                pdf_response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
                if pdf_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in pdf_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    if os.path.getsize(output_path) > 1000:
                        with open(output_path, 'rb') as f:
                            header = f.read(8)
                            if b'%PDF' in header:
                                print(f"Download 1 of 1 -> {os.path.basename(output_path)}")
                                return True
    except Exception as e:
        print(f"Error with Unpaywall: {str(e)}")
    
    return False

def search_and_download_paper(query, output_dir):
    """
    Busca y descarga un artículo basado en su DOI o URL
    
    Args:
        query: DOI o URL completa del artículo
        output_dir: Directorio donde guardar el PDF descargado
    
    Returns:
        tuple: (resultado_diccionario, error_mensaje)
    """
    # Asegurarse de que el directorio existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraer DOI de la URL o query
    doi, error = extract_doi_from_url(query)
    
    if error or not doi:
        return None, error or "DOI no válido o no encontrado"
    
    # Crear un directorio temporal para la descarga
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Obtener información del paper
        paper_info, error = get_paper_info(query)
        
        if error or not paper_info:
            return None, error or "No se encontró información para el DOI proporcionado"
        
        # A esta altura, estamos seguros de que doi no es None
        # Preparar nombres de archivo
        pdf_filename = f"{doi.replace('/', '_')}.pdf"
        temp_pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Intentar descargar el PDF
        download_success = download_from_scihub(doi, temp_pdf_path)
        
        if not download_success or not os.path.exists(temp_pdf_path):
            return None, "No se pudo descargar el PDF del artículo"
        
        # Copiar el PDF a la carpeta de destino
        target_pdf_path = os.path.join(output_dir, pdf_filename)
        shutil.copy2(temp_pdf_path, target_pdf_path)
        
        # Tomar el primer resultado como referencia para la respuesta
        first_source = paper_info["sources"][0] if paper_info["sources"] else {}
        
        # Preparar la respuesta
        result = {
            "doi": doi,
            "title": first_source.get("title", "Sin título"),
            "authors": first_source.get("authors", ["Autores desconocidos"]),
            "year": first_source.get("year"),
            "jurnal": first_source.get("jurnal"),
            "abstract": first_source.get("abstract", ""),
            "pdf_url": f"/pdf/{pdf_filename}"
        }
        
        # Asegurar que authors sea siempre un array
        if not isinstance(result["authors"], list):
            if isinstance(result["authors"], str):
                # Intentar dividir por "and" primero, luego por comas
                authors = [author.strip() for author in result["authors"].split('and') if author.strip()]
                if not authors:
                    authors = [a.strip() for a in result["authors"].split(',') if a.strip()]
                if not authors:
                    authors = [result["authors"]]
                result["authors"] = authors
            else:
                result["authors"] = ["Autores desconocidos"]
        
        return result, None
        
    except Exception as e:
        return None, f"Error al procesar la solicitud: {str(e)}"
    
    finally:
        # Eliminar el directorio temporal
        shutil.rmtree(temp_dir, ignore_errors=True) 