"""
Cliente para Gemini API usando la libreria google.genai.
"""

import logging
import os
from typing import List, Optional
from dataclasses import dataclass

from google import genai

logger = logging.getLogger(__name__)


@dataclass
class ModeloInfo:
    """Informacion de un modelo disponible."""
    nombre: str
    tipo: str
    descripcion: str


class GeminiClient:
    """
    Cliente para interactuar con Gemini API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de Gemini.
        
        Args:
            api_key: API key de Gemini
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None
        self._modelos_chat = []
        self._modelos_embedding = []
    
    @property
    def client(self):
        """Obtiene el cliente de Gemini (lazy loading)."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("API key no proporcionada")
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    def validar_api_key(self) -> bool:
        """
        Valida que la API key sea correcta.
        
        Returns:
            True si es valida, False en caso contrario
        """
        try:
            list(self.client.models.list())
            return True
        except Exception as e:
            logger.error(f"Error validando API key: {e}")
            return False
    
    def listar_modelos_chat(self) -> List[ModeloInfo]:
        """
        Lista los modelos disponibles para chat.
        
        Returns:
            Lista de modelos de chat
        """
        if self._modelos_chat:
            return self._modelos_chat
        
        try:
            modelos = self.client.models.list()
            
            # Modelos validos para chat
            modelos_validos = [
                "gemini-2.5-flash",
                "gemini-2.5-pro", 
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-1.5-flash",
                "gemini-1.5-pro"
            ]
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                # Solo incluir modelos Gemini de texto
                if "gemini" in nombre_limpio.lower():
                    # Excluir modelos no deseados
                    excluir = ["image", "audio", "video", "embed", "tts", 
                              "preview", "robotics", "computer-use", "deep-research"]
                    if not any(x in nombre_limpio.lower() for x in excluir):
                        if any(v in nombre_limpio for v in modelos_validos):
                            if nombre_limpio not in [m.nombre for m in self._modelos_chat]:
                                descripcion = self._generar_descripcion_chat(nombre_limpio)
                                self._modelos_chat.append(ModeloInfo(
                                    nombre=nombre_limpio,
                                    tipo="chat",
                                    descripcion=descripcion
                                ))
            
            return self._modelos_chat
            
        except Exception as e:
            logger.error(f"Error listando modelos chat: {e}")
            return []
    
    def listar_modelos_embedding(self) -> List[ModeloInfo]:
        """
        Lista los modelos disponibles para embeddings.
        
        Returns:
            Lista de modelos de embedding
        """
        if self._modelos_embedding:
            return self._modelos_embedding
        
        try:
            modelos = self.client.models.list()
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                if "embed" in nombre_limpio.lower():
                    if nombre_limpio not in [m.nombre for m in self._modelos_embedding]:
                        descripcion = self._generar_descripcion_embedding(nombre_limpio)
                        self._modelos_embedding.append(ModeloInfo(
                            nombre=nombre_limpio,
                            tipo="embedding",
                            descripcion=descripcion
                        ))
            
            return self._modelos_embedding
            
        except Exception as e:
            logger.error(f"Error listando modelos embedding: {e}")
            return []
    
    def _generar_descripcion_chat(self, nombre: str) -> str:
        """Genera descripcion para modelo de chat."""
        if "2.5-flash" in nombre:
            return "Rapido, gratuito, ideal para uso diario"
        elif "2.5-pro" in nombre:
            return "Mayor calidad, para analisis profundos"
        elif "2.0-flash" in nombre:
            return "Rapido y confiable"
        elif "1.5-flash" in nombre:
            return "Estable y eficiente"
        elif "1.5-pro" in nombre:
            return "Alta calidad"
        else:
            return "Modelo de lenguaje"
    
    def _generar_descripcion_embedding(self, nombre: str) -> str:
        """Genera descripcion para modelo de embedding."""
        if "embedding-2" in nombre:
            return "Nuevo, mejor calidad para RAG"
        elif "embedding-001" in nombre:
            return "Estable y confiable"
        else:
            return "Modelo de embeddings"
    
    def probar_modelo(self, modelo_nombre: str, mensaje: str = "Hola") -> bool:
        """
        Prueba un modelo especifico.
        
        Args:
            modelo_nombre: Nombre del modelo a probar
            mensaje: Mensaje de prueba
            
        Returns:
            True si funciona correctamente
        """
        try:
            response = self.client.models.generate_content(
                model=modelo_nombre,
                contents=mensaje
            )
            return response.text is not None
        except Exception as e:
            logger.error(f"Error probando modelo {modelo_nombre}: {e}")
            return False