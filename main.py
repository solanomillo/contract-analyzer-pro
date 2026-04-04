"""
Contract Analyzer Pro - Punto de entrada principal.
"""

import sys
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from interface.tkinter.config_window import ConfigWindow


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
    
    # Iniciar ventana de configuracion
    config = ConfigWindow()
    config.run()


if __name__ == "__main__":
    main()