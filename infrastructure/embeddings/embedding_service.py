"""
Servicio de embeddings utilizando Gemini API.
Convierte texto en vectores numericos para busqueda semantica.
"""

import logging
import os
from typing import List, Optional
import numpy as np

from google import genai

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Servicio para generar embeddings usando Gemini.
    
    Convierte fragmentos de texto en vectores numericos
    para busqueda semantica y recuperacion en RAG.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-embedding-2-preview"):
        """
        Inicializa el servicio de embeddings.
        
        Args:
            api_key: API key de Gemini (si no se provee, usa .env)
            model_name: Modelo de embedding a utilizar
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None
        self._dimension: Optional[int] = None
        
        logger.info(f"Servicio de embeddings inicializado con modelo: {model_name}")
    
    @property
    def client(self):
        """Obtiene el cliente de Gemini."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("API key no configurada")
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    @property
    def dimension(self) -> int:
        """
        Obtiene la dimension de los embeddings.
        
        Returns:
            Dimension del vector de embedding
        """
        if self._dimension is None:
            # Probar con un texto corto
            embedding = self.embed_text("test")
            self._dimension = len(embedding)
            logger.info(f"Dimension de embedding detectada: {self._dimension}")
        return self._dimension
    
    def embed_text(self, texto: str) -> np.ndarray:
        """
        Genera embedding para un solo texto.
        
        Args:
            texto: Texto a convertir en embedding
            
        Returns:
            Vector numpy con el embedding
        """
        if not texto or len(texto.strip()) == 0:
            logger.warning("Texto vacio para embedding")
            return np.zeros(self.dimension)
        
        try:
            # Limitar texto a 2000 caracteres (limite recomendado)
            texto_procesado = texto[:2000] if len(texto) > 2000 else texto
            
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=texto_procesado
            )
            
            embedding = np.array(result.embeddings[0].values, dtype=np.float32)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise
    
    def embed_texts(self, textos: List[str]) -> np.ndarray:
        """
        Genera embeddings para multiples textos.
        
        Args:
            textos: Lista de textos a convertir
            
        Returns:
            Matriz numpy con los embeddings
        """
        if not textos:
            logger.warning("Lista de textos vacia")
            return np.array([])
        
        # Filtrar textos vacios
        textos_validos = []
        for t in textos:
            if t and len(t.strip()) > 0:
                textos_validos.append(t[:2000] if len(t) > 2000 else t)
        
        if not textos_validos:
            logger.warning("No hay textos validos")
            return np.array([])
        
        try:
            embeddings = []
            for texto in textos_validos:
                emb = self.embed_text(texto)
                embeddings.append(emb)
            
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error generando embeddings batch: {e}")
            raise
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Genera embeddings para una lista de chunks y los enriquece.
        
        Args:
            chunks: Lista de chunks con campo 'texto'
            
        Returns:
            Lista de chunks enriquecidos con campo 'embedding'
        """
        if not chunks:
            return []
        
        textos = [chunk["texto"] for chunk in chunks]
        embeddings = self.embed_texts(textos)
        
        chunks_con_embedding = []
        for i, chunk in enumerate(chunks):
            nuevo_chunk = chunk.copy()
            nuevo_chunk["embedding"] = embeddings[i]
            chunks_con_embedding.append(nuevo_chunk)
        
        logger.info(f"Embeddings generados para {len(chunks_con_embedding)} chunks")
        return chunks_con_embedding