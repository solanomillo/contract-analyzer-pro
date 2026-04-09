"""
Workflow de agentes usando LangGraph.
"""

import logging
import asyncio
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

from application.agents.risk_agent import RiskDetectionAgent
from application.agents.date_agent import DateExtractionAgent
from application.agents.obligation_agent import ObligationAgent
from application.agents.complete_analysis_agent import CompleteAnalysisAgent
from application.services.response_formatter import ResponseFormatter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class EstadoAnalisis(TypedDict):
    texto: str
    consulta: Optional[str]
    hallazgos: List[Dict[str, Any]]
    agente_usado: str
    errores: List[str]
    resumen: str


class AnalisisWorkflow:
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
        self.complete_agent = CompleteAnalysisAgent(api_key=api_key)
        self.risk_agent = RiskDetectionAgent(api_key=api_key)
        self.date_agent = DateExtractionAgent(api_key=api_key)
        self.obligation_agent = ObligationAgent(api_key=api_key)
        
        self.graph = self._build_graph()
        
        logger.info("Workflow de analisis inicializado")
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(EstadoAnalisis)
        
        workflow.add_node("router", self._router_node)
        workflow.add_node("completo", self._complete_node)
        workflow.add_node("riesgo", self._risk_node)
        workflow.add_node("fechas", self._date_node)
        workflow.add_node("obligaciones", self._obligation_node)
        workflow.add_node("final", self._final_node)
        
        workflow.add_edge(START, "router")
        
        workflow.add_conditional_edges(
            "router",
            self._router_decision,
            {
                "completo": "completo",
                "riesgo": "riesgo",
                "fechas": "fechas",
                "obligaciones": "obligaciones"
            }
        )
        
        workflow.add_edge("completo", "final")
        workflow.add_edge("riesgo", "final")
        workflow.add_edge("fechas", "final")
        workflow.add_edge("obligaciones", "final")
        workflow.add_edge("final", END)
        
        return workflow.compile()
    
    def _router_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info(f"Router analizando consulta: {estado.get('consulta', 'ninguna')}")
        estado["hallazgos"] = []
        estado["errores"] = []
        estado["agente_usado"] = "router"
        estado["resumen"] = ""
        return estado
    
    def _router_decision(self, estado: EstadoAnalisis) -> str:
        consulta = estado.get("consulta", "").lower()
        
        logger.info(f"Router evaluando consulta: '{consulta}'")
        
        palabras_completo = ["analizar", "completo", "todos", "analisis legal", "que opinas"]
        palabras_riesgo = ["penalizacion", "multa", "riesgo", "clausula", "rescicion", "terminacion"]
        palabras_fechas = ["fecha", "vencimiento", "plazo", "renovacion", "termina", "inicia", "vigencia"]
        palabras_obligaciones = ["pago", "obligacion", "debe", "abonara", "monto", "precio"]
        
        if any(p in consulta for p in palabras_completo):
            logger.info("=== ROUTER: Usando agente COMPLETO ===")
            return "completo"
        if any(p in consulta for p in palabras_riesgo):
            logger.info("=== ROUTER: Usando agente de RIESGOS ===")
            return "riesgo"
        if any(p in consulta for p in palabras_fechas):
            logger.info("=== ROUTER: Usando agente de FECHAS ===")
            return "fechas"
        if any(p in consulta for p in palabras_obligaciones):
            logger.info("=== ROUTER: Usando agente de OBLIGACIONES ===")
            return "obligaciones"
        
        logger.info("=== ROUTER: Consulta general, usando agente COMPLETO ===")
        return "completo"
    
    def _complete_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Agente Completo: analizando...")
        try:
            texto = estado.get("texto", "")
            hallazgos = self.complete_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "completo"
            logger.info(f"Hallazgos: {len(estado['hallazgos'])}")
        except Exception as e:
            logger.error(f"Error: {e}")
            estado["hallazgos"] = [{"tipo": "error", "descripcion": str(e), "riesgo": "ALTO"}]
            estado["errores"].append(str(e))
        return estado
    
    def _risk_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Agente Riesgo: analizando...")
        try:
            texto = estado.get("texto", "")
            hallazgos = self.risk_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "riesgo"
            logger.info(f"Hallazgos: {len(estado['hallazgos'])}")
        except Exception as e:
            logger.error(f"Error: {e}")
            estado["hallazgos"] = [{"tipo": "error", "descripcion": str(e), "riesgo": "ALTO"}]
            estado["errores"].append(str(e))
        return estado
    
    def _date_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Agente Fechas: extrayendo...")
        try:
            texto = estado.get("texto", "")
            hallazgos = self.date_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "fechas"
            logger.info(f"Hallazgos: {len(estado['hallazgos'])}")
        except Exception as e:
            logger.error(f"Error: {e}")
            estado["hallazgos"] = [{"tipo": "error", "descripcion": str(e), "riesgo": "MEDIO"}]
            estado["errores"].append(str(e))
        return estado
    
    def _obligation_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Agente Obligaciones: detectando...")
        try:
            texto = estado.get("texto", "")
            hallazgos = self.obligation_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "obligaciones"
            logger.info(f"Hallazgos: {len(estado['hallazgos'])}")
        except Exception as e:
            logger.error(f"Error: {e}")
            estado["hallazgos"] = [{"tipo": "error", "descripcion": str(e), "riesgo": "MEDIO"}]
            estado["errores"].append(str(e))
        return estado
    
    def _final_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Final: generando resumen...")
        
        hallazgos = estado.get("hallazgos", [])
        agente = estado.get("agente_usado", "")
        
        # Detectar error
        if hallazgos and hallazgos[0].get("tipo") == "error":
            estado["resumen"] = ResponseFormatter.format_error(hallazgos[0].get("descripcion", "Error desconocido"))
            return estado
        
        # Usar el formateador centralizado segun el agente
        if agente == "fechas":
            estado["resumen"] = ResponseFormatter.format_fechas(hallazgos)
        elif agente == "riesgo":
            estado["resumen"] = ResponseFormatter.format_riesgos(hallazgos)
        elif agente == "obligaciones":
            estado["resumen"] = ResponseFormatter.format_obligaciones(hallazgos)
        else:
            estado["resumen"] = ResponseFormatter.format_completo(hallazgos)
        
        estado["resultado_final"] = estado["resumen"]
        return estado
    
    async def ejecutar(self, texto: str, consulta: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Ejecutando workflow con consulta: {consulta or 'general'}")
        
        estado_inicial: EstadoAnalisis = {
            "texto": texto[:8000],
            "consulta": consulta,
            "hallazgos": [],
            "agente_usado": "",
            "errores": [],
            "resumen": ""
        }
        
        try:
            resultado = await self.graph.ainvoke(estado_inicial)
            
            return {
                "exito": True,
                "resumen": resultado.get("resumen", ""),
                "hallazgos": resultado.get("hallazgos", []),
                "agente_usado": resultado.get("agente_usado", ""),
                "errores": resultado.get("errores", [])
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {
                "exito": False,
                "error": str(e),
                "resumen": f"Error en el analisis: {e}"
            }
    
    def ejecutar_sync(self, texto: str, consulta: Optional[str] = None) -> Dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.ejecutar(texto, consulta))