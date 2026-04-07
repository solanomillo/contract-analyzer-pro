"""
Ventana principal de la aplicacion.
Maneja la carga de PDF, RAG, agentes y analisis de riesgos.
"""

import logging
import os
import sys
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox, filedialog

from interface.tkinter.components import FileUploadFrame, ProgressCard
from interface.tkinter.styles import configurar_tema, crear_titulo, crear_card
from application.services.processing_service import ProcessingService
from application.services.config_service import ConfigService
from application.services.rag_service import RAGService
from application.graph.workflow import AnalisisWorkflow

logger = logging.getLogger(__name__)


class MainWindow:
    """Ventana principal de Contract Analyzer Pro."""
    
    def __init__(self):
        """Inicializa la ventana principal."""
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Analizador de Contratos")
        
        # Configurar ventana - Tamaño inicial adecuado
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        
        # Tamaño inicial: 70% de la pantalla (ni muy grande ni muy chico)
        ancho_inicial = int(ancho_pantalla * 0.7)
        alto_inicial = int(alto_pantalla * 0.7)
        
        # Posicionar en el centro
        x = (ancho_pantalla - ancho_inicial) // 2
        y = (alto_pantalla - alto_inicial) // 2
        
        self.root.geometry(f"{ancho_inicial}x{alto_inicial}+{x}+{y}")
        self.root.minsize(1000, 700)  # Tamaño mínimo para no perder botones
        self.root.maxsize(ancho_pantalla, alto_pantalla)  # Máximo = pantalla completa
        
        # Configurar tema
        self.colores = configurar_tema()
        
        # Servicios
        self.processing_service = ProcessingService()
        self.config_service = ConfigService()
        self.rag_service = RAGService()
        
        # Inicializar workflow sin bloquear (en segundo plano)
        self.workflow = None
        self._inicializar_workflow_async()
        
        self.current_contract_data = None
        self.current_pdf_path = None
        
        # Estado
        self.is_processing = False
        self.is_answering = False
        self.is_analyzing = False
        
        # Construir UI
        self._build_ui()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _inicializar_workflow_async(self):
        """Inicializa el workflow en segundo plano para no bloquear la UI."""
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
        
        # Frame principal usando grid para mejor comportamiento
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configurar grid del frame principal
        main_frame.grid_rowconfigure(0, weight=0)  # Header
        main_frame.grid_rowconfigure(1, weight=1)  # Contenido (expande)
        main_frame.grid_rowconfigure(2, weight=0)  # Footer
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self._build_header(main_frame)
        
        # Contenido principal (2 columnas)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Columna izquierda
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_column.grid_rowconfigure(1, weight=1)
        left_column.grid_columnconfigure(0, weight=1)
        self._build_upload_area(left_column)
        
        # Columna derecha
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_column.grid_rowconfigure(0, weight=1)
        right_column.grid_columnconfigure(0, weight=1)
        self._build_preview_area(right_column)
        
        # Footer
        self._build_footer(main_frame)
    
    def _build_header(self, parent):
        """Construye el header."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        titulo = crear_titulo(header_frame, "CONTRACT ANALYZER PRO", 24)
        titulo.grid(row=0, column=0, sticky="w")
        
        # Botones header
        header_buttons = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_buttons.grid(row=0, column=1, sticky="e")
        
        self.btn_cambiar_api = ctk.CTkButton(
            header_buttons,
            text="🔑 Cambiar API Key",
            command=self._cambiar_api_key,
            width=140,
            height=30,
            fg_color="#f39c12",
            hover_color="#e67e22"
        )
        self.btn_cambiar_api.pack(side="left", padx=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            header_buttons,
            text="✅ Sistema listo",
            font=ctk.CTkFont(size=12),
            text_color="#2ecc71"
        )
        self.status_label.pack(side="left")
    
    def _build_upload_area(self, parent):
        """Construye el area de carga."""
        # Card de carga - altura fija pero responsive
        upload_card = crear_card(parent)
        upload_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(
            upload_card,
            text="📁 Cargar Contrato",
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
        
        # Info contrato - expandible
        info_card = crear_card(parent)
        info_card.grid(row=1, column=0, sticky="nsew", pady=(0, 0))
        
        ctk.CTkLabel(
            info_card,
            text="📋 Informacion del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.info_text = ctk.CTkTextbox(info_card, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.info_text.insert("1.0", "Esperando carga de documento...")
        self.info_text.configure(state="disabled")
    
    def _build_preview_area(self, parent):
        """Construye el area de preview con pestañas."""
        
        preview_card = crear_card(parent)
        preview_card.pack(fill="both", expand=True)
        
        # Pestañas
        tabview = ctk.CTkTabview(preview_card)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Pestaña de texto
        tab_texto = tabview.add("📄 Texto del Contrato")
        self._build_text_tab(tab_texto)
        
        # Pestaña de preguntas
        tab_preguntas = tabview.add("❓ Preguntar al Contrato")
        self._build_qa_tab(tab_preguntas)
        
        # Pestaña de analisis
        tab_analisis = tabview.add("📊 Analisis Legal")
        self._build_analysis_tab(tab_analisis)
        
        # Pestaña de resultados
        tab_resultados = tabview.add("📋 Resultados")
        self._build_results_tab(tab_resultados)
    
    def _build_text_tab(self, parent):
        """Construye la pestaña de texto."""
        self.progress_card = ProgressCard(parent)
        self.progress_card.hide()
        
        self.preview_text = ctk.CTkTextbox(parent, wrap="word")
        self.preview_text.pack(fill="both", expand=True)
        self.preview_text.insert("1.0", "El texto del contrato aparecera aqui...")
        self.preview_text.configure(state="disabled")
        
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(10, 0))
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.stats_label.pack()
    
    def _build_qa_tab(self, parent):
        """Construye la pestaña de preguntas y respuestas."""
        # Area de pregunta
        ctk.CTkLabel(
            parent,
            text="Haz una pregunta sobre el contrato:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.question_entry = ctk.CTkTextbox(parent, height=80, wrap="word")
        self.question_entry.pack(fill="x", pady=(0, 10))
        self.question_entry.insert("1.0", "Ejemplo: Cuales son las penalizaciones por incumplimiento?")
        
        # Boton preguntar
        self.btn_ask = ctk.CTkButton(
            parent,
            text="🔍 Preguntar",
            command=self._ask_question,
            width=150,
            state="disabled"
        )
        self.btn_ask.pack(anchor="w", pady=(0, 15))
        
        # Area de respuesta
        ctk.CTkLabel(
            parent,
            text="Respuesta:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.answer_text = ctk.CTkTextbox(parent, wrap="word", height=150)
        self.answer_text.pack(fill="x", pady=(0, 10))
        self.answer_text.insert("1.0", "Las respuestas apareceran aqui...")
        self.answer_text.configure(state="disabled")
        
        # Contexto usado
        ctk.CTkLabel(
            parent,
            text="Contexto utilizado (chunks relevantes):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(5, 5))
        
        self.context_text = ctk.CTkTextbox(parent, height=120, wrap="word")
        self.context_text.pack(fill="x")
        self.context_text.insert("1.0", "El contexto usado para generar la respuesta aparecera aqui...")
        self.context_text.configure(state="disabled")
    
    def _build_analysis_tab(self, parent):
        """Construye la pestaña de analisis legal."""
        ctk.CTkLabel(
            parent,
            text="Analisis Legal del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(
            parent,
            text="Selecciona el tipo de analisis:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 5))
        
        # Frame para opciones de analisis
        options_frame = ctk.CTkFrame(parent, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, 10))
        
        self.analysis_type_var = ctk.StringVar(value="completo")
        
        self.radio_completo = ctk.CTkRadioButton(
            options_frame,
            text="Analisis Completo (todos los agentes)",
            variable=self.analysis_type_var,
            value="completo"
        )
        self.radio_completo.pack(anchor="w", pady=2)
        
        self.radio_riesgo = ctk.CTkRadioButton(
            options_frame,
            text="Solo Riesgos (clausulas peligrosas)",
            variable=self.analysis_type_var,
            value="riesgo"
        )
        self.radio_riesgo.pack(anchor="w", pady=2)
        
        self.radio_fechas = ctk.CTkRadioButton(
            options_frame,
            text="Solo Fechas (vencimientos, plazos)",
            variable=self.analysis_type_var,
            value="fechas"
        )
        self.radio_fechas.pack(anchor="w", pady=2)
        
        self.radio_obligaciones = ctk.CTkRadioButton(
            options_frame,
            text="Solo Obligaciones (pagos, condiciones)",
            variable=self.analysis_type_var,
            value="obligaciones"
        )
        self.radio_obligaciones.pack(anchor="w", pady=2)
        
        # Boton para generar analisis
        self.btn_analyze = ctk.CTkButton(
            parent,
            text="🚀 Iniciar Analisis",
            command=self._start_analysis,
            width=200,
            height=40,
            fg_color="#3498db",
            state="disabled"
        )
        self.btn_analyze.pack(anchor="w", pady=(10, 15))
        
        # Barra de progreso del analisis
        self.analysis_progress = ctk.CTkProgressBar(parent, width=400)
        self.analysis_progress.pack(fill="x", pady=(0, 10))
        self.analysis_progress.set(0)
        self.analysis_progress.pack_forget()
    
    def _build_results_tab(self, parent):
        """Construye la pestaña de resultados del analisis."""
        results_frame = ctk.CTkScrollableFrame(parent)
        results_frame.pack(fill="both", expand=True)
        
        self.results_title = ctk.CTkLabel(
            results_frame,
            text="Resultados del Analisis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.results_title.pack(anchor="w", pady=(10, 10))
        
        # Frame para resumen
        summary_card = crear_card(results_frame)
        summary_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            summary_card,
            text="📊 Resumen Ejecutivo",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.summary_text = ctk.CTkTextbox(summary_card, height=150, wrap="word")
        self.summary_text.pack(fill="x", padx=15, pady=(0, 15))
        self.summary_text.insert("1.0", "Los resultados del analisis apareceran aqui...")
        self.summary_text.configure(state="disabled")
        
        # Frame para riesgos altos
        high_card = crear_card(results_frame)
        high_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            high_card,
            text="🔴 RIESGOS ALTOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.high_risks_text = ctk.CTkTextbox(high_card, height=120, wrap="word")
        self.high_risks_text.pack(fill="x", padx=15, pady=(0, 15))
        self.high_risks_text.insert("1.0", "No se han detectado riesgos altos...")
        self.high_risks_text.configure(state="disabled")
        
        # Frame para riesgos medios
        medium_card = crear_card(results_frame)
        medium_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            medium_card,
            text="🟡 RIESGOS MEDIOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f39c12"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.medium_risks_text = ctk.CTkTextbox(medium_card, height=120, wrap="word")
        self.medium_risks_text.pack(fill="x", padx=15, pady=(0, 15))
        self.medium_risks_text.insert("1.0", "No se han detectado riesgos medios...")
        self.medium_risks_text.configure(state="disabled")
        
        # Frame para riesgos bajos
        low_card = crear_card(results_frame)
        low_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            low_card,
            text="🟢 RIESGOS BAJOS / INFORMATIVOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2ecc71"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.low_risks_text = ctk.CTkTextbox(low_card, height=100, wrap="word")
        self.low_risks_text.pack(fill="x", padx=15, pady=(0, 15))
        self.low_risks_text.insert("1.0", "No se han detectado riesgos bajos...")
        self.low_risks_text.configure(state="disabled")
    
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
            text="🗑️ Limpiar Contrato",
            command=self._on_clear,
            width=150,
            height=40,
            fg_color="transparent",
            border_width=1
        )
        self.btn_clear.pack(side="left")
        
        self.btn_export = ctk.CTkButton(
            buttons_frame,
            text="📎 Exportar Analisis",
            command=self._export_analysis,
            width=150,
            height=40,
            fg_color="transparent",
            border_width=1,
            state="disabled"
        )
        self.btn_export.pack(side="left", padx=(10, 0))
    
    def _cambiar_api_key(self):
        """Cambia la API key usando ConfigService."""
        dialog = ctk.CTkInputDialog(
            text="Ingresa tu nueva API key de Gemini:",
            title="Cambiar API Key"
        )
        
        nueva_api_key = dialog.get_input()
        if nueva_api_key and nueva_api_key.strip():
            if self.config_service.actualizar_api_key(nueva_api_key.strip()):
                messagebox.showinfo("Exito", "API key actualizada. La app se reiniciara.")
                self.root.destroy()
                os.startfile(sys.argv[0])
            else:
                messagebox.showerror("Error", "No se pudo guardar la API key")
    
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
        """Procesa el PDF e indexa en RAG."""
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
        """Actualiza el progreso."""
        self.progress_card.update_progress(0.5, mensaje, "")
        self.status_label.configure(text=f"🔄 {mensaje}")
    
    def _on_process_complete(self, resultado: dict):
        """Maneja la finalizacion del procesamiento."""
        self.current_contract_data = resultado
        self.is_processing = False
        
        self.file_upload.set_success(resultado["nombre_archivo"])
        self.progress_card.update_progress(1.0, "Indexando en base vectorial...", "")
        
        # Indexar en RAG
        try:
            self.status_label.configure(text="🔄 Indexando en base vectorial...")
            index_result = self.rag_service.index_contract(resultado)
            
            if index_result.get("estado") == "exito":
                self.progress_card.update_progress(1.0, "Procesamiento completado!", 
                                                   f"Indexados {index_result['chunks_indexados']} chunks")
                self.status_label.configure(text="✅ Documento procesado e indexado")
                
                # Habilitar botones
                self.btn_ask.configure(state="normal")
                self.btn_analyze.configure(state="normal")
                self.btn_export.configure(state="normal")
            else:
                self.status_label.configure(text="⚠️ Indexacion fallida")
                
        except Exception as e:
            logger.error(f"Error en indexacion: {e}")
            self.status_label.configure(text="❌ Error en indexacion")
        
        # Actualizar UI
        self._update_contract_info(resultado)
        self._update_preview(resultado)
        
        # Ocultar progreso
        self.root.after(2000, self.progress_card.hide)
    
    def _on_process_error(self, error: str):
        """Maneja error en el procesamiento con mensajes amigables."""
        self.is_processing = False
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        self.status_label.configure(text="❌ Error en procesamiento")
        
        # Manejo especifico para error 503 (servicio no disponible)
        if "503" in error or "UNAVAILABLE" in error or "high demand" in error.lower():
            messagebox.showerror(
                "Servicio Temporalmente No Disponible",
                "El servicio de Gemini está experimentando alta demanda.\n\n"
                "Sugerencias para resolver:\n"
                "1. Espera unos minutos y vuelve a intentar\n"
                "2. Cambia a otro modelo en la configuración\n"
                "   - Edita el archivo .env y cambia GEMINI_MODEL=gemini-2.0-flash\n"
                "3. Reinicia la aplicación\n\n"
                f"Error técnico: {error}"
            )
        elif "quota" in error.lower() or "exceeded" in error.lower():
            messagebox.showerror(
                "Cuota de API Agotada",
                "La cuota de la API key se ha agotado.\n\n"
                "Soluciones:\n"
                "1. Usa otra API key (botón 'Cambiar API Key')\n"
                "2. Espera a que se renueve la cuota (generalmente al día siguiente)\n"
                "3. Considera actualizar a un plan de pago\n\n"
                f"Error: {error}"
            )
        elif "invalid" in error.lower() or "unauthorized" in error.lower():
            messagebox.showerror(
                "API Key Invalida",
                "La API key configurada no es valida.\n\n"
                "Soluciones:\n"
                "1. Haz clic en 'Cambiar API Key' para ingresar una nueva\n"
                "2. Obtén una API key gratis en: https://makersuite.google.com/app/apikey\n\n"
                f"Error: {error}"
            )
        else:
            messagebox.showerror(
                "Error de Procesamiento", 
                f"No se pudo procesar el PDF:\n\n{error}\n\n"
                "Posibles causas:\n"
                "- El PDF puede estar dañado o ser una imagen\n"
                "- El archivo no tiene texto extraible\n"
                "- Problema de conexión con Gemini"
            )
    
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
        """Actualiza el preview del texto."""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        
        texto = resultado['texto_completo'][:3000]
        if len(resultado['texto_completo']) > 3000:
            texto += "\n\n... [texto truncado, usar preguntas para buscar informacion especifica]"
        
        self.preview_text.insert("1.0", texto)
        self.preview_text.configure(state="disabled")
        
        self.stats_label.configure(
            text=f"Total: {resultado['total_caracteres']} caracteres | {resultado['total_chunks']} chunks indexados"
        )
    
    def _ask_question(self):
        """Realiza una pregunta sobre el contrato usando RAG."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Primero carga un contrato")
            return
        
        if self.is_answering:
            messagebox.showwarning("En proceso", "Espera a que termine la respuesta actual")
            return
        
        pregunta = self.question_entry.get("1.0", "end-1c").strip()
        
        if not pregunta or pregunta == "Ejemplo: Cuales son las penalizaciones por incumplimiento?":
            messagebox.showwarning("Sin pregunta", "Ingresa una pregunta valida")
            return
        
        self.is_answering = True
        self.btn_ask.configure(state="disabled", text="Procesando...")
        self.answer_text.configure(state="normal")
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", "🔍 Buscando informacion en el contrato...")
        self.answer_text.configure(state="disabled")
        
        self.context_text.configure(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", "Buscando chunks relevantes...")
        self.context_text.configure(state="disabled")
        
        def task():
            try:
                if self.workflow is None:
                    self.root.after(0, lambda: self._show_answer(
                        "⚠️ El sistema de analisis no esta disponible.\n\n"
                        "Posibles causas:\n"
                        "- API key no configurada o invalida\n"
                        "- Problema de conexion con Gemini\n\n"
                        "Solucion: Haz clic en 'Cambiar API Key' para configurar una nueva.",
                        ""
                    ))
                    return
                
                resultado = self.workflow.ejecutar_sync(
                    self.current_contract_data['texto_completo'],
                    consulta=pregunta
                )
                
                if resultado.get("exito"):
                    respuesta = resultado.get("resumen", "No se encontro informacion relevante.")
                    contexto = "\n".join([
                        f"- {h.get('descripcion', '')}" 
                        for h in resultado.get("hallazgos_riesgo", [])[:3]
                    ])
                else:
                    respuesta = f"Error en el analisis: {resultado.get('error', 'Error desconocido')}"
                    contexto = ""
                
                self.root.after(0, lambda: self._show_answer(respuesta, contexto))
                
            except Exception as e:
                logger.error(f"Error en pregunta: {e}")
                error_msg = str(e)
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    respuesta = "El servicio de Gemini está con alta demanda. Por favor, intenta nuevamente en unos minutos."
                else:
                    respuesta = f"Error al procesar la pregunta: {error_msg}"
                self.root.after(0, lambda: self._show_answer(respuesta, ""))
        
        threading.Thread(target=task, daemon=True).start()
    
    def _show_answer(self, respuesta: str, contexto: str):
        """Muestra la respuesta en la UI."""
        self.answer_text.configure(state="normal")
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", respuesta)
        self.answer_text.configure(state="disabled")
        
        if contexto:
            self.context_text.configure(state="normal")
            self.context_text.delete("1.0", "end")
            self.context_text.insert("1.0", contexto)
            self.context_text.configure(state="disabled")
        
        self.btn_ask.configure(state="normal", text="🔍 Preguntar")
        self.is_answering = False
    
    def _start_analysis(self):
        """Inicia el analisis legal con los agentes."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Primero carga un contrato")
            return
        
        if self.is_analyzing:
            messagebox.showwarning("En proceso", "Ya hay un analisis en curso")
            return
        
        analysis_type = self.analysis_type_var.get()
        
        consulta_map = {
            "completo": "analizar todo el contrato",
            "riesgo": "clausulas peligrosas penalizaciones rescision",
            "fechas": "fechas importantes vencimiento plazo",
            "obligaciones": "obligaciones de pago condiciones"
        }
        
        consulta = consulta_map.get(analysis_type, "analizar")
        
        self.is_analyzing = True
        self.btn_analyze.configure(state="disabled", text="Analizando...")
        
        self.analysis_progress.pack(fill="x", pady=(0, 10))
        self.analysis_progress.set(0.2)
        
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "🔍 Analizando contrato...\n\nEsto puede tomar unos segundos...")
        self.summary_text.configure(state="disabled")
        
        def task():
            try:
                if self.workflow is None:
                    self.root.after(0, lambda: self._show_analysis_error(
                        "El sistema de analisis no esta disponible.\n\n"
                        "Verifica que tu API key sea valida y tenga cuota disponible."
                    ))
                    return
                
                self.root.after(0, lambda: self.analysis_progress.set(0.5))
                
                resultado = self.workflow.ejecutar_sync(
                    self.current_contract_data['texto_completo'],
                    consulta=consulta
                )
                
                self.root.after(0, lambda: self.analysis_progress.set(0.9))
                
                if resultado.get("exito"):
                    self.root.after(0, lambda: self._show_analysis_results(resultado))
                else:
                    error_msg = resultado.get("error", "Error desconocido")
                    if "503" in error_msg or "UNAVAILABLE" in error_msg:
                        error_msg = "El servicio de Gemini está con alta demanda. Intenta nuevamente en unos minutos."
                    self.root.after(0, lambda: self._show_analysis_error(error_msg))
                
                self.root.after(0, lambda: self.analysis_progress.set(1.0))
                
            except Exception as e:
                logger.error(f"Error en analisis: {e}")
                error_msg = str(e)
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    error_msg = "El servicio de Gemini está con alta demanda. Intenta nuevamente en unos minutos."
                self.root.after(0, lambda: self._show_analysis_error(error_msg))
        
        threading.Thread(target=task, daemon=True).start()
    
    def _show_analysis_results(self, resultado: dict):
        """Muestra los resultados del analisis."""
        
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", resultado.get("resumen", "No se genero resumen"))
        self.summary_text.configure(state="disabled")
        
        altos = []
        medios = []
        bajos = []
        
        for h in resultado.get("hallazgos_riesgo", []):
            riesgo = h.get("riesgo", "MEDIO")
            texto = f"• {h.get('descripcion', '')}\n  📍 {h.get('texto_relevante', '')[:100]}...\n  💡 {h.get('recomendacion', '')}\n\n"
            if riesgo == "ALTO":
                altos.append(texto)
            elif riesgo == "MEDIO":
                medios.append(texto)
            else:
                bajos.append(texto)
        
        for h in resultado.get("hallazgos_fechas", []):
            riesgo = h.get("riesgo", "MEDIO")
            texto = f"• {h.get('descripcion', '')}\n  📍 {h.get('texto_relevante', '')[:100]}...\n  💡 {h.get('recomendacion', '')}\n\n"
            if riesgo == "ALTO":
                altos.append(texto)
            elif riesgo == "MEDIO":
                medios.append(texto)
            else:
                bajos.append(texto)
        
        for h in resultado.get("hallazgos_obligaciones", []):
            riesgo = h.get("riesgo", "MEDIO")
            texto = f"• {h.get('descripcion', '')}\n  📍 {h.get('texto_relevante', '')[:100]}...\n  💡 {h.get('recomendacion', '')}\n\n"
            if riesgo == "ALTO":
                altos.append(texto)
            elif riesgo == "MEDIO":
                medios.append(texto)
            else:
                bajos.append(texto)
        
        self.high_risks_text.configure(state="normal")
        self.high_risks_text.delete("1.0", "end")
        self.high_risks_text.insert("1.0", "".join(altos) if altos else "✅ No se detectaron riesgos altos")
        self.high_risks_text.configure(state="disabled")
        
        self.medium_risks_text.configure(state="normal")
        self.medium_risks_text.delete("1.0", "end")
        self.medium_risks_text.insert("1.0", "".join(medios) if medios else "✅ No se detectaron riesgos medios")
        self.medium_risks_text.configure(state="disabled")
        
        self.low_risks_text.configure(state="normal")
        self.low_risks_text.delete("1.0", "end")
        self.low_risks_text.insert("1.0", "".join(bajos) if bajos else "✅ No se detectaron riesgos bajos")
        self.low_risks_text.configure(state="disabled")
        
        self.btn_export.configure(state="normal")
        
        self.btn_analyze.configure(state="normal", text="🚀 Iniciar Analisis")
        self.is_analyzing = False
        
        self.root.after(2000, lambda: self.analysis_progress.pack_forget())
        
        self.status_label.configure(text="✅ Analisis completado")
        messagebox.showinfo("Analisis Completado", 
                           f"Analisis finalizado.\n\n"
                           f"Riesgos Altos: {len(altos)}\n"
                           f"Riesgos Medios: {len(medios)}\n"
                           f"Riesgos Bajos: {len(bajos)}")
    
    def _show_analysis_error(self, error: str):
        """Muestra error en el analisis."""
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", f"❌ Error en el analisis:\n\n{error}")
        self.summary_text.configure(state="disabled")
        
        self.btn_analyze.configure(state="normal", text="🚀 Iniciar Analisis")
        self.is_analyzing = False
        self.analysis_progress.pack_forget()
        self.status_label.configure(text="❌ Error en analisis")
    
    def _export_analysis(self):
        """Exporta el analisis completo."""
        resumen = self.summary_text.get("1.0", "end-1c")
        altos = self.high_risks_text.get("1.0", "end-1c")
        medios = self.medium_risks_text.get("1.0", "end-1c")
        bajos = self.low_risks_text.get("1.0", "end-1c")
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("CONTRACT ANALYZER PRO - ANALISIS LEGAL\n")
                    f.write("=" * 60 + "\n\n")
                    f.write("RESUMEN EJECUTIVO\n")
                    f.write("-" * 40 + "\n")
                    f.write(resumen + "\n\n")
                    f.write("RIESGOS ALTOS\n")
                    f.write("-" * 40 + "\n")
                    f.write(altos + "\n\n")
                    f.write("RIESGOS MEDIOS\n")
                    f.write("-" * 40 + "\n")
                    f.write(medios + "\n\n")
                    f.write("RIESGOS BAJOS\n")
                    f.write("-" * 40 + "\n")
                    f.write(bajos + "\n")
                
                messagebox.showinfo("Exito", f"Analisis exportado a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _on_clear(self):
        """Limpia el contrato actual y restaura todos los componentes."""
        if self.is_processing or self.is_analyzing or self.is_answering:
            messagebox.showwarning("En proceso", "Espera a que termine el proceso actual")
            return
        
        self.current_contract_data = None
        self.current_pdf_path = None
        
        if self.rag_service:
            self.rag_service.clear()
        
        # Limpiar UI
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", "Esperando carga de documento...")
        self.info_text.configure(state="disabled")
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "El texto del contrato aparecera aqui...")
        self.preview_text.configure(state="disabled")
        
        self.answer_text.configure(state="normal")
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", "Las respuestas apareceran aqui...")
        self.answer_text.configure(state="disabled")
        
        self.context_text.configure(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", "El contexto usado para generar la respuesta aparecera aqui...")
        self.context_text.configure(state="disabled")
        
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "Los resultados del analisis apareceran aqui...")
        self.summary_text.configure(state="disabled")
        
        self.high_risks_text.configure(state="normal")
        self.high_risks_text.delete("1.0", "end")
        self.high_risks_text.insert("1.0", "No se han detectado riesgos altos...")
        self.high_risks_text.configure(state="disabled")
        
        self.medium_risks_text.configure(state="normal")
        self.medium_risks_text.delete("1.0", "end")
        self.medium_risks_text.insert("1.0", "No se han detectado riesgos medios...")
        self.medium_risks_text.configure(state="disabled")
        
        self.low_risks_text.configure(state="normal")
        self.low_risks_text.delete("1.0", "end")
        self.low_risks_text.insert("1.0", "No se han detectado riesgos bajos...")
        self.low_risks_text.configure(state="disabled")
        
        self.question_entry.delete("1.0", "end")
        self.question_entry.insert("1.0", "Ejemplo: Cuales son las penalizaciones por incumplimiento?")
        
        self.stats_label.configure(text="")
        self.status_label.configure(text="✅ Sistema listo")
        
        self.btn_ask.configure(state="disabled")
        self.btn_analyze.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        
        # Restaurar componente de carga
        self.file_upload.reset_state()
        self.file_upload.set_loading(False)
        
        self.progress_card.hide()
        self.analysis_progress.pack_forget()
        self.progress_card.reset()
        
        messagebox.showinfo("Limpieza", "Contrato eliminado correctamente.\n\nPuedes cargar un nuevo contrato.")
    
    def _on_closing(self):
        """Maneja el cierre de la ventana."""
        if self.is_processing or self.is_analyzing or self.is_answering:
            respuesta = messagebox.askyesno("Salir", "Hay un proceso en curso. ¿Seguro que quieres salir?")
            if respuesta:
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Ejecuta la ventana."""
        self.root.mainloop()