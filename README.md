# Asistente de Búsqueda y Descarga de Artículos Científicos

Este proyecto permite buscar artículos científicos usando un DOI o un enlace completo (por ejemplo, https://doi.org/10.1021/jacs.4c12550), descargar el PDF usando PyPaperBot, visualizarlo en un visor integrado y eliminarlo automáticamente 5 minutos después de cerrar el visor.

## Requisitos
- Python 3.9+
- Flask
- PyPaperBot

## Instalación

1. Clona el repositorio
2. Instala las dependencias:
```bash
pip install flask PyPaperBot
```
3. Inicia el backend:
```bash
python backend/app.py
```
4. Abre el archivo `frontend/index.html` en tu navegador web

## Estructura del proyecto

```
research_assistant/
├── backend/
│   ├── app.py
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
└── README.md
```

## Uso
- Ingresa un DOI o un enlace completo en el buscador.
- Selecciona un artículo de la lista de resultados.
- Si hay PDF disponible, se mostrará en el visor integrado.
- Al cerrar el visor, el PDF se eliminará automáticamente después de 5 minutos. 