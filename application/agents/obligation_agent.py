"""
Agente de deteccion de obligaciones.
Identifica obligaciones de pago y condiciones contractuales.
"""

import logging
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class ObligationAgent(BaseAgent):
    """
    Agente especializado en detectar obligaciones.
    
    Detecta:
    - Obligaciones de pago
    - Plazos de pago
    - Condiciones para pagos
    - Obligaciones de cumplimiento
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa el agente de obligaciones."""
        super().__init__(api_key)
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        """
        Detecta obligaciones en el contrato.
        
        Args:
            texto: Texto del contrato
            contexto: Contexto adicional
            
        Returns:
            Lista de hallazgos con obligaciones
        """
        logger.info("Detectando obligaciones...")
        
        prompt = f"""
        Actua como un abogado experto en derecho contractual.
        
        Analiza el siguiente texto y extrae TODAS las obligaciones que una de las partes
        debe cumplir, especialmente las relacionadas con pagos y plazos.
        
        Busca:
        1. Montos de pago (cantidades exactas)
        2. Plazos de pago (dias, fechas)
        3. Formas de pago (transferencia, cheque, etc.)
        4. Condiciones para pagos (hitos, entregables)
        5. Obligaciones de cumplimiento especificas
        
        Texto del contrato:
        ---
        {texto[:3000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("pago", "plazo", "condicion", "cumplimiento")
        - descripcion: string (que obligacion se debe cumplir)
        - riesgo: string ("ALTO" si es financiero critico, "MEDIO" si es importante, "BAJO" si es informativo)
        - texto_relevante: string (la frase exacta de la obligacion)
        - recomendacion: string (como cumplir con la obligacion)
        
        Ejemplo:
        [
            {{
                "tipo": "pago",
                "descripcion": "Pago de 50,000 euros al firmar el contrato",
                "riesgo": "ALTO",
                "texto_relevante": "El CLIENTE abonara la cantidad de 50.000 euros en el momento de la firma",
                "recomendacion": "Verificar que el servicio este incluido antes de pagar"
            }}
        ]
        
        Si no encuentras obligaciones, devuelve un array vacio: []
        """
        
        respuesta = self._call_llm(prompt)
        datos = self._parsear_respuesta_json(respuesta)
        
        hallazgos = []
        for dato in datos:
            hallazgo = self._crear_hallazgo(dato)
            hallazgos.append(hallazgo)
        
        logger.info(f"Obligaciones detectadas: {len(hallazgos)}")
        return hallazgos