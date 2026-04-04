"""
Cliente para Gemini API usando la nueva libreria google.genai.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class ModeloInfo:
    """Informacion de un modelo disponible."""
    nombre: str
    tipo: str  # "chat" o "embedding"
    descripcion: str


class GeminiClient:
    """
    Cliente para interactuar con Gemini API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None
        self._modelos_chat = []
        self._modelos_embedding = []
    
    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("API key no proporcionada")
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    def validar_api_key(self) -> bool:
        """
        Valida que la API key sea correcta y tenga cuota.
        
        Returns:
            True si es valida, False en caso contrario
        """
        try:
            # Intentar listar modelos como prueba
            list(self.client.models.list())
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "exceeded" in error_msg:
                logger.error(f"Cuota agotada: {e}")
            elif "invalid" in error_msg or "unauthorized" in error_msg:
                logger.error(f"API key invalida: {e}")
            else:
                logger.error(f"Error validando API key: {e}")
            return False
    
    def listar_modelos_chat(self) -> List[ModeloInfo]:
        """Lista los modelos disponibles para chat."""
        if self._modelos_chat:
            return self._modelos_chat
        
        try:
            modelos = self.client.models.list()
            
            # Modelos validos para chat (filtrado)
            modelos_validos = [
                "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash",
                "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"
            ]
            
            for modelo in modelos:
                nombre = modelo.name
                # Limpiar nombre (quitar "models/")
                nombre_limpio = nombre.replace("models/", "")
                
                # Verificar si es modelo de chat valido
                if any(v in nombre_limpio for v in modelos_validos):
                    if "embed" not in nombre_limpio.lower():
                        descripcion = self._generar_descripcion(nombre_limpio)
                        self._modelos_chat.append(ModeloInfo(
                            nombre=nombre_limpio,
                            tipo="chat",
                            descripcion=descripcion
                        ))
            
            # Eliminar duplicados
            vistos = set()
            self._modelos_chat = [m for m in self._modelos_chat if m.nombre not in vistos and not vistos.add(m.nombre)]
            
            return self._modelos_chat
            
        except Exception as e:
            logger.error(f"Error listando modelos chat: {e}")
            return []
    
    def listar_modelos_embedding(self) -> List[ModeloInfo]:
        """Lista los modelos disponibles para embeddings."""
        if self._modelos_embedding:
            return self._modelos_embedding
        
        try:
            modelos = self.client.models.list()
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                if "embed" in nombre_limpio.lower():
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
    
    def _generar_descripcion(self, nombre: str) -> str:
        if "2.5-flash" in nombre:
            return "Rapido, gratuito, ideal para uso diario"
        elif "2.5-pro" in nombre:
            return "Mayor calidad, para analisis profundos"
        elif "2.0-flash" in nombre:
            return "Rapido y confiable"
        else:
            return "Modelo de lenguaje"
    
    def _generar_descripcion_embedding(self, nombre: str) -> str:
        if "embedding-2" in nombre:
            return "Nuevo, mejor calidad para RAG"
        elif "embedding-001" in nombre:
            return "Estable y confiable"
        else:
            return "Modelo de embeddings"
    
    def probar_modelo(self, modelo_nombre: str, mensaje: str = "Hola") -> bool:
        try:
            response = self.client.models.generate_content(
                model=modelo_nombre,
                contents=mensaje
            )
            return response.text is not None
        except Exception as e:
            logger.error(f"Error probando modelo {modelo_nombre}: {e}")
            return False
    
    def guardar_configuracion(self, modelo_chat: str, modelo_embedding: str) -> bool:
        try:
            env_path = ".env"
            contenido = f"""# Gemini API Configuration
GEMINI_API_KEY={self.api_key}
GEMINI_MODEL={modelo_chat}
GEMINI_EMBEDDING_MODEL={modelo_embedding}

# Application Configuration
VECTOR_DB_PATH=./data/vector_store
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
"""
            with open(env_path, "w") as f:
                f.write(contenido.strip())
            
            logger.info(f"Configuracion guardada en {env_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando configuracion: {e}")
            return False