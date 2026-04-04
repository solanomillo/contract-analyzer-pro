"""
Servicio de threading para manejo de tareas en segundo plano.

Proporciona utilidades seguras de threading para integracion con Tkinter.
"""

import threading
import queue
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class ThreadingService:
    """
    Servicio para manejar hilos en segundo plano y comunicacion con UI.
    
    Asegura actualizaciones seguras para Tkinter usando colas.
    """
    
    def __init__(self):
        """Inicializa el servicio de threading."""
        self._hilos = []
        self._cola_tareas = queue.Queue()
        
    def ejecutar_en_segundo_plano(
        self,
        objetivo: Callable,
        args: tuple = (),
        callback: Optional[Callable] = None,
        callback_error: Optional[Callable] = None
    ) -> threading.Thread:
        """
        Ejecuta una funcion en un hilo de segundo plano.
        
        Args:
            objetivo: Funcion a ejecutar
            args: Argumentos para la funcion
            callback: Funcion a llamar en caso de exito (recibe el resultado)
            callback_error: Funcion a llamar en caso de error (recibe la excepcion)
            
        Returns:
            Objeto Thread
        """
        def _envoltorio():
            try:
                resultado = objetivo(*args)
                if callback:
                    self._cola_tareas.put(("callback", callback, resultado))
            except Exception as e:
                logger.error(f"Tarea en segundo plano fallo: {e}")
                if callback_error:
                    self._cola_tareas.put(("error", callback_error, e))
        
        hilo = threading.Thread(target=_envoltorio, daemon=True)
        hilo.start()
        self._hilos.append(hilo)
        return hilo
    
    def procesar_cola(self, app):
        """
        Procesa elementos pendientes en la cola (llamar desde el loop principal de UI).
        
        Args:
            app: Instancia de la app Tkinter con metodo after()
        """
        try:
            while True:
                item = self._cola_tareas.get_nowait()
                if item[0] == "callback":
                    _, callback, resultado = item
                    callback(resultado)
                elif item[0] == "error":
                    _, callback_error, error = item
                    callback_error(error)
        except queue.Empty:
            pass
        finally:
            if hasattr(app, 'after'):
                app.after(100, lambda: self.procesar_cola(app))
    
    def esperar_finalizacion(self, timeout: Optional[float] = None):
        """
        Espera a que todos los hilos en segundo plano terminen.
        
        Args:
            timeout: Tiempo maximo de espera en segundos
        """
        for hilo in self._hilos:
            hilo.join(timeout)