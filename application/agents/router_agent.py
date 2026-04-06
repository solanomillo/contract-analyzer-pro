"""
Agente router que decide que agente usar segun la consulta.
"""

import logging
from typing import Dict, Any, List
from enum import Enum

from application.agents.base_agent import BaseAgent, Hallazgo

logger = logging.getLogger(__name__)


class AgenteTipo(Enum):
    """Tipos de agentes disponibles."""
    RIESGO = "riesgo"
    FECHAS = "fechas"
    OBLIGACIONES = "obligaciones"
    TODOS = "todos"


class RouterAgent(BaseAgent):
    """
    Agente que analiza la consulta y decide que agente usar.
    
    Tambien puede orquestar la ejecucion de multiples agentes.
    """
    
    def __init__(self, api_key: str = None):
        """Inicializa el agente router."""
        super().__init__(api_key)
        self.agentes = {
            AgenteTipo.RIESGO: None,
            AgenteTipo.FECHAS: None,
            AgenteTipo.OBLIGACIONES: None
        }
    
    def registrar_agente(self, tipo: AgenteTipo, agente: BaseAgent):
        """
        Registra un agente en el router.
        
        Args:
            tipo: Tipo de agente
            agente: Instancia del agente
        """
        self.agentes[tipo] = agente
        logger.info(f"Agente registrado: {tipo.value}")
    
    def decidir_agente(self, consulta: str) -> AgenteTipo:
        """
        Decide que agente usar segun la consulta.
        
        Args:
            consulta: Consulta del usuario
            
        Returns:
            Tipo de agente a usar
        """
        consulta_lower = consulta.lower()
        
        # Palabras clave para cada tipo
        palabras_riesgo = ["penalizacion", "multa", "riesgo", "clausula", "rescicion", 
                          "terminacion", "responsabilidad", "exclusividad"]
        
        palabras_fechas = ["fecha", "vencimiento", "plazo", "renovacion", "dias", 
                          "meses", "anios", "termina", "inicia"]
        
        palabras_obligaciones = ["pago", "obligacion", "debe", "abonara", "pagara", 
                                "monto", "precio", "costo", "honorarios"]
        
        # Contar coincidencias
        score_riesgo = sum(1 for p in palabras_riesgo if p in consulta_lower)
        score_fechas = sum(1 for p in palabras_fechas if p in consulta_lower)
        score_obligaciones = sum(1 for p in palabras_obligaciones if p in consulta_lower)
        
        # Si la consulta es general o tiene muchos temas, usar todos
        if consulta_lower in ["analizar", "analizar contrato", "analisis completo", "todos"]:
            return AgenteTipo.TODOS
        
        # Determinar el agente con mayor score
        scores = {
            AgenteTipo.RIESGO: score_riesgo,
            AgenteTipo.FECHAS: score_fechas,
            AgenteTipo.OBLIGACIONES: score_obligaciones
        }
        
        mejor_agente = max(scores, key=scores.get)
        
        # Si el mejor score es 0, usar todos
        if scores[mejor_agente] == 0:
            return AgenteTipo.TODOS
        
        logger.info(f"Consulta: '{consulta}' -> Agente: {mejor_agente.value}")
        return mejor_agente
    
    def ejecutar_agente(self, tipo: AgenteTipo, texto: str) -> List[Hallazgo]:
        """
        Ejecuta un agente especifico.
        
        Args:
            tipo: Tipo de agente a ejecutar
            texto: Texto a analizar
            
        Returns:
            Lista de hallazgos
        """
        agente = self.agentes.get(tipo)
        if not agente:
            logger.warning(f"Agente no registrado: {tipo.value}")
            return []
        
        return agente.analizar(texto)
    
    def ejecutar_todos(self, texto: str) -> Dict[str, List[Hallazgo]]:
        """
        Ejecuta todos los agentes registrados.
        
        Args:
            texto: Texto a analizar
            
        Returns:
            Diccionario con resultados por tipo
        """
        resultados = {}
        
        for tipo, agente in self.agentes.items():
            if agente:
                try:
                    hallazgos = agente.analizar(texto)
                    resultados[tipo.value] = hallazgos
                    logger.info(f"Agente {tipo.value} completo: {len(hallazgos)} hallazgos")
                except Exception as e:
                    logger.error(f"Error en agente {tipo.value}: {e}")
                    resultados[tipo.value] = []
        
        return resultados
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        """
        Metodo principal que analiza segun la consulta.
        
        Args:
            texto: Texto a analizar
            contexto: Consulta o contexto (opcional)
            
        Returns:
            Lista de hallazgos
        """
        consulta = contexto or "analizar"
        tipo_agente = self.decidir_agente(consulta)
        
        if tipo_agente == AgenteTipo.TODOS:
            # Ejecutar todos y combinar resultados
            todos_resultados = self.ejecutar_todos(texto)
            hallazgos = []
            for resultados in todos_resultados.values():
                hallazgos.extend(resultados)
            return hallazgos
        else:
            return self.ejecutar_agente(tipo_agente, texto)