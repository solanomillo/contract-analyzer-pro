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
        
        pregunta = contexto if contexto else "detecta todas las clausulas de riesgo"
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        El usuario hizo la siguiente pregunta: "{pregunta}"
        
        Analiza el contrato y responde SOLO lo que se pregunta.
        
        Texto del contrato:
        ---
        {texto[:3000]}
        ---
        
        IMPORTANTE:
        - Si pregunta por PENALIZACIONES, responde SOLO el porcentaje o monto.
        - Si pregunta por RESCISION, responde SOLO los dias de aviso.
        - NO devuelvas riesgos que no sean relevantes a la pregunta.
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("penalizacion", "rescision")
        - descripcion: string (respuesta CONCISA)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (opcional)
        
        Ejemplo para "cual es la penalizacion?":
        [
            {{
                "tipo": "penalizacion",
                "descripcion": "30% del valor total del contrato",
                "riesgo": "ALTO",
                "texto_relevante": "multa del 30% del valor total",
                "recomendacion": ""
            }}
        ]
        
        Devuelve SOLO 1 elemento si la pregunta es especifica.
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"RiskDetectionAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        
        if contexto and len(datos) > 2:
            datos = datos[:2]
        
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Riesgos detectados: {len(hallazgos)}")
        return hallazgos