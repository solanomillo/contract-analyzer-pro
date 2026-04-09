"""
Agente de deteccion de riesgos.
"""

import logging
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class RiskDetectionAgent(BaseAgent):
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        logger.info("Analizando riesgos en el contrato...")
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        Analiza el siguiente texto y detecta clausulas que representen riesgos legales:
        1. Penalizaciones economicas
        2. Rescision unilateral
        3. Renovacion automatica
        4. Exclusividad
        5. Limitacion de responsabilidad
        
        Texto:
        ---
        {texto[:3000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("penalizacion", "rescision", "renovacion_automatica", "exclusividad", "limitacion_responsabilidad")
        - descripcion: string (explicacion clara)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (que deberia hacer la parte)
        
        Si no encuentras nada, devuelve: []
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"RiskDetectionAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Riesgos detectados: {len(hallazgos)}")
        return hallazgos