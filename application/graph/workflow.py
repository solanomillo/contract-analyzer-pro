"""
Workflow simplificado para análisis de contratos.
Un solo agente que maneja preguntas y análisis completo.
"""

import logging
import asyncio
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

from application.agents.contract_agent import ContractAgent
from application.services.response_formatter import ResponseFormatter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class EstadoAnalisis(TypedDict):
    texto: str
    consulta: Optional[str]
    tipo: str  # "pregunta" o "analisis"
    hallazgos: List[Dict[str, Any]]
    resumen: str


class AnalisisWorkflow:
    """
    Workflow simplificado.
    - Preguntas: respuesta concreta
    - Análisis: respuesta detallada
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.agent = ContractAgent(api_key=api_key)
        self.graph = self._build_graph()
        logger.info("Workflow simplificado inicializado")
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(EstadoAnalisis)
        
        workflow.add_node("procesar", self._procesar_node)
        workflow.add_node("final", self._final_node)
        
        workflow.add_edge(START, "procesar")
        workflow.add_edge("procesar", "final")
        workflow.add_edge("final", END)
        
        return workflow.compile()
    
    def _procesar_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        tipo = estado.get("tipo", "pregunta")
        consulta = estado.get("consulta", "")
        texto = estado.get("texto", "")
        
        logger.info(f"Procesando: tipo={tipo}, consulta={consulta[:50] if consulta else 'ninguna'}")
        
        if tipo == "analisis":
            contexto = "analisis_completo"
        else:
            contexto = consulta if consulta else "analiza este contrato"
        
        hallazgos = self.agent.analizar(texto, contexto=contexto)
        estado["hallazgos"] = [h.to_dict() for h in hallazgos]
        
        return estado
    
    def _final_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        hallazgos = estado.get("hallazgos", [])
        tipo = estado.get("tipo", "pregunta")
        
        if tipo == "analisis":
            estado["resumen"] = ResponseFormatter.format_completo(hallazgos)
        else:
            estado["resumen"] = ResponseFormatter.format_respuesta_concreta(hallazgos)
        
        return estado
    
    async def ejecutar(self, texto: str, consulta: Optional[str] = None, tipo: str = "pregunta") -> Dict[str, Any]:
        logger.info(f"Ejecutando: tipo={tipo}, consulta={consulta[:50] if consulta else 'ninguna'}")
        
        estado_inicial: EstadoAnalisis = {
            "texto": texto[:8000],
            "consulta": consulta,
            "tipo": tipo,
            "hallazgos": [],
            "resumen": ""
        }
        
        try:
            resultado = await self.graph.ainvoke(estado_inicial)
            return {
                "exito": True,
                "resumen": resultado.get("resumen", ""),
                "hallazgos": resultado.get("hallazgos", [])
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {
                "exito": False,
                "error": str(e),
                "resumen": f"Error: {e}"
            }
    
    def ejecutar_sync(self, texto: str, consulta: Optional[str] = None, tipo: str = "pregunta") -> Dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.ejecutar(texto, consulta, tipo))