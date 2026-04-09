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
        
        pregunta = contexto if contexto else "extrae todas las fechas importantes"
        
        prompt = f"""
        Actua como un abogado especializado en contratos.
        
        El usuario hizo la siguiente pregunta: "{pregunta}"
        
        Analiza el contrato y responde SOLO lo que se pregunta, de forma CONCISA.
        
        Texto del contrato:
        ---
        {texto[:3000]}
        ---
        
        IMPORTANTE:
        - Si pregunta por la FECHA DE INICIO, responde SOLO esa fecha.
        - Si pregunta por la FECHA DE TERMINO, responde SOLO esa fecha.
        - Si pregunta por PLAZOS, responde SOLO los plazos.
        - NO devuelvas fechas que no sean relevantes a la pregunta.
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("inicio", "termino", "plazo_pago", "preaviso")
        - descripcion: string (la fecha o plazo de forma clara)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (opcional)
        
        Ejemplo para "cuando termina el contrato?":
        [
            {{
                "tipo": "termino",
                "descripcion": "31 de diciembre de 2026",
                "riesgo": "MEDIO",
                "texto_relevante": "finalizando el 31 de diciembre de 2026",
                "recomendacion": ""
            }}
        ]
        
        Devuelve SOLO 1 elemento si la pregunta es especifica.
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"DateExtractionAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        
        if contexto and len(datos) > 2:
            datos = datos[:2]
        
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Fechas extraidas: {len(hallazgos)}")
        return hallazgos