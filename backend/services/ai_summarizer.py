from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize
from .ai_models import AIModelManager

# Descargar recursos necesarios de NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Inicializar el gestor de modelos de IA
ai_manager = AIModelManager()

def generate_summary(text, model='transformers'):
    """
    Genera un resumen del texto usando el modelo especificado
    """
    try:
        if model == 'transformers':
            return generate_summary_transformers(text)
        elif model == 'openai':
            return ai_manager.generate_summary_openai(text)
        elif model == 'gemini':
            return ai_manager.generate_summary_gemini(text)
        else:
            raise ValueError(f"Modelo no soportado: {model}")
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def generate_summary_transformers(text):
    """
    Genera un resumen usando el modelo de transformers
    """
    try:
        # Inicializar el modelo de resumen
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        
        # Dividir el texto en secciones si es muy largo
        sections = split_into_sections(text)
        
        summaries = []
        for section in sections:
            if len(section.split()) > 100:  # Solo resumir secciones largas
                summary = summarizer(section, max_length=130, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            else:
                summaries.append(section)
        
        # Organizar el resumen en secciones
        organized_summary = {
            'objective': extract_section(summaries, ['objective', 'aim', 'goal', 'purpose']),
            'methodology': extract_section(summaries, ['method', 'methodology', 'approach']),
            'analysis': extract_section(summaries, ['analysis', 'results', 'findings']),
            'conclusions': extract_section(summaries, ['conclusion', 'conclusions', 'summary'])
        }
        
        return {
            'success': True,
            'summary': organized_summary,
            'model': 'transformers'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'model': 'transformers'
        }

def split_into_sections(text):
    """
    Divide el texto en secciones basadas en oraciones
    """
    sentences = sent_tokenize(text)
    sections = []
    current_section = []
    
    for sentence in sentences:
        current_section.append(sentence)
        if len(current_section) >= 5:  # Agrupar cada 5 oraciones
            sections.append(' '.join(current_section))
            current_section = []
    
    if current_section:
        sections.append(' '.join(current_section))
    
    return sections

def extract_section(summaries, keywords):
    """
    Extrae la sección relevante basada en palabras clave
    """
    for summary in summaries:
        summary_lower = summary.lower()
        if any(keyword in summary_lower for keyword in keywords):
            return summary
    return "" 