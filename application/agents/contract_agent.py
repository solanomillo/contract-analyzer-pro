"""
Agente unificado para análisis de contratos.
Maneja tanto preguntas específicas como análisis completos.
"""

import logging
from typing import List, Optional
from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class ContractAgent(BaseAgent):
    """
    Agente unificado que maneja:
    - Preguntas específicas (respuesta concreta)
    - Análisis completo (respuesta detallada)
    """
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        """
        Analiza el contrato según el contexto.
        
        Args:
            texto: Texto del contrato
            contexto: Puede ser:
                - Una pregunta específica del usuario
                - "analisis_completo" para análisis detallado
        """
        es_analisis_completo = contexto == "analisis_completo"
        
        if es_analisis_completo:
            return self._analisis_completo(texto)
        else:
            return self._respuesta_especifica(texto, contexto)
    
    def _respuesta_especifica(self, texto: str, pregunta: str) -> List[Hallazgo]:
        """Responde una pregunta específica de forma concreta."""
        logger.info(f"Respondiendo pregunta específica: {pregunta}")
        
        prompt = f"""
        Actúa como un asistente legal experto en contratos.
        
        El usuario pregunta: "{pregunta}"
        
        Basado en este contrato, responde de forma CONCISA y DIRECTA.
        Usa SOLO la información del contrato. No inventes información.
        Responde en 1-2 líneas máximo. No des explicaciones largas.
        
        Contrato:
        ---
        {texto[:4000]}
        ---
        
        Responde SOLO con un array JSON con UN SOLO elemento:
        [
            {{
                "tipo": "respuesta",
                "descripcion": "tu respuesta concreta aqui",
                "riesgo": "MEDIO",
                "texto_relevante": "la frase del contrato que respalda tu respuesta",
                "recomendacion": ""
            }}
        ]
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            return [self._crear_hallazgo_error("No se pudo procesar la pregunta")]
        
        datos = self._parsear_respuesta_json(respuesta)
        
        if not datos:
            return [self._crear_hallazgo_error("No se encontró información relevante")]
        
        hallazgos = [self._crear_hallazgo(d) for d in datos[:1]]
        return hallazgos
    
    def _analisis_completo(self, texto: str) -> List[Hallazgo]:
        """Realiza un análisis completo y detallado del contrato."""
        logger.info("Realizando análisis completo del contrato")
        
        prompt = f"""
        Actúa como un abogado experto en derecho contractual.
        
        Realiza un análisis COMPLETO y DETALLADO de este contrato.
        
        Contrato:
        ---
        {texto[:5000]}
        ---
        
        Extrae y clasifica:
        
        1. RIESGOS Y CLAUSULAS PELIGROSAS:
           - Penalizaciones económicas (porcentajes, montos)
           - Rescisión unilateral (condiciones, plazos)
           - Renovación automática
           - Limitación de responsabilidad
        
        2. FECHAS IMPORTANTES:
           - Fecha de inicio
           - Fecha de término
           - Plazos de pago
           - Plazos de preaviso
        
        3. OBLIGACIONES:
           - Montos de pago
           - Plazos de pago
           - Obligaciones de las partes
        
        Responde SOLO con un array JSON. Cada hallazgo debe tener:
        - tipo: string ("penalizacion", "rescision", "fecha", "pago", "obligacion")
        - descripcion: string (explicación clara)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase exacta)
        - recomendacion: string (qué hacer)
        
        Devuelve tantos elementos como hallazgos encuentres.
        Si no encuentras algo, no lo incluyas.
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            return [self._crear_hallazgo_error("Error en el análisis")]
        
        datos = self._parsear_respuesta_json(respuesta)
        hallazgos = [self._crear_hallazgo(d) for d in datos]
        
        logger.info(f"Análisis completo generado: {len(hallazgos)} hallazgos")
        return hallazgos
    
    def _crear_hallazgo_error(self, mensaje: str) -> Hallazgo:
        """Crea un hallazgo de error."""
        return Hallazgo(
            tipo="error",
            descripcion=mensaje,
            riesgo="ALTO",
            texto_relevante="",
            recomendacion="Intenta nuevamente o reformula tu pregunta"
        )