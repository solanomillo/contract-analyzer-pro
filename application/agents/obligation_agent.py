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
        
        # Usar el contexto (pregunta del usuario) para enfocar la respuesta
        pregunta = contexto if contexto else "extrae todas las obligaciones"
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        El usuario hizo la siguiente pregunta: "{pregunta}"
        
        Analiza el contrato y responde SOLO lo que se pregunta, de forma CONCISA y ESPECIFICA.
        
        Texto del contrato:
        ---
        {texto[:3000]}
        ---
        
        IMPORTANTE: 
        - Si pregunta por el MONTO del pago, responde SOLO el monto exacto.
        - Si pregunta por la FORMA de pago, responde SOLO los plazos.
        - Si pregunta por las OBLIGACIONES, responde SOLO las obligaciones especificas.
        - NO devuelvas informacion que no sea relevante a la pregunta.
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("pago", "plazo", "obligacion")
        - descripcion: string (respuesta CONCISA a la pregunta)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (opcional, solo si es relevante)
        
        Ejemplo para "cuanto es el pago mensual?":
        [
            {{
                "tipo": "pago",
                "descripcion": "$50.000 mensuales",
                "riesgo": "MEDIO",
                "texto_relevante": "El LOCATARIO abonará la suma de $50.000 mensuales",
                "recomendacion": ""
            }}
        ]
        
        Devuelve SOLO 1 elemento si la pregunta es especifica.
        Devuelve varios SOLO si la pregunta es general como "que obligaciones tengo?".
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"ObligationAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        
        # Limitar a maximo 3 hallazgos para preguntas especificas
        if contexto and len(datos) > 3:
            logger.info(f"Limitando hallazgos de {len(datos)} a 3 para pregunta especifica")
            datos = datos[:3]
        
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Obligaciones detectadas: {len(hallazgos)}")
        return hallazgos