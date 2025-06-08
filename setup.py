#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import platform

def print_step(message):
    """Imprime un mensaje formateado como paso de instalación"""
    print("\n" + "="*80)
    print(f">> {message}")
    print("="*80)

def run_command(command):
    """Ejecuta un comando y muestra su salida"""
    print(f"Ejecutando: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Mostrar salida en tiempo real
    for line in process.stdout:
        sys.stdout.write(line)
    
    process.wait()
    return process.returncode

def create_virtual_env():
    """Crea un entorno virtual para el proyecto"""
    print_step("Creando entorno virtual")
    
    if not os.path.exists("venv"):
        run_command("python -m venv venv")
        print("Entorno virtual creado correctamente.")
    else:
        print("El entorno virtual ya existe.")
    
    # Activar el entorno virtual
    if platform.system() == "Windows":
        activate_cmd = ".\\venv\\Scripts\\activate"
    else:
        activate_cmd = "source ./venv/bin/activate"
    
    print(f"\nPara activar el entorno virtual, ejecuta: {activate_cmd}")

def install_dependencies():
    """Instala las dependencias del proyecto"""
    print_step("Instalando dependencias")
    
    # Detectar si estamos en un entorno virtual activo
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("ADVERTENCIA: No estás en un entorno virtual activo.")
        response = input("¿Deseas continuar con la instalación? (s/n): ")
        if response.lower() != 's':
            print("Instalación cancelada.")
            return False
    
    if os.path.exists("backend/requirements.txt"):
        run_command("pip install -r backend/requirements.txt")
        print("Dependencias instaladas correctamente.")
        return True
    else:
        print("ERROR: No se encontró el archivo backend/requirements.txt")
        return False

def setup_project():
    """Configura el proyecto para su uso"""
    print_step("Configurando el proyecto")
    
    # Crear directorios necesarios
    dirs_to_create = [
        "backend/temp_pdfs",
    ]
    
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directorio creado: {directory}")
    
    print("\nConfiguración completada correctamente.")

def main():
    """Función principal del script de instalación"""
    print_step("Iniciando instalación del Asistente de Búsqueda de Artículos Científicos")
    
    # Crear entorno virtual
    create_virtual_env()
    
    # Preguntar si desea activar el entorno virtual ahora
    response = input("\n¿Has activado el entorno virtual? (s/n): ")
    if response.lower() != 's':
        print("Por favor, activa el entorno virtual y ejecuta este script nuevamente.")
        sys.exit(0)
    
    # Instalar dependencias
    if install_dependencies():
        # Configurar proyecto
        setup_project()
        
        print_step("Instalación completada correctamente")
        print("""
Para iniciar el backend:
    cd backend
    python app.py

Para acceder al frontend:
    Abre el archivo frontend/index.html en tu navegador
    o utiliza un servidor web simple como:
    cd frontend
    python -m http.server 8000
        """)
    else:
        print_step("La instalación no pudo completarse")

if __name__ == "__main__":
    main() 