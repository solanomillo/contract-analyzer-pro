"""
Agente de deteccion de obligaciones.
"""

import logging
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class ObligationAgent(BaseAgent):
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        logger.info("Detectando obligaciones...")
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        Analiza el siguiente texto y extrae las obligaciones:
        1. Montos de pago
        2. Plazos de pago
        3. Obligaciones de mantenimiento
        4. Obligaciones de las partes
        
        Texto:
        ---
        {texto[:3000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("pago", "plazo", "obligacion")
        - descripcion: string (que obligacion se debe cumplir)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (como cumplir con la obligacion)
        
        IMPORTANTE: Para preguntas sobre cuanto pagar, enfocate en el monto exacto.
        
        Si no encuentras obligaciones, devuelve: []
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"ObligationAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Obligaciones detectadas: {len(hallazgos)}")
        return hallazgos