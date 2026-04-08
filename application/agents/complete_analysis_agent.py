"""
Agente para analisis completo del contrato en UNA sola llamada a Gemini.
"""

import logging
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class CompleteAnalysisAgent(BaseAgent):
    """
    Agente que realiza un analisis completo del contrato en UNA sola llamada.
    """
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        """
        Analiza el contrato completo y extrae: riesgos, fechas y obligaciones.
        
        UNA sola llamada a Gemini para todo el analisis.
        """
        logger.info("CompleteAnalysisAgent: analisis completo en una sola llamada...")
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        Analiza el siguiente contrato y extrae TODA la informacion relevante:
        
        1. RIESGOS Y CLAUSULAS PELIGROSAS:
           - Penalizaciones economicas
           - Rescision unilateral
           - Renovacion automatica
           - Exclusividad
           - Limitacion de responsabilidad
           - Clausulas abusivas
        
        2. FECHAS IMPORTANTES:
           - Fecha de inicio
           - Fecha de termino
           - Plazos de pago
           - Fechas de renovacion
           - Plazos de preaviso
        
        3. OBLIGACIONES:
           - Montos de pago
           - Plazos de pago
           - Obligaciones de mantenimiento
           - Obligaciones de las partes
        
        Texto del contrato:
        ---
        {texto[:5000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("penalizacion", "rescision", "fecha", "pago", "obligacion", etc.)
        - descripcion: string (explicacion clara del hallazgo)
        - riesgo: string ("ALTO", "MEDIO", o "BAJO")
        - texto_relevante: string (la frase exacta donde se encontro)
        - recomendacion: string (que deberia hacer la parte)
        
        Ejemplo:
        [
            {{
                "tipo": "penalizacion",
                "descripcion": "Multa del 30% por incumplimiento",
                "riesgo": "ALTO",
                "texto_relevante": "En caso de incumplimiento, multa del 30%",
                "recomendacion": "Negociar una penalizacion menor"
            }},
            {{
                "tipo": "fecha",
                "descripcion": "Contrato vigente desde 01/01/2026 hasta 31/12/2026",
                "riesgo": "MEDIO",
                "texto_relevante": "Duracion de 12 meses desde 01/01/2026",
                "recomendacion": "Marcar fecha de renovacion en calendario"
            }}
        ]
        
        Si no encuentras informacion para alguna categoria, simplemente no la incluyas.
        """
        
        respuesta = self._call_llm(prompt)
        datos = self._parsear_respuesta_json(respuesta)
        
        hallazgos = []
        for dato in datos:
            hallazgo = self._crear_hallazgo(dato)
            hallazgos.append(hallazgo)
        
        logger.info(f"Analisis completo generado: {len(hallazgos)} hallazgos")
        return hallazgos