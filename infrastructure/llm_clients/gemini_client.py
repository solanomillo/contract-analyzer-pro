"""
Cliente para Gemini API con manejo profesional de errores, retry y fallback.
MEJORADO: Incluye caché, optimización de tokens, backoff exponencial.
"""

import logging
import os
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from google import genai
from dotenv import load_dotenv

# Importar nuevos módulos
from infrastructure.cache.response_cache import get_global_cache, ResponseCache
from application.services.token_optimizer import get_token_optimizer, TokenOptimizer

logger = logging.getLogger(__name__)


@dataclass
class ModeloInfo:
    nombre: str
    tipo: str
    descripcion: str


class GeminiClient:
    """
    Cliente profesional para Gemini API.
    MEJORADO: Con caché, optimización de tokens, backoff exponencial.
    """
    
    # Modelos estables por defecto (fallback)
    DEFAULT_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-pro"]
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.modelo_predeterminado = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._client = None
        self._modelos_chat = []
        self._modelos_embedding = []
        self._modelos_validados = set()  # Cache de modelos validados
        
        # Nuevos componentes
        self._cache = get_global_cache()
        self._token_optimizer = get_token_optimizer(self.modelo_predeterminado)
        
        # Configuración de caché por tipo de operación
        self._cache_ttl = {
            "embedding": 86400,      # 24 horas (embeddings no cambian)
            "analysis": 3600,        # 1 hora (análisis de contrato)
            "chat": 1800,            # 30 minutos (conversación)
            "summary": 7200,         # 2 horas (resúmenes)
        }
        
        logger.info(f"GeminiClient inicializado con modelo: {self.modelo_predeterminado}, caché activa")
    
    def update_model(self, model_name: str):
        """Actualiza el modelo dinámicamente (cuando usuario cambia en UI)"""
        if model_name != self.modelo_predeterminado:
            self.modelo_predeterminado = model_name
            self._token_optimizer.update_model(model_name)
            logger.info(f"Modelo actualizado a: {model_name}")
    
    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("API key no proporcionada")
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    def _validar_modelo_existe(self, modelo: str) -> bool:
        """
        Valida si un modelo existe y está disponible.
        Usa caché para no llamar a la API repetidamente.
        """
        if modelo in self._modelos_validados:
            return True
        
        try:
            # Intentar listar modelos para verificar
            modelos = self.client.models.list()
            for m in modelos:
                nombre_limpio = m.name.replace("models/", "")
                if nombre_limpio == modelo:
                    self._modelos_validados.add(modelo)
                    return True
            return False
        except Exception as e:
            logger.warning(f"No se pudo validar modelo {modelo}: {e}")
            # Si no podemos validar, asumimos que existe (fallback)
            return modelo in self.DEFAULT_MODELS
    
    def _calcular_backoff(self, intento: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """
        Calcula tiempo de espera con backoff exponencial y jitter.
        
        Args:
            intento: Número de intento (0-indexado)
            base_delay: Demora base en segundos
            max_delay: Demora máxima en segundos
            
        Returns:
            Segundos a esperar
        """
        import random
        delay = min(base_delay * (2 ** intento), max_delay)
        # Agregar jitter (±20%) para evitar thundering herd
        jitter = delay * 0.2 * random.random()
        return delay + jitter

    def generar_contenido(
        self,
        prompt: str,
        modelo: Optional[str] = None,
        max_retries: int = 3,
        fallback_modelo: str = "gemini-2.0-flash",
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        operation_type: str = "chat"
    ) -> Optional[str]:
        """
        Genera contenido usando Gemini con reintentos, fallback y CACHÉ.
        
        Args:
            prompt: Prompt para el modelo
            modelo: Modelo a usar (si no se especifica, usa el de configuracion)
            max_retries: Numero maximo de reintentos
            fallback_modelo: Modelo alternativo si falla el principal
            use_cache: Si usar caché (default True)
            cache_ttl: TTL específico para esta llamada
            operation_type: Tipo de operación para TTL (chat/analysis/summary)
            
        Returns:
            Texto generado o None si falla
        """
        if modelo is None:
            modelo = self.modelo_predeterminado
        
        # Verificar límites de tokens antes de enviar
        prompt_tokens = self._token_optimizer.count_tokens(prompt)
        if not self._token_optimizer.is_safe_to_send(prompt, buffer_tokens=500):
            logger.warning(f"Prompt excede límite del modelo: {prompt_tokens} tokens")
            # Intentar truncar inteligentemente
            max_safe = self._token_optimizer.get_model_limit() - 1000
            prompt = self._token_optimizer.truncate_to_limit(prompt, max_safe)
            logger.info(f"Prompt truncado a {self._token_optimizer.count_tokens(prompt)} tokens")
        
        # Clave para caché
        cache_key = {
            "prompt": prompt,
            "modelo": modelo,
            "operation_type": operation_type
        }
        
        # Verificar caché
        if use_cache:
            ttl = cache_ttl or self._cache_ttl.get(operation_type, 3600)
            cached_response = self._cache.get(cache_key)
            if cached_response is not None:
                logger.info(f"Cache HIT para modelo {modelo}")
                return cached_response
        
        logger.info(f"Generando contenido con modelo: {modelo}, tokens: {prompt_tokens}")
        
        # Intentar con reintentos y backoff exponencial
        for intento in range(max_retries):
            try:
                logger.debug(f"Intento {intento+1}/{max_retries} - Modelo: {modelo}")
                
                response = self.client.models.generate_content(
                    model=modelo,
                    contents=prompt
                )
                
                if response and response.text:
                    logger.info(f"Éxito con modelo {modelo}")
                    result = response.text
                    
                    # Guardar en caché
                    if use_cache:
                        ttl = cache_ttl or self._cache_ttl.get(operation_type, 3600)
                        self._cache.set(cache_key, result, ttl)
                        logger.debug(f"Respuesta cacheada (TTL: {ttl}s)")
                    
                    # Registrar costo estimado
                    cost_estimate = self._token_optimizer.estimate_cost(prompt, result)
                    logger.debug(f"Costo estimado: ${cost_estimate['total_cost_usd']:.6f} USD")
                    
                    return result
                else:
                    logger.warning(f"Respuesta vacía del modelo {modelo}")
                    
            except Exception as e:
                error_msg = str(e)
                
                # 404 - Modelo no encontrado
                if "404" in error_msg or "not found" in error_msg.lower():
                    logger.error(f"Modelo no encontrado: {modelo}")
                    # Intentar con un modelo por defecto
                    for default_model in self.DEFAULT_MODELS:
                        if default_model != modelo:
                            logger.info(f"Intentando con modelo por defecto: {default_model}")
                            return self.generar_contenido(
                                prompt, default_model, max_retries, fallback_modelo,
                                use_cache, cache_ttl, operation_type
                            )
                    break
                
                # 503 - Servicio no disponible (Gemini saturado)
                elif "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
                    wait_time = self._calcular_backoff(intento)
                    logger.warning(f"Gemini saturado con {modelo} - Esperando {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                
                # 429 - Rate limit
                elif "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    wait_time = self._calcular_backoff(intento, base_delay=2.0)
                    logger.warning(f"Rate limit - Esperando {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                
                # 401 - API Key inválida
                elif "401" in error_msg or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                    logger.error(f"API Key inválida: {error_msg}")
                    raise ValueError("API key inválida")
                
                # Otros errores
                else:
                    logger.error(f"Error inesperado (intento {intento+1}): {error_msg[:200]}")
                    if intento == max_retries - 1:
                        break
                    wait_time = self._calcular_backoff(intento, base_delay=1.0)
                    time.sleep(wait_time)
                    continue
        
        # Fallback final si todo falló
        if fallback_modelo and modelo != fallback_modelo:
            try:
                logger.info(f"Fallback final con modelo: {fallback_modelo}")
                return self.generar_contenido(
                    prompt, fallback_modelo, max_retries, None,
                    use_cache, cache_ttl, operation_type
                )
            except Exception as e:
                logger.error(f"Fallback final falló: {e}")
        
        logger.error("Todos los intentos fallaron")
        return None

    def generar_contenido_con_chunking(
        self,
        prompt: str,
        contexto_largo: str,
        modelo: Optional[str] = None,
        max_chunks: int = 5,
        **kwargs
    ) -> Optional[str]:
        """
        Genera contenido procesando texto largo en chunks.
        Útil para contratos muy extensos.
        
        Args:
            prompt: Prompt principal
            contexto_largo: Texto largo a procesar (ej. contrato completo)
            modelo: Modelo a usar
            max_chunks: Máximo número de chunks a procesar
            **kwargs: Argumentos adicionales para generar_contenido
            
        Returns:
            Respuesta combinada
        """
        if modelo is None:
            modelo = self.modelo_predeterminado
        
        # Dividir contexto largo en chunks
        chunks = self._token_optimizer.chunk_text_intelligent(
            contexto_largo,
            max_tokens=6000,  # Dejar espacio para el prompt
            overlap_tokens=200
        )
        
        if len(chunks) <= max_chunks:
            # Procesar todos los chunks
            all_responses = []
            for i, chunk in enumerate(chunks[:max_chunks]):
                chunk_prompt = f"{prompt}\n\n--- Parte {i+1}/{len(chunks)} ---\n\n{chunk.text}"
                response = self.generar_contenido(chunk_prompt, modelo, **kwargs)
                if response:
                    all_responses.append(response)
            
            if not all_responses:
                return None
            
            # Combinar respuestas
            if len(all_responses) == 1:
                return all_responses[0]
            else:
                combined = "\n\n---\n\n".join(all_responses)
                return combined
        else:
            # Demasiados chunks, usar resumen primero
            logger.warning(f"Demasiados chunks ({len(chunks)}), usando solo primeros {max_chunks}")
            return self.generar_contenido_con_chunking(prompt, contexto_largo, modelo, max_chunks, **kwargs)

    def listar_modelos_chat(self) -> List[ModeloInfo]:
        """
        Lista TODOS los modelos disponibles para chat de Gemini.
        SIN FILTROS - Devuelve todo lo que la API proporciona.
        """
        if self._modelos_chat:
            return self._modelos_chat
        
        try:
            modelos = self.client.models.list()
            
            for modelo in modelos:
                nombre = modelo.name
                nombre_limpio = nombre.replace("models/", "")
                
                # Solo filtrar modelos que NO son de chat (embeddings, audio, etc.)
                # No filtramos por preview/live/latest - eso es decisión del usuario
                if "gemini" in nombre_limpio.lower():
                    excluir = ["embed", "audio", "video", "tts", "imagen", "veo", "robotics"]
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
            # Devolver modelos por defecto si falla la API
            return [ModeloInfo(nombre=m, tipo="chat", descripcion="Modelo por defecto") for m in self.DEFAULT_MODELS]
    
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
        """Genera descripción dinámica para modelos de chat."""
        nombre_lower = nombre.lower()
        
        if "3.1-pro" in nombre_lower:
            return "Última generación Pro, máxima calidad"
        elif "3.1-flash" in nombre_lower:
            return "Última generación Flash, rápido y potente"
        elif "3-pro" in nombre_lower:
            return "Versión 3 Pro, alta calidad"
        elif "3-flash" in nombre_lower:
            return "Versión 3 Flash, rápido y eficiente"
        elif "2.5-pro" in nombre_lower:
            return "Versión 2.5 Pro, excelente calidad"
        elif "2.5-flash" in nombre_lower:
            return "Versión 2.5 Flash, rápido"
        elif "2.0-pro" in nombre_lower:
            return "Versión 2.0 Pro, buena calidad"
        elif "2.0-flash" in nombre_lower:
            return "Versión 2.0 Flash, estable y confiable"
        elif "1.5-pro" in nombre_lower:
            return "Versión 1.5 Pro, confiable"
        elif "1.5-flash" in nombre_lower:
            return "Versión 1.5 Flash, muy estable"
        else:
            return "Modelo de lenguaje Gemini"
    
    def _generar_descripcion_embedding(self, nombre: str) -> str:
        """Genera descripción para modelos de embedding."""
        nombre_lower = nombre.lower()
        
        if "embedding-2" in nombre_lower:
            return "Nuevo modelo de embeddings, mejor calidad para RAG"
        elif "embedding-001" in nombre_lower:
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
    
    def limpiar_cache(self, operation_type: Optional[str] = None):
        """
        Limpia el caché.
        
        Args:
            operation_type: Si se especifica, solo limpia ese tipo (no implementado aún)
        """
        self._cache.clear()
        logger.info("Caché del cliente Gemini limpiado")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché"""
        return self._cache.get_stats()