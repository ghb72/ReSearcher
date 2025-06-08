from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import requests
from .Crossref import getPapersInfoFromDOIs

# Función para buscar artículos relacionados
def find_related_papers(paper_id, context='', model='tfidf'):
    """
    Encuentra artículos relacionados basados en el contenido y contexto
    """
    try:
        # Obtener el artículo original
        original_paper = getPapersInfoFromDOIs(paper_id, restrict=1)
        
        if not original_paper or not original_paper.DOI:
            return {
                'success': False,
                'error': 'No se encontró el artículo original',
                'model': model
            }
        
        # Preparar el texto para análisis
        title = original_paper.title if hasattr(original_paper, 'title') and original_paper.title else ""
        abstract = getattr(original_paper, 'abstract', '')
        text_to_analyze = f"{title} {abstract} {context}".strip()
        
        if not text_to_analyze:
            return {
                'success': False,
                'error': 'No hay suficiente texto para analizar',
                'model': model
            }
        
        # Obtener palabras clave
        keywords = extract_keywords(text_to_analyze)
        if not keywords:
            return {
                'success': False,
                'error': 'No se pudieron extraer palabras clave',
                'model': model
            }
        
        # Buscar artículos relacionados en Crossref
        related_papers = search_crossref_papers(' '.join(keywords))
        
        if not related_papers:
            return {
                'success': False,
                'error': 'No se encontraron artículos relacionados',
                'model': model
            }
        
        # Verificar que hay suficientes datos
        if len(related_papers) < 1:
            return {
                'success': False,
                'error': 'No hay suficientes artículos para comparar',
                'model': model
            }
        
        # Calcular similitud sin usar matrices TF-IDF para evitar errores
        # Usar las palabras clave directamente para puntuar
        results = []
        for paper in related_papers:
            # Crear texto completo del paper
            paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
            
            # Calcular cuántas keywords están en el texto del paper (puntuación simple)
            score = 0
            for keyword in keywords:
                if keyword.lower() in paper_text.lower():
                    score += 1
            
            # Normalizar puntuación
            similarity = score / len(keywords) if keywords else 0
            
            # Evitar incluir el mismo paper
            if paper.get('doi') == paper_id:
                continue
                
            results.append({
                'title': paper.get('title', 'Sin título'),
                'authors': paper.get('authors', ['Autores desconocidos']),
                'abstract': paper.get('abstract', ''),
                'doi': paper.get('doi', ''),
                'url': paper.get('url', ''),
                'year': paper.get('year', None),
                'cites_num': paper.get('citation_count', None),
                'similarity_score': float(similarity)
            })
        
        # Ordenar por puntuación de similitud
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Devolver solo los 10 primeros resultados
        return {
            'success': True,
            'results': results[:10],
            'model': model
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'model': model
        }

def extract_keywords(text, max_keywords=10):
    """
    Extrae palabras clave del texto de manera simplificada
    """
    # Eliminar caracteres especiales y convertir a minúsculas
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Dividir en palabras
    words = text.split()
    
    # Eliminar palabras comunes (stop words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'into', 'like', 'through', 'after', 'over', 'between', 'out', 'against', 'during', 'without', 'before', 'under', 'around', 'among'}
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Contar frecuencia de palabras
    word_freq = {}
    for word in filtered_words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    
    # Ordenar por frecuencia
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Devolver las palabras más frecuentes
    return [word for word, freq in sorted_words[:max_keywords]]

def search_crossref_papers(query, max_results=30):
    """
    Busca artículos científicos en Crossref
    """
    headers = {
        'User-Agent': 'ResearchAssistant/1.0 (mailto:example@example.com)'
    }
    
    try:
        url = "https://api.crossref.org/works"
        params = {
            'query': query,
            'rows': max_results,
            'sort': 'relevance',
            'select': 'DOI,title,abstract,author,published-print,published-online,container-title,reference,is-referenced-by-count'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return []
            
        data = response.json()
        
        if 'message' not in data or 'items' not in data['message']:
            return []
            
        results = []
        for item in data['message']['items']:
            # Extraer título
            title = item.get('title', [''])[0] if item.get('title') and len(item['title']) > 0 else 'Sin título'
            
            # Extraer autores
            authors = []
            if 'author' in item:
                for author in item['author']:
                    name_parts = []
                    if 'given' in author:
                        name_parts.append(author['given'])
                    if 'family' in author:
                        name_parts.append(author['family'])
                    if name_parts:
                        authors.append(' '.join(name_parts))
            
            # Extraer año de publicación
            year = None
            if 'published-print' in item and 'date-parts' in item['published-print']:
                year = item['published-print']['date-parts'][0][0]
            elif 'published-online' in item and 'date-parts' in item['published-online']:
                year = item['published-online']['date-parts'][0][0]
            
            # Extraer resumen
            abstract = item.get('abstract', '')
            
            # Extraer DOI
            doi = item.get('DOI', '')
            
            # Extraer revista
            journal = item.get('container-title', [''])[0] if item.get('container-title') and len(item['container-title']) > 0 else ''
            
            # Extraer número de citas
            citation_count = item.get('is-referenced-by-count', 0)
            
            results.append({
                'title': title,
                'authors': authors,
                'year': year,
                'abstract': abstract,
                'doi': doi,
                'journal': journal,
                'citation_count': citation_count,
                'url': f"https://doi.org/{doi}" if doi else None
            })
            
        return results
    
    except Exception as e:
        print(f"Error buscando en Crossref: {str(e)}")
        return [] 