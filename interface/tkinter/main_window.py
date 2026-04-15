"""
Ventana principal de la aplicacion.
Version CORREGIDA: Todas las actualizaciones de UI en el hilo principal.
"""

import logging
import os
import sys
import threading
import time
import re
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox, filedialog

from interface.tkinter.components import FileUploadFrame, ProgressCard
from interface.tkinter.styles import configurar_tema, crear_titulo, crear_card
from application.services.processing_service import ProcessingService
from application.services.config_service import ConfigService
from application.services.rag_service import RAGService
from application.graph.workflow import AnalisisWorkflow
from application.services.pdf_export_service import PDFExportService
from application.services.conversation_memory import ConversationMemoryFactory
from application.services.token_optimizer import get_token_optimizer

logger = logging.getLogger(__name__)


class MainWindow:
    """Ventana principal de Contract Analyzer Pro - Con Chat Conversacional."""
    
    def __init__(self):
        """Inicializa la ventana principal."""
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Analizador de Contratos")
        
        # Configurar ventana
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        
        ancho_inicial = int(ancho_pantalla * 0.7)
        alto_inicial = int(alto_pantalla * 0.7)
        
        x = (ancho_pantalla - ancho_inicial) // 2
        y = (alto_pantalla - alto_inicial) // 2
        
        self.root.geometry(f"{ancho_inicial}x{alto_inicial}+{x}+{y}")
        self.root.minsize(1000, 700)
        self.root.maxsize(ancho_pantalla, alto_pantalla)
        
        # Configurar tema
        self.colores = configurar_tema()
        
        # Servicios
        self.processing_service = ProcessingService()
        self.config_service = ConfigService()
        self.rag_service = RAGService()
        
        # Inicializar workflow
        self.workflow = None
        self._inicializar_workflow_async()
        
        self.current_contract_data = None
        self.current_pdf_path = None
        self.current_model = None
        
        # Estado
        self.is_processing = False
        self.is_answering = False
        self.is_analyzing = False
        
        # Estado del chat
        self.chat_session_id = None
        
        # Construir UI
        self._build_ui()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _inicializar_workflow_async(self):
        """Inicializa el workflow en segundo plano."""
        def init_workflow():
            try:
                api_key = self.config_service.get_api_key()
                if api_key:
                    self.workflow = AnalisisWorkflow(api_key=api_key)
                    logger.info("Workflow inicializado correctamente")
                else:
                    logger.warning("No hay API key para inicializar workflow")
            except Exception as e:
                logger.error(f"Error inicializando workflow: {e}")
                self.workflow = None
        
        threading.Thread(target=init_workflow, daemon=True).start()
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configurar grid
        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=0)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self._build_header(main_frame)
        
        # Contenido principal (2 columnas)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Columna izquierda - Carga de PDF
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_column.grid_rowconfigure(1, weight=1)
        left_column.grid_columnconfigure(0, weight=1)
        self._build_upload_area(left_column)
        
        # Columna derecha - Pestañas
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_column.grid_rowconfigure(0, weight=1)
        right_column.grid_columnconfigure(0, weight=1)
        self._build_tab_area(right_column)
        
        # Footer
        self._build_footer(main_frame)
    
    def _build_header(self, parent):
        """Construye el header."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        titulo = crear_titulo(header_frame, "CONTRACT ANALYZER PRO", 24)
        titulo.grid(row=0, column=0, sticky="w")
        
        header_buttons = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_buttons.grid(row=0, column=1, sticky="e")
        
        self.btn_cambiar_api = ctk.CTkButton(
            header_buttons,
            text="Cambiar API Key",
            command=self._cambiar_api_key,
            width=140,
            height=30,
            fg_color="#f39c12",
            hover_color="#e67e22"
        )
        self.btn_cambiar_api.pack(side="left", padx=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            header_buttons,
            text="Sistema listo",
            font=ctk.CTkFont(size=12),
            text_color="#2ecc71"
        )
        self.status_label.pack(side="left")
    
    def _build_upload_area(self, parent):
        """Construye el area de carga."""
        upload_card = crear_card(parent)
        upload_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(
            upload_card,
            text="Cargar Contrato",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.file_upload = FileUploadFrame(
            upload_card,
            on_file_selected=self._on_file_selected,
            height=200,
            corner_radius=10,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.file_upload.pack(fill="x", padx=20, pady=(0, 20))
        
        info_card = crear_card(parent)
        info_card.grid(row=1, column=0, sticky="nsew", pady=(0, 0))
        
        ctk.CTkLabel(
            info_card,
            text="Informacion del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.info_text = ctk.CTkTextbox(info_card, wrap="word", height=120)
        self.info_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.info_text.insert("1.0", "Esperando carga de documento...")
        self.info_text.configure(state="disabled")
    
    def _build_tab_area(self, parent):
        """Construye el area de pestañas."""
        
        tabview = ctk.CTkTabview(parent)
        tabview.pack(fill="both", expand=True)
        
        # Pestaña 1: Texto del Contrato
        tab_texto = tabview.add("Texto del Contrato")
        self._build_text_tab(tab_texto)
        
        # Pestaña 2: Chat con IA
        tab_chat = tabview.add("Chat con IA")
        self._build_chat_tab(tab_chat)
        
        # Pestaña 3: Analisis Legal
        tab_analisis = tabview.add("Analisis Legal")
        self._build_analysis_tab(tab_analisis)
    
    def _build_text_tab(self, parent):
        """Construye la pestaña de texto del contrato."""
        self.progress_card = ProgressCard(parent)
        self.progress_card.hide()
        
        self.preview_text = ctk.CTkTextbox(parent, wrap="word")
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_text.insert("1.0", "El texto del contrato aparecera aqui...")
        self.preview_text.configure(state="disabled")
        
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.stats_label.pack()
    
    def _build_chat_tab(self, parent):
        """Construye la pestaña de chat conversacional con memoria persistente."""
        
        # Frame principal
        chat_frame = ctk.CTkFrame(parent, fg_color="transparent")
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header del chat
        header_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="Chat Inteligente con tu Contrato",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Información del modelo
        self.chat_model_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.chat_model_label.pack(side="left", padx=(10, 0))
        
        # Botones de control
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        self.btn_new_chat = ctk.CTkButton(
            btn_frame,
            text="Nueva Conversacion",
            command=self._new_conversation,
            width=160,
            height=32,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            state="disabled"
        )
        self.btn_new_chat.pack(side="left", padx=(0, 10))
        
        self.btn_clear_chat = ctk.CTkButton(
            btn_frame,
            text="Limpiar Chat",
            command=self._clear_chat_display,
            width=140,
            height=32,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            state="disabled"
        )
        self.btn_clear_chat.pack(side="left")
        
        # Área de mensajes (scrollable)
        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            wrap="word",
            font=ctk.CTkFont(size=13)
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 10))
        self.chat_display.insert("1.0", self._get_welcome_message())
        self.chat_display.configure(state="disabled")
        
        # Frame de entrada
        input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        input_frame.pack(fill="x")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.chat_entry = ctk.CTkTextbox(
            input_frame,
            height=80,
            wrap="word",
            font=ctk.CTkFont(size=13)
        )
        self.chat_entry.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.chat_entry.insert("1.0", "Escribe tu pregunta sobre el contrato...")
        self.chat_entry.bind("<FocusIn>", self._on_chat_entry_focus)
        self.chat_entry.bind("<Return>", self._on_chat_enter)
        
        # Botones de acción
        action_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="n")
        
        self.btn_send = ctk.CTkButton(
            action_frame,
            text="Enviar",
            command=self._send_chat_message,
            width=100,
            height=40,
            state="disabled"
        )
        self.btn_send.pack(pady=(0, 5))
        
        self.chat_status = ctk.CTkLabel(
            action_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.chat_status.pack()
        
        # Progress bar para chat
        self.chat_progress = ctk.CTkProgressBar(action_frame, width=100)
        self.chat_progress.set(0)
        
        # Bind para Ctrl+Enter
        self.chat_entry.bind("<Control-Return>", lambda e: self._send_chat_message())
    
    def _get_welcome_message(self) -> str:
        """Mensaje de bienvenida del chat."""
        return """Asistente Legal IA - Listo para ayudarte

