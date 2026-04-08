"""
Cliente para Gemini API con manejo profesional de errores, retry y fallback.
"""

import logging
import os
import time
from typing import List, Optional
from dataclasses import dataclass

from google import genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class ModeloInfo:
    nombre: str
    tipo: str
    descripcion: str


class GeminiClient:
    """
    Cliente profesional para Gemini API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.modelo_predeterminado = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = None
        self._modelos_chat = []
        self._modelos_embedding = []
        logger.info(f"GeminiClient inicializado con modelo predeterminado: {self.modelo_predeterminado}")
    
    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("API key no proporcionada")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generar_contenido(
        self,
        prompt: str,
        modelo: Optional[str] = None,
        max_retries: int = 3,
        fallback_modelo: str = "gemini-2.0-flash"
    ) -> Optional[str]:
        """
        Genera contenido usando Gemini con reintentos y fallback.
        
        Args:
            prompt: Prompt para el modelo
            modelo: Modelo a usar (si no se especifica, usa el de configuracion)
            max_retries: Numero maximo de reintentos
            fallback_modelo: Modelo alternativo si falla el principal
            
        Returns:
            Texto generado o None si falla
        """
        if modelo is None:
            modelo = self.modelo_predeterminado
        
        logger.info(f"Usando modelo: {modelo}")
        
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
                    logger.warning(f"Gemini saturado con modelo {modelo} (intento {intento+1}/{max_retries}) - Esperando {wait_time}s")
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
                
                elif "404" in error_msg or "not found" in error_msg.lower():
                    logger.error(f"Modelo no encontrado: {modelo}")
                    if fallback_modelo and modelo != fallback_modelo:
                        logger.info(f"Intentando con modelo alternativo: {fallback_modelo}")
                        return self.generar_contenido(prompt, fallback_modelo, max_retries, None)
                    raise ValueError(f"Modelo no disponible: {modelo}")
                
                else:
                    logger.error(f"Error inesperado en intento {intento+1}: {error_msg}")
                    if intento == max_retries - 1:
                        break
                    time.sleep(2)
                    continue
        
        if fallback_modelo and modelo != fallback_modelo:
            try:
                logger.info(f"Intentando fallback con modelo: {fallback_modelo}")
                return self.generar_contenido(prompt, fallback_modelo, max_retries, None)
            except Exception as e:
                logger.error(f"Fallback fallo: {e}")
        
        logger.error("Todos los intentos fallaron")
        return None

    def listar_modelos_chat(self) -> List[ModeloInfo]:
        """Lista TODOS los modelos disponibles para chat de Gemini."""
        if self._modelos_chat:
            return self._modelos_chat
        
        try:
            modelos = self.client.models.list()
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                if "gemini" in nombre_limpio.lower():
                    excluir = ["embed", "image", "audio", "video", "tts", "imagen", "veo", "robotics"]
                    if not any(x in nombre_limpio.lower() for x in excluir):
                        if nombre_limpio not in [m.nombre for m in self._modelos_chat]:
                            descripcion = self._generar_descripcion_chat(nombre_limpio)
                            self._modelos_chat.append(ModeloInfo(
                                nombre=nombre_limpio,
                                tipo="chat",
                                descripcion=descripcion
                            ))
            
            self._modelos_chat.sort(key=lambda x: x.nombre, reverse=True)
            logger.info(f"Modelos de chat encontrados: {len(self._modelos_chat)}")
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
            
            logger.info(f"Modelos de embedding encontrados: {len(self._modelos_embedding)}")
            return self._modelos_embedding
            
        except Exception as e:
            logger.error(f"Error listando modelos embedding: {e}")
            return []
    
    def _generar_descripcion_chat(self, nombre: str) -> str:
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
        else:
            return "Modelo de lenguaje Gemini"
    
    def _generar_descripcion_embedding(self, nombre: str) -> str:
        if "embedding-2" in nombre:
            return "Nuevo modelo de embeddings, mejor calidad para RAG"
        elif "embedding-001" in nombre:
            return "Modelo de embeddings estable y confiable"
        else:
            return "Modelo de embeddings"
    
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