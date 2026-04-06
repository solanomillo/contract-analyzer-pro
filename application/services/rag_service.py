"""
Servicio RAG (Retrieval-Augmented Generation) para contratos.
Integra embeddings, vector store y busqueda semantica.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from infrastructure.embeddings.embedding_service import EmbeddingService
from infrastructure.vector_db.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGService:
    """
    Servicio RAG para procesamiento y consulta de contratos.
    
    Permite indexar contratos y hacer consultas semanticas.
    """
    
    def __init__(self, persist_dir: Path = Path("data/vector_store")):
        """
        Inicializa el servicio RAG.
        
        Args:
            persist_dir: Directorio para persistencia
        """
        self.persist_dir = persist_dir
        self.embedding_service = EmbeddingService()
        self.vector_store: Optional[VectorStore] = None
        self.current_index_name: Optional[str] = None
        
        logger.info("Servicio RAG inicializado")
    
    def _ensure_vector_store(self) -> VectorStore:
        """Asegura que el vector store esta inicializado."""
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
        
        # Generar embeddings
        chunks_con_embedding = self.embedding_service.embed_chunks(chunks)
        
        # Obtener vector store
        vector_store = self._ensure_vector_store()
        
        # Limpiar indice anterior
        nombre_indice = contract_data.get("nombre_archivo", "contract").replace(".pdf", "").replace(".txt", "")
        
        if self.current_index_name != nombre_indice:
            vector_store.clear()
            self.current_index_name = nombre_indice
        
        # Agregar chunks
        chunks_agregados = vector_store.add_chunks(chunks_con_embedding)
        
        # Guardar
        vector_store.save(nombre_indice)
        
        resultado = {
            "nombre_indice": nombre_indice,
            "chunks_indexados": chunks_agregados,
            "total_chunks": len(chunks),
            "estado": "exito" if chunks_agregados > 0 else "fallo"
        }
        
        logger.info(f"Indexacion completada: {resultado}")
        return resultado
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca chunks relevantes para una consulta.
        
        Args:
            query: Texto de la consulta
            k: Numero de resultados
            
        Returns:
            Lista de chunks relevantes
        """
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
    
    def get_context_for_query(self, query: str, k: int = 3) -> str:
        """
        Obtiene contexto relevante para una consulta.
        
        Args:
            query: Consulta del usuario
            k: Numero de chunks a recuperar
            
        Returns:
            Texto concatenado de los chunks relevantes
        """
        resultados = self.search(query, k)
        
        if not resultados:
            return "No se encontro informacion relevante en el contrato."
        
        contextos = []
        for i, resultado in enumerate(resultados, 1):
            texto = resultado.get("texto", "")
            score = resultado.get("score", 0)
            contextos.append(f"[Contexto {i} - Relevancia: {score:.3f}]\n{texto}")
        
        return "\n\n".join(contextos)
    
    def load_contract(self, contract_name: str) -> bool:
        """
        Carga un contrato previamente indexado.
        
        Args:
            contract_name: Nombre del contrato
            
        Returns:
            True si se cargo exitosamente
        """
        vector_store = self._ensure_vector_store()
        
        if vector_store.load(contract_name):
            self.current_index_name = contract_name
            logger.info(f"Contrato cargado: {contract_name}")
            return True
        
        logger.warning(f"No se pudo cargar: {contract_name}")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas del indice actual.
        
        Returns:
            Diccionario con estadisticas
        """
        if self.vector_store is None:
            return {"error": "No hay vector store inicializado"}
        
        return self.vector_store.get_stats()
    
    def clear(self) -> None:
        """Limpia el indice actual."""
        if self.vector_store:
            self.vector_store.clear()
            self.current_index_name = None
            logger.info("Indice limpiado")