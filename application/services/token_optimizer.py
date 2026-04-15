"""
Optimizador de tokens para Gemini API.
Implementa conteo preciso de tokens, chunking inteligente y ventanas deslizantes.
TOTALMENTE DINÁMICO - No tiene modelos estáticos hardcodeados.
"""

import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Intentar importar tiktoken para conteo preciso de tokens
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken no instalado. Usando estimación aproximada de tokens.")


@dataclass
class ChunkInfo:
    """Información de un chunk de texto"""
    text: str
    start_index: int
    end_index: int
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class TokenOptimizer:
    """
    Optimizador de tokens para Gemini.
    TOTALMENTE DINÁMICO - Soporta cualquier modelo que Gemini devuelva.
    
    Características:
    - Conteo preciso de tokens (usando tiktoken)
    - Chunking inteligente por cláusulas/secciones
    - Ventana deslizante para contexto conversacional
    - Estimación de costos dinámica por modelo
    """
    
    # Límite por defecto para cualquier modelo Gemini (1M tokens)
    DEFAULT_MODEL_LIMIT = 1_048_576
    
    # Límite para modelos Pro (2M tokens)
    PRO_MODEL_LIMIT = 2_097_152
    
    # Costos por defecto (estimación conservadora)
    DEFAULT_COSTS = {"input": 0.10, "output": 0.40}
    
    def __init__(self, model_name: str = None):
        """
        Args:
            model_name: Nombre del modelo Gemini (puede ser None, se setea después)
        """
        self._model_name = model_name
        self._encoder = None
        
        if TIKTOKEN_AVAILABLE:
            try:
                self._encoder = tiktoken.get_encoding("cl100k_base")
                logger.info(f"TokenOptimizer inicializado con tiktoken")
            except Exception as e:
                logger.warning(f"No se pudo inicializar tiktoken: {e}")
    
    @property
    def model_name(self) -> str:
        """Retorna el nombre del modelo actual"""
        return self._model_name or "desconocido"
    
    @model_name.setter
    def model_name(self, value: str):
        """Actualiza el modelo dinámicamente"""
        old = self._model_name
        self._model_name = value
        if old != value:
            logger.info(f"TokenOptimizer modelo actualizado: {old} -> {value}")
    
    def update_model(self, model_name: str):
        """Método explícito para actualizar el modelo (desde UI)"""
        self.model_name = model_name
    
    def get_model_limit(self) -> int:
        """
        Retorna el límite de tokens del modelo actual.
        Dinámico - basado en el nombre del modelo, no en una lista fija.
        """
        if not self._model_name:
            return self.DEFAULT_MODEL_LIMIT
        
        nombre_lower = self._model_name.lower()
        
        # Modelos Pro tienen 2M tokens
        if "pro" in nombre_lower and "flash" not in nombre_lower:
            return self.PRO_MODEL_LIMIT
        
        # Por defecto, 1M tokens
        return self.DEFAULT_MODEL_LIMIT
    
    def get_costs(self) -> Dict[str, float]:
        """
        Retorna los costos estimados del modelo actual.
        Dinámico - basado en el nombre del modelo.
        """
        if not self._model_name:
            return self.DEFAULT_COSTS
        
        nombre_lower = self._model_name.lower()
        
        # Modelos Flash (económicos)
        if "flash" in nombre_lower:
            return {"input": 0.075, "output": 0.30}
        
        # Modelos Pro (caros)
        elif "pro" in nombre_lower:
            return {"input": 1.25, "output": 5.00}
        
        # Modelos desconocidos - estimación conservadora
        else:
            return self.DEFAULT_COSTS
    
    def count_tokens(self, text: str) -> int:
        """Cuenta tokens en un texto"""
        if not text:
            return 0
        
        if self._encoder:
            return len(self._encoder.encode(text))
        
        # Estimación aproximada: ~4 caracteres por token para español/inglés
        return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Cuenta tokens en una lista de mensajes (formato chat)"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get("content", ""))
            total += 4  # Overhead por mensaje
        total += 2  # Overhead inicial
        return total
    
    def chunk_text_intelligent(
        self,
        text: str,
        max_tokens: int = 8000,
        overlap_tokens: int = 200
    ) -> List[ChunkInfo]:
        """
        Divide texto en chunks inteligentes.
        
        Args:
            text: Texto a dividir
            max_tokens: Máximo de tokens por chunk
            overlap_tokens: Tokens de superposición entre chunks
        """
        if self.count_tokens(text) <= max_tokens:
            return [ChunkInfo(
                text=text,
                start_index=0,
                end_index=len(text),
                token_count=self.count_tokens(text),
                metadata={"type": "single"}
            )]
        
        chunks = []
        current_position = 0
        
        # Dividir por párrafos
        paragraphs = self._split_by_paragraphs(text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_start = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            if current_tokens + para_tokens <= max_tokens:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    chunk_start = text.find(para, current_position)
                current_tokens += para_tokens
            else:
                # Guardar chunk actual
                if current_chunk:
                    chunks.append(ChunkInfo(
                        text=current_chunk,
                        start_index=chunk_start,
                        end_index=chunk_start + len(current_chunk),
                        token_count=current_tokens,
                        metadata={"type": "paragraph"}
                    ))
                
                # Si el párrafo es muy largo, dividirlo
                if para_tokens > max_tokens:
                    sub_chunks = self._chunk_long_paragraph(para, max_tokens, overlap_tokens)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                    current_tokens = 0
                else:
                    current_chunk = para
                    chunk_start = text.find(para, current_position)
                    current_tokens = para_tokens
            
            current_position = text.find(para, current_position) + len(para)
        
        # Último chunk
        if current_chunk:
            chunks.append(ChunkInfo(
                text=current_chunk,
                start_index=chunk_start,
                end_index=chunk_start + len(current_chunk),
                token_count=current_tokens,
                metadata={"type": "paragraph"}
            ))
        
        # Agregar overlap
        if overlap_tokens > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks, overlap_tokens)
        
        logger.info(f"Chunking: {len(chunks)} chunks, avg tokens: {sum(c.token_count for c in chunks)//len(chunks)}")
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Divide texto en párrafos"""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _chunk_long_paragraph(
        self,
        paragraph: str,
        max_tokens: int,
        overlap_tokens: int
    ) -> List[ChunkInfo]:
        """Divide un párrafo muy largo por oraciones"""
        sentences = self._split_by_sentences(paragraph)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        start_idx = 0
        
        for sent in sentences:
            sent_tokens = self.count_tokens(sent)
            
            if current_tokens + sent_tokens <= max_tokens:
                if current_chunk:
                    current_chunk += " " + sent
                else:
                    current_chunk = sent
                current_tokens += sent_tokens
            else:
                if current_chunk:
                    chunks.append(ChunkInfo(
                        text=current_chunk,
                        start_index=start_idx,
                        end_index=start_idx + len(current_chunk),
                        token_count=current_tokens,
                        metadata={"type": "sentence"}
                    ))
                    start_idx += len(current_chunk)
                
                current_chunk = sent
                current_tokens = sent_tokens
        
        if current_chunk:
            chunks.append(ChunkInfo(
                text=current_chunk,
                start_index=start_idx,
                end_index=start_idx + len(current_chunk),
                token_count=current_tokens,
                metadata={"type": "sentence"}
            ))
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Divide texto en oraciones"""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _add_overlap(self, chunks: List[ChunkInfo], overlap_tokens: int) -> List[ChunkInfo]:
        """Agrega superposición entre chunks"""
        if overlap_tokens <= 0:
            return chunks
        
        result = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                prev_chunk = result[-1]
                prev_text = prev_chunk.text
                prev_tokens = prev_chunk.token_count
                
                if prev_tokens > overlap_tokens:
                    overlap_len = int(len(prev_text) * (overlap_tokens / prev_tokens))
                    overlap_text = prev_text[-overlap_len:] if overlap_len > 0 else ""
                else:
                    overlap_text = prev_text
                
                chunk.text = overlap_text + "\n...\n" + chunk.text
            
            result.append(chunk)
        
        return result
    
    def sliding_window_context(
        self,
        conversation_history: List[Dict[str, str]],
        max_tokens: int,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Crea ventana deslizante de contexto conversacional"""
        if not conversation_history:
            return []
        
        system_tokens = self.count_tokens(system_prompt) if system_prompt else 0
        available_tokens = max_tokens - system_tokens - 100
        
        selected_messages = []
        total_tokens = 0
        
        for msg in reversed(conversation_history):
            msg_tokens = self.count_tokens(msg.get("content", "")) + 4
            
            if total_tokens + msg_tokens <= available_tokens:
                selected_messages.insert(0, msg)
                total_tokens += msg_tokens
            else:
                break
        
        if len(selected_messages) < len(conversation_history):
            logger.info(f"Ventana: {len(selected_messages)}/{len(conversation_history)} mensajes, {total_tokens} tokens")
        
        return selected_messages
    
    def estimate_cost(
        self,
        input_text: str,
        output_text: Optional[str] = None
    ) -> Dict[str, float]:
        """Estimación del costo de una llamada a Gemini"""
        input_tokens = self.count_tokens(input_text)
        costs = self.get_costs()
        
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        
        output_cost = 0
        output_tokens = 0
        if output_text:
            output_tokens = self.count_tokens(output_text)
            output_cost = (output_tokens / 1_000_000) * costs["output"]
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(input_cost + output_cost, 6),
            "model": self.model_name
        }
    
    def truncate_to_limit(
        self,
        text: str,
        max_tokens: int,
        suffix: str = "..."
    ) -> str:
        """Trunca texto a un límite de tokens"""
        if self.count_tokens(text) <= max_tokens:
            return text
        
        if self._encoder:
            tokens = self._encoder.encode(text)
            truncated_tokens = tokens[:max_tokens - self.count_tokens(suffix)]
            return self._encoder.decode(truncated_tokens) + suffix
        
        return text[:max_tokens * 4] + suffix
    
    def is_safe_to_send(self, text: str, buffer_tokens: int = 1000) -> bool:
        """Verifica si es seguro enviar texto al modelo"""
        token_count = self.count_tokens(text)
        limit = self.get_model_limit()
        return token_count + buffer_tokens <= limit


# Instancia global
_global_optimizer: Optional[TokenOptimizer] = None

def get_token_optimizer(model_name: Optional[str] = None) -> TokenOptimizer:
    """Obtiene instancia global del optimizador de tokens"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = TokenOptimizer(model_name)
    elif model_name is not None and _global_optimizer.model_name != model_name:
        _global_optimizer.update_model(model_name)
    return _global_optimizer