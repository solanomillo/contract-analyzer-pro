"""
Servicio de procesamiento de documentos con threading mejorado.
"""

import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from application.services.pdf_service import PDFService

logger = logging.getLogger(__name__)


class ProcessingService:
    """
    Servicio para procesar documentos en segundo plano.
    
    Maneja la comunicacion entre el hilo de procesamiento y la UI.
    """
    
    def __init__(self):
        """Inicializa el servicio de procesamiento."""
        self.pdf_service = PDFService(chunk_size=1000, chunk_overlap=200)
        self._current_thread: Optional[threading.Thread] = None
        self._current_pdf_path: Optional[Path] = None
        self._is_cancelled = False
    
    def procesar_pdf(
        self,
        pdf_path: Path,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> threading.Thread:
        """
        Procesa un PDF en segundo plano.
        
        Args:
            pdf_path: Ruta al PDF
            on_progress: Callback para progreso (recibe mensaje)
            on_complete: Callback para completado (recibe resultado)
            on_error: Callback para error (recibe error)
            
        Returns:
            Thread del procesamiento
        """
        self._current_pdf_path = pdf_path
        self._is_cancelled = False
        
        def _procesar():
            try:
                # Reportar inicio
                self._report_progress(on_progress, "Iniciando procesamiento del PDF...")
                
                # Extraer texto
                self._report_progress(on_progress, "Extrayendo texto del PDF...")
                extraccion = self.pdf_service.extract_text(pdf_path)
                
                if self._is_cancelled:
                    return
                
                # Limpiar y segmentar
                self._report_progress(on_progress, "Segmentando texto en chunks...")
                chunks = self.pdf_service.segmentar_texto(extraccion["texto_completo"])
                
                if self._is_cancelled:
                    return
                
                # Preparar resultado
                resultado = {
                    "nombre_archivo": pdf_path.name,
                    "texto_completo": extraccion["texto_completo"],
                    "chunks": chunks,
                    "metadatos": extraccion["metadatos"],
                    "total_paginas": extraccion["total_paginas"],
                    "total_chunks": len(chunks),
                    "total_caracteres": len(extraccion["texto_completo"])
                }
                
                self._report_progress(on_progress, "Procesamiento completado!")
                
                if on_complete:
                    on_complete(resultado)
                    
            except Exception as e:
                logger.error(f"Error procesando PDF: {e}")
                if on_error:
                    on_error(str(e))
        
        self._current_thread = threading.Thread(target=_procesar, daemon=True)
        self._current_thread.start()
        return self._current_thread
    
    def _report_progress(self, callback: Optional[Callable], mensaje: str):
        """
        Reporta progreso via callback.
        
        Args:
            callback: Funcion callback
            mensaje: Mensaje de progreso
        """
        if callback:
            callback(mensaje)
    
    def cancelar(self):
        """Cancela el procesamiento actual."""
        self._is_cancelled = True
        logger.info("Procesamiento cancelado por el usuario")
    
    def esta_procesando(self) -> bool:
        """
        Verifica si hay un procesamiento en curso.
        
        Returns:
            True si hay un thread activo
        """
        return self._current_thread is not None and self._current_thread.is_alive()