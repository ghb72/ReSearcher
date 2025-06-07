import os
import openai
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configurar Google Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class AIModelManager:
    def __init__(self):
        self.openai_model = "gpt-3.5-turbo"
        self.gemini_model = genai.GenerativeModel('gemini-pro')
    
    def generate_summary_openai(self, text, sections=None):
        """
        Genera un resumen usando OpenAI
        """
        try:
            if sections is None:
                sections = ['objective', 'methodology', 'analysis', 'conclusions']
            
            summary = {}
            for section in sections:
                prompt = f"""Analiza el siguiente texto y extrae la sección de {section}. 
                Si no encuentras información específica para esta sección, indica 'No disponible'.
                Texto: {text}"""
                
                response = openai.ChatCompletion.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "Eres un asistente experto en análisis de textos académicos."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                summary[section] = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'summary': summary,
                'model': 'openai'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': 'openai'
            }
    
    def generate_summary_gemini(self, text, sections=None):
        """
        Genera un resumen usando Google Gemini
        """
        try:
            if sections is None:
                sections = ['objective', 'methodology', 'analysis', 'conclusions']
            
            summary = {}
            for section in sections:
                prompt = f"""Analiza el siguiente texto y extrae la sección de {section}. 
                Si no encuentras información específica para esta sección, indica 'No disponible'.
                Texto: {text}"""
                
                response = self.gemini_model.generate_content(prompt)
                summary[section] = response.text.strip()
            
            return {
                'success': True,
                'summary': summary,
                'model': 'gemini'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': 'gemini'
            }
    
    def find_related_papers_ai(self, text, context='', model='openai'):
        """
        Encuentra artículos relacionados usando IA
        """
        try:
            prompt = f"""Basado en el siguiente texto y contexto, sugiere palabras clave para buscar artículos relacionados.
            No incluyas las referencias que ya están citadas en el texto.
            Texto: {text}
            Contexto adicional: {context}
            
            Proporciona las palabras clave en formato de lista, separadas por comas."""
            
            if model == 'openai':
                response = openai.ChatCompletion.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "Eres un experto en investigación académica."},
                        {"role": "user", "content": prompt}
                    ]
                )
                keywords = response.choices[0].message.content.strip()
            else:  # gemini
                response = self.gemini_model.generate_content(prompt)
                keywords = response.text.strip()
            
            # Limpiar y formatear las palabras clave
            keywords = [k.strip() for k in keywords.split(',')]
            
            return {
                'success': True,
                'keywords': keywords,
                'model': model
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': model
            } 