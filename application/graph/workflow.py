"""
Workflow de agentes usando LangGraph.
Construye un grafo de ejecucion con nodos y conexiones condicionales.
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional, Literal, Union
from dataclasses import dataclass

from langgraph.graph import StateGraph, START, END

from application.agents.base_agent import Hallazgo
from application.agents.risk_agent import RiskDetectionAgent
from application.agents.date_agent import DateExtractionAgent
from application.agents.obligation_agent import ObligationAgent

logger = logging.getLogger(__name__)


class EstadoAnalisis(TypedDict):
    """
    Estado que fluye a traves del grafo.
    """
    # Entrada
    texto: str
    consulta: Optional[str]
    
    # Resultados de cada nodo
    hallazgos_riesgo: List[Dict[str, Any]]
    hallazgos_fechas: List[Dict[str, Any]]
    hallazgos_obligaciones: List[Dict[str, Any]]
    
    # Metadatos de ejecucion
    nodo_actual: str
    errores: List[str]
    completado: bool
    
    # Salida final
    resultado_final: str
    resumen: str


class AnalisisWorkflow:
    """
    Workflow para analisis de contratos usando LangGraph.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el workflow y construye el grafo.
        
        Args:
            api_key: API key de Gemini
        """
        self.api_key = api_key
        
        # Inicializar agentes
        self.risk_agent = RiskDetectionAgent(api_key=api_key)
        self.date_agent = DateExtractionAgent(api_key=api_key)
        self.obligation_agent = ObligationAgent(api_key=api_key)
        
        # Construir el grafo
        self.graph = self._build_graph()
        
        logger.info("Workflow de analisis con LangGraph inicializado")
    
    def _build_graph(self) -> StateGraph:
        """
        Construye el grafo de ejecucion.
        
        Estructura:
        START → router → (riesgo/fechas/obligaciones) → union → final → END
        """
        # Crear el grafo
        workflow = StateGraph(EstadoAnalisis)
        
        # ============ NODOS ============
        workflow.add_node("router", self._router_node)
        workflow.add_node("riesgo", self._risk_node)
        workflow.add_node("fechas", self._date_node)
        workflow.add_node("obligaciones", self._obligation_node)
        workflow.add_node("union", self._union_node)
        workflow.add_node("final", self._final_node)
        
        # ============ EDGES ============
        # START -> Router
        workflow.add_edge(START, "router")
        
        # Router -> decide que camino tomar (condicional)
        workflow.add_conditional_edges(
            "router",
            self._router_decision,
            {
                "riesgo": "riesgo",
                "fechas": "fechas",
                "obligaciones": "obligaciones",
                "union": "union"  # Si no hay agentes especificos, ir directo a union
            }
        )
        
        # Agentes -> Union (todos van a union)
        workflow.add_edge("riesgo", "union")
        workflow.add_edge("fechas", "union")
        workflow.add_edge("obligaciones", "union")
        
        # Union -> Final
        workflow.add_edge("union", "final")
        
        # Final -> END
        workflow.add_edge("final", END)
        
        # Compilar
        return workflow.compile()
    
    def _router_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """Nodo router: analiza la consulta y prepara el estado."""
        logger.info("Router: analizando consulta...")
        
        consulta = estado.get("consulta", "")
        estado["nodo_actual"] = "router"
        
        # Limpiar resultados previos
        estado["hallazgos_riesgo"] = []
        estado["hallazgos_fechas"] = []
        estado["hallazgos_obligaciones"] = []
        estado["errores"] = []
        
        return estado
    
    def _router_decision(self, estado: EstadoAnalisis) -> str:
        """
        Decide que nodo ejecutar basado en la consulta.
        Retorna el nombre del nodo, NO una lista.
        """
        consulta = estado.get("consulta", "").lower()
        
        # Si no hay consulta o es analisis completo
        if not consulta or consulta in ["todos", "analizar", "analisis completo", "completo"]:
            # Para analisis completo, ejecutamos los agentes en paralelo
            # En LangGraph, ejecutamos un nodo que luego llama a los otros
            return "riesgo"  # Comenzamos con riesgo, luego los otros se encadenan
        
        # Palabras clave para cada tipo
        palabras_riesgo = ["penalizacion", "multa", "riesgo", "clausula", "rescicion", 
                          "terminacion", "responsabilidad", "exclusividad"]
        
        palabras_fechas = ["fecha", "vencimiento", "plazo", "renovacion", "dias", 
                          "meses", "anios", "termina", "inicia"]
        
        palabras_obligaciones = ["pago", "obligacion", "debe", "abonara", "pagara", 
                                "monto", "precio", "costo", "honorarios"]
        
        if any(p in consulta for p in palabras_riesgo):
            return "riesgo"
        
        if any(p in consulta for p in palabras_fechas):
            return "fechas"
        
        if any(p in consulta for p in palabras_obligaciones):
            return "obligaciones"
        
        # Por defecto, ir a union (sin agentes)
        return "union"
    
    def _risk_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """Nodo de deteccion de riesgos."""
        logger.info("Nodo Riesgo: analizando clausulas peligrosas...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.risk_agent.analizar(texto)
            estado["hallazgos_riesgo"] = [h.to_dict() for h in hallazgos]
            logger.info(f"Riesgos encontrados: {len(hallazgos)}")
        except Exception as e:
            logger.error(f"Error en nodo riesgo: {e}")
            estado["errores"].append(f"Riesgo: {str(e)}")
        
        # Si es analisis completo, encadenar al siguiente agente
        consulta = estado.get("consulta", "").lower()
        if not consulta or consulta in ["todos", "analizar", "analisis completo", "completo"]:
            # Ejecutamos fechas como siguiente paso
            estado = self._date_node(estado)
        
        return estado
    
    def _date_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """Nodo de extraccion de fechas."""
        logger.info("Nodo Fechas: extrayendo fechas criticas...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.date_agent.analizar(texto)
            estado["hallazgos_fechas"] = [h.to_dict() for h in hallazgos]
            logger.info(f"Fechas encontradas: {len(hallazgos)}")
        except Exception as e:
            logger.error(f"Error en nodo fechas: {e}")
            estado["errores"].append(f"Fechas: {str(e)}")
        
        # Si es analisis completo, encadenar al siguiente agente
        consulta = estado.get("consulta", "").lower()
        if not consulta or consulta in ["todos", "analizar", "analisis completo", "completo"]:
            estado = self._obligation_node(estado)
        
        return estado
    
    def _obligation_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """Nodo de deteccion de obligaciones."""
        logger.info("Nodo Obligaciones: detectando obligaciones...")
        
        try:
            texto = estado.get("texto", "")
            hallazgos = self.obligation_agent.analizar(texto)
            estado["hallazgos_obligaciones"] = [h.to_dict() for h in hallazgos]
            logger.info(f"Obligaciones encontradas: {len(hallazgos)}")
        except Exception as e:
            logger.error(f"Error en nodo obligaciones: {e}")
            estado["errores"].append(f"Obligaciones: {str(e)}")
        
        return estado
    
    def _union_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """Nodo union: combina los resultados de todos los agentes."""
        logger.info("Union: combinando resultados...")
        
        total = (len(estado.get("hallazgos_riesgo", [])) +
                len(estado.get("hallazgos_fechas", [])) +
                len(estado.get("hallazgos_obligaciones", [])))
        
        logger.info(f"Total hallazgos combinados: {total}")
        estado["completado"] = True
        
        return estado
    
    def _final_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        """Nodo final: genera el resumen del analisis."""
        logger.info("Final: generando resumen...")
        
        riesgos = estado.get("hallazgos_riesgo", [])
        fechas = estado.get("hallazgos_fechas", [])
        obligaciones = estado.get("hallazgos_obligaciones", [])
        
        # Clasificar por nivel de riesgo
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
        
        # Generar resumen
        resumen = []
        resumen.append("=" * 60)
        resumen.append("RESUMEN DEL ANALISIS LEGAL")
        resumen.append("=" * 60)
        
        resumen.append(f"\n🔴 RIESGOS ALTOS: {len(altos)}")
        for r in altos[:5]:
            desc = r.get('descripcion', '')[:80]
            if desc:
                resumen.append(f"  • {desc}")
        
        resumen.append(f"\n🟡 RIESGOS MEDIOS: {len(medios)}")
        for r in medios[:5]:
            desc = r.get('descripcion', '')[:80]
            if desc:
                resumen.append(f"  • {desc}")
        
        resumen.append(f"\n🟢 RIESGOS BAJOS: {len(bajos)}")
        
        if altos:
            resumen.append("\n" + "!" * 60)
            resumen.append("RECOMENDACIONES PRIORITARIAS:")
            resumen.append("!" * 60)
            for r in altos[:3]:
                rec = r.get('recomendacion', '')
                if rec:
                    resumen.append(f"  • {rec}")
        
        estado["resumen"] = "\n".join(resumen)
        estado["resultado_final"] = estado["resumen"]
        
        return estado
    
    async def ejecutar(self, texto: str, consulta: Optional[str] = None) -> Dict[str, Any]:
        """
        Ejecuta el workflow.
        
        Args:
            texto: Texto del contrato
            consulta: Consulta del usuario
            
        Returns:
            Diccionario con resultados
        """
        logger.info(f"Ejecutando workflow con consulta: {consulta or 'completa'}")
        
        # Estado inicial
        estado_inicial: EstadoAnalisis = {
            "texto": texto[:5000],
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
        """Version sincrona de ejecutar."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.ejecutar(texto, consulta))