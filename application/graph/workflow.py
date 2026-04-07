"""
Workflow de agentes usando LangGraph.
Construye un grafo de ejecucion con nodos y conexiones condicionales.
"""

import logging
import asyncio
import operator
from typing import TypedDict, List, Dict, Any, Optional, Annotated

from langgraph.graph import StateGraph, START, END

from application.agents.risk_agent import RiskDetectionAgent
from application.agents.date_agent import DateExtractionAgent
from application.agents.obligation_agent import ObligationAgent

logger = logging.getLogger(__name__)


class EstadoAnalisis(TypedDict):
    texto: str
    consulta: Optional[str]
    hallazgos_riesgo: Annotated[List[Dict[str, Any]], operator.add]
    hallazgos_fechas: Annotated[List[Dict[str, Any]], operator.add]
    hallazgos_obligaciones: Annotated[List[Dict[str, Any]], operator.add]
    nodo_actual: str
    errores: Annotated[List[str], operator.add]
    completado: bool
    resultado_final: str
    resumen: str


class AnalisisWorkflow:
    """
    Workflow para analisis de contratos usando LangGraph.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
        self.risk_agent = RiskDetectionAgent(api_key=api_key)
        self.date_agent = DateExtractionAgent(api_key=api_key)
        self.obligation_agent = ObligationAgent(api_key=api_key)
        
        self.graph = self._build_graph()
        
        logger.info("Workflow de analisis con LangGraph inicializado")
    
    def _build_graph(self) -> StateGraph:
        """
        Construye el grafo de ejecucion.
        
        IMPORTANTE: NO usar listas en conditional edges.
        Usamos un nodo "dispatcher" que ejecuta los agentes secuencialmente.
        """
        workflow = StateGraph(EstadoAnalisis)
        
        # Nodos
        workflow.add_node("router", self._router_node)
        workflow.add_node("dispatcher", self._dispatcher_node)
        workflow.add_node("riesgo", self._risk_node)
        workflow.add_node("fechas", self._date_node)
        workflow.add_node("obligaciones", self._obligation_node)
        workflow.add_node("union", self._union_node)
        workflow.add_node("final", self._final_node)
        
        # START -> Router
        workflow.add_edge(START, "router")
        
        # Router -> Dispatcher o agente individual
        workflow.add_conditional_edges(
            "router",
            self._router_decision,
            {
                "riesgo": "riesgo",
                "fechas": "fechas",
                "obligaciones": "obligaciones",
                "todos": "dispatcher"
            }
        )
        
        # Dispatcher ejecuta los agentes secuencialmente
        workflow.add_edge("dispatcher", "riesgo")
        workflow.add_edge("riesgo", "fechas")
        workflow.add_edge("fechas", "obligaciones")
        workflow.add_edge("obligaciones", "union")
        
        # Agentes individuales también van a union
        workflow.add_edge("riesgo", "union")
        workflow.add_edge("fechas", "union")
        workflow.add_edge("obligaciones", "union")
        
        # Union -> Final -> END
        workflow.add_edge("union", "final")
        workflow.add_edge("final", END)
        
        return workflow.compile()
    
    def _router_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info(f"Router analizando consulta: {estado.get('consulta', 'ninguna')}")
        
        estado["nodo_actual"] = "router"
        estado["hallazgos_riesgo"] = []
        estado["hallazgos_fechas"] = []
        estado["hallazgos_obligaciones"] = []
        estado["errores"] = []
        estado["completado"] = False
        estado["resultado_final"] = ""
        estado["resumen"] = ""
        
        return estado
    
    def _dispatcher_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """Nodo dispatcher: solo pasa el estado sin modificarlo."""
        logger.info("Dispatcher: ejecutando todos los agentes secuencialmente")
        estado["nodo_actual"] = "dispatcher"
        return estado
    
    def _router_decision(self, estado: EstadoAnalisis) -> str:
        consulta = estado.get("consulta", "").lower()
        
        # Analisis completo
        if not consulta or consulta in ["todos", "analizar", "analisis completo", "completo", "analizar contrato"]:
            logger.info("Router: ejecutando todos los agentes")
            return "todos"
        
        # Palabras clave para riesgos
        palabras_riesgo = ["penalizacion", "multa", "riesgo", "clausula", "rescicion", 
                          "terminacion", "responsabilidad", "exclusividad", "peligrosa"]
        
        # Palabras clave para fechas
        palabras_fechas = ["fecha", "vencimiento", "plazo", "renovacion", "dias", 
                          "meses", "anios", "termina", "inicia", "vigencia"]
        
        # Palabras clave para obligaciones
        palabras_obligaciones = ["pago", "obligacion", "debe", "abonara", "pagara", 
                                "monto", "precio", "costo", "honorarios", "abonar"]
        
        if any(p in consulta for p in palabras_riesgo):
            logger.info("Router: seleccionado agente de riesgos")
            return "riesgo"
        
        if any(p in consulta for p in palabras_fechas):
            logger.info("Router: seleccionado agente de fechas")
            return "fechas"
        
        if any(p in consulta for p in palabras_obligaciones):
            logger.info("Router: seleccionado agente de obligaciones")
            return "obligaciones"
        
        logger.info("Router: consulta general, ejecutando todos los agentes")
        return "todos"
    
    def _risk_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Nodo Riesgo: analizando clausulas peligrosas...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.risk_agent.analizar(texto)
            estado["hallazgos_riesgo"] = [h.to_dict() for h in hallazgos]
            logger.info(f"Riesgos encontrados: {len(hallazgos)}")
            
            for h in hallazgos:
                logger.info(f"  - {h.tipo}: {h.descripcion[:50]}... (riesgo: {h.riesgo})")
                
        except Exception as e:
            logger.error(f"Error en nodo riesgo: {e}")
            estado["errores"].append(f"Riesgo: {str(e)}")
        
        return estado
    
    def _date_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Nodo Fechas: extrayendo fechas criticas...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.date_agent.analizar(texto)
            estado["hallazgos_fechas"] = [h.to_dict() for h in hallazgos]
            logger.info(f"Fechas encontradas: {len(hallazgos)}")
            
            for h in hallazgos:
                logger.info(f"  - {h.tipo}: {h.descripcion[:50]}...")
                
        except Exception as e:
            logger.error(f"Error en nodo fechas: {e}")
            estado["errores"].append(f"Fechas: {str(e)}")
        
        return estado
    
    def _obligation_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Nodo Obligaciones: detectando obligaciones...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.obligation_agent.analizar(texto)
            estado["hallazgos_obligaciones"] = [h.to_dict() for h in hallazgos]
            logger.info(f"Obligaciones encontradas: {len(hallazgos)}")
            
            for h in hallazgos:
                logger.info(f"  - {h.tipo}: {h.descripcion[:50]}...")
                
        except Exception as e:
            logger.error(f"Error en nodo obligaciones: {e}")
            estado["errores"].append(f"Obligaciones: {str(e)}")
        
        return estado
    
    def _union_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        total = (len(estado.get("hallazgos_riesgo", [])) +
                len(estado.get("hallazgos_fechas", [])) +
                len(estado.get("hallazgos_obligaciones", [])))
        
        logger.info(f"Union: combinando {total} hallazgos")
        estado["completado"] = True
        
        return estado
    
    def _final_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Final: generando resumen...")
        
        riesgos = estado.get("hallazgos_riesgo", [])
        fechas = estado.get("hallazgos_fechas", [])
        obligaciones = estado.get("hallazgos_obligaciones", [])
        
        altos = []
        medios = []
        bajos = []
        
        for h in riesgos + fechas + obligaciones:
            riesgo = h.get("riesgo", "MEDIO")
            if riesgo == "ALTO":
                altos.append(h)
            elif riesgo == "MEDIO":
                medios.append(h)
            else:
                bajos.append(h)
        
        resumen = []
        resumen.append("=" * 60)
        resumen.append("RESUMEN DEL ANALISIS LEGAL")
        resumen.append("=" * 60)
        
        resumen.append(f"\n🔴 RIESGOS ALTOS: {len(altos)}")
        for r in altos[:5]:
            desc = r.get('descripcion', '')[:100]
            if desc:
                resumen.append(f"  • {desc}")
        
        resumen.append(f"\n🟡 RIESGOS MEDIOS: {len(medios)}")
        for r in medios[:5]:
            desc = r.get('descripcion', '')[:100]
            if desc:
                resumen.append(f"  • {desc}")
        
        resumen.append(f"\n🟢 RIESGOS BAJOS / INFORMATIVOS: {len(bajos)}")
        
        if altos:
            resumen.append("\n" + "!" * 60)
            resumen.append("RECOMENDACIONES PRIORITARIAS:")
            resumen.append("!" * 60)
            for r in altos[:3]:
                rec = r.get('recomendacion', '')
                if rec:
                    resumen.append(f"  • {rec[:150]}")
        
        estado["resumen"] = "\n".join(resumen)
        estado["resultado_final"] = estado["resumen"]
        
        logger.info(f"Resumen generado: {len(altos)} altos, {len(medios)} medios, {len(bajos)} bajos")
        
        return estado
    
    async def ejecutar(self, texto: str, consulta: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Ejecutando workflow con consulta: {consulta or 'completa'}")
        
        estado_inicial: EstadoAnalisis = {
            "texto": texto[:8000],
            "consulta": consulta,
            "hallazgos_riesgo": [],
            "hallazgos_fechas": [],
            "hallazgos_obligaciones": [],
            "nodo_actual": "inicio",
            "errores": [],
            "completado": False,
            "resultado_final": "",
            "resumen": ""
        }
        
        try:
            resultado = await self.graph.ainvoke(estado_inicial)
            
            return {
                "exito": True,
                "resumen": resultado.get("resumen", ""),
                "hallazgos_riesgo": resultado.get("hallazgos_riesgo", []),
                "hallazgos_fechas": resultado.get("hallazgos_fechas", []),
                "hallazgos_obligaciones": resultado.get("hallazgos_obligaciones", []),
                "errores": resultado.get("errores", [])
            }
        except Exception as e:
            logger.error(f"Error ejecutando workflow: {e}")
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