"""
Agente base para todos los agentes del sistema.
Define la interfaz comun y funcionalidades compartidas.
"""

import logging
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from infrastructure.llm_clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


@dataclass
class Hallazgo:
    """
    Representa un hallazgo encontrado por un agente.
    
    Attributes:
        tipo: Tipo de hallazgo (penalizacion, rescision, etc.)
        descripcion: Descripcion detallada del hallazgo
        riesgo: Nivel de riesgo (ALTO, MEDIO, BAJO)
        texto_relevante: Texto original donde se encontro
        recomendacion: Recomendacion para el usuario
        ubicacion: Ubicacion en el contrato (opcional)
    """
    tipo: str
    descripcion: str
    riesgo: str
    texto_relevante: str
    recomendacion: str
    ubicacion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el hallazgo a diccionario."""
        return {
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "riesgo": self.riesgo,
            "texto_relevante": self.texto_relevante,
            "recomendacion": self.recomendacion,
            "ubicacion": self.ubicacion
        }


class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = GeminiClient(api_key=api_key)
        self._ultimo_error: Optional[str] = None
        logger.info(f"Inicializando agente: {self.__class__.__name__}")
    
    def get_ultimo_error(self) -> Optional[str]:
        """Retorna el ultimo error ocurrido."""
        return self._ultimo_error
    
    @abstractmethod
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        """
        Analiza el texto y retorna hallazgos.
        
        Args:
            texto: Texto a analizar
            contexto: Contexto adicional (opcional)
            
        Returns:
            Lista de hallazgos encontrados
        """
        pass
    
    def _call_llm(self, prompt: str, modelo: str = "gemini-2.5-flash") -> str:
        """
        Realiza una llamada al LLM de Gemini con manejo de errores.
        
        Args:
            prompt: Prompt para el LLM
            modelo: Modelo a usar
            
        Returns:
            Respuesta del LLM o cadena vacia si hay error
        """
        try:
            response = self.client.generar_contenido(
                prompt=prompt,
                modelo=modelo,
                max_retries=3,
                fallback_modelo="gemini-2.0-flash"
            )
            
            if response is None:
                self._ultimo_error = "El servicio de Gemini no respondio. Intenta de nuevo."
                logger.error(self._ultimo_error)
                return ""
            
            self._ultimo_error = None
            return response
            
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                self._ultimo_error = "Servicio de Gemini saturado. Espera unos minutos o cambia a gemini-2.0-flash en la configuracion."
            elif "quota" in error_msg.lower():
                self._ultimo_error = "Cuota de API agotada. Cambia tu API key."
            elif "invalid" in error_msg.lower():
                self._ultimo_error = "API key invalida. Verifica tu configuracion."
            else:
                self._ultimo_error = f"Error en Gemini: {error_msg[:100]}"
            
            logger.error(f"Error llamando a Gemini: {error_msg}")
            return ""
    
    def _parsear_respuesta_json(self, respuesta: str) -> List[Dict[str, Any]]:
        """
        Parsea la respuesta del LLM a formato JSON.
        
        Args:
            respuesta: Respuesta del LLM
            
        Returns:
            Lista de diccionarios con los hallazgos
        """
        if not respuesta:
            return []
        
        try:
            json_match = re.search(r'\[.*\]', respuesta, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            return []
    
    def _crear_hallazgo(self, datos: Dict[str, Any]) -> Hallazgo:
        """
        Crea un objeto Hallazgo desde un diccionario.
        
        Args:
            datos: Diccionario con los datos del hallazgo
            
        Returns:
            Objeto Hallazgo
        """
        return Hallazgo(
            tipo=datos.get("tipo", "desconocido"),
            descripcion=datos.get("descripcion", ""),
            riesgo=datos.get("riesgo", "MEDIO"),
            texto_relevante=datos.get("texto_relevante", ""),
            recomendacion=datos.get("recomendacion", ""),
            ubicacion=datos.get("ubicacion")
        )