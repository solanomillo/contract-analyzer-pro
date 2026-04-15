"""
Servicio RAG (Retrieval-Augmented Generation) para contratos.
MEJORADO: Memoria conversacional, búsqueda con contexto histórico, resúmenes.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from infrastructure.embeddings.embedding_service import EmbeddingService
from infrastructure.vector_db.vector_store import VectorStore
from infrastructure.llm_clients.gemini_client import GeminiClient
from application.services.conversation_memory import ConversationMemory, ConversationMemoryFactory, MessageRole
from application.services.token_optimizer import get_token_optimizer
from application.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Servicio RAG para procesamiento y consulta de contratos.
    MEJORADO: Con memoria conversacional, búsqueda contextual y resúmenes.
    """
    
    def __init__(
        self,
        persist_dir: Path = Path("data/vector_store"),
        gemini_client: Optional[GeminiClient] = None
    ):
        """
        Inicializa el servicio RAG.
        
        Args:
            persist_dir: Directorio para persistencia
            gemini_client: Cliente de Gemini (opcional)
        """
        self.persist_dir = persist_dir
        self.embedding_service = EmbeddingService()
        self.vector_store: Optional[VectorStore] = None
        self.current_index_name: Optional[str] = None
        
        # Cliente Gemini
        self.gemini_client = gemini_client or GeminiClient()
        
        # Config service para obtener modelo actual
        self.config_service = ConfigService()
        
        # Memoria conversacional (se crea por sesión)
        self.conversation_memory: Optional[ConversationMemory] = None
        
        # Token optimizer
        self.token_optimizer = get_token_optimizer()
        
        # Resumen del contrato (para contexto rápido)
        self.contract_summary: Optional[str] = None
        self.contract_metadata: Dict[str, Any] = {}
        
        logger.info("Servicio RAG mejorado inicializado")
    
    def _limpiar_respuesta(self, respuesta: str) -> str:
        """
        Limpia el formato markdown y referencias de la respuesta.
        """
        if not respuesta:
            return respuesta
        
        # Eliminar referencias entre corchetes [Contexto 1], [Resumen], etc.
        respuesta = re.sub(r'\[.*?\]\s*', '', respuesta)
        
        # Eliminar markdown de negritas ** **
        respuesta = re.sub(r'\*\*(.*?)\*\*', r'\1', respuesta)
        
        # Eliminar markdown de cursivas * *
        respuesta = re.sub(r'\*(.*?)\*', r'\1', respuesta)
        
        # Eliminar líneas que contienen referencias
        lineas = respuesta.split('\n')
        lineas_limpias = []
        for linea in lineas:
            if not any(x in linea for x in ['Referencia:', 'Fuente:', 'Contexto', '---', '⏱️', '💰', '📊']):
                lineas_limpias.append(linea)
        
        respuesta = '\n'.join(lineas_limpias)
        
        # Eliminar múltiples saltos de línea
        respuesta = re.sub(r'\n\s*\n', '\n\n', respuesta)
        
        # Limpiar espacios al inicio y final
        respuesta = respuesta.strip()
        
        return respuesta
    
    def _get_current_model(self) -> str:
        """Obtiene el modelo actual desde la configuración y actualiza el cliente."""
        model = self.config_service.get_model()
        if model and self.gemini_client.modelo_predeterminado != model:
            self.gemini_client.update_model(model)
            self.token_optimizer.update_model(model)
            logger.info(f"Modelo actualizado a: {model}")
        return model or self.gemini_client.modelo_predeterminado
    
    def initialize_conversation(self, session_id: Optional[str] = None) -> ConversationMemory:
        """
        Inicializa o recupera una conversación para la sesión actual.
        
        Args:
            session_id: ID de sesión (opcional)
            
        Returns:
            Instancia de ConversationMemory
        """
        self.conversation_memory = ConversationMemoryFactory.get_or_create(
            session_id=session_id,
            max_tokens_short_term=8000,
            max_messages_short_term=20
        )
        logger.info(f"Conversación inicializada: {self.conversation_memory.session_id}")
        return self.conversation_memory
    
    def set_contract_summary(self, summary: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Establece un resumen del contrato para contexto rápido.
        
        Args:
            summary: Resumen del contrato
            metadata: Metadatos adicionales
        """
        # Limpiar el resumen también
        summary = self._limpiar_respuesta(summary)
        self.contract_summary = summary
        self.contract_metadata = metadata or {}
        logger.info(f"Resumen de contrato establecido ({len(summary)} caracteres)")
    
    def generate_contract_summary(self, contract_text: str, max_tokens: int = 2000) -> str:
        """
        Genera un resumen del contrato usando Gemini.
        
        Args:
            contract_text: Texto completo del contrato
            max_tokens: Máximo de tokens para el resumen
            
        Returns:
            Resumen del contrato
        """
        current_model = self._get_current_model()
        
        preview_text = contract_text[:50000] if len(contract_text) > 50000 else contract_text
        
        prompt = f"""
        Por favor, genera un resumen ejecutivo SIMPLE del siguiente contrato.
        
        Incluye:
        1. Tipo de contrato
        2. Partes involucradas
        3. Obligaciones principales
        4. Plazos importantes
        5. Cláusulas de riesgo identificadas
        
        Contrato:
        {preview_text}
        
        Resumen (conciso, máximo 500 palabras, SIN formato markdown, SIN negritas, texto plano):
        """
        
        summary = self.gemini_client.generar_contenido(
            prompt,
            modelo=current_model,
            operation_type="summary",
            use_cache=True,
            cache_ttl=7200
        )
        
        if summary:
            summary_limpio = self._limpiar_respuesta(summary)
            self.set_contract_summary(summary_limpio)
            return summary_limpio
        
        return "No se pudo generar resumen del contrato."
    
    def _ensure_vector_store(self) -> VectorStore:
        """Asegura que el vector store está inicializado."""
        if self.vector_store is None:
            self.vector_store = VectorStore(
                dimension=self.embedding_service.dimension,
                persist_dir=self.persist_dir
            )
        return self.vector_store
    
    def index_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Indexa un contrato en la base de datos vectorial.
        
        Args:
            contract_data: Datos del contrato (con chunks)
            
        Returns:
            Estadisticas de la indexacion
        """
        logger.info(f"Indexando contrato: {contract_data.get('nombre_archivo')}")
        
        chunks = contract_data.get("chunks", [])
        if not chunks:
            return {"error": "No hay chunks para indexar", "chunks_indexados": 0}
        
        chunks_con_embedding = self.embedding_service.embed_chunks(chunks)
        
        vector_store = self._ensure_vector_store()
        
        nombre_indice = contract_data.get("nombre_archivo", "contract").replace(".pdf", "").replace(".txt", "")
        
        if self.current_index_name != nombre_indice:
            vector_store.clear()
            self.current_index_name = nombre_indice
        
        chunks_agregados = vector_store.add_chunks(chunks_con_embedding)
        vector_store.save(nombre_indice)
        
        texto_completo = " ".join([chunk.get("texto", "") for chunk in chunks])
        self.generate_contract_summary(texto_completo)
        
        resultado = {
            "nombre_indice": nombre_indice,
            "chunks_indexados": chunks_agregados,
            "total_chunks": len(chunks),
            "estado": "exito" if chunks_agregados > 0 else "fallo",
            "tiene_resumen": self.contract_summary is not None
        }
        
        logger.info(f"Indexacion completada: {resultado}")
        return resultado
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Busca chunks relevantes para una consulta."""
        if not query or len(query.strip()) == 0:
            logger.warning("Consulta vacia")
            return []
        
        vector_store = self._ensure_vector_store()
        
        if vector_store.index.ntotal == 0:
            logger.warning("No hay chunks indexados")
            return []
        
        query_embedding = self.embedding_service.embed_text(query)
        resultados = vector_store.search(query_embedding, k)
        
        logger.info(f"Busqueda retorno {len(resultados)} resultados")
        return resultados
    
    def search_with_history(
        self,
        query: str,
        k: int = 5,
        use_conversation_context: bool = True
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Busca chunks relevantes considerando el contexto de la conversación."""
        enriched_query = query
        
        if use_conversation_context and self.conversation_memory:
            context, _ = self.conversation_memory.get_context_for_prompt(
                query,
                include_summaries=True,
                max_tokens=2000
            )
            
            if context:
                enriched_query = f"""
                Contexto de conversación anterior:
                {context}
                
                Pregunta actual del usuario:
                {query}
                
                Basado en el contexto anterior, responde la pregunta actual.
                """
        
        resultados = self.search(enriched_query, k)
        return resultados, enriched_query
    
    def get_context_for_query(
        self,
        query: str,
        k: int = 3,
        include_summary: bool = True,
        include_history: bool = True
    ) -> str:
        """Obtiene contexto relevante para una consulta."""
        context_parts = []
        
        if include_summary and self.contract_summary:
            context_parts.append(f"RESUMEN DEL CONTRATO:\n{self.contract_summary}")
        
        resultados, _ = self.search_with_history(query, k, include_history)
        
        if resultados:
            context_chunks = []
            for i, resultado in enumerate(resultados, 1):
                texto = resultado.get("texto", "")
                context_chunks.append(f"CONTEXTO {i}:\n{texto}")
            context_parts.append("\n\n".join(context_chunks))
        else:
            context_parts.append("No se encontró información relevante en el contrato.")
        
        return "\n\n---\n\n".join(context_parts)
    
    def ask_question(
        self,
        question: str,
        k: int = 5,
        include_history: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Realiza una pregunta sobre el contrato con contexto RAG.
        """
        start_time = datetime.now()
        
        if model is None:
            model = self._get_current_model()
        else:
            self.gemini_client.update_model(model)
            self.token_optimizer.update_model(model)
        
        logger.info(f"Usando modelo para pregunta: {model}")
        
        if self.conversation_memory and include_history:
            self.conversation_memory.add_message(
                content=question,
                role=MessageRole.USER,
                metadata={"timestamp": start_time.isoformat()}
            )
        
        context = self.get_context_for_query(question, k, include_summary=True, include_history=include_history)
        
        conversation_context = ""
        if self.conversation_memory and include_history:
            conv_context, _ = self.conversation_memory.get_context_for_prompt(
                question,
                include_summaries=True,
                max_tokens=3000
            )
            if conv_context:
                conversation_context = f"\n\nCONVERSACIÓN ANTERIOR:\n{conv_context}\n"
        
        prompt = f"""
        Eres un asistente experto en análisis de contratos legales.
        
        {conversation_context}
        
        CONTEXTO DEL CONTRATO:
        {context}
        
        PREGUNTA DEL USUARIO:
        {question}
        
        Instrucciones:
        1. Responde basándote ESTRICTAMENTE en el contexto proporcionado
        2. Si la información no está en el contexto, indícalo claramente
        3. Sé conciso y directo
        4. NO uses formato markdown, NO uses negritas, NO uses asteriscos
        5. Responde en texto plano, con viñetas simples usando guiones (-)
        
        Respuesta:
        """
        
        prompt_tokens = self.token_optimizer.count_tokens(prompt)
        if not self.token_optimizer.is_safe_to_send(prompt):
            logger.warning(f"Prompt muy largo ({prompt_tokens} tokens), truncando contexto")
            context = self.get_context_for_query(question, k=3, include_summary=True, include_history=False)
            prompt = prompt.replace(context, context[:8000])
        
        response = self.gemini_client.generar_contenido(
            prompt,
            modelo=model,
            operation_type="chat",
            use_cache=False
        )
        
        # Limpiar la respuesta
        if response:
            response = self._limpiar_respuesta(response)
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        if response and self.conversation_memory and include_history:
            self.conversation_memory.add_message(
                content=response,
                role=MessageRole.ASSISTANT,
                metadata={
                    "response_time_ms": elapsed_ms,
                    "chunks_retrieved": k,
                    "model": model
                }
            )
        
        cost_estimate = self.token_optimizer.estimate_cost(prompt, response if response else "")
        
        return {
            "pregunta": question,
            "respuesta": response,
            "tiempo_ms": round(elapsed_ms, 2),
            "tokens_entrada": prompt_tokens,
            "tokens_salida": self.token_optimizer.count_tokens(response) if response else 0,
            "costo_estimado_usd": cost_estimate["total_cost_usd"],
            "modelo_usado": model,
            "sesion_id": self.conversation_memory.session_id if self.conversation_memory else None
        }
    
    def clear_conversation(self):
        """Limpia la conversación actual."""
        if self.conversation_memory:
            self.conversation_memory.clear()
            logger.info("Conversación limpiada")
    
    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene el historial de conversación formateado."""
        if self.conversation_memory:
            return self.conversation_memory.get_conversation_for_display(limit)
        return []
    
    def save_conversation(self) -> bool:
        """Guarda la conversación actual en disco."""
        if self.conversation_memory:
            return self.conversation_memory.save_to_disk()
        return False
    
    def load_contract(self, contract_name: str) -> bool:
        """Carga un contrato previamente indexado."""
        vector_store = self._ensure_vector_store()
        
        if vector_store.load(contract_name):
            self.current_index_name = contract_name
            logger.info(f"Contrato cargado: {contract_name}")
            return True
        
        logger.warning(f"No se pudo cargar: {contract_name}")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadisticas del servicio."""
        stats = {
            "contrato_cargado": self.current_index_name,
            "tiene_resumen": self.contract_summary is not None,
            "tiene_conversacion": self.conversation_memory is not None,
            "modelo_actual": self._get_current_model()
        }
        
        if self.vector_store:
            stats["vector_store"] = self.vector_store.get_stats()
        
        if self.conversation_memory:
            stats["conversacion"] = self.conversation_memory.get_stats()
        
        if self.gemini_client:
            stats["cache"] = self.gemini_client.get_cache_stats()
        
        return stats
    
    def clear(self) -> None:
        """Limpia el indice actual y la conversación."""
        if self.vector_store:
            self.vector_store.clear()
            self.current_index_name = None
        
        if self.conversation_memory:
            self.conversation_memory.clear()
        
        self.contract_summary = None
        self.contract_metadata = {}
        
        logger.info("Servicio RAG limpiado")