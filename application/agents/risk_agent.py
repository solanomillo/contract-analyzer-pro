"""
Agente de deteccion de riesgos.
Identifica clausulas peligrosas en contratos.
"""

import logging
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class RiskDetectionAgent(BaseAgent):
    """
    Agente especializado en detectar clausulas de riesgo.
    
    Detecta:
    - Penalizaciones economicas
    - Rescision unilateral
    - Clausulas abusivas
    - Renovacion automatica
    - Exclusividad
    - Limitacion de responsabilidad
    - Multas
    - Intereses elevados
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa el agente de riesgos."""
        super().__init__(api_key)
        self.tipos_riesgo = [
            "penalizacion", "rescision_unilateral", "clausula_abusiva",
            "renovacion_automatica", "exclusividad", "limitacion_responsabilidad",
            "multa", "interes_elevado"
        ]
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        """
        Analiza el texto en busca de clausulas de riesgo.
        
        Args:
            texto: Texto del contrato a analizar
            contexto: Contexto adicional (no usado)
            
        Returns:
            Lista de hallazgos de riesgo
        """
        logger.info("Analizando riesgos en el contrato...")
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        Analiza el siguiente texto de un contrato y detecta clausulas que representen 
        riesgos legales para la parte que recibe el servicio.
        
        Busca especificamente:
        1. PENALIZACIONES: Multas por incumplimiento, penalizaciones economicas
        2. RESCISION UNILATERAL: Capacidad de una parte de terminar el contrato sin justificacion
        3. CLAUSULAS ABUSIVAS: Condiciones desproporcionadas o injustas
        4. RENOVACION AUTOMATICA: Renovacion sin consentimiento explicito
        5. EXCLUSIVIDAD: Prohibicion de trabajar con terceros
        6. LIMITACION DE RESPONSABILIDAD: Limites bajos de responsabilidad
        7. MULTAS: Penalizaciones especificas
        8. INTERESES ELEVADOS: Tasas de interes por mora excesivas
        
        Texto del contrato:
        ---
        {texto[:3000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string (el tipo de riesgo)
        - descripcion: string (explicacion clara del riesgo)
        - riesgo: string ("ALTO", "MEDIO", o "BAJO")
        - texto_relevante: string (la frase exacta donde se encontro)
        - recomendacion: string (que deberia hacer la parte)
        
        Ejemplo:
        [
            {{
                "tipo": "penalizacion",
                "descripcion": "Multa del 25% por cancelacion anticipada",
                "riesgo": "ALTO",
                "texto_relevante": "En caso de cancelacion, se aplicara una penalizacion del 25%",
                "recomendacion": "Negociar una penalizacion menor o escalonada"
            }}
        ]
        
        Si no encuentras nada, devuelve un array vacio: []
        """
        
        respuesta = self._call_llm(prompt)
        
        if not respuesta:
            logger.warning(f"RiskDetectionAgent: {self._ultimo_error}")
            return []
        
        datos = self._parsear_respuesta_json(respuesta)
        
        hallazgos = []
        for dato in datos:
            hallazgo = self._crear_hallazgo(dato)
            hallazgos.append(hallazgo)
        
        logger.info(f"Riesgos detectados: {len(hallazgos)}")
        return hallazgos