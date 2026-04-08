"""
Servicio unificado de configuracion de la aplicacion.
Centraliza toda la logica de API key, modelos y persistencia.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass, field

from dotenv import load_dotenv
from infrastructure.llm_clients.gemini_client import GeminiClient, ModeloInfo

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Configuracion completa de la aplicacion."""
    api_key: str
    modelo_chat: str
    modelo_embedding: str
    es_valida: bool = False
    modelos_chat_disponibles: List[ModeloInfo] = field(default_factory=list)
    modelos_embedding_disponibles: List[ModeloInfo] = field(default_factory=list)


class ConfigService:
    """
    Servicio centralizado para manejar la configuracion.
    """
    
    def __init__(self, env_path: Path = Path(".env")):
        self.env_path = env_path
        self._client: Optional[GeminiClient] = None
        self._temp_api_key: Optional[str] = None  # API key temporal para validacion
        self._config: Optional[AppConfig] = None
        load_dotenv(env_path)
    
    @property
    def client(self) -> GeminiClient:
        """Obtiene el cliente Gemini (lazy loading)."""
        if self._client is None:
            # Priorizar API key temporal, luego la del .env
            api_key = self._temp_api_key or self.get_api_key()
            if not api_key:
                raise ValueError("No hay API key configurada")
            self._client = GeminiClient(api_key=api_key)
        return self._client
    
    def get_api_key(self) -> Optional[str]:
        """Obtiene la API key actual del .env."""
        return os.getenv("GEMINI_API_KEY")
    
    def has_api_key(self) -> bool:
        """Verifica si hay una API key configurada en .env."""
        api_key = self.get_api_key()
        return bool(api_key and api_key.strip() and api_key != "tu_api_key_aqui")
    
    def validar_api_key(self, api_key: str) -> Tuple[bool, str]:
        """
        Valida una API key.
        
        Args:
            api_key: API key a validar
            
        Returns:
            Tuple[bool, str]: (es_valida, mensaje)
        """
        try:
            # Guardar temporalmente la API key
            self._temp_api_key = api_key
            self._client = None  # Resetear cliente para usar nueva key
            
            client = GeminiClient(api_key=api_key)
            if client.validar_api_key():
                return True, "API key valida"
            else:
                self._temp_api_key = None
                return False, "API key invalida"
        except Exception as e:
            self._temp_api_key = None
            error_msg = str(e).lower()
            if "quota" in error_msg:
                return False, "Cuota de API agotada"
            elif "invalid" in error_msg:
                return False, "API key invalida"
            else:
                return False, f"Error: {error_msg[:100]}"
    
    def guardar_configuracion(self, api_key: str, modelo_chat: str, modelo_embedding: str) -> bool:
        """
        Guarda la configuracion completa en .env.
        
        Args:
            api_key: API key de Gemini
            modelo_chat: Modelo de chat seleccionado
            modelo_embedding: Modelo de embedding seleccionado
            
        Returns:
            bool: True si se guardo correctamente
        """
        try:
            contenido = f"""# Google Gemini API Configuration
GEMINI_API_KEY={api_key}
GEMINI_MODEL={modelo_chat}
GEMINI_EMBEDDING_MODEL={modelo_embedding}

# Application Configuration
VECTOR_DB_PATH=./data/vector_store
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
"""
            self.env_path.write_text(contenido, encoding="utf-8")
            load_dotenv(self.env_path, override=True)
            self._client = None
            self._temp_api_key = None  # Limpiar API key temporal
            self._config = None
            logger.info("Configuracion guardada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error guardando configuracion: {e}")
            return False
    
    def actualizar_api_key(self, nueva_api_key: str) -> bool:
        """
        Actualiza solo la API key, manteniendo los modelos.
        
        Args:
            nueva_api_key: Nueva API key
            
        Returns:
            bool: True si se actualizo correctamente
        """
        config_actual = self.cargar_configuracion()
        if config_actual:
            return self.guardar_configuracion(
                nueva_api_key,
                config_actual.modelo_chat,
                config_actual.modelo_embedding
            )
        return False
    
    def cargar_configuracion(self) -> Optional[AppConfig]:
        """
        Carga la configuracion actual desde .env.
        
        Returns:
            AppConfig o None si no hay configuracion
        """
        if self._config:
            return self._config
        
        api_key = self.get_api_key()
        if not self.has_api_key():
            return None
        
        modelo_chat = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        modelo_embedding = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2-preview")
        
        self._config = AppConfig(
            api_key=api_key,
            modelo_chat=modelo_chat,
            modelo_embedding=modelo_embedding
        )
        
        return self._config
    
    def cargar_modelos_disponibles(self) -> Tuple[List[ModeloInfo], List[ModeloInfo]]:
        """
        Carga los modelos disponibles desde Gemini.
        
        Returns:
            Tuple[List[ModeloInfo], List[ModeloInfo]]: (modelos_chat, modelos_embedding)
        """
        try:
            # Usar el cliente que ya tiene la API key temporal
            modelos_chat = self.client.listar_modelos_chat()
            modelos_embedding = self.client.listar_modelos_embedding()
            return modelos_chat, modelos_embedding
        except Exception as e:
            logger.error(f"Error cargando modelos: {e}")
            return [], []
    
    def verificar_cuota(self) -> Tuple[bool, str]:
        """
        Verifica si la API key actual tiene cuota disponible.
        
        Returns:
            Tuple[bool, str]: (tiene_cuota, mensaje)
        """
        if not self.has_api_key() and not self._temp_api_key:
            return False, "No hay API key configurada"
        
        try:
            response = self.client.client.models.generate_content(
                model="gemini-2.0-flash",
                contents="OK"
            )
            return True, "Cuota disponible"
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "exceeded" in error_msg:
                return False, "Cuota de API agotada"
            return False, f"Error: {error_msg[:100]}"