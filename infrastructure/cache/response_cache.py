# infrastructure/cache/response_cache.py
"""
Sistema de caché persistente para respuestas de LLM y embeddings.
Implementa TTL, LRU y persistencia en disco.
"""

import json
import hashlib
import time
import threading
from pathlib import Path
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, asdict
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Entrada individual en el caché"""
    key: str
    value: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_access: float = None
    
    def __post_init__(self):
        if self.last_access is None:
            self.last_access = self.timestamp
    
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl
    
    def touch(self):
        self.last_access = time.time()
        self.access_count += 1


class ResponseCache:
    """
    Caché genérico con persistencia en disco.
    Features: TTL, LRU, thread-safe, persistencia automática
    """
    
    def __init__(self, cache_dir: str = "data/cache", 
                 max_size: int = 1000,
                 default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        self._load_from_disk()
        logger.info(f"ResponseCache inicializado en {cache_dir}, max_size={max_size}, ttl={default_ttl}s")
    
    def _generate_key(self, data: Any) -> str:
        """Genera clave SHA256 a partir de datos serializables"""
        if isinstance(data, str):
            key_str = data
        elif isinstance(data, dict):
            key_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, (list, tuple)):
            key_str = json.dumps(data, sort_keys=True)
        else:
            key_str = str(data)
        
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()
    
    def get(self, key_or_data: Any) -> Optional[Any]:
        """Obtiene valor del caché"""
        with self._lock:
            if isinstance(key_or_data, str) and len(key_or_data) == 64:
                key = key_or_data
            else:
                key = self._generate_key(key_or_data)
            
            if key in self._cache:
                entry = self._cache[key]
                
                if entry.is_expired():
                    del self._cache[key]
                    logger.debug(f"Cache entry expired: {key[:16]}...")
                    return None
                
                entry.touch()
                self._cache.move_to_end(key)
                logger.debug(f"Cache HIT: {key[:16]}...")
                return entry.value
            
            logger.debug(f"Cache MISS: {key[:16]}...")
            return None
    
    def set(self, data: Any, value: Any, ttl: Optional[int] = None) -> str:
        """Almacena valor en caché"""
        with self._lock:
            key = self._generate_key(data)
            ttl = ttl if ttl is not None else self.default_ttl
            
            if len(self._cache) >= self.max_size:
                evicted = self._cache.popitem(last=False)
                logger.debug(f"Cache LRU evicted: {evicted[0][:16]}...")
            
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            self._save_to_disk()
            logger.debug(f"Cached entry: {key[:16]}...")
            return key
    
    def get_or_set(self, data: Any, factory_func, ttl: Optional[int] = None) -> Any:
        """Obtiene o ejecuta factory si no existe"""
        cached = self.get(data)
        if cached is not None:
            return cached
        
        value = factory_func()
        self.set(data, value, ttl)
        return value
    
    def invalidate(self, key_or_data: Any):
        """Invalida entrada específica"""
        with self._lock:
            if isinstance(key_or_data, str) and len(key_or_data) == 64:
                key = key_or_data
            else:
                key = self._generate_key(key_or_data)
            
            if key in self._cache:
                del self._cache[key]
                self._save_to_disk()
                logger.debug(f"Cache invalidated: {key[:16]}...")
    
    def clear(self):
        """Limpia todo el caché"""
        with self._lock:
            self._cache.clear()
            self._save_to_disk()
            logger.info("Cache cleared")
    
    def _save_to_disk(self):
        """Persiste caché en disco"""
        try:
            cache_file = self.cache_dir / "cache_data.json"
            serializable_cache = {}
            
            for key, entry in self._cache.items():
                serializable_cache[key] = {
                    'key': entry.key,
                    'value': entry.value,
                    'timestamp': entry.timestamp,
                    'ttl': entry.ttl,
                    'access_count': entry.access_count,
                    'last_access': entry.last_access
                }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _load_from_disk(self):
        """Carga caché desde disco"""
        try:
            cache_file = self.cache_dir / "cache_data.json"
            if not cache_file.exists():
                return
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                serializable_cache = json.load(f)
            
            loaded = 0
            for key, data in serializable_cache.items():
                entry = CacheEntry(
                    key=data['key'],
                    value=data['value'],
                    timestamp=data['timestamp'],
                    ttl=data['ttl'],
                    access_count=data.get('access_count', 0),
                    last_access=data.get('last_access', data['timestamp'])
                )
                
                if not entry.is_expired():
                    self._cache[key] = entry
                    loaded += 1
            
            logger.info(f"Loaded {loaded} entries from disk cache")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del caché"""
        with self._lock:
            return {
                'total_entries': len(self._cache),
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'cache_dir': str(self.cache_dir),
                'memory_usage_mb': self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> float:
        """Estimación aproximada de uso de memoria"""
        try:
            import sys
            size = sum(sys.getsizeof(v.value) for v in self._cache.values())
            return size / (1024 * 1024)
        except:
            return 0.0


# Singleton para uso global
_global_cache: Optional[ResponseCache] = None

def get_global_cache() -> ResponseCache:
    global _global_cache
    if _global_cache is None:
        _global_cache = ResponseCache()
    return _global_cache