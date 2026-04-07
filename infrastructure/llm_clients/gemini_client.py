"""
Cliente para Gemini API con manejo profesional de errores, retry y fallback.
"""

import logging
import os
import time
from typing import List, Optional
from dataclasses import dataclass

from google import genai

logger = logging.getLogger(__name__)


@dataclass
class ModeloInfo:
    nombre: str
    tipo: str
    descripcion: str


class GeminiClient:
    """
    Cliente profesional para Gemini API.
    
    Caracteristicas:
    - Reintentos automáticos con backoff progresivo
    - Fallback a modelo más estable (gemini-2.0-flash)
    - Manejo diferenciado de errores (503, 429, 401)
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

    # ==================== MÉTODO CENTRAL ====================
    def generar_contenido(
        self,
        prompt: str,
        modelo: str = "gemini-2.5-flash",
        max_retries: int = 3,
        fallback_modelo: str = "gemini-2.0-flash"
    ) -> Optional[str]:
        """
        Genera contenido usando Gemini con reintentos y fallback.
        
        Args:
            prompt: Prompt para el modelo
            modelo: Modelo principal a usar
            max_retries: Número máximo de reintentos
            fallback_modelo: Modelo alternativo si falla el principal
            
        Returns:
            Texto generado o None si falla
        """
        # Probar con el modelo principal
        for intento in range(max_retries):
            try:
                logger.info(f"Intento {intento+1}/{max_retries} - Modelo: {modelo}")
                
                response = self.client.models.generate_content(
                    model=modelo,
                    contents=prompt
                )
                
                if response and response.text:
                    logger.info(f"Éxito con modelo {modelo}")
                    return response.text
                else:
                    logger.warning(f"Respuesta vacía del modelo {modelo}")
                    
            except Exception as e:
                error_msg = str(e)
                
                # Error 503: Servicio saturado (reintentar con backoff)
                if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
                    wait_time = 2 * (intento + 1)
                    logger.warning(f"Gemini saturado (intento {intento+1}/{max_retries}) - Esperando {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                # Error 429: Rate limit (reintentar con espera)
                elif "429" in error_msg or "quota" in error_msg.lower():
                    wait_time = 5 * (intento + 1)
                    logger.warning(f"Rate limit (intento {intento+1}/{max_retries}) - Esperando {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                # Error 401: API Key inválida (no reintentar)
                elif "401" in error_msg or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                    logger.error(f"API Key inválida: {error_msg}")
                    raise ValueError("API key inválida")
                
                # Otros errores
                else:
                    logger.error(f"Error inesperado en intento {intento+1}: {error_msg}")
                    if intento == max_retries - 1:
                        break
                    time.sleep(2)
                    continue
        
        # ==================== FALLBACK ====================
        if fallback_modelo and modelo != fallback_modelo:
            try:
                logger.info(f"Intentando fallback con modelo: {fallback_modelo}")
                
                response = self.client.models.generate_content(
                    model=fallback_modelo,
                    contents=prompt
                )
                
                if response and response.text:
                    logger.info(f"Fallback exitoso con {fallback_modelo}")
                    return response.text
                else:
                    logger.warning(f"Fallback sin respuesta")
                    
            except Exception as e:
                logger.error(f"Fallback falló: {e}")
        
        logger.error("Todos los intentos fallaron")
        return None

    # ==================== MÉTODOS EXISTENTES ====================
    def validar_api_key(self) -> bool:
        """Valida que la API key sea correcta."""
        try:
            list(self.client.models.list())
            return True
        except Exception as e:
            logger.error(f"Error validando API key: {e}")
            return False
    
    def listar_modelos_chat(self) -> List[ModeloInfo]:
        """Lista los modelos disponibles para chat."""
        if self._modelos_chat:
            return self._modelos_chat
        
        try:
            modelos = self.client.models.list()
            
            modelos_validos = [
                "gemini-2.0-flash",
                "gemini-2.5-flash", 
                "gemini-1.5-flash",
                "gemini-2.0-flash-lite"
            ]
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                if "gemini" in nombre_limpio.lower():
                    if "embed" not in nombre_limpio.lower():
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
        """Lista los modelos disponibles para embeddings."""
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
        if "2.0-flash" in nombre:
            return "Estable, recomendado para uso general"
        elif "2.5-flash" in nombre:
            return "Más rápido pero puede tener alta demanda"
        elif "1.5-flash" in nombre:
            return "Muy estable, ideal para análisis"
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
        """Prueba un modelo especifico."""
        try:
            response = self.client.models.generate_content(
                model=modelo_nombre,
                contents=mensaje
            )
            return response.text is not None
        except Exception as e:
            logger.error(f"Error probando modelo {modelo_nombre}: {e}")
            return False