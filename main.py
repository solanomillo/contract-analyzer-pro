"""
Main entry point for the Contract Analyzer Pro application.

This module initializes the application, sets up logging,
and launches the Tkinter UI.
"""

import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables before any other imports
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('contract_analyzer.log')
    ]
)

logger = logging.getLogger(__name__)


def verify_configuration() -> bool:
    """
    Verifica que la configuración del proyecto sea correcta.

    Comprueba:
    - Variables de entorno necesarias
    - Directorios requeridos
    - Dependencias básicas

    Returns:
        bool: True si la configuración es correcta, False en caso contrario.
    """
    logger.info("Verificando configuración del proyecto...")

    # Verificar API key de Gemini
    import os
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY no encontrada en .env")
        return False
    logger.info("GEMINI_API_KEY encontrada")

    # Verificar directorios
    required_dirs = [
        "data/contracts",
        "data/vector_store",
        "logs"
    ]

    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio verificado/creado: {dir_path}")

    # Verificar versión de Python
    if sys.version_info < (3, 12):
        logger.error("Se requiere Python 3.12 o superior")
        return False

    logger.info("Configuración verificada correctamente")
    return True


def main():
    """Función principal de la aplicación."""
    logger.info("Iniciando Contract Analyzer Pro")

    if not verify_configuration():
        logger.error("Fallo en la verificación de configuración")
        sys.exit(1)

    # Placeholder para la UI (se implementará en FASE 6)
    logger.info("Aplicación lista. La UI se implementará en la FASE 6")

    # Por ahora, solo mostramos un mensaje
    print("Contract Analyzer Pro - Configuración completada exitosamente")
    print("Las siguientes fases implementarán la funcionalidad completa")


if __name__ == "__main__":
    main()