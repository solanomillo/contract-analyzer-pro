"""
Ventana principal de la aplicacion.
Maneja la carga de PDF, RAG, agentes y analisis de riesgos.
"""

import logging
import os
import sys
import threading
import time
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

logger = logging.getLogger(__name__)


class MainWindow:
    """Ventana principal de Contract Analyzer Pro."""
    
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
        
        # Estado
        self.is_processing = False
        self.is_answering = False
        self.is_analyzing = False
        
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
        
        # Contenido principal
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
        
        self.info_text = ctk.CTkTextbox(info_card, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.info_text.insert("1.0", "Esperando carga de documento...")
        self.info_text.configure(state="disabled")
    
    def _build_preview_area(self, parent):
        """Construye el area de preview con pestañas."""
        preview_card = crear_card(parent)
        preview_card.pack(fill="both", expand=True)
        
        tabview = ctk.CTkTabview(preview_card)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        tab_texto = tabview.add("Texto del Contrato")
        self._build_text_tab(tab_texto)
        
        tab_preguntas = tabview.add("Preguntar al Contrato")
        self._build_qa_tab(tab_preguntas)
        
        tab_analisis = tabview.add("Analisis Legal")
        self._build_analysis_tab(tab_analisis)
        
        tab_resultados = tabview.add("Resultados")
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
        qa_frame = ctk.CTkFrame(parent, fg_color="transparent")
        qa_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            qa_frame,
            text="Haz una pregunta sobre el contrato:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.question_entry = ctk.CTkTextbox(qa_frame, height=80, wrap="word")
        self.question_entry.pack(fill="x", pady=(0, 10))
        self.question_entry.insert("1.0", "Ejemplo: Cuales son las penalizaciones por incumplimiento?")
        
        btn_frame = ctk.CTkFrame(qa_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))
        
        self.btn_ask = ctk.CTkButton(
            btn_frame,
            text="Preguntar",
            command=self._ask_question,
            width=150,
            state="disabled"
        )
        self.btn_ask.pack(side="left")
        
        self.qa_progress = ctk.CTkProgressBar(btn_frame, width=300)
        self.qa_progress.pack(side="left", padx=(10, 0))
        self.qa_progress.set(0)
        self.qa_progress.pack_forget()
        
        ctk.CTkLabel(
            qa_frame,
            text="Respuesta:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.answer_text = ctk.CTkTextbox(qa_frame, wrap="word", height=150)
        self.answer_text.pack(fill="x", pady=(0, 10))
        self.answer_text.insert("1.0", "Las respuestas apareceran aqui...")
        self.answer_text.configure(state="disabled")
        
        ctk.CTkLabel(
            qa_frame,
            text="Contexto utilizado:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(5, 5))
        
        self.context_text = ctk.CTkTextbox(qa_frame, height=120, wrap="word")
        self.context_text.pack(fill="x")
        self.context_text.insert("1.0", "El contexto usado aparecera aqui...")
        self.context_text.configure(state="disabled")
    
    def _build_analysis_tab(self, parent):
        """Construye la pestaña de analisis legal."""
        analysis_frame = ctk.CTkFrame(parent, fg_color="transparent")
        analysis_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            analysis_frame,
            text="Analisis Legal del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(
            analysis_frame,
            text="Selecciona el tipo de analisis:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 5))
        
        options_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, 10))
        
        self.analysis_type_var = ctk.StringVar(value="completo")
        
        self.radio_completo = ctk.CTkRadioButton(
            options_frame,
            text="Analisis Completo (todos los aspectos)",
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
        
        btn_analysis_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        btn_analysis_frame.pack(fill="x", pady=(10, 5))
        
        self.btn_analyze = ctk.CTkButton(
            btn_analysis_frame,
            text="Iniciar Analisis",
            command=self._start_analysis,
            width=200,
            height=40,
            fg_color="#3498db",
            state="disabled"
        )
        self.btn_analyze.pack(side="left")
        
        self.analysis_progress = ctk.CTkProgressBar(btn_analysis_frame, width=300)
        self.analysis_progress.pack(side="left", padx=(10, 0))
        self.analysis_progress.set(0)
        self.analysis_progress.pack_forget()
    
    def _build_results_tab(self, parent):
        """Construye la pestaña de resultados - SOLO resumen ejecutivo."""
        results_frame = ctk.CTkScrollableFrame(parent)
        results_frame.pack(fill="both", expand=True)
        
        # Un solo card para todos los resultados
        main_card = crear_card(results_frame)
        main_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            main_card,
            text="RESULTADOS DEL ANALISIS",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.summary_text = ctk.CTkTextbox(main_card, wrap="word", height=500)
        self.summary_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.summary_text.insert("1.0", "Los resultados completos del analisis apareceran aqui...")
        self.summary_text.configure(state="disabled")
    
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
        """Abre la ventana de configuracion completa para cambiar API key y modelos."""
        # Cerrar ventana actual
        self.root.destroy()
        
        # Abrir ventana de configuracion
        from interface.tkinter.config_window import ConfigWindow
        config = ConfigWindow()
        config.run()
    
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
        self.progress_card.update_progress(0.5, mensaje, "")
        self.status_label.configure(text=f"Procesando: {mensaje}")
    
    def _on_process_complete(self, resultado: dict):
        self.current_contract_data = resultado
        self.is_processing = False
        
        self.file_upload.set_success(resultado["nombre_archivo"])
        self.progress_card.update_progress(1.0, "Indexando...", "")
        
        try:
            self.status_label.configure(text="Indexando...")
            index_result = self.rag_service.index_contract(resultado)
            
            if index_result.get("estado") == "exito":
                self.progress_card.update_progress(1.0, "Completado!", 
                                                   f"Indexados {index_result['chunks_indexados']} chunks")
                self.status_label.configure(text="Documento procesado")
                
                self.btn_ask.configure(state="normal")
                self.btn_analyze.configure(state="normal")
                self.btn_export.configure(state="normal")
            else:
                self.status_label.configure(text="Indexacion fallida")
        except Exception as e:
            logger.error(f"Error en indexacion: {e}")
            self.status_label.configure(text="Error en indexacion")
        
        self._update_contract_info(resultado)
        self._update_preview(resultado)
        self.root.after(2000, self.progress_card.hide)
    
    def _on_process_error(self, error: str):
        self.is_processing = False
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        self.status_label.configure(text="Error")
        
        if "503" in error or "UNAVAILABLE" in error or "high demand" in error.lower():
            messagebox.showerror(
                "Servicio No Disponible",
                "El servicio de Gemini esta con alta demanda.\n\n"
                "Sugerencias:\n"
                "1. Espera unos minutos\n"
                "2. Cambia el modelo en .env a: GEMINI_MODEL=gemini-2.0-flash"
            )
        else:
            messagebox.showerror("Error", f"No se pudo procesar:\n{error}")
    
    def _update_contract_info(self, resultado: dict):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        info = f"""Nombre: {resultado['nombre_archivo']}
Paginas: {resultado['total_paginas']}
Caracteres: {resultado['total_caracteres']:,}
Chunks: {resultado['total_chunks']}"""
        self.info_text.insert("1.0", info)
        self.info_text.configure(state="disabled")
    
    def _update_preview(self, resultado: dict):
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        texto = resultado['texto_completo'][:3000]
        if len(resultado['texto_completo']) > 3000:
            texto += "\n\n... [texto truncado]"
        self.preview_text.insert("1.0", texto)
        self.preview_text.configure(state="disabled")
        self.stats_label.configure(text=f"Total: {resultado['total_caracteres']} caracteres | {resultado['total_chunks']} chunks")
    
    def _generar_respuesta_especifica(self, pregunta: str, resultado: dict) -> str:
        """Genera una respuesta especifica sin emojis ni formato."""
        pregunta_lower = pregunta.lower()
        hallazgos = resultado.get("hallazgos", [])
        
        if hallazgos and hallazgos[0].get("tipo") == "error":
            return f"Error: {hallazgos[0].get('descripcion', 'Error desconocido')}\n\nRecomendacion: {hallazgos[0].get('recomendacion', '')}"
        
        if not hallazgos:
            return "No se encontro informacion relevante en el contrato para responder a tu pregunta."
        
        # Penalizaciones
        if "penalizacion" in pregunta_lower or "multa" in pregunta_lower or "penalización" in pregunta_lower:
            for h in hallazgos:
                if "penalizacion" in h.get("tipo", "").lower():
                    return f"Respuesta:\n\n{h.get('descripcion', '')}\n\nRecomendacion:\n{h.get('recomendacion', '')}"
            for h in hallazgos:
                if "penalización" in h.get("descripcion", "").lower() or "incumplimiento" in h.get("descripcion", "").lower():
                    return f"Respuesta:\n\n{h.get('descripcion', '')}\n\nRecomendacion:\n{h.get('recomendacion', '')}"
        
        # Rescision
        if any(p in pregunta_lower for p in ["rescindir", "terminar", "cancelar", "rescisión", "terminación"]):
            for h in hallazgos:
                if "rescision" in h.get("tipo", "").lower():
                    return f"Respuesta:\n\n{h.get('descripcion', '')}\n\nRecomendacion:\n{h.get('recomendacion', '')}"
        
        # Fechas
        if any(p in pregunta_lower for p in ["fecha", "vencimiento", "plazo", "comienza", "termina", "inicia", "dura"]):
            for h in hallazgos:
                if "fecha" in h.get("tipo", "").lower():
                    return f"Respuesta:\n\n{h.get('descripcion', '')}"
        
        # Pagos
        if any(p in pregunta_lower for p in ["pago", "precio", "costo", "monto", "abonar", "pagar"]):
            for h in hallazgos:
                if "pago" in h.get("tipo", "").lower():
                    return f"Respuesta:\n\n{h.get('descripcion', '')}\n\nRecomendacion:\n{h.get('recomendacion', '')}"
        
        # Un solo hallazgo
        if len(hallazgos) == 1:
            h = hallazgos[0]
            return f"Respuesta:\n\n{h.get('descripcion', '')}\n\nRecomendacion:\n{h.get('recomendacion', '')}"
        
        # Respuesta general
        respuesta = "Respuesta:\n\n"
        for i, h in enumerate(hallazgos[:3], 1):
            respuesta += f"{i}. {h.get('descripcion', '')}\n"
            if h.get('recomendacion'):
                respuesta += f"   Recomendacion: {h.get('recomendacion', '')}\n\n"
        
        return respuesta if len(respuesta) > 20 else "No se encontro informacion especifica para tu pregunta."

    def _extraer_contexto_resumido(self, resultado: dict) -> str:
        """Extrae un contexto resumido para mostrar."""
        hallazgos = resultado.get("hallazgos", [])
        if not hallazgos:
            return ""
        
        if hallazgos[0].get("tipo") == "error":
            return ""
        
        contexto = "Contexto utilizado:\n\n"
        for i, h in enumerate(hallazgos[:2], 1):
            texto = h.get('texto_relevante', '')[:200]
            if texto:
                contexto += f"{i}. {texto}...\n\n"
        
        return contexto
    
    def _ask_question(self):
        """Realiza una pregunta sobre el contrato."""
        if not self.current_contract_data:
            messagebox.showwarning("Advertencia", "Primero carga un contrato")
            return

        if self.is_answering:
            messagebox.showwarning("En proceso", "Espera a que termine la respuesta actual")
            return

        pregunta = self.question_entry.get("1.0", "end-1c").strip()

        if not pregunta:
            messagebox.showwarning("Advertencia", "Escribe una pregunta")
            return

        self.is_answering = True
        self.btn_ask.configure(state="disabled", text="Procesando...")
        self.status_label.configure(text="Buscando...")
        
        self.qa_progress.pack(side="left", padx=(10, 0))
        self.qa_progress.set(0.2)

        def task():
            for intento in range(3):
                try:
                    if self.workflow is None:
                        raise Exception("Sistema no disponible")

                    self.root.after(0, lambda: self.qa_progress.set(0.5))
                    self.root.after(0, lambda: self.status_label.configure(
                        text=f"Procesando pregunta (intento {intento+1}/3)..."
                    ))

                    resultado = self.workflow.ejecutar_sync(
                        self.current_contract_data['texto_completo'],
                        consulta=pregunta
                    )

                    if resultado.get("exito"):
                        respuesta = self._generar_respuesta_especifica(pregunta, resultado)
                        contexto = self._extraer_contexto_resumido(resultado)
                        self.root.after(0, lambda: self._show_answer(respuesta, contexto))
                        return
                    else:
                        raise Exception(resultado.get("error", "Error desconocido"))

                except Exception as e:
                    error = str(e)
                    logger.error(f"Error en pregunta: {error}")

                    if "503" in error or "UNAVAILABLE" in error or "high demand" in error.lower():
                        if intento < 2:
                            time.sleep(2 * (intento + 1))
                            continue
                        respuesta = "Servidor de Gemini saturado. Intenta de nuevo en unos minutos. Se recomienda cambiar a gemini-2.0-flash en la configuracion."
                    elif "quota" in error.lower() or "exceeded" in error.lower():
                        respuesta = "Cuota de API agotada. Cambia tu API key."
                    else:
                        respuesta = f"Error: {error[:200]}"

                    self.root.after(0, lambda: self._show_answer(respuesta, ""))
                    return
                finally:
                    self.root.after(0, lambda: self.qa_progress.set(1.0))
                    self.root.after(0, lambda: self.qa_progress.pack_forget())

            self.root.after(0, self._reset_ask_button)

        threading.Thread(target=task, daemon=True).start()
    
    def _reset_ask_button(self):
        """Resetea el boton de preguntar."""
        self.btn_ask.configure(state="normal", text="Preguntar")
        self.status_label.configure(text="Listo")
        self.is_answering = False
    
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

        self.btn_ask.configure(state="normal", text="Preguntar")
        self.status_label.configure(text="Listo")
        self.is_answering = False
        self.qa_progress.pack_forget()
    
    def _start_analysis(self):
        """Inicia el analisis legal."""
        if not self.current_contract_data:
            messagebox.showwarning("Advertencia", "Carga un contrato primero")
            return

        self.is_analyzing = True
        self.btn_analyze.configure(state="disabled", text="Analizando...")
        self.status_label.configure(text="Analizando contrato...")
        
        self.analysis_progress.pack(side="left", padx=(10, 0))
        self.analysis_progress.set(0.2)

        def task():
            for intento in range(3):
                try:
                    if self.workflow is None:
                        raise Exception("Sistema no disponible")

                    self.root.after(0, lambda: self.analysis_progress.set(0.5))
                    self.root.after(0, lambda: self.status_label.configure(
                        text=f"Analizando contrato (intento {intento+1}/3)..."
                    ))

                    resultado = self.workflow.ejecutar_sync(
                        self.current_contract_data['texto_completo'],
                        consulta="analizar contrato"
                    )

                    if resultado.get("exito"):
                        self.root.after(0, lambda: self._show_analysis_results(resultado))
                        return
                    else:
                        raise Exception(resultado.get("error", "Error desconocido"))

                except Exception as e:
                    error = str(e)
                    logger.error(f"Error en analisis: {error}")

                    if "503" in error or "UNAVAILABLE" in error or "high demand" in error.lower():
                        if intento < 2:
                            time.sleep(2 * (intento + 1))
                            continue
                        error_msg = "Servidor de Gemini saturado. Intenta de nuevo en unos minutos. Se recomienda cambiar a gemini-2.0-flash en la configuracion."
                    elif "quota" in error.lower() or "exceeded" in error.lower():
                        error_msg = "Cuota de API agotada. Cambia tu API key."
                    else:
                        error_msg = f"Error: {error[:200]}"

                    self.root.after(0, lambda: self._show_analysis_error(error_msg))
                    return
                finally:
                    self.root.after(0, lambda: self.analysis_progress.set(1.0))
                    self.root.after(0, lambda: self.analysis_progress.pack_forget())

            self.root.after(0, self._reset_analyze_button)

        threading.Thread(target=task, daemon=True).start()
    
    def _reset_analyze_button(self):
        """Resetea el boton de analizar."""
        self.btn_analyze.configure(state="normal", text="Iniciar Analisis")
        self.status_label.configure(text="Listo")
        self.is_analyzing = False
    
    def _show_analysis_results(self, resultado: dict):
        """Muestra los resultados del analisis."""
        
        hallazgos = resultado.get("hallazgos", [])
        
        hay_error = any(h.get("tipo") == "error" for h in hallazgos)
        
        if hay_error:
            mensaje_error = "ERROR EN EL ANALISIS\n\n"
            for h in hallazgos:
                if h.get("tipo") == "error":
                    mensaje_error += f"{h.get('descripcion', '')}\n"
                    mensaje_error += f"Recomendacion: {h.get('recomendacion', '')}\n\n"
            
            self.summary_text.configure(state="normal")
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", mensaje_error)
            self.summary_text.configure(state="disabled")
            
            self.status_label.configure(text="Error en analisis")
            self.btn_analyze.configure(state="normal", text="Iniciar Analisis")
            self.is_analyzing = False
            self.analysis_progress.pack_forget()
            
            messagebox.showerror("Error de Analisis", mensaje_error)
            return
        
        altos = []
        medios = []
        bajos = []
        
        for h in hallazgos:
            riesgo = h.get("riesgo", "MEDIO")
            texto = f"""* {h.get('descripcion', '')}
  Texto: "{h.get('texto_relevante', '')}"
  Recomendacion: {h.get('recomendacion', '')}

"""
            if riesgo == "ALTO":
                altos.append(texto)
            elif riesgo == "MEDIO":
                medios.append(texto)
            else:
                bajos.append(texto)
        
        resumen_completo = []
        resumen_completo.append("=" * 60)
        resumen_completo.append("RESULTADOS DEL ANALISIS LEGAL")
        resumen_completo.append("=" * 60)
        resumen_completo.append(f"\nAgente utilizado: {resultado.get('agente_usado', 'desconocido')}")
        
        resumen_completo.append(f"\n{'=' * 60}")
        resumen_completo.append(f"RIESGOS ALTOS ({len(altos)})")
        resumen_completo.append("=" * 60)
        if altos:
            resumen_completo.extend(altos)
        else:
            resumen_completo.append("No se detectaron riesgos altos\n")
        
        resumen_completo.append(f"\n{'=' * 60}")
        resumen_completo.append(f"RIESGOS MEDIOS ({len(medios)})")
        resumen_completo.append("=" * 60)
        if medios:
            resumen_completo.extend(medios)
        else:
            resumen_completo.append("No se detectaron riesgos medios\n")
        
        resumen_completo.append(f"\n{'=' * 60}")
        resumen_completo.append(f"RIESGOS BAJOS / INFORMATIVOS ({len(bajos)})")
        resumen_completo.append("=" * 60)
        if bajos:
            resumen_completo.extend(bajos)
        else:
            resumen_completo.append("No se detectaron riesgos bajos\n")
        
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "\n".join(resumen_completo))
        self.summary_text.configure(state="disabled")
        
        self.btn_export.configure(state="normal")
        self.status_label.configure(text="Analisis completado")
        
        self.btn_analyze.configure(state="normal", text="Iniciar Analisis")
        self.is_analyzing = False
        self.analysis_progress.pack_forget()
        
        altos_count = len(altos)
        medios_count = len(medios)
        bajos_count = len(bajos)
        
        messagebox.showinfo("Analisis Completado", 
                           f"Analisis finalizado.\n\n"
                           f"Riesgos Altos: {altos_count}\n"
                           f"Riesgos Medios: {medios_count}\n"
                           f"Riesgos Bajos: {bajos_count}\n\n"
                           f"Los detalles completos estan en la pestaña de Resultados.")
    
    def _show_analysis_error(self, error: str):
        """Muestra error en el analisis."""
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", f"Error en el analisis:\n\n{error}")
        self.summary_text.configure(state="disabled")
        
        self.btn_analyze.configure(state="normal", text="Iniciar Analisis")
        self.is_analyzing = False
        self.analysis_progress.pack_forget()
        self.status_label.configure(text="Error en analisis")
    
    def _export_analysis(self):
        """Exporta el analisis a PDF."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Carga un contrato primero")
            return
        
        resumen = self.summary_text.get("1.0", "end-1c")
        
        if not resumen or resumen == "Los resultados del analisis apareceran aqui...":
            messagebox.showwarning("Sin analisis", "Primero realiza un analisis del contrato")
            return
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            title="Guardar Analisis como PDF",
            filetypes=[
                ("Documento PDF", "*.pdf"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if archivo:
            try:
                export_service = PDFExportService()
                
                pdf_path = export_service.exportar_analisis(
                    resumen=resumen,
                    contrato_nombre=self.current_contract_data['nombre_archivo'],
                    archivo_salida=Path(archivo)
                )
                
                messagebox.showinfo(
                    "Exportacion Exitosa", 
                    f"Analisis exportado a PDF:\n\n{pdf_path}\n\n"
                    "El archivo se ha guardado correctamente."
                )
            except Exception as e:
                logger.error(f"Error exportando a PDF: {e}")
                messagebox.showerror("Error", f"No se pudo exportar el analisis:\n\n{e}")
    
    def _on_clear(self):
        """Limpia el contrato actual."""
        if self.is_processing or self.is_analyzing or self.is_answering:
            messagebox.showwarning("En proceso", "Espera a que termine")
            return
        
        self.current_contract_data = None
        self.current_pdf_path = None
        
        if self.rag_service:
            self.rag_service.clear()
        
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", "Esperando carga...")
        self.info_text.configure(state="disabled")
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "El texto aparecera aqui...")
        self.preview_text.configure(state="disabled")
        
        self.answer_text.configure(state="normal")
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", "Las respuestas apareceran aqui...")
        self.answer_text.configure(state="disabled")
        
        self.context_text.configure(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", "El contexto aparecera aqui...")
        self.context_text.configure(state="disabled")
        
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "Los resultados apareceran aqui...")
        self.summary_text.configure(state="disabled")
        
        self.question_entry.delete("1.0", "end")
        self.question_entry.insert("1.0", "Ejemplo: Cuales son las penalizaciones?")
        
        self.stats_label.configure(text="")
        self.status_label.configure(text="Sistema listo")
        
        self.btn_ask.configure(state="disabled")
        self.btn_analyze.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        
        self.file_upload.reset_state()
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        self.progress_card.reset()
        
        messagebox.showinfo("Limpieza", "Contrato eliminado. Puedes cargar otro.")
    
    def _on_closing(self):
        """Maneja el cierre."""
        if self.is_processing or self.is_analyzing or self.is_answering:
            if messagebox.askyesno("Salir", "Hay procesos en curso. ¿Salir?"):
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Ejecuta la ventana."""
        self.root.mainloop()