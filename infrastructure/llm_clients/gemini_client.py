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
    - Reintentos automaticos con backoff progresivo
    - Fallback a modelo mas estable (gemini-2.0-flash)
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

    # ==================== METODO CENTRAL ====================
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
            max_retries: Numero maximo de reintentos
            fallback_modelo: Modelo alternativo si falla el principal
            
        Returns:
            Texto generado o None si falla
        """
        for intento in range(max_retries):
            try:
                logger.info(f"Intento {intento+1}/{max_retries} - Modelo: {modelo}")
                
                response = self.client.models.generate_content(
                    model=modelo,
                    contents=prompt
                )
                
                if response and response.text:
                    logger.info(f"Exito con modelo {modelo}")
                    return response.text
                else:
                    logger.warning(f"Respuesta vacia del modelo {modelo}")
                    
            except Exception as e:
                error_msg = str(e)
                
                if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
                    wait_time = 2 * (intento + 1)
                    logger.warning(f"Gemini saturado (intento {intento+1}/{max_retries}) - Esperando {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                elif "429" in error_msg or "quota" in error_msg.lower():
                    wait_time = 5 * (intento + 1)
                    logger.warning(f"Rate limit (intento {intento+1}/{max_retries}) - Esperando {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                elif "401" in error_msg or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                    logger.error(f"API Key invalida: {error_msg}")
                    raise ValueError("API key invalida")
                
                else:
                    logger.error(f"Error inesperado en intento {intento+1}: {error_msg}")
                    if intento == max_retries - 1:
                        break
                    time.sleep(2)
                    continue
        
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
                logger.error(f"Fallback fallo: {e}")
        
        logger.error("Todos los intentos fallaron")
        return None

    # ==================== LISTAR TODOS LOS MODELOS ====================
    def listar_modelos_chat(self) -> List[ModeloInfo]:
        """
        Lista TODOS los modelos disponibles para chat de Gemini.
        """
        if self._modelos_chat:
            return self._modelos_chat
        
        try:
            modelos = self.client.models.list()
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                # Solo incluir modelos de Gemini (no Gemma)
                if "gemini" in nombre_limpio.lower():
                    # Excluir modelos que no son de chat
                    excluir = ["embed", "image", "audio", "video", "tts", "imagen", "veo", "robotics"]
                    if not any(x in nombre_limpio.lower() for x in excluir):
                        if nombre_limpio not in [m.nombre for m in self._modelos_chat]:
                            descripcion = self._generar_descripcion_chat(nombre_limpio)
                            self._modelos_chat.append(ModeloInfo(
                                nombre=nombre_limpio,
                                tipo="chat",
                                descripcion=descripcion
                            ))
            
            # Ordenar por version (mas nuevos primero)
            self._modelos_chat.sort(key=lambda x: x.nombre, reverse=True)
            
            logger.info(f"Modelos de chat encontrados: {len(self._modelos_chat)}")
            return self._modelos_chat
            
        except Exception as e:
            logger.error(f"Error listando modelos chat: {e}")
            return []
    
    def listar_modelos_embedding(self) -> List[ModeloInfo]:
        """
        Lista TODOS los modelos disponibles para embeddings.
        """
        if self._modelos_embedding:
            return self._modelos_embedding
        
        try:
            modelos = self.client.models.list()
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                # Incluir todos los modelos que contengan "embed"
                if "embed" in nombre_limpio.lower():
                    if nombre_limpio not in [m.nombre for m in self._modelos_embedding]:
                        descripcion = self._generar_descripcion_embedding(nombre_limpio)
                        self._modelos_embedding.append(ModeloInfo(
                            nombre=nombre_limpio,
                            tipo="embedding",
                            descripcion=descripcion
                        ))
            
            logger.info(f"Modelos de embedding encontrados: {len(self._modelos_embedding)}")
            return self._modelos_embedding
            
        except Exception as e:
            logger.error(f"Error listando modelos embedding: {e}")
            return []
    
    def _generar_descripcion_chat(self, nombre: str) -> str:
        """Genera descripcion para modelo de chat."""
        if "3.1-pro" in nombre:
            return "Ultima generacion Pro, maxima calidad"
        elif "3.1-flash" in nombre:
            return "Ultima generacion Flash, rapido y potente"
        elif "3-pro" in nombre:
            return "Version 3 Pro, alta calidad"
        elif "3-flash" in nombre:
            return "Version 3 Flash, rapido y eficiente"
        elif "2.5-pro" in nombre:
            return "Version 2.5 Pro, excelente calidad"
        elif "2.5-flash" in nombre:
            return "Version 2.5 Flash, rapido y gratuito"
        elif "2.0-pro" in nombre:
            return "Version 2.0 Pro, buena calidad"
        elif "2.0-flash" in nombre:
            return "Version 2.0 Flash, estable y confiable"
        elif "1.5-pro" in nombre:
            return "Version 1.5 Pro, confiable"
        elif "1.5-flash" in nombre:
            return "Version 1.5 Flash, muy estable"
        elif "flash-latest" in nombre:
            return "Ultima version del modelo Flash"
        elif "pro-latest" in nombre:
            return "Ultima version del modelo Pro"
        elif "computer-use" in nombre:
            return "Modelo para uso con computadora"
        else:
            return "Modelo de lenguaje Gemini"
    
    def _generar_descripcion_embedding(self, nombre: str) -> str:
        """Genera descripcion para modelo de embedding."""
        if "embedding-2" in nombre:
            return "Nuevo modelo de embeddings, mejor calidad para RAG"
        elif "embedding-001" in nombre:
            return "Modelo de embeddings estable y confiable"
        else:
            return "Modelo de embeddings"
    
    # ==================== METODOS EXISTENTES ====================
    def validar_api_key(self) -> bool:
        """Valida que la API key sea correcta."""
        try:
            list(self.client.models.list())
            return True
        except Exception as e:
            logger.error(f"Error validando API key: {e}")
            return False
    
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