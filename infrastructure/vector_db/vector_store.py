"""
Servicio de base de datos vectorial con FAISS.
Almacena y recupera embeddings para busqueda semantica.
"""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Almacen vectorial usando FAISS para busqueda de similitud.
    
    Permite guardar, cargar y buscar embeddings de chunks de texto.
    """
    
    def __init__(self, dimension: int, persist_dir: Path = Path("data/vector_store")):
        """
        Inicializa el almacen vectorial.
        
        Args:
            dimension: Dimension de los embeddings
            persist_dir: Directorio para persistencia
        """
        self.dimension = dimension
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Indice FAISS usando producto interno (cosine similarity)
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks: List[Dict[str, Any]] = []
        self.current_id = 0
        
        logger.info(f"Vector store inicializado. Dimension: {dimension}")
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Agrega chunks al indice vectorial.
        
        Args:
            chunks: Lista de chunks con campo 'embedding'
            
        Returns:
            Numero de chunks agregados
        """
        if not chunks:
            logger.warning("No hay chunks para agregar")
            return 0
        
        embeddings = []
        chunks_validos = []
        
        for chunk in chunks:
            if "embedding" in chunk and chunk["embedding"] is not None:
                embedding = chunk["embedding"]
                if isinstance(embedding, np.ndarray):
                    embeddings.append(embedding)
                    chunks_validos.append(chunk)
        
        if not embeddings:
            logger.warning("No hay embeddings validos")
            return 0
        
        embeddings_matrix = np.array(embeddings).astype('float32')
        self.index.add(embeddings_matrix)
        
        for chunk in chunks_validos:
            chunk["id"] = self.current_id
            self.chunks.append(chunk)
            self.current_id += 1
        
        logger.info(f"Agregados {len(chunks_validos)} chunks")
        return len(chunks_validos)
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca los chunks mas similares.
        
        Args:
            query_embedding: Embedding de la consulta
            k: Numero de resultados
            
        Returns:
            Lista de chunks con scores
        """
        if self.index.ntotal == 0:
            logger.warning("Indice vacio")
            return []
        
        query_vector = query_embedding.reshape(1, -1).astype('float32')
        scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        resultados = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(score)
                resultados.append(chunk)
        
        logger.info(f"Busqueda retorno {len(resultados)} resultados")
        return resultados
    
    def save(self, name: str = "contract_index") -> None:
        """
        Guarda el indice en disco.
        
        Args:
            name: Nombre base del archivo
        """
        index_path = self.persist_dir / f"{name}.faiss"
        faiss.write_index(self.index, str(index_path))
        
        metadata_path = self.persist_dir / f"{name}.pkl"
        metadata = {
            "chunks": self.chunks,
            "current_id": self.current_id,
            "dimension": self.dimension
        }
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Vector store guardado en: {self.persist_dir}")
    
    def load(self, name: str = "contract_index") -> bool:
        """
        Carga el indice desde disco.
        
        Args:
            name: Nombre base del archivo
            
        Returns:
            True si se cargo correctamente
        """
        index_path = self.persist_dir / f"{name}.faiss"
        metadata_path = self.persist_dir / f"{name}.pkl"
        
        if not index_path.exists() or not metadata_path.exists():
            logger.warning(f"No se encontraron archivos: {name}")
            return False
        
        try:
            self.index = faiss.read_index(str(index_path))
            
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.chunks = metadata["chunks"]
            self.current_id = metadata["current_id"]
            self.dimension = metadata["dimension"]
            
            logger.info(f"Vector store cargado. {len(self.chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando: {e}")
            return False
    
    def clear(self) -> None:
        """Limpia el indice."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []
        self.current_id = 0
        logger.info("Vector store limpiado")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas.
        
        Returns:
            Diccionario con estadisticas
        """
        return {
            "total_chunks": len(self.chunks),
            "dimension": self.dimension,
            "index_size": self.index.ntotal,
            "persist_dir": str(self.persist_dir)
        }