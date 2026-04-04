"""
Contract Analyzer Pro - Punto de entrada principal.
"""

import sys
import os
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent))


def is_api_key_configured() -> bool:
    """
    Verifica si hay una API key configurada en .env.
    No valida si funciona, solo si existe y no esta vacia.
    
    Returns:
        True si hay API key configurada, False en caso contrario
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Verificar que exista y no este vacia
    if not api_key or api_key.strip() == "":
        return False
    
    # Verificar que no sea la key por defecto
    if api_key == "tu_api_key_aqui":
        return False
    
    return True


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
    
    # Solo verificar si hay API key configurada, no validar
    if is_api_key_configured():
        # Ir a ventana principal
        print("[INFO] API key configurada. Cargando aplicacion...")
        from interface.tkinter.main_window import MainWindow
        app = MainWindow()
        app.run()
    else:
        # Mostrar configuracion
        print("[INFO] No hay API key configurada. Abriendo configuracion...")
        from interface.tkinter.config_window import ConfigWindow
        config = ConfigWindow()
        config.run()


if __name__ == "__main__":
    main()