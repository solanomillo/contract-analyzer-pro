"""
Contract Analyzer Pro - Punto de entrada principal.
"""

import sys
import os
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

# Verificar si ya existe configuracion
def is_configured() -> bool:
    """Verifica si el sistema ya esta configurado."""
    env_path = Path(".env")
    if not env_path.exists():
        return False
    
    # Verificar que tenga API key
    with open(env_path, "r") as f:
        content = f.read()
        return "GEMINI_API_KEY=" in content and "GEMINI_API_KEY=tu_api_key" not in content

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
    
    if is_configured():
        # Ir directamente a la ventana principal
        from interface.tkinter.main_window import MainWindow
        app = MainWindow()
        app.run()
    else:
        # Mostrar configuracion inicial
        from interface.tkinter.config_window import ConfigWindow
        config = ConfigWindow()
        config.run()
        
        # Despues de configurar, abrir main
        if is_configured():
            print("\n[INFO] Configuracion completada. Iniciando aplicacion...\n")
            from interface.tkinter.main_window import MainWindow
            app = MainWindow()
            app.run()


if __name__ == "__main__":
    main()