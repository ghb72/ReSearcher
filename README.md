# Asistente de Búsqueda y Descarga de Artículos Científicos

Este proyecto permite buscar artículos científicos usando un DOI o un enlace completo (por ejemplo, https://doi.org/10.1021/jacs.4c12550), descargar el PDF usando PyPaperBot, visualizarlo en un visor integrado y eliminarlo automáticamente 5 minutos después de cerrar el visor.

## Características

- 🔍 Búsqueda de artículos científicos por DOI o URL completa
- 📑 Descarga automática de PDFs a través de múltiples fuentes académicas
- 👁️ Visor de PDF integrado
- 🔗 Búsqueda de artículos relacionados
- 📊 Análisis básico de documentos subidos
- 🧹 Limpieza automática de archivos temporales

## Tecnologías

- **Backend**: Flask, PyPaperBot, CrossRef API
- **Frontend**: HTML5, CSS3, JavaScript
- **Inteligencia Artificial**: Modelos de procesamiento de texto y análisis semántico

## Requisitos

- Python 3.9+
- Flask
- PyPaperBot
- Otros paquetes especificados en requirements.txt

## Instalación

1. Clone el repositorio
```bash
git clone https://github.com/tu-usuario/research_assistant_br.git
cd research_assistant_br
```

2. Cree un entorno virtual (opcional pero recomendado)
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

3. Instale las dependencias
```bash
pip install -r backend/requirements.txt
```

4. Inicie el backend
```bash
python backend/app.py
```

5. Abra el archivo `frontend/index.html` en su navegador web o use un servidor web simple
```bash
# Si tiene Python instalado
cd frontend
python -m http.server 8000
# Luego visite http://localhost:8000 en su navegador
```

## Estructura del proyecto

```
research_assistant_br/
├── backend/
│   ├── app.py                # Aplicación Flask principal
│   ├── requirements.txt      # Dependencias del backend
│   ├── services/             # Servicios y módulos
│   │   ├── __main__.py       # Punto de entrada para PyPaperBot
│   │   ├── paper_service.py  # Servicio de búsqueda y descarga
│   │   ├── reference_finder.py # Búsqueda de artículos relacionados
│   │   ├── ai_models.py      # Modelos de IA para análisis
│   │   └── ...
│   └── temp_pdfs/            # Almacenamiento temporal de PDFs
├── frontend/
│   ├── index.html            # Página principal
│   ├── css/
│   │   └── styles.css        # Estilos CSS
│   └── js/
│       └── main.js           # Lógica del frontend
└── README.md
```

## Uso

1. Ingrese un DOI o un enlace completo en el buscador (por ejemplo: 10.1021/jacs.4c12550)
2. Haga clic en "Buscar" para obtener el artículo
3. Si hay un PDF disponible, se mostrará en el visor integrado
4. Puede buscar artículos relacionados haciendo clic en el botón correspondiente
5. Al cerrar el visor, el PDF se eliminará automáticamente después de 5 minutos

## APIs disponibles

- **POST /api/search**: Busca y descarga un artículo por DOI o URL
- **GET /pdf/<filename>**: Sirve archivos PDF para visualización
- **POST /api/close_pdf**: Notifica que se ha cerrado un PDF para programar su eliminación
- **POST /api/find_related**: Encuentra artículos relacionados
- **POST /api/analyze_document**: Analiza documentos subidos por el usuario

## Desarrollo

Para contribuir al proyecto:

1. Bifurque el repositorio
2. Cree una rama para su característica (`git checkout -b feature/amazing-feature`)
3. Confirme sus cambios (`git commit -m 'Add some amazing feature'`)
4. Envíe a la rama (`git push origin feature/amazing-feature`)
5. Abra una Pull Request

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).

## Agradecimientos

- [PyPaperBot](https://github.com/ferru97/PyPaperBot) por proporcionar la funcionalidad de búsqueda y descarga de artículos
- [CrossRef API](https://www.crossref.org/services/metadata-delivery/rest-api/) por el acceso a metadatos de artículos académicos 