Puedes hacer preguntas sobre el contrato cargado. El chat mantiene contexto de toda la conversacion.

Ejemplos de preguntas:
- Cuales son las obligaciones principales?
- Que dice la clausula 3 sobre pagos?
- Explicame los plazos de entrega
- Hay clausulas de penalizacion?
- Compara la seccion 5 con la seccion 8

Consejos:
- El chat recuerda todo lo que has preguntado antes
- Puedes hacer preguntas de seguimiento como "Que dijiste sobre X?"
- Usa "Nueva Conversacion" para empezar de cero

---


"""
    
    def _on_chat_entry_focus(self, event):
        """Maneja el foco en el entry del chat."""
        if self.chat_entry.get("1.0", "end-1c") == "Escribe tu pregunta sobre el contrato...":
            self.chat_entry.delete("1.0", "end")
    
    def _on_chat_enter(self, event):
        """Maneja Enter en el chat (sin Shift, envía mensaje)."""
        if not event.state & 0x1:
            self._send_chat_message()
            return "break"
    
    def _build_analysis_tab(self, parent):
        """Construye la pestaña de analisis legal."""
        analysis_frame = ctk.CTkFrame(parent, fg_color="transparent")
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            analysis_frame,
            text="Analisis Legal del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(
            analysis_frame,
            text="Genera un analisis completo del contrato, incluyendo:",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            analysis_frame,
            text="- Riesgos y clausulas peligrosas\n- Fechas importantes (inicio, termino, plazos)\n- Obligaciones de pago y condiciones",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
            justify="left"
        ).pack(anchor="w", pady=(0, 15))
        
        btn_analysis_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        btn_analysis_frame.pack(fill="x", pady=(10, 5))
        
        self.btn_analyze = ctk.CTkButton(
            btn_analysis_frame,
            text="Generar Analisis Completo",
            command=self._start_analysis,
            width=220,
            height=45,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled"
        )
        self.btn_analyze.pack(side="left")
        
        self.analysis_progress = ctk.CTkProgressBar(btn_analysis_frame, width=300)
        self.analysis_progress.pack(side="left", padx=(10, 0))
        self.analysis_progress.set(0)
        self.analysis_progress.pack_forget()
        
        ctk.CTkLabel(
            analysis_frame,
            text="Resultados del Analisis:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(20, 5))
        
        self.analysis_text = ctk.CTkTextbox(analysis_frame, wrap="word", height=350)
        self.analysis_text.pack(fill="both", expand=True, pady=(0, 10))
        self.analysis_text.insert("1.0", "Los resultados del analisis apareceran aqui...")
        self.analysis_text.configure(state="disabled")
    
    def _build_footer(self, parent):
        """Construye el footer."""
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        separator = ctk.CTkFrame(footer_frame, height=1, fg_color="#3d3d3d")
        separator.pack(fill="x", pady=(0, 15))
        
        buttons_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        self.btn_clear = ctk.CTkButton(
            buttons_frame,
            text="Limpiar Contrato",
            command=self._on_clear,
            width=150,
            height=40,
            fg_color="transparent",
            border_width=1
        )
        self.btn_clear.pack(side="left")
        
        self.btn_export = ctk.CTkButton(
            buttons_frame,
            text="Exportar Analisis",
            command=self._export_analysis,
            width=150,
            height=40,
            fg_color="transparent",
            border_width=1,
            state="disabled"
        )
        self.btn_export.pack(side="left", padx=(10, 0))
    
    def _cambiar_api_key(self):
        """Abre ventana modal de configuracion."""
        from interface.tkinter.config_window import ConfigWindow
        
        def on_config_saved():
            from application.graph.workflow import AnalisisWorkflow
            api_key = self.config_service.get_api_key()
            self.workflow = AnalisisWorkflow(api_key=api_key)
            
            model = self.config_service.get_model()
            if model and self.rag_service:
                self.rag_service.gemini_client.update_model(model)
                self.current_model = model
                self._update_chat_model_label()
            
            self.status_label.configure(text="Configuracion actualizada")
            messagebox.showinfo("Exito", "Configuracion actualizada.")
        
        config = ConfigWindow(parent=self.root, on_config_saved=on_config_saved)
        config.run()
    
    def _update_chat_model_label(self):
        """Actualiza la etiqueta del modelo en el chat."""
        if hasattr(self, 'chat_model_label') and self.current_model:
            self.chat_model_label.configure(text=f"Modelo: {self.current_model}")
    
    def _on_file_selected(self, pdf_path: Path):
        """Maneja seleccion de archivo."""
        if self.is_processing:
            messagebox.showwarning("En proceso", "Ya hay un documento en procesamiento")
            return
        
        if pdf_path.suffix.lower() != '.pdf':
            messagebox.showerror("Error", "Solo se permiten archivos PDF")
            return
        
        if pdf_path.stat().st_size > 50 * 1024 * 1024:
            messagebox.showerror("Error", "Archivo demasiado grande (max 50MB)")
            return
        
        self.current_pdf_path = pdf_path
        self._procesar_pdf()
    
    def _procesar_pdf(self):
        """Procesa el PDF."""
        self.is_processing = True
        self.file_upload.set_loading(True)
        self.progress_card.show()
        self.progress_card.update_progress(0.1, "Iniciando procesamiento...", "")
        
        def on_progress(mensaje: str):
            self.root.after(0, lambda: self._update_progress(mensaje))
        
        def on_complete(resultado: dict):
            self.root.after(0, lambda: self._on_process_complete(resultado))
        
        def on_error(error: str):
            self.root.after(0, lambda: self._on_process_error(error))
        
        self.processing_service.procesar_pdf(
            self.current_pdf_path,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error
        )
    
    def _update_progress(self, mensaje: str):
        """Actualiza el progreso - llamado desde hilo principal."""
        self.progress_card.update_progress(0.5, mensaje, "")
        self.status_label.configure(text=f"Procesando: {mensaje}")
    
    def _on_process_complete(self, resultado: dict):
        """Maneja la finalizacion del procesamiento - EN HILO PRINCIPAL."""
        self.current_contract_data = resultado
        self.is_processing = False
        
        # Actualizar UI
        self.file_upload.set_success(resultado["nombre_archivo"])
        self.progress_card.update_progress(1.0, "Indexando...", "")
        
        try:
            self.status_label.configure(text="Indexando...")
            index_result = self.rag_service.index_contract(resultado)
            
            if index_result.get("estado") == "exito":
                self.progress_card.update_progress(1.0, "Completado!", 
                                                   f"Indexados {index_result['chunks_indexados']} chunks")
                self.status_label.configure(text="Documento procesado")
                
                # Habilitar botones
                self.btn_analyze.configure(state="normal")
                self.btn_export.configure(state="normal")
                
                # Habilitar chat
                self.btn_send.configure(state="normal")
                self.btn_new_chat.configure(state="normal")
                self.btn_clear_chat.configure(state="normal")
                
                # Obtener modelo actual
                self.current_model = self.config_service.get_model() or "gemini-2.0-flash"
                self.rag_service.gemini_client.update_model(self.current_model)
                self._update_chat_model_label()
                
                # Inicializar conversación
                self.rag_service.initialize_conversation()
                
                # Mensaje de bienvenida en chat
                self._append_to_chat("system", f"Contrato cargado: {resultado['nombre_archivo']}\n\nPuedes empezar a hacer preguntas.")
                
                if self.rag_service.contract_summary:
                    self._append_to_chat("system", "Resumen del contrato generado automaticamente.")
            else:
                self.status_label.configure(text="Indexacion fallida")
                self._append_to_chat("system", "Error en la indexacion del contrato")
        except Exception as e:
            logger.error(f"Error en indexacion: {e}")
            self.status_label.configure(text="Error en indexacion")
            self._append_to_chat("system", f"Error procesando contrato: {str(e)[:100]}")
        
        self._update_contract_info(resultado)
        self._update_preview(resultado)
        
        self.root.after(2000, self.progress_card.hide)
    
    def _on_process_error(self, error: str):
        """Maneja error en procesamiento - EN HILO PRINCIPAL."""
        self.is_processing = False
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        self.status_label.configure(text="Error")
        
        if "503" in error or "UNAVAILABLE" in error:
            messagebox.showerror(
                "Servicio No Disponible",
                "El servicio de Gemini esta con alta demanda.\n\nEspera unos minutos o cambia el modelo."
            )
        else:
            messagebox.showerror("Error", f"No se pudo procesar:\n{error}")
    
    def _update_contract_info(self, resultado: dict):
        """Actualiza la informacion del contrato."""
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        info = f"""Nombre: {resultado['nombre_archivo']}
Paginas: {resultado['total_paginas']}
Caracteres: {resultado['total_caracteres']:,}
Chunks: {resultado['total_chunks']}"""
        self.info_text.insert("1.0", info)
        self.info_text.configure(state="disabled")
    
    def _update_preview(self, resultado: dict):
        """Actualiza el preview del texto en la pestaña Texto del Contrato."""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        
        texto = resultado['texto_completo'][:5000]
        if len(resultado['texto_completo']) > 5000:
            texto += "\n\n... [texto truncado]"
        
        self.preview_text.insert("1.0", texto)
        self.preview_text.configure(state="disabled")
        
        self.stats_label.configure(
            text=f"Total: {resultado['total_caracteres']} caracteres | {resultado['total_chunks']} chunks"
        )
    
    # ==================== CHAT CONVERSACIONAL ====================
    
    def _new_conversation(self):
        """Inicia una nueva conversación (limpia memoria)."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin contrato", "Carga un contrato primero")
            return
        
        if messagebox.askyesno("Nueva Conversacion", "Iniciar nueva conversacion? Se perdera el historial actual."):
            if self.rag_service:
                self.rag_service.clear_conversation()
                self.rag_service.initialize_conversation()
            
            self._clear_chat_display()
            self.chat_status.configure(text="Nueva conversacion iniciada")
            self.status_label.configure(text="Chat reiniciado")
            self._append_to_chat("system", self._get_welcome_message())
            self._append_to_chat("system", f"Contrato actual: {self.current_contract_data['nombre_archivo']}")
    
    def _clear_chat_display(self):
        """Limpia solo el display del chat (no la memoria)."""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.insert("1.0", "")
        self.chat_display.configure(state="disabled")
    
    def _append_to_chat(self, role: str, message: str):
        """Agrega un mensaje al display del chat."""
        self.chat_display.configure(state="normal")
        
        # Limpiar markdown
        message_clean = re.sub(r'\*\*(.*?)\*\*', r'\1', message)
        message_clean = re.sub(r'\*(.*?)\*', r'\1', message_clean)
        
        # Formato según rol
        if role == "user":
            prefix = "Tu: "
            self.chat_display.tag_config("user_color", foreground="#3498db")
            self.chat_display.insert("end", "\n\n" if self.chat_display.get("1.0", "end-1c") else "")
            self.chat_display.insert("end", prefix)
            self.chat_display.insert("end", message_clean, "user_color")
        elif role == "assistant":
            prefix = "Asistente: "
            self.chat_display.tag_config("assistant_color", foreground="#2ecc71")
            self.chat_display.insert("end", "\n\n" if self.chat_display.get("1.0", "end-1c") else "")
            self.chat_display.insert("end", prefix)
            self.chat_display.insert("end", message_clean, "assistant_color")
        elif role == "system":
            prefix = "Sistema: "
            self.chat_display.tag_config("system_color", foreground="#f39c12")
            self.chat_display.insert("end", "\n\n" if self.chat_display.get("1.0", "end-1c") else "")
            self.chat_display.insert("end", prefix)
            self.chat_display.insert("end", message_clean, "system_color")
        
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
    
    def _send_chat_message(self):
        """Envía un mensaje al chat usando RAG con memoria."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin contrato", "Primero carga un contrato")
            return
        
        if self.is_answering:
            self.chat_status.configure(text="Espera respuesta anterior...")
            return
        
        pregunta = self.chat_entry.get("1.0", "end-1c").strip()
        
        if not pregunta or pregunta == "Escribe tu pregunta sobre el contrato...":
            return
        
        self.chat_entry.delete("1.0", "end")
        self._append_to_chat("user", pregunta)
        
        self.is_answering = True
        self.btn_send.configure(state="disabled", text="Pensando...")
        self.chat_status.configure(text="Procesando...")
        self.chat_progress.pack(pady=(5, 0))
        self.chat_progress.set(0.2)
        
        def task():
            try:
                if not self.rag_service.conversation_memory:
                    self.root.after(0, lambda: self.rag_service.initialize_conversation())
                
                current_model = self.config_service.get_model()
                if current_model and current_model != self.current_model:
                    self.current_model = current_model
                    self.rag_service.gemini_client.update_model(current_model)
                    self.root.after(0, self._update_chat_model_label)
                
                self.root.after(0, lambda: self.chat_progress.set(0.5))
                
                resultado = self.rag_service.ask_question(
                    question=pregunta,
                    k=5,
                    include_history=True,
                    model=self.current_model
                )
                
                self.root.after(0, lambda: self.chat_progress.set(0.9))
                
                if resultado and resultado.get("respuesta"):
                    respuesta = resultado["respuesta"]
                    self.root.after(0, lambda: self._append_to_chat("assistant", respuesta))
                    self.root.after(0, lambda: self.chat_status.configure(text="Respuesta completada"))
                else:
                    error_msg = "No se pudo obtener respuesta. Verifica tu conexion."
                    self.root.after(0, lambda: self._append_to_chat("assistant", error_msg))
                    self.root.after(0, lambda: self.chat_status.configure(text="Error en respuesta"))
                
            except Exception as e:
                logger.error(f"Error en chat: {e}")
                error_msg = str(e)
                if "503" in error_msg or "saturado" in error_msg.lower():
                    respuesta = "El servicio de Gemini esta con alta demanda. Espera unos momentos y reintenta."
                else:
                    respuesta = f"Error: {error_msg[:200]}"
                self.root.after(0, lambda: self._append_to_chat("assistant", respuesta))
                self.root.after(0, lambda: self.chat_status.configure(text="Error"))
            
            finally:
                self.root.after(0, lambda: self.chat_progress.set(1.0))
                self.root.after(0, lambda: self.chat_progress.pack_forget())
                self.root.after(0, lambda: self.btn_send.configure(state="normal", text="Enviar"))
                self.root.after(0, lambda: self.chat_status.configure(text=""))
                self.root.after(0, lambda: setattr(self, 'is_answering', False))
        
        threading.Thread(target=task, daemon=True).start()
    
    # ==================== ANÁLISIS LEGAL ====================
    
    def _start_analysis(self):
        """Inicia el analisis legal completo."""
        if not self.current_contract_data:
            messagebox.showwarning("Advertencia", "Carga un contrato primero")
            return

        self.is_analyzing = True
        self.btn_analyze.configure(state="disabled", text="Generando analisis...")
        self.status_label.configure(text="Analizando contrato...")
        
        self.analysis_progress.pack(side="left", padx=(10, 0))
        self.analysis_progress.set(0.2)
        
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "Generando analisis... Esto puede tomar unos segundos.")
        self.analysis_text.configure(state="disabled")

        def task():
            try:
                if self.workflow is None:
                    raise Exception("Sistema no disponible")

                self.root.after(0, lambda: self.analysis_progress.set(0.5))

                resultado = self.workflow.ejecutar_sync(
                    self.current_contract_data['texto_completo'],
                    consulta="",
                    tipo="analisis"
                )

                if resultado.get("exito"):
                    analisis = resultado.get("resumen", "No se genero analisis")
                    self.root.after(0, lambda: self._show_analysis(analisis))
                    return
                else:
                    raise Exception(resultado.get("error", "Error desconocido"))

            except Exception as e:
                error = str(e)
                logger.error(f"Error en analisis: {error}")

                if "503" in error or "UNAVAILABLE" in error:
                    error_msg = "Servidor de Gemini saturado. Intenta de nuevo en unos minutos."
                else:
                    error_msg = f"Error: {error[:200]}"

                self.root.after(0, lambda: self._show_analysis_error(error_msg))
            finally:
                self.root.after(0, lambda: self.analysis_progress.set(1.0))
                self.root.after(0, lambda: self.analysis_progress.pack_forget())
                self.root.after(0, self._reset_analyze_button)

        threading.Thread(target=task, daemon=True).start()
    
    def _reset_analyze_button(self):
        self.btn_analyze.configure(state="normal", text="Generar Analisis Completo")
        self.status_label.configure(text="Listo")
        self.is_analyzing = False
    
    def _show_analysis(self, analisis: str):
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", analisis)
        self.analysis_text.configure(state="disabled")
        
        self.btn_export.configure(state="normal")
        self.status_label.configure(text="Analisis completado")
    
    def _show_analysis_error(self, error: str):
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", f"Error en el analisis:\n\n{error}")
        self.analysis_text.configure(state="disabled")
        self.btn_analyze.configure(state="normal", text="Generar Analisis Completo")
        self.is_analyzing = False
        self.analysis_progress.pack_forget() 
        self.status_label.configure(text="Error en analisis")
    
    def _export_analysis(self):
        """Exporta el analisis a PDF."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Carga un contrato primero")
            return
        
        analisis = self.analysis_text.get("1.0", "end-1c")
        
        if not analisis or analisis == "Los resultados del analisis apareceran aqui...":
            messagebox.showwarning("Sin analisis", "Primero realiza un analisis del contrato")
            return
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            title="Guardar Analisis como PDF",
            filetypes=[("Documento PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                export_service = PDFExportService()
                pdf_path = export_service.exportar_analisis(
                    resumen=analisis,
                    contrato_nombre=self.current_contract_data['nombre_archivo'],
                    archivo_salida=Path(archivo)
                )
                messagebox.showinfo("Exito", f"Analisis exportado a:\n{pdf_path}")
            except Exception as e:
                logger.error(f"Error exportando: {e}")
                messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
    
    def _on_clear(self):
        """Limpia el contrato actual Y el chat."""
        if self.is_processing or self.is_analyzing or self.is_answering:
            messagebox.showwarning("En proceso", "Espera a que termine")
            return
        
        self.current_contract_data = None
        self.current_pdf_path = None
        
        if self.rag_service:
            self.rag_service.clear()
            self.rag_service.clear_conversation()
        
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", "Esperando carga...")
        self.info_text.configure(state="disabled")
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "El texto del contrato aparecera aqui...")
        self.preview_text.configure(state="disabled")
        
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "Los resultados del analisis apareceran aqui...")
        self.analysis_text.configure(state="disabled")
        
        self.stats_label.configure(text="")
        self.status_label.configure(text="Sistema listo")
        
        self.btn_analyze.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        
        # Limpiar chat
        self.btn_send.configure(state="disabled")
        self.btn_new_chat.configure(state="disabled")
        self.btn_clear_chat.configure(state="disabled")
        self._clear_chat_display()
        self._append_to_chat("system", "Chat limpiado. Carga un nuevo contrato para comenzar.")
        
        self.file_upload.reset_state()
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        
        messagebox.showinfo("Limpieza", "Contrato eliminado. Puedes cargar otro.")
    
    def _on_closing(self):
        if self.is_processing or self.is_analyzing or self.is_answering:
            if messagebox.askyesno("Salir", "Hay procesos en curso. Salir?"):
                if self.rag_service and self.rag_service.conversation_memory:
                    self.rag_service.save_conversation()
                self.root.destroy()
        else:
            if self.rag_service and self.rag_service.conversation_memory:
                self.rag_service.save_conversation()
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()