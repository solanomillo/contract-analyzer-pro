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
        
        Analiza el contrato y responde SOLO lo que se pregunta, de forma CONCISA.
        
        Texto del contrato:
        ---
        {texto[:3000]}
        ---
        
        REGLAS ESTRICTAS:
        1. Si pregunta "pueden rescindir el contrato?" -> Responde SOLO si se puede rescindir y con cuantos dias.
        2. Si pregunta "cual es la penalizacion?" -> Responde SOLO el porcentaje de la multa.
        3. Si pregunta "de cuanto es la multa?" -> Responde SOLO el porcentaje.
        4. NO incluyas informacion sobre penalizaciones si la pregunta es sobre rescision.
        5. NO incluyas informacion sobre rescision si la pregunta es sobre penalizaciones.
        6. Devuelve SOLO 1 elemento, el mas relevante a la pregunta.
        
        Responde SOLO con un array JSON de UN SOLO elemento:
        [
            {{
                "tipo": string ("penalizacion" o "rescision"),
                "descripcion": string (respuesta CONCISA a la pregunta),
                "riesgo": string ("ALTO" o "MEDIO" o "BAJO"),
                "texto_relevante": string (la frase exacta del contrato),
                "recomendacion": string (opcional, solo si es necesario)
            }}
        ]
        
        Ejemplos:
        
        Pregunta: "pueden rescindir el contrato?"
        Respuesta:
        [{{
            "tipo": "rescision",
            "descripcion": "Si, cualquiera de las partes puede rescindir con 30 dias de aviso",
            "riesgo": "MEDIO",
            "texto_relevante": "Cualquiera de las partes podra rescindir el contrato con previo aviso de 30 dias",
            "recomendacion": "Dar aviso por escrito con 30 dias de anticipacion"
        }}]
        
        Pregunta: "cual es la penalizacion?"
        Respuesta:
        [{{
            "tipo": "penalizacion",
            "descripcion": "30% del valor total del contrato",
            "riesgo": "ALTO",
            "texto_relevante": "multa del 30% del valor total del contrato",
            "recomendacion": ""
        }}]
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"RiskDetectionAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        
        # Limitar a 1 elemento para preguntas especificas
        if contexto and len(datos) > 1:
            logger.info(f"Limitando hallazgos de {len(datos)} a 1 para pregunta especifica")
            datos = datos[:1]
        
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Riesgos detectados: {len(hallazgos)}")
        return hallazgos