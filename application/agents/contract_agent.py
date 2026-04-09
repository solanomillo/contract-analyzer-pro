"""
Agente unificado para análisis de contratos.
Maneja tanto preguntas específicas como análisis completos.
"""

import logging
import re
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
        
        Extrae y organiza la información en las siguientes categorías:
        
        1. RIESGOS Y CLAUSULAS PELIGROSAS:
           - Penalizaciones económicas (porcentajes, montos exactos)
           - Rescisión unilateral (condiciones, plazos exactos en días)
           - Renovación automática
           - Limitación de responsabilidad
           - Cláusulas abusivas
        
        2. FECHAS IMPORTANTES (con formato día/mes/año):
           - Fecha de inicio del contrato
           - Fecha de término del contrato
           - Plazos de pago (ej: "del día 1 al día 10 de cada mes")
           - Plazos de preaviso (ej: "30 días")
        
        3. OBLIGACIONES DE LAS PARTES:
           - Montos de pago (cantidad exacta)
           - Plazos de pago
           - Servicios a cargo (luz, agua, gas, etc.)
           - Obligaciones de mantenimiento
           - Restricciones de uso
        
        Para CADA hallazgo, incluye:
        - tipo: string ("penalizacion", "rescision", "fecha_inicio", "fecha_termino", "plazo_pago", "preaviso", "obligacion_pago", "obligacion_servicios", "obligacion_mantenimiento")
        - descripcion: string (explicación CLARA y CONCISA con datos exactos)
        - riesgo: string ("ALTO", "MEDIO", "BAJO")
        - texto_relevante: string (la frase EXACTA del contrato)
        - recomendacion: string (qué debe hacer la parte, con acciones concretas)
        
        IMPORTANTE:
        - Para fechas, escribe el día, mes y año completo
        - Para plazos, escribe el número exacto de días
        - Para montos, escribe la cantidad exacta con símbolo $
        - Para servicios, enumera específicamente cuáles (luz, agua, gas, etc.)
        
        Responde SOLO con un array JSON. Ejemplo:
        [
            {{
                "tipo": "fecha_inicio",
                "descripcion": "El contrato comienza el 01 de enero de 2026",
                "riesgo": "MEDIO",
                "texto_relevante": "comenzando el 01 de enero de 2026",
                "recomendacion": "Preparar documentación necesaria para la fecha de inicio"
            }},
            {{
                "tipo": "plazo_pago",
                "descripcion": "El pago debe realizarse entre el día 1 y el día 10 de cada mes",
                "riesgo": "ALTO",
                "texto_relevante": "El pago deberá realizarse del día 1 al día 10 de cada mes",
                "recomendacion": "Configurar pago automático o recordatorio para no atrasarse"
            }},
            {{
                "tipo": "obligacion_servicios",
                "descripcion": "Los servicios de luz, agua y gas son a cargo del LOCATARIO",
                "riesgo": "MEDIO",
                "texto_relevante": "Los servicios (luz, agua, gas, etc.) estarán a cargo del LOCATARIO",
                "recomendacion": "Solicitar el cambio de titularidad de los servicios a su nombre"
            }}
        ]
        
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