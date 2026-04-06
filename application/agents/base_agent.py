"""
Agente base para todos los agentes del sistema.
Define la interfaz comun y funcionalidades compartidas.
"""

import logging
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
    
    Proporciona funcionalidad comun como:
    - Cliente Gemini para llamadas a LLM
    - Metodos de formateo de prompts
    - Parseo de respuestas
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el agente base.
        
        Args:
            api_key: API key de Gemini (opcional)
        """
        self.client = GeminiClient(api_key=api_key)
        logger.info(f"Inicializando agente: {self.__class__.__name__}")
    
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
    
    def _call_llm(self, prompt: str) -> str:
        """
        Realiza una llamada al LLM de Gemini.
        
        Args:
            prompt: Prompt para el LLM
            
        Returns:
            Respuesta del LLM
        """
        try:
            response = self.client.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Error llamando a Gemini: {e}")
            return ""
    
    def _parsear_respuesta_json(self, respuesta: str) -> List[Dict[str, Any]]:
        """
        Parsea la respuesta del LLM a formato JSON.
        
        Args:
            respuesta: Respuesta del LLM
            
        Returns:
            Lista de diccionarios con los hallazgos
        """
        import json
        import re
        
        try:
            # Intentar extraer JSON de la respuesta
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