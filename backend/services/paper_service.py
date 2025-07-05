import os
import re
from urllib.parse import urlparse
import tempfile
import shutil
import requests
import cloudscraper
from .Crossref import getPapersInfoFromDOIs
import time
import random
from .Scholar import ScholarPapersInfo
from .ScholarExtractor import ScholarExtractor
import concurrent.futures
import threading
from bs4 import BeautifulSoup

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
        "abstract": paper_info.abstract if hasattr(paper_info, 'abstract') else None,
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
        if not results:
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

def download_from_scihub(doi, output_path=None, get_link_only=False):
    """
    Intenta encontrar un enlace de descarga desde Sci-Hub y opcionalmente descarga el archivo
    
    Args:
        doi: DOI del artículo
        output_path: Ruta donde guardar el PDF (None si solo se quiere el enlace)
        get_link_only: Si es True, solo devuelve el enlace sin descargar
    
    Returns:
        str o bool: URL de descarga si get_link_only=True, sino True/False según éxito de descarga
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
        "https://sci-hub.mksa.top",
        "https://sci-hub.mk"
    ]
    
    # Aleatorizar el orden de los espejos para distribuir la carga
    random.shuffle(mirrors)

    scrapper = cloudscraper.create_scraper()  # Usar cloudscraper para manejar captchas y bloqueos
    
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
    
    print(f"Searching paper with DOI {doi}")
    print("Searching for a sci-hub mirror")
    
    for mirror in mirrors:
        try:
            print(f"Trying with {mirror}...")
            url = f"{mirror}/{doi}"
            response = scrapper.get(url, timeout=10)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            # response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Buscar el enlace de descarga en la página
                soup = BeautifulSoup(response.text, 'html.parser')
                print('Souped', url)
                pdf_element = soup.find(id='pdf')
                if pdf_element and 'src' in pdf_element.attrs:
                    download_link = str(pdf_element['src'])
                    if download_link.startswith('//'):
                        download_link = 'https:' + download_link
                    elif not download_link.startswith('http'):
                        base_url = '/'.join(mirror.split('/')[:3])  # Obtener el esquema y dominio
                        download_link = base_url + download_link.lstrip('/')
                    if not download_link.startswith('http'):
                        download_link = mirror + download_link
                        
                    if get_link_only:
                        return download_link
                        
                    # Si se requiere descarga, intentar descargar
                    if output_path:
                        pdf_response = scrapper.get(download_link, headers={'Referer': url}, timeout=60)
                        pdf_response.raise_for_status()
                        if pdf_response.status_code == 200:
                            with open(output_path, 'wb') as f:
                                f.write(pdf_response.content)
                            return True
        except cloudscraper.exceptions.CloudflareException as e:
            print(f"Cloudflare challenge encountered: {e}")

        except requests.exceptions.RequestException as e:
            print(f"Error de red o de HTTP con el espejo {mirror}: {str(e)}")

        except Exception as e:
            print(f"Error with mirror {mirror}: {str(e)}")
        
        time.sleep(random.uniform(2, 5))
    
    # Si no se encontró en Sci-Hub, intentar con otras fuentes
    try:
        print("Using Annas-Archive...")
        url = f"https://annas-archive.org/scidb/{doi}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Extraer enlace de descarga
            soup = BeautifulSoup(response.text, 'html.parser')
            download_link = soup.find('a', class_='download-link')
            if download_link and 'href' in download_link.attrs:
                link_url = str(download_link['href'])
                if get_link_only:
                    return link_url
                    
                if output_path:
                    pdf_response = requests.get(link_url, headers=headers, timeout=30)
                    if pdf_response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(pdf_response.content)
                        return True
                        
    except Exception as e:
        print(f"Error with Annas-Archive: {str(e)}")
    
    return None if get_link_only else False

def download_paper_from_link(download_link, output_path):
    """
    Descarga un paper desde un enlace previamente obtenido
    
    Args:
        download_link: URL de descarga del PDF
        output_path: Ruta donde guardar el archivo
        
    Returns:
        bool: True si se descargó correctamente, False en caso contrario
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(download_link, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error downloading paper: {str(e)}")
        return False
    
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

def search_papers_by_keywords(query, max_results=10):
    """
    Busca papers por título o palabras clave utilizando solicitudes paralelas a Scholar y Crossref
    
    Args:
        query: Texto de búsqueda (título o palabras clave)
        max_results: Número máximo de resultados a devolver
    
    Returns:
        tuple: (resultados_lista, error_mensaje)
    """
    if not query or len(query.strip()) < 3:
        return None, "La consulta de búsqueda debe tener al menos 3 caracteres"
    
    # Resultados combinados de ambas fuentes
    combined_results = []
    errors = []
    
    # Semáforo para proteger el acceso a los resultados combinados
    results_lock = threading.Lock()
    
    def search_scholar():
        """Función para buscar en Google Scholar en paralelo"""
        try:
            # Buscar en Google Scholar
            scholar_papers = ScholarPapersInfo(
                query=query, 
                scholar_pages=range(1, 2),  # Solo primera página
                restrict=None, 
                scholar_results=max_results
            )
            
            if scholar_papers:
                # Enriquecer con información adicional
                scholar_extractor = ScholarExtractor()
                enriched_papers = []
                
                for paper in scholar_papers:
                    if hasattr(paper, 'title') and paper.title:
                        # Formatear la información del paper
                        paper_info = {
                            "title": paper.title,
                            "authors": getattr(paper, 'authors', []),
                            "year": getattr(paper, 'year', None),
                            "abstract": getattr(paper, 'abstract', ''),
                            "doi": getattr(paper, 'DOI', None),
                            "url": getattr(paper, 'url', None),
                            "cites_num": getattr(paper, 'cites_num', None),
                            "source": "Google Scholar"
                        }
                        
                        # Enriquecer con información adicional
                        paper_info = scholar_extractor.enrich_paper_info(paper_info)
                        enriched_papers.append(paper_info)
                
                # Agregar a los resultados combinados
                with results_lock:
                    combined_results.extend(enriched_papers)
        
        except Exception as e:
            errors.append(f"Error en Google Scholar: {str(e)}")
    
    def search_crossref():
        """Función para buscar en Crossref en paralelo"""
        try:
            # Preparar la consulta para Crossref
            from crossref_commons.iteration import iterate_publications_as_json
            
            # Parámetros de búsqueda para Crossref
            queries = {
                'query.bibliographic': query,
                'sort': 'relevance',
                'rows': max_results,
                'select': 'DOI,title,deposited,author,short-container-title,abstract'
            }
            
            crossref_results = []
            
            # Iterar sobre los resultados de Crossref
            for paper in iterate_publications_as_json(max_results=max_results, queries=queries):
                try:
                    # Extraer información del paper
                    paper_info = {
                        "title": paper.get("title", ["Sin título"])[0] if "title" in paper and paper["title"] else "Sin título",
                        "doi": paper.get("DOI"),
                        "source": "Crossref"
                    }
                    
                    # Extraer autores
                    if "author" in paper and paper["author"]:
                        authors = []
                        for author in paper["author"]:
                            if "given" in author and "family" in author:
                                authors.append(f"{author['family']}, {author['given']}")
                            elif "family" in author:
                                authors.append(author["family"])
                        paper_info["authors"] = authors
                    
                    # Extraer año de publicación
                    if "published-print" in paper and "date-parts" in paper["published-print"]:
                        paper_info["year"] = paper["published-print"]["date-parts"][0][0]
                    elif "published-online" in paper and "date-parts" in paper["published-online"]:
                        paper_info["year"] = paper["published-online"]["date-parts"][0][0]
                    
                    # Extraer revista
                    if "short-container-title" in paper and paper["short-container-title"]:
                        paper_info["jurnal"] = paper["short-container-title"][0]
                    
                    # Extraer abstract
                    if "abstract" in paper and paper["abstract"]:
                        paper_info["abstract"] = paper["abstract"]
                    
                    # Añadir URL
                    if "DOI" in paper:
                        paper_info["url"] = f"https://doi.org/{paper['DOI']}"
                    
                    # Añadir bibtex
                    if "DOI" in paper:
                        try:
                            from .Crossref import getBibtex
                            paper_info["bibtex"] = getBibtex(paper["DOI"])
                        except:
                            pass
                    
                    crossref_results.append(paper_info)
                    
                except Exception as e:
                    print(f"Error procesando resultado de Crossref: {str(e)}")
            
            # Agregar a los resultados combinados
            with results_lock:
                combined_results.extend(crossref_results)
                
        except Exception as e:
            errors.append(f"Error en Crossref: {str(e)}")
    
    # Ejecutar búsquedas en paralelo
    with concurrent.futures.ThreadPoolExecutor() as executor:
        scholar_future = executor.submit(search_scholar)
        crossref_future = executor.submit(search_crossref)
        
        # Esperar a que ambas búsquedas terminen
        concurrent.futures.wait([scholar_future, crossref_future])
    
    # Si no se encontraron resultados
    if not combined_results:
        error_msg = "No se encontraron papers que coincidan con la búsqueda"
        if errors:
            error_msg += ": " + "; ".join(errors)
        return None, error_msg
    
    # Eliminar duplicados basados en DOI o título similar
    unique_results = []
    seen_dois = set()
    seen_titles = set()
    
    for paper in combined_results:
        # Normalizar título para comparación
        title_normalized = paper.get("title", "").lower().strip()
        doi = paper.get("doi")
        
        # Verificar si es un duplicado
        is_duplicate = False
        if doi and doi in seen_dois:
            is_duplicate = True
        elif title_normalized and any(title_normalized == t for t in seen_titles):
            is_duplicate = True
        
        # Si no es duplicado, añadirlo a los resultados
        if not is_duplicate:
            if doi:
                seen_dois.add(doi)
            if title_normalized:
                seen_titles.add(title_normalized)
            unique_results.append(paper)
    
    # Ordenar por relevancia (actualmente simplificado)
    # En una implementación más avanzada, se podría usar un algoritmo de ranking más sofisticado
    sorted_results = sorted(unique_results, 
                           key=lambda x: (x.get("cites_num", 0) or 0) * 10 + 
                                        (1 if x.get("abstract") else 0) * 5 +
                                        (1 if x.get("doi") else 0) * 3,
                           reverse=True)
    
    # Limitar el número de resultados
    final_results = sorted_results[:max_results]
    
    return final_results, None