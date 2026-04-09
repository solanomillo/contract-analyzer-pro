"""
Agente para analisis completo del contrato.
"""

import logging
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class CompleteAnalysisAgent(BaseAgent):
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        logger.info("CompleteAnalysisAgent: analisis completo...")
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        Analiza el siguiente contrato y extrae TODA la informacion relevante:
        
        1. RIESGOS: Penalizaciones, rescision unilateral, renovacion automatica, exclusividad
        2. FECHAS: Inicio, termino, plazos de pago, preaviso
        3. OBLIGACIONES: Montos, plazos de pago, obligaciones de mantenimiento
        
        Texto:
        ---
        {texto[:5000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("penalizacion", "rescision", "fecha", "pago", "obligacion")
        - descripcion: string (explicacion clara)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (que deberia hacer la parte)
        
        Si no encuentras informacion, devuelve: []
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"CompleteAnalysisAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Analisis completo generado: {len(hallazgos)} hallazgos")
        return hallazgos