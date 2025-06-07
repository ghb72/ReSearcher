import PyPDF2
from docx import Document
import os
import re

def analyze_document(file):
    """
    Analiza un documento y extrae su contenido
    """
    try:
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Guardar el archivo temporalmente
        temp_path = f"temp_{filename}"
        file.save(temp_path)
        
        content = ""
        
        # Procesar según el tipo de archivo
        if file_extension == '.pdf':
            content = extract_from_pdf(temp_path)
        elif file_extension == '.docx':
            content = extract_from_docx(temp_path)
        elif file_extension == '.txt':
            content = extract_from_txt(temp_path)
        elif file_extension == '.tex':
            content = extract_from_latex(temp_path)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {file_extension}")
        
        # Limpiar archivo temporal
        os.remove(temp_path)
        
        return {
            'success': True,
            'content': content,
            'metadata': extract_metadata(content)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def extract_from_pdf(file_path):
    """Extrae texto de un archivo PDF"""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_from_docx(file_path):
    """Extrae texto de un archivo DOCX"""
    doc = Document(file_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_from_txt(file_path):
    """Extrae texto de un archivo TXT"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_from_latex(file_path):
    """Extrae texto de un archivo LaTeX"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        # Eliminar comandos LaTeX básicos
        content = re.sub(r'\\[a-zA-Z]+{.*?}', '', content)
        content = re.sub(r'%.*$', '', content, flags=re.MULTILINE)
        return content

def extract_metadata(content):
    """Extrae metadatos básicos del contenido"""
    # Aquí se pueden implementar más reglas de extracción
    return {
        'word_count': len(content.split()),
        'estimated_pages': len(content.split()) // 250,  # Estimación aproximada
        'has_references': bool(re.search(r'references|bibliography', content.lower()))
    } 