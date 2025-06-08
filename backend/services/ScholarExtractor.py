import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import quote_plus, urlencode

class ScholarExtractor:
    """
    Clase para extraer información detallada de artículos desde Google Scholar,
    especialmente enfocada en obtener el abstract/resumen que no está disponible
    en otras fuentes como Crossref.
    """
    
    def __init__(self):
        # Headers para simular un navegador y evitar bloqueos
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://scholar.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
    def extract_paper_details(self, doi=None, title=None):
        """
        Extrae detalles de un artículo científico desde Google Scholar,
        usando el DOI o el título como término de búsqueda.
        
        Args:
            doi: El DOI del artículo a buscar
            title: El título del artículo a buscar
            
        Returns:
            dict: Información detallada del artículo incluyendo abstract si está disponible
        """
        if not doi and not title:
            return None, "Se requiere un DOI o título para buscar"
        
        # Determinar el término de búsqueda
        if doi:
            search_term = f'"{doi}"'
        else:
            search_term = title
            
        # Construir URL de búsqueda
        params = {
            'q': search_term,
            'hl': 'es',
            'as_sdt': '0,5',
        }
        search_url = f"https://scholar.google.com/scholar?{urlencode(params)}"
        
        try:
            # Añadir un retraso aleatorio para evitar bloqueos
            time.sleep(random.uniform(1, 3))
            
            # Realizar la solicitud HTTP
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None, f"Error al conectar con Google Scholar: {response.status_code}"
            
            # Parsear el HTML con BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar resultados
            results = soup.select('.gs_r.gs_or.gs_scl')
            if not results:
                return None, "No se encontraron resultados en Google Scholar"
            
            # Tomar el primer resultado (el más relevante)
            result = results[0]
            
            # Extraer información
            paper_info = {}
            
            # Título
            title_tag = result.select_one('.gs_rt')
            if title_tag:
                paper_info['title'] = title_tag.get_text(strip=True).replace('[HTML]', '').replace('[PDF]', '').strip()
            
            # Autores, año y fuente
            meta_tag = result.select_one('.gs_a')
            if meta_tag:
                meta_text = meta_tag.get_text(strip=True)
                # Intentar separar autores y fecha
                if '-' in meta_text:
                    authors_part = meta_text.split('-')[0].strip()
                    paper_info['authors'] = authors_part
                    
                    # Extraer año
                    import re
                    year_match = re.search(r'\b(19|20)\d{2}\b', meta_text)
                    if year_match:
                        paper_info['year'] = year_match.group(0)
                    
                    # Extraer revista/fuente
                    journal_parts = meta_text.split('-')
                    if len(journal_parts) > 1:
                        paper_info['journal'] = journal_parts[1].strip()
            
            # Abstract / Resumen
            abstract_tag = result.select_one('.gs_rs')
            if abstract_tag:
                abstract_text = abstract_tag.get_text(strip=True)
                # Eliminar indicadores de elipsis y limpiar
                abstract_text = abstract_text.replace('…', '...').strip()
                paper_info['abstract'] = abstract_text
            
            # URL del artículo
            url_tag = result.select_one('.gs_rt a')
            if url_tag and 'href' in url_tag.attrs:
                paper_info['url'] = url_tag['href']
            
            # Número de citas
            cite_tag = result.select_one('a:contains("Cited by")')
            if cite_tag:
                cite_text = cite_tag.get_text(strip=True)
                cite_count = ''.join(filter(str.isdigit, cite_text))
                if cite_count:
                    paper_info['cited_by'] = int(cite_count)
            
            return paper_info, None
            
        except Exception as e:
            return None, f"Error al extraer información de Google Scholar: {str(e)}"
    
    def enrich_paper_info(self, paper_info):
        """
        Enriquece la información existente de un artículo con datos adicionales
        de Google Scholar, especialmente el abstract.
        
        Args:
            paper_info: Diccionario con información existente del artículo
            
        Returns:
            dict: Información del artículo enriquecida
        """
        if not paper_info:
            return paper_info
            
        # Intentar buscar por DOI primero
        if 'doi' in paper_info and paper_info['doi']:
            enriched_info, error = self.extract_paper_details(doi=paper_info['doi'])
            if not error and enriched_info:
                # Fusionar información, priorizando los datos originales
                for key, value in enriched_info.items():
                    if key not in paper_info or not paper_info[key]:
                        paper_info[key] = value
                return paper_info
                
        # Si no hay DOI o falló la búsqueda, intentar por título
        if 'title' in paper_info and paper_info['title']:
            enriched_info, error = self.extract_paper_details(title=paper_info['title'])
            if not error and enriched_info:
                # Fusionar información, priorizando los datos originales
                for key, value in enriched_info.items():
                    if key not in paper_info or not paper_info[key]:
                        paper_info[key] = value
                        
        return paper_info
