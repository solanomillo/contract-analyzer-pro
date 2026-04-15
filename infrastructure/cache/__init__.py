# infrastructure/cache/__init__.py
"""Módulo de caché para respuestas de LLM y embeddings"""

from infrastructure.cache.response_cache import ResponseCache, get_global_cache

__all__ = ['ResponseCache', 'get_global_cache']