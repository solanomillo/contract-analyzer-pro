"""
Workflow simplificado para análisis de contratos.
REFACTORIZADO: Usa RAGService internamente y actualiza modelo dinámicamente.
"""

import logging
import asyncio
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

from application.services.rag_service import RAGService
from application.services.config_service import ConfigService
from application.services.token_optimizer import get_token_optimizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class EstadoAnalisis(TypedDict):
    texto: str
    consulta: Optional[str]
    tipo: str
    hallazgos: List[Dict[str, Any]]
    resumen: str


class AnalisisWorkflow:
    """
    Workflow simplificado.
    REFACTORIZADO: Usa RAGService con caché y actualización dinámica de modelo.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.config_service = ConfigService()
        self.rag_service = RAGService()
        self.token_optimizer = get_token_optimizer()
        
        if api_key and self.config_service.get_api_key() != api_key:
            self.config_service.actualizar_api_key(api_key)
        
        self.graph = self._build_graph()
        logger.info("Workflow refactorizado inicializado (usando RAGService con caché)")
    
    def _get_current_model(self) -> str:
        """Obtiene el modelo actual desde configuración."""
        model = self.config_service.get_model()
        if model:
            self.rag_service.gemini_client.update_model(model)
            self.token_optimizer.update_model(model)
        return model or "gemini-2.0-flash"
    
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
        
        # Obtener modelo actual
        current_model = self._get_current_model()
        logger.info(f"Usando modelo: {current_model}")
        
        if not self.rag_service.current_index_name and texto:
            self._indexar_texto_temporal(texto)
        
        if tipo == "analisis":
            pregunta = """
            Realiza un análisis legal COMPLETO y ESTRUCTURADO de este contrato.
            
            Incluye:
            1. RIESGOS Y CLÁUSULAS PELIGROSAS (penalizaciones, rescisión, renovación)
            2. FECHAS IMPORTANTES (inicio, término, plazos de pago, preaviso)
            3. OBLIGACIONES DE LAS PARTES (montos, servicios, mantenimiento)
            
            Sé específico: incluye números, fechas exactas y montos cuando los encuentres.
            """
        else:
            pregunta = consulta if consulta else "¿Cuál es el propósito principal de este contrato?"
        
        resultado = self.rag_service.ask_question(
            question=pregunta,
            k=10 if tipo == "analisis" else 5,
            include_history=False,
            model=current_model
        )
        
        estado["resumen"] = resultado.get("respuesta", "No se pudo generar respuesta")
        estado["hallazgos"] = [{
            "tipo": "respuesta" if tipo == "pregunta" else "analisis",
            "descripcion": estado["resumen"][:500],
            "riesgo": "BAJO",
            "texto_relevante": "",
            "recomendacion": "Revisar la respuesta completa para más detalles"
        }]
        
        costo = resultado.get("costo_estimado_usd", 0)
        tiempo = resultado.get("tiempo_ms", 0)
        logger.info(f"Respuesta generada: {tiempo}ms, costo: ${costo:.6f}")
        
        return estado
    
    def _indexar_texto_temporal(self, texto: str):
        """Indexa texto temporalmente para análisis."""
        logger.info(f"Indexando texto temporal de {len(texto)} caracteres")
        
        chunks = self.token_optimizer.chunk_text_intelligent(
            texto, 
            max_tokens=2000, 
            overlap_tokens=200
        )
        
        contract_data = {
            "nombre_archivo": "temp_workflow.txt",
            "texto_completo": texto,
            "chunks": [
                {
                    "texto": chunk.text, 
                    "indice": i,
                    "token_count": chunk.token_count
                } 
                for i, chunk in enumerate(chunks)
            ]
        }
        
        self.rag_service.index_contract(contract_data)
        logger.info(f"Texto temporal indexado: {len(chunks)} chunks")
    
    def _final_node(self, estado: EstadoAnalisis) -> EstadoAnalisis:
        return estado
    
    async def ejecutar(self, texto: str, consulta: Optional[str] = None, tipo: str = "pregunta") -> Dict[str, Any]:
        logger.info(f"Ejecutando: tipo={tipo}, consulta={consulta[:50] if consulta else 'ninguna'}")
        
        estado_inicial: EstadoAnalisis = {
            "texto": texto,
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
            logger.error(f"Error en workflow: {e}")
            return {
                "exito": False,
                "error": str(e),
                "resumen": f"Error en el análisis: {str(e)[:200]}"
            }
    
    def ejecutar_sync(self, texto: str, consulta: Optional[str] = None, tipo: str = "pregunta") -> Dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.ejecutar(texto, consulta, tipo))
    
    def limpiar_cache(self):
        if self.rag_service:
            self.rag_service.clear()
            logger.info("Caché del workflow limpiado")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "rag_service": self.rag_service.get_stats() if self.rag_service else {},
            "modelo_actual": self._get_current_model(),
            "tiene_api_key": self.config_service.has_api_key()
        }