"""
Servicio de embeddings para convertir texto en vectores numericos.

Utiliza Google Generative AI (Gemini) para generar embeddings.
"""

import logging
from typing import List, Optional
import numpy as np

from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Servicio para generar embeddings de texto.

    Convierte fragmentos de texto en vectores numericos para
    busqueda semantica y recuperacion en RAG.
    """

    def __init__(self, model_name: str = "models/embedding-001"):
        """
        Inicializa el servicio de embeddings.

        Args:
            model_name: Modelo de embeddings de Gemini
        """
        self.model_name = model_name
        self._model: Optional[GoogleGenerativeAIEmbeddings] = None
        self._dimension: Optional[int] = None

        logger.info(f"Inicializando embeddings con Gemini: {model_name}")

    @property
    def model(self) -> GoogleGenerativeAIEmbeddings:
        """
        Lazy loading del modelo.
        """
        if self._model is None:
            logger.info("Cargando modelo de embeddings Gemini...")
            self._model = GoogleGenerativeAIEmbeddings(
                model=self.model_name
            )
        return self._model

    @property
    def dimension(self) -> int:
        """
        Dimension del embedding.

        NOTA: Gemini no la expone directamente,
        así que la calculamos dinámicamente.
        """
        if self._dimension is None:
            test_embedding = self.embed_text("test")
            self._dimension = len(test_embedding)
            logger.info(f"Dimension detectada: {self._dimension}")

        return self._dimension

    def embed_text(self, texto: str) -> np.ndarray:
        """
        Embedding de un solo texto.
        """
        if not texto or not texto.strip():
            logger.warning("Texto vacío para embedding")
            return np.zeros(self.dimension)

        try:
            embedding = self.model.embed_query(texto)
            return np.array(embedding, dtype=np.float32)

        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise

    def embed_texts(self, textos: List[str]) -> np.ndarray:
        """
        Embeddings batch.
        """
        if not textos:
            logger.warning("Lista vacía")
            return np.array([])

        textos_validos = [t for t in textos if t and t.strip()]

        if not textos_validos:
            logger.warning("No hay textos válidos")
            return np.array([])

        try:
            embeddings = self.model.embed_documents(textos_validos)
            return np.array(embeddings, dtype=np.float32)

        except Exception as e:
            logger.error(f"Error en batch embeddings: {e}")
            raise

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Agrega embeddings a chunks.
        """
        if not chunks:
            return []

        textos = [chunk["texto"] for chunk in chunks]
        embeddings = self.embed_texts(textos)

        resultado = []
        for i, chunk in enumerate(chunks):
            nuevo = chunk.copy()
            nuevo["embedding"] = embeddings[i]
            resultado.append(nuevo)

        logger.info(f"Embeddings generados para {len(resultado)} chunks")
        return resultado