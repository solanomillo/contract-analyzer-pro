"""
Contract Analyzer Pro - Punto de entrada principal.
Sistema de Analisis Legal Inteligente.
"""

import sys
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from application.services.config_service import ConfigService


def main():
    """Funcion principal de la aplicacion."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     C O N T R A C T   A N A L Y Z E R   P R O               ║
    ║     Sistema de Analisis Legal Inteligente                   ║
    ║     Version 1.0 - 2026                                      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Usar servicio centralizado de configuracion
    config_service = ConfigService()
    
    if config_service.has_api_key():
        print("[INFO] Configuracion encontrada. Iniciando aplicacion...")
        from interface.tkinter.main_window import MainWindow
        app = MainWindow()
        app.run()
    else:
        print("[INFO] Primera ejecucion. Abriendo configuracion...")
        from interface.tkinter.config_window import ConfigWindow
        app = ConfigWindow()
        app.run()


if __name__ == "__main__":
    main()