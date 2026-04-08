"""
Workflow de agentes usando LangGraph.
Router decide qué agente usar según la consulta.
OPTIMIZADO: Analisis completo usa UNA sola llamada, no 3 agentes.
"""

import logging
import asyncio
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

from application.agents.risk_agent import RiskDetectionAgent
from application.agents.date_agent import DateExtractionAgent
from application.agents.obligation_agent import ObligationAgent
from application.agents.complete_analysis_agent import CompleteAnalysisAgent

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
    """
    Workflow para analisis de contratos.
    - Preguntas especificas: usan agente especifico (1 llamada)
    - Analisis completo: usa CompleteAnalysisAgent (1 llamada)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
        self.complete_agent = CompleteAnalysisAgent(api_key=api_key)
        self.risk_agent = RiskDetectionAgent(api_key=api_key)
        self.date_agent = DateExtractionAgent(api_key=api_key)
        self.obligation_agent = ObligationAgent(api_key=api_key)
        
        self.graph = self._build_graph()
        
        logger.info("Workflow de analisis optimizado inicializado")
    
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
        
        # Palabras clave para analisis completo (USA UNA SOLA LLAMADA)
        palabras_completo = ["analizar", "analisis completo", "completo", "todos", 
                            "analiza este contrato", "resumen general", "todo el contrato",
                            "analisis legal", "que opinas", "que riesgos tiene"]
        
        # Palabras clave para riesgos
        palabras_riesgo = ["penalizacion", "multa", "riesgo", "clausula", "rescicion", 
                          "terminacion", "responsabilidad", "exclusividad", "peligrosa"]
        
        # Palabras clave para fechas
        palabras_fechas = ["fecha", "vencimiento", "plazo", "renovacion", "dias", 
                          "meses", "anios", "termina", "inicia", "vigencia", "duracion"]
        
        # Palabras clave para obligaciones
        palabras_obligaciones = ["pago", "obligacion", "debe", "abonara", "pagara", 
                                "monto", "precio", "costo", "honorarios", "abonar"]
        
        # Detectar analisis completo (USA UNA SOLA LLAMADA)
        if any(p in consulta for p in palabras_completo):
            logger.info("Router: usando agente COMPLETO (una sola llamada)")
            return "completo"
        
        # Detectar tipo especifico
        if any(p in consulta for p in palabras_riesgo):
            logger.info("Router: usando agente de RIESGOS")
            return "riesgo"
        
        if any(p in consulta for p in palabras_fechas):
            logger.info("Router: usando agente de FECHAS")
            return "fechas"
        
        if any(p in consulta for p in palabras_obligaciones):
            logger.info("Router: usando agente de OBLIGACIONES")
            return "obligaciones"
        
        # Por defecto, usar agente completo (una sola llamada)
        logger.info("Router: consulta general, usando agente COMPLETO")
        return "completo"
    
    def _complete_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """UNA SOLA LLAMADA a Gemini para todo el analisis."""
        logger.info("Agente Completo: analizando contrato en UNA sola llamada...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.complete_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "completo"
            logger.info(f"Analisis completo generado: {len(hallazgos)} hallazgos")
                
        except Exception as e:
            logger.error(f"Error en agente completo: {e}")
            estado["errores"].append(str(e))
        
        return estado
    
    def _risk_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Agente Riesgo: analizando...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.risk_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "riesgo"
            logger.info(f"Hallazgos encontrados: {len(hallazgos)}")
            
            for h in hallazgos:
                logger.info(f"  - {h.tipo}: {h.descripcion[:50]}... (riesgo: {h.riesgo})")
                
        except Exception as e:
            logger.error(f"Error en agente riesgo: {e}")
            estado["errores"].append(str(e))
        
        return estado
    
    def _date_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Agente Fechas: extrayendo...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.date_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "fechas"
            logger.info(f"Hallazgos encontrados: {len(hallazgos)}")
            
            for h in hallazgos:
                logger.info(f"  - {h.tipo}: {h.descripcion[:50]}...")
                
        except Exception as e:
            logger.error(f"Error en agente fechas: {e}")
            estado["errores"].append(str(e))
        
        return estado
    
    def _obligation_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Agente Obligaciones: detectando...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.obligation_agent.analizar(texto)
            estado["hallazgos"] = [h.to_dict() for h in hallazgos]
            estado["agente_usado"] = "obligaciones"
            logger.info(f"Hallazgos encontrados: {len(hallazgos)}")
            
            for h in hallazgos:
                logger.info(f"  - {h.tipo}: {h.descripcion[:50]}...")
                
        except Exception as e:
            logger.error(f"Error en agente obligaciones: {e}")
            estado["errores"].append(str(e))
        
        return estado
    
    def _final_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        logger.info("Final: generando resumen...")
        
        hallazgos = estado.get("hallazgos", [])
        
        altos = [h for h in hallazgos if h.get("riesgo") == "ALTO"]
        medios = [h for h in hallazgos if h.get("riesgo") == "MEDIO"]
        bajos = [h for h in hallazgos if h.get("riesgo") == "BAJO"]
        
        resumen = []
        resumen.append("=" * 60)
        resumen.append("RESULTADO DEL ANALISIS")
        resumen.append("=" * 60)
        resumen.append(f"\nAgente utilizado: {estado.get('agente_usado', 'desconocido')}")
        
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
            resumen.append("RECOMENDACIONES:")
            resumen.append("!" * 60)
            for r in altos[:3]:
                rec = r.get('recomendacion', '')
                if rec:
                    resumen.append(f"  • {rec[:150]}")
        
        estado["resumen"] = "\n".join(resumen)
        
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