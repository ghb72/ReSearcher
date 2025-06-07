from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from Scholar import ScholarPapersInfo
from Crossref import getPapersInfoFromDOIs
import re
from .ai_models import AIModelManager

# Inicializar el gestor de modelos de IA
ai_manager = AIModelManager()

def find_related_papers(paper_id, context='', model='tfidf'):
    """
    Encuentra artículos relacionados basados en el contenido y contexto
    """
    try:
        # Obtener el artículo original usando getPapersInfoFromDOIs
        original_paper = getPapersInfoFromDOIs(paper_id, restrict=1)
        
        if not original_paper:
            return {
                'success': False,
                'error': 'No se encontró el artículo original',
                'model': model
            }
        
        # Preparar el texto para análisis
        text_to_analyze = f"{original_paper.abstract} {context}"
        
        # Obtener palabras clave según el modelo
        if model == 'tfidf':
            keywords = extract_keywords(text_to_analyze)
        else:  # openai o gemini
            ai_result = ai_manager.find_related_papers_ai(text_to_analyze, context, model)
            if not ai_result['success']:
                return {
                    'success': False,
                    'error': f"Error al obtener palabras clave con {model}: {ai_result['error']}",
                    'model': model
                }
            keywords = ai_result['keywords']
        
        # Buscar artículos relacionados usando ScholarPapersInfo
        related_papers = ScholarPapersInfo(
            query=' '.join(keywords),
            scholar_pages=2,  # Buscar en las primeras 2 páginas
            restrict=1,  # Descargar solo PDFs
            min_date=None,  # Sin filtro de fecha mínima
            scholar_results=10  # 10 resultados por página
        )
        
        if not related_papers:
            return {
                'success': False,
                'error': 'No se encontraron artículos relacionados',
                'model': model
            }
        
        # Calcular similitud
        vectorizer = TfidfVectorizer(stop_words='english')
        texts = [text_to_analyze] + [paper.abstract for paper in related_papers if paper.abstract]
        if len(texts) < 2:
            return {
                'success': False,
                'error': 'No hay suficientes textos para calcular similitud',
                'model': model
            }
            
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Calcular similitud de coseno
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        
        # Ordenar resultados por similitud
        similar_indices = cosine_similarities[0].argsort()[::-1]
        
        # Formatear resultados
        results = []
        for idx in similar_indices[:10]:  # Top 10 resultados
            paper = related_papers[idx]
            results.append({
                'title': paper.title,
                'authors': paper.authors,
                'abstract': paper.abstract,
                'doi': paper.doi,
                'url': paper.url,
                'year': paper.year if hasattr(paper, 'year') else None,
                'cites_num': paper.cites_num if hasattr(paper, 'cites_num') else None,
                'similarity_score': float(cosine_similarities[0][idx])
            })
        
        return {
            'success': True,
            'results': results,
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
    Extrae palabras clave del texto usando TF-IDF
    """
    # Eliminar caracteres especiales y convertir a minúsculas
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Crear vectorizador TF-IDF
    vectorizer = TfidfVectorizer(max_features=max_keywords, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text])
    
    # Obtener las palabras clave
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]
    
    # Ordenar por score
    keyword_scores = list(zip(feature_names, scores))
    keyword_scores.sort(key=lambda x: x[1], reverse=True)
    
    return [keyword for keyword, score in keyword_scores] 