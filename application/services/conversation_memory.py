# application/services/conversation_memory.py
"""
Sistema de memoria conversacional para chat con contratos.
Implementa memoria corto/mediano plazo y resúmenes automáticos.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Rol del mensaje en la conversación"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Mensaje individual en la conversación"""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Crea desde diccionario"""
        return cls(
            id=data["id"],
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationSummary:
    """Resumen de la conversación para memoria mediano plazo"""
    summary: str
    created_at: datetime
    message_range: Tuple[int, int]  # Índices de mensajes que resume
    token_count: int = 0


class ConversationMemory:
    """
    Memoria conversacional con múltiples niveles.
    
    Niveles de memoria:
    - Corto plazo: Últimos N mensajes (ventana deslizante por tokens)
    - Mediano plazo: Resúmenes periódicos de conversaciones pasadas
    - Largo plazo: Persistencia en disco por sesión
    
    Soporta:
    - Preguntas de seguimiento ("¿Qué dijiste sobre...?")
    - Referencias a mensajes anteriores
    - Contexto coherente entre preguntas
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        max_tokens_short_term: int = 8000,
        max_messages_short_term: int = 20,
        summary_interval: int = 10,  # Resumir cada N mensajes
        persist_dir: str = "data/conversations"
    ):
        """
        Args:
            session_id: ID de sesión (si None, se genera uno nuevo)
            max_tokens_short_term: Máximo de tokens en memoria corto plazo
            max_messages_short_term: Máximo de mensajes en memoria corto plazo
            summary_interval: Cada cuántos mensajes generar resumen
            persist_dir: Directorio para persistencia
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.max_tokens_short_term = max_tokens_short_term
        self.max_messages_short_term = max_messages_short_term
        self.summary_interval = summary_interval
        
        # Memoria corto plazo (mensajes recientes)
        self.short_term_messages: List[Message] = []
        
        # Memoria mediano plazo (resúmenes)
        self.summaries: List[ConversationSummary] = []
        
        # Contador para resúmenes
        self._message_count_since_last_summary = 0
        
        # Metadatos de sesión
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata: Dict[str, Any] = {}
        
        # Referencias para preguntas de seguimiento
        self._message_references: Dict[str, List[str]] = {}  # "palabra_clave" -> [message_ids]
        
        self.persist_dir = persist_dir
        
        logger.info(f"ConversationMemory creada: session_id={self.session_id}")
    
    def add_message(
        self,
        content: str,
        role: MessageRole,
        token_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Agrega un mensaje a la conversación.
        
        Args:
            content: Contenido del mensaje
            role: Rol (user/assistant/system)
            token_count: Conteo de tokens (opcional)
            metadata: Metadatos adicionales
            
        Returns:
            Mensaje creado
        """
        if token_count is None:
            from application.services.token_optimizer import get_token_optimizer
            optimizer = get_token_optimizer()
            token_count = optimizer.count_tokens(content)
        
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            token_count=token_count,
            metadata=metadata or {}
        )
        
        self.short_term_messages.append(message)
        self.last_activity = datetime.now()
        
        # Extraer referencias para preguntas de seguimiento
        self._extract_references(message)
        
        # Verificar si necesitamos resumir
        self._message_count_since_last_summary += 1
        if self._message_count_since_last_summary >= self.summary_interval:
            self._summarize_conversation()
        
        # Mantener ventana deslizante
        self._maintain_window()
        
        logger.debug(f"Mensaje agregado: {message.id[:8]}..., rol={role.value}, tokens={token_count}")
        return message
    
    def _extract_references(self, message: Message):
        """
        Extrae palabras clave para referencias cruzadas.
        Útil para preguntas como "¿Qué dijiste sobre la cláusula X?"
        """
        import re
        
        # Patrones de referencia comunes
        patterns = [
            r'cláusula\s+(\d+(?:\.\d+)?)',  # cláusula 3, cláusula 4.1
            r'sección\s+(\d+(?:\.\d+)?)',   # sección 2
            r'artículo\s+(\d+(?:\.\d+)?)',   # artículo 5
            r'página\s+(\d+)',               # página 42
            r'\"([^\"]+)\"',                  # "término específico"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message.content, re.IGNORECASE)
            for match in matches:
                key = f"{pattern}:{match.lower()}"
                if key not in self._message_references:
                    self._message_references[key] = []
                self._message_references[key].append(message.id)
    
    def get_relevant_messages_for_query(self, query: str) -> List[Message]:
        """
        Obtiene mensajes relevantes para una pregunta de seguimiento.
        
        Args:
            query: Pregunta del usuario
            
        Returns:
            Lista de mensajes relevantes
        """
        relevant = []
        
        # Buscar por referencias explícitas
        import re
        for pattern, keys in self._message_references.items():
            pattern_type, value = pattern.split(":", 1)
            if value.lower() in query.lower():
                # Encontrar mensajes con esta referencia
                for msg_id in keys:
                    msg = self._find_message_by_id(msg_id)
                    if msg and msg not in relevant:
                        relevant.append(msg)
        
        # Si no hay referencias, devolver últimos 3 mensajes
        if not relevant:
            relevant = self.short_term_messages[-6:-2] if len(self.short_term_messages) > 4 else []
        
        return relevant
    
    def _find_message_by_id(self, message_id: str) -> Optional[Message]:
        """Encuentra un mensaje por su ID"""
        for msg in self.short_term_messages:
            if msg.id == message_id:
                return msg
        return None
    
    def _maintain_window(self):
        """Mantiene la ventana deslizante de memoria corto plazo"""
        # Recortar por número de mensajes
        while len(self.short_term_messages) > self.max_messages_short_term:
            removed = self.short_term_messages.pop(0)
            logger.debug(f"Removido por límite de mensajes: {removed.id[:8]}...")
        
        # Recortar por tokens
        total_tokens = sum(m.token_count for m in self.short_term_messages)
        while total_tokens > self.max_tokens_short_term and len(self.short_term_messages) > 2:
            removed = self.short_term_messages.pop(0)
            total_tokens -= removed.token_count
            logger.debug(f"Removido por límite de tokens: {removed.id[:8]}...")
    
    def _summarize_conversation(self):
        """Genera resumen de la conversación para memoria mediano plazo"""
        if len(self.short_term_messages) < 3:
            return
        
        # Tomar mensajes desde el último resumen
        start_idx = 0
        if self.summaries:
            last_summary = self.summaries[-1]
            start_idx = last_summary.message_range[1]
        
        messages_to_summarize = self.short_term_messages[start_idx:]
        
        if len(messages_to_summarize) < 3:
            return
        
        # Construir texto para resumir
        conversation_text = "\n".join([
            f"{msg.role.value}: {msg.content}"
            for msg in messages_to_summarize
        ])
        
        # Aquí se llamaría a Gemini para generar el resumen
        # Por ahora, creamos un resumen simple
        summary_text = f"[Resumen de {len(messages_to_summarize)} mensajes: {conversation_text[:200]}...]"
        
        summary = ConversationSummary(
            summary=summary_text,
            created_at=datetime.now(),
            message_range=(start_idx, len(self.short_term_messages)),
            token_count=len(summary_text) // 4  # Estimación
        )
        
        self.summaries.append(summary)
        self._message_count_since_last_summary = 0
        
        logger.info(f"Resumen generado: {len(messages_to_summarize)} mensajes -> {summary.token_count} tokens")
    
    def get_context_for_prompt(
        self,
        current_query: str,
        include_summaries: bool = True,
        max_tokens: int = 6000
    ) -> Tuple[str, List[Message]]:
        """
        Obtiene contexto para incluir en el prompt.
        
        Args:
            current_query: Consulta actual del usuario
            include_summaries: Incluir resúmenes de conversaciones pasadas
            max_tokens: Máximo de tokens para el contexto
            
        Returns:
            Tuple de (contexto_texto, lista_de_mensajes_relevantes)
        """
        from application.services.token_optimizer import get_token_optimizer
        optimizer = get_token_optimizer()
        
        context_parts = []
        used_messages = []
        current_tokens = 0
        
        # 1. Resúmenes (memoria mediano plazo)
        if include_summaries and self.summaries:
            for summary in reversed(self.summaries):
                if current_tokens + summary.token_count <= max_tokens:
                    context_parts.insert(0, f"[Resumen de conversación anterior]:\n{summary.summary}")
                    current_tokens += summary.token_count
                else:
                    break
        
        # 2. Mensajes recientes (memoria corto plazo)
        for msg in reversed(self.short_term_messages):
            msg_text = f"{msg.role.value}: {msg.content}"
            msg_tokens = optimizer.count_tokens(msg_text)
            
            if current_tokens + msg_tokens <= max_tokens:
                context_parts.insert(0, msg_text)
                used_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        # 3. Mensajes relevantes para la consulta actual
        relevant_messages = self.get_relevant_messages_for_query(current_query)
        for msg in relevant_messages:
            if msg not in used_messages:
                msg_text = f"[Referencia anterior - {msg.role.value}]: {msg.content[:200]}..."
                msg_tokens = optimizer.count_tokens(msg_text)
                if current_tokens + msg_tokens <= max_tokens:
                    context_parts.append(msg_text)
                    current_tokens += msg_tokens
        
        context = "\n\n".join(context_parts) if context_parts else ""
        
        logger.info(f"Contexto preparado: {len(context_parts)} partes, {current_tokens} tokens")
        return context, used_messages
    
    def get_conversation_for_display(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene la conversación formateada para mostrar en UI"""
        messages = self.short_term_messages[-limit:]
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.strftime("%H:%M:%S"),
                "id": msg.id
            }
            for msg in messages
        ]
    
    def clear(self):
        """Limpia toda la memoria (nueva conversación)"""
        self.short_term_messages.clear()
        self.summaries.clear()
        self._message_count_since_last_summary = 0
        self._message_references.clear()
        self.last_activity = datetime.now()
        logger.info(f"Memoria limpiada: session_id={self.session_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria"""
        total_tokens = sum(m.token_count for m in self.short_term_messages)
        
        return {
            "session_id": self.session_id,
            "total_messages": len(self.short_term_messages),
            "total_tokens": total_tokens,
            "num_summaries": len(self.summaries),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_references": len(self._message_references)
        }
    
    def save_to_disk(self) -> bool:
        """Persiste la conversación en disco"""
        try:
            import os
            from pathlib import Path
            
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            filepath = Path(self.persist_dir) / f"{self.session_id}.json"
            
            data = {
                "session_id": self.session_id,
                "created_at": self.created_at.isoformat(),
                "last_activity": self.last_activity.isoformat(),
                "short_term_messages": [m.to_dict() for m in self.short_term_messages],
                "summaries": [
                    {
                        "summary": s.summary,
                        "created_at": s.created_at.isoformat(),
                        "message_range": s.message_range,
                        "token_count": s.token_count
                    }
                    for s in self.summaries
                ],
                "metadata": self.metadata
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Conversación guardada: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error guardando conversación: {e}")
            return False
    
    def load_from_disk(self, session_id: str) -> bool:
        """Carga una conversación desde disco"""
        try:
            from pathlib import Path
            
            filepath = Path(self.persist_dir) / f"{session_id}.json"
            if not filepath.exists():
                return False
            
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.session_id = data["session_id"]
            self.created_at = datetime.fromisoformat(data["created_at"])
            self.last_activity = datetime.fromisoformat(data["last_activity"])
            self.short_term_messages = [Message.from_dict(m) for m in data["short_term_messages"]]
            self.summaries = [
                ConversationSummary(
                    summary=s["summary"],
                    created_at=datetime.fromisoformat(s["created_at"]),
                    message_range=tuple(s["message_range"]),
                    token_count=s["token_count"]
                )
                for s in data.get("summaries", [])
            ]
            self.metadata = data.get("metadata", {})
            
            logger.info(f"Conversación cargada: {filepath}, {len(self.short_term_messages)} mensajes")
            return True
        except Exception as e:
            logger.error(f"Error cargando conversación: {e}")
            return False


# Fábrica para gestionar múltiples sesiones
class ConversationMemoryFactory:
    """Fábrica para crear y gestionar múltiples conversaciones"""
    
    _instances: Dict[str, ConversationMemory] = {}
    
    @classmethod
    def get_or_create(
        cls,
        session_id: Optional[str] = None,
        **kwargs
    ) -> ConversationMemory:
        """Obtiene una conversación existente o crea una nueva"""
        if session_id and session_id in cls._instances:
            return cls._instances[session_id]
        
        memory = ConversationMemory(session_id=session_id, **kwargs)
        cls._instances[memory.session_id] = memory
        return memory
    
    @classmethod
    def clear_session(cls, session_id: str):
        """Limpia y elimina una sesión"""
        if session_id in cls._instances:
            cls._instances[session_id].clear()
            del cls._instances[session_id]
    
    @classmethod
    def list_sessions(cls) -> List[str]:
        """Lista todas las sesiones activas"""
        return list(cls._instances.keys())