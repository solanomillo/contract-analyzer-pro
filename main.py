"""
Contract Analyzer Pro - Punto de entrada principal.
"""

import sys
import os
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent))


def is_api_key_valid() -> bool:
    """
    Verifica si la API key es valida y funciona.
    
    Returns:
        True si la API key es valida, False en caso contrario
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Verificar que exista y no este vacia
    if not api_key or api_key.strip() == "":
        print("[INFO] No hay API key configurada")
        return False
    
    # Verificar que no sea la key por defecto
    if api_key == "tu_api_key_aqui":
        print("[INFO] API key por defecto detectada")
        return False
    
    # Verificar que la API key funcione realmente
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        # Intentar listar modelos como prueba de conexion
        list(client.models.list())
        print("[INFO] API key valida y funcionando")
        return True
    except Exception as e:
        print(f"[INFO] API key invalida o sin acceso: {e}")
        return False


def main():
    """Funcion principal."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     C O N T R A C T   A N A L Y Z E R   P R O               ║
    ║     Sistema de Analisis Legal Inteligente                   ║
    ║     Version 1.0 - 2026                                      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Validar API key real
    if is_api_key_valid():
        # Ir a ventana principal
        print("[INFO] API key valida. Cargando aplicacion...")
        from interface.tkinter.main_window import MainWindow
        app = MainWindow()
        app.run()
    else:
        # Mostrar configuracion
        print("[INFO] Se requiere configuracion de API key")
        from interface.tkinter.config_window import ConfigWindow
        config = ConfigWindow()
        config.run()


if __name__ == "__main__":
    main()