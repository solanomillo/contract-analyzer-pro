"""
Agente unificado para análisis de contratos.
REFACTORIZADO: Usa RAGService internamente con actualización dinámica de modelo.
"""

import logging
from typing import List, Optional
from application.agents.base_agent import BaseAgent, Hallazgo
from application.services.rag_service import RAGService
from application.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class ContractAgent(BaseAgent):
    """
    Agente unificado que maneja preguntas específicas y análisis completo.
    REFACTORIZADO: Delega en RAGService con actualización dinámica de modelo.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.config_service = ConfigService()
        self.rag_service = RAGService()
        
        if api_key and self.config_service.get_api_key() != api_key:
            self.config_service.actualizar_api_key(api_key)
        
        logger.info("ContractAgent refactorizado (usando RAGService)")
    
    def _get_current_model(self) -> str:
        """Obtiene el modelo actual desde configuración."""
        model = self.config_service.get_model()
        if model:
            self.rag_service.gemini_client.update_model(model)
        return model or "gemini-2.0-flash"
    
    def analizar(self, texto: str, contexto: Optional[str] = None) -> List[Hallazgo]:
        es_analisis_completo = contexto == "analisis_completo"
        
        if not self.rag_service.current_index_name and texto:
            self._indexar_texto_temporal(texto)
        
        if es_analisis_completo:
            return self._analisis_completo_via_rag()
        else:
            return self._respuesta_especifica_via_rag(contexto or "Analiza este contrato")
    
    def _indexar_texto_temporal(self, texto: str):
        from application.services.token_optimizer import get_token_optimizer
        
        logger.info(f"Indexando texto temporal de {len(texto)} caracteres")
        
        optimizer = get_token_optimizer()
        chunks = optimizer.chunk_text_intelligent(texto, max_tokens=2000, overlap_tokens=200)
        
        contract_data = {
            "nombre_archivo": "temp_analysis.txt",
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
    
    def _respuesta_especifica_via_rag(self, pregunta: str) -> List[Hallazgo]:
        current_model = self._get_current_model()
        logger.info(f"Respondiendo vía RAG con modelo {current_model}: {pregunta[:100]}...")
        
        resultado = self.rag_service.ask_question(
            question=pregunta,
            k=5,
            include_history=False,
            model=current_model
        )
        
        respuesta = resultado.get("respuesta", "No se pudo obtener respuesta")
        costo = resultado.get("costo_estimado_usd", 0)
        
        logger.info(f"Respuesta generada (costo: ${costo:.6f})")
        
        return [Hallazgo(
            tipo="respuesta",
            descripcion=respuesta[:1000],
            riesgo="MEDIO",
            texto_relevante="",
            recomendacion="",
            ubicacion=None
        )]
    
    def _analisis_completo_via_rag(self) -> List[Hallazgo]:
        current_model = self._get_current_model()
        logger.info(f"Analizando completo vía RAG con modelo {current_model}")
        
        pregunta_analisis = """
        Realiza un análisis legal COMPLETO y ESTRUCTURADO de este contrato.
        
        Incluye las siguientes secciones:
        
        1. RIESGOS Y CLÁUSULAS PELIGROSAS
        2. FECHAS IMPORTANTES
        3. OBLIGACIONES DE LAS PARTES
        
        Sé específico: incluye números, fechas exactas y montos cuando los encuentres.
        """
        
        resultado = self.rag_service.ask_question(
            question=pregunta_analisis,
            k=10,
            include_history=False,
            model=current_model
        )
        
        respuesta = resultado.get("respuesta", "No se pudo generar análisis")
        costo = resultado.get("costo_estimado_usd", 0)
        
        logger.info(f"Análisis completo generado (costo: ${costo:.6f})")
        
        return [Hallazgo(
            tipo="analisis_completo",
            descripcion=respuesta,
            riesgo="MEDIO",
            texto_relevante="",
            recomendacion="Revisar el análisis completo para más detalles",
            ubicacion=None
        )]
    
    def limpiar_cache(self):
        if self.rag_service:
            self.rag_service.clear()
            logger.info("Caché del ContractAgent limpiado")
    
    def get_stats(self) -> dict:
        return {
            "rag_service": self.rag_service.get_stats() if self.rag_service else {},
            "modelo_actual": self._get_current_model(),
            "tiene_api_key": self.config_service.has_api_key()
        }