"""
Agente de extraccion de fechas.
"""

import logging
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class DateExtractionAgent(BaseAgent):
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        logger.info("Extrayendo fechas criticas...")
        
        prompt = f"""
        Actua como un abogado especializado en contratos.
        
        Analiza el siguiente texto y extrae las fechas IMPORTANTES:
        1. Fecha de inicio del contrato
        2. Fecha de termino del contrato
        3. Plazos de pago
        4. Plazos de preaviso
        
        Texto:
        ---
        {texto[:3000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("inicio", "termino", "plazo_pago", "preaviso")
        - descripcion: string (la fecha o plazo de forma clara)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (que accion tomar)
        
        Si no encuentras fechas, devuelve: []
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"DateExtractionAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Fechas extraidas: {len(hallazgos)}")
        return hallazgos