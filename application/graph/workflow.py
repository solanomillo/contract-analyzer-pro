"""
Workflow de agentes usando LangGraph.
Orquesta la ejecucion de multiples agentes para analizar contratos.
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

from application.agents.base_agent import Hallazgo
from application.agents.risk_agent import RiskDetectionAgent
from application.agents.date_agent import DateExtractionAgent
from application.agents.obligation_agent import ObligationAgent
from application.agents.router_agent import RouterAgent, AgenteTipo

logger = logging.getLogger(__name__)


class EstadoAnalisis(TypedDict):
    """
    Estado del workflow de analisis.
    
    Attributes:
        texto: Texto del contrato a analizar
        consulta: Consulta del usuario (opcional)
        hallazgos_riesgo: Hallazgos del agente de riesgos
        hallazgos_fechas: Hallazgos del agente de fechas
        hallazgos_obligaciones: Hallazgos del agente de obligaciones
        resultado_final: Resultado combinado del analisis
    """
    texto: str
    consulta: Optional[str]
    hallazgos_riesgo: List[Dict[str, Any]]
    hallazgos_fechas: List[Dict[str, Any]]
    hallazgos_obligaciones: List[Dict[str, Any]]
    resultado_final: str


class AnalisisWorkflow:
    """
    Workflow para analisis de contratos usando LangGraph.
    
    Orquesta la ejecucion de los agentes y combina los resultados.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el workflow.
        
        Args:
            api_key: API key de Gemini
        """
        self.api_key = api_key
        self.router = RouterAgent(api_key=api_key)
        
        # Registrar agentes
        self.router.registrar_agente(AgenteTipo.RIESGO, RiskDetectionAgent(api_key=api_key))
        self.router.registrar_agente(AgenteTipo.FECHAS, DateExtractionAgent(api_key=api_key))
        self.router.registrar_agente(AgenteTipo.OBLIGACIONES, ObligationAgent(api_key=api_key))
        
        logger.info("Workflow de analisis inicializado")
    
    def analizar_completo(self, texto: str) -> Dict[str, Any]:
        """
        Analiza el contrato completo con todos los agentes.
        
        Args:
            texto: Texto del contrato
            
        Returns:
            Diccionario con todos los hallazgos
        """
        logger.info("Iniciando analisis completo del contrato...")
        
        # Ejecutar todos los agentes
        resultados = self.router.ejecutar_todos(texto)
        
        # Clasificar por nivel de riesgo
        riesgos_altos = []
        riesgos_medios = []
        riesgos_bajos = []
        
        for tipo, hallazgos in resultados.items():
            for hallazgo in hallazgos:
                if hallazgo.riesgo == "ALTO":
                    riesgos_altos.append(hallazgo.to_dict())
                elif hallazgo.riesgo == "MEDIO":
                    riesgos_medios.append(hallazgo.to_dict())
                else:
                    riesgos_bajos.append(hallazgo.to_dict())
        
        # Generar resumen
        resumen = self._generar_resumen(riesgos_altos, riesgos_medios, riesgos_bajos)
        
        return {
            "hallazgos_riesgo": [h.to_dict() for h in resultados.get("riesgo", [])],
            "hallazgos_fechas": [h.to_dict() for h in resultados.get("fechas", [])],
            "hallazgos_obligaciones": [h.to_dict() for h in resultados.get("obligaciones", [])],
            "riesgos_altos": riesgos_altos,
            "riesgos_medios": riesgos_medios,
            "riesgos_bajos": riesgos_bajos,
            "total_hallazgos": sum(len(h) for h in resultados.values()),
            "resumen": resumen
        }
    
    def analizar_por_consulta(self, texto: str, consulta: str) -> Dict[str, Any]:
        """
        Analiza el contrato segun una consulta especifica.
        
        Args:
            texto: Texto del contrato
            consulta: Consulta del usuario
            
        Returns:
            Diccionario con los hallazgos relevantes
        """
        logger.info(f"Analizando contrato por consulta: {consulta}")
        
        # Decidir que agente usar
        tipo_agente = self.router.decidir_agente(consulta)
        
        if tipo_agente == AgenteTipo.TODOS:
            return self.analizar_completo(texto)
        
        # Ejecutar el agente especifico
        hallazgos = self.router.ejecutar_agente(tipo_agente, texto)
        
        # Clasificar resultados
        riesgos_altos = [h.to_dict() for h in hallazgos if h.riesgo == "ALTO"]
        riesgos_medios = [h.to_dict() for h in hallazgos if h.riesgo == "MEDIO"]
        riesgos_bajos = [h.to_dict() for h in hallazgos if h.riesgo == "BAJO"]
        
        return {
            "tipo_analisis": tipo_agente.value,
            "consulta": consulta,
            "hallazgos": [h.to_dict() for h in hallazgos],
            "riesgos_altos": riesgos_altos,
            "riesgos_medios": riesgos_medios,
            "riesgos_bajos": riesgos_bajos,
            "total_hallazgos": len(hallazgos),
            "resumen": self._generar_resumen(riesgos_altos, riesgos_medios, riesgos_bajos)
        }
    
    def _generar_resumen(self, altos: List, medios: List, bajos: List) -> str:
        """
        Genera un resumen del analisis.
        
        Args:
            altos: Riesgos altos
            medios: Riesgos medios
            bajos: Riesgos bajos
            
        Returns:
            Resumen en texto
        """
        resumen = []
        resumen.append("=" * 60)
        resumen.append("RESUMEN DEL ANALISIS LEGAL")
        resumen.append("=" * 60)
        
        resumen.append(f"\n🔴 RIESGOS ALTOS: {len(altos)}")
        for riesgo in altos:
            resumen.append(f"  - {riesgo['descripcion'][:100]}")
        
        resumen.append(f"\n🟡 RIESGOS MEDIOS: {len(medios)}")
        for riesgo in medios:
            resumen.append(f"  - {riesgo['descripcion'][:100]}")
        
        resumen.append(f"\n🟢 RIESGOS BAJOS: {len(bajos)}")
        for riesgo in bajos:
            resumen.append(f"  - {riesgo['descripcion'][:100]}")
        
        if len(altos) > 0:
            resumen.append("\n" + "!" * 60)
            resumen.append("RECOMENDACIONES PRIORITARIAS:")
            resumen.append("!" * 60)
            for riesgo in altos[:3]:
                resumen.append(f"  • {riesgo['recomendacion']}")
        
        return "\n".join(resumen)