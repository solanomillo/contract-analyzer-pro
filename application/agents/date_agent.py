"""
Agente de extraccion de fechas.
Identifica fechas criticas en contratos.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class DateExtractionAgent(BaseAgent):
    """
    Agente especializado en extraer fechas importantes.
    
    Detecta:
    - Fechas de vencimiento
    - Fechas de renovacion
    - Plazos legales
    - Fechas de pago
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa el agente de fechas."""
        super().__init__(api_key)
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        """
        Extrae fechas criticas del texto.
        
        Args:
            texto: Texto del contrato
            contexto: Contexto adicional
            
        Returns:
            Lista de hallazgos con fechas
        """
        logger.info("Extrayendo fechas criticas...")
        
        prompt = f"""
        Actua como un abogado especializado en contratos.
        
        Analiza el siguiente texto y extrae TODAS las fechas importantes que podrian
        tener implicaciones legales o comerciales.
        
        Busca:
        1. Fechas de vencimiento del contrato
        2. Fechas de renovacion automatica
        3. Plazos de preaviso para terminacion
        4. Fechas limite para pagos
        5. Fechas de inicio y fin de obligaciones
        
        Texto del contrato:
        ---
        {texto[:3000]}
        ---
        
        Responde SOLO con un array JSON. Cada elemento debe tener:
        - tipo: string ("vencimiento", "renovacion", "plazo_legal", "pago")
        - descripcion: string (que representa esta fecha)
        - riesgo: string ("ALTO" si es critico, "MEDIO" si es importante, "BAJO" si es informativo)
        - texto_relevante: string (la frase exacta con la fecha)
        - recomendacion: string (que accion tomar antes de esa fecha)
        
        Ejemplo:
        [
            {{
                "tipo": "vencimiento",
                "descripcion": "El contrato termina el 31/12/2026",
                "riesgo": "ALTO",
                "texto_relevante": "El presente contrato tendra vigencia hasta el 31 de diciembre de 2026",
                "recomendacion": "Iniciar negociacion de renovacion con 3 meses de anticipacion"
            }}
        ]
        
        Si no encuentras fechas, devuelve un array vacio: []
        """
        
        respuesta = self._call_llm(prompt)
        datos = self._parsear_respuesta_json(respuesta)
        
        hallazgos = []
        for dato in datos:
            hallazgo = self._crear_hallazgo(dato)
            hallazgos.append(hallazgo)
        
        logger.info(f"Fechas extraidas: {len(hallazgos)}")
        return hallazgos
    
    def _extraer_fechas_regex(self, texto: str) -> List[str]:
        """
        Metodo auxiliar para extraer fechas usando regex.
        
        Args:
            texto: Texto a analizar
            
        Returns:
            Lista de fechas encontradas
        """
        patrones = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # DD/MM/YYYY
            r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',  # DD de MES de YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY-MM-DD
        ]
        
        fechas = []
        for patron in patrones:
            encontradas = re.findall(patron, texto, re.IGNORECASE)
            fechas.extend(encontradas)
        
        return list(set(fechas))