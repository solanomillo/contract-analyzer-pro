"""
Ventana principal de la aplicacion.
Version simplificada: solo preguntas y analisis completo.
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
        
        # Columna derecha - Preguntas y Analisis
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_column.grid_rowconfigure(0, weight=1)
        right_column.grid_columnconfigure(0, weight=1)
        self._build_right_area(right_column)
        
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
    
    def _build_right_area(self, parent):
        """Construye el area derecha (preguntas + analisis)."""
        
        # Pestañas
        tabview = ctk.CTkTabview(parent)
        tabview.pack(fill="both", expand=True)
        
        # Pestaña de preguntas
        tab_preguntas = tabview.add("Preguntar al Contrato")
        self._build_qa_tab(tab_preguntas)
        
        # Pestaña de analisis
        tab_analisis = tabview.add("Analisis Legal")
        self._build_analysis_tab(tab_analisis)
    
    def _build_qa_tab(self, parent):
        """Construye la pestaña de preguntas y respuestas."""
        qa_frame = ctk.CTkFrame(parent, fg_color="transparent")
        qa_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            qa_frame,
            text="Haz una pregunta sobre el contrato:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.question_entry = ctk.CTkTextbox(qa_frame, height=80, wrap="word")
        self.question_entry.pack(fill="x", pady=(0, 10))
        self.question_entry.insert("1.0", "Ejemplo: Cuanto es el pago mensual?")
        
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
        analysis_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            analysis_frame,
            text="Analisis Legal del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(
            analysis_frame,
            text="Genera un analisis completo del contrato, incluyendo riesgos, fechas y obligaciones.",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(anchor="w", pady=(0, 15))
        
        btn_analysis_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        btn_analysis_frame.pack(fill="x", pady=(10, 5))
        
        self.btn_analyze = ctk.CTkButton(
            btn_analysis_frame,
            text="Generar Analisis Completo",
            command=self._start_analysis,
            width=220,
            height=45,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled"
        )
        self.btn_analyze.pack(side="left")
        
        self.analysis_progress = ctk.CTkProgressBar(btn_analysis_frame, width=300)
        self.analysis_progress.pack(side="left", padx=(10, 0))
        self.analysis_progress.set(0)
        self.analysis_progress.pack_forget()
        
        # Resultados del analisis
        ctk.CTkLabel(
            analysis_frame,
            text="Resultados:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(20, 5))
        
        self.analysis_text = ctk.CTkTextbox(analysis_frame, wrap="word", height=400)
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
            self.status_label.configure(text="Configuracion actualizada")
            messagebox.showinfo("Exito", "Configuracion actualizada.")
        
        config = ConfigWindow(parent=self.root, on_config_saved=on_config_saved)
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
        
        # Crear barra de progreso temporal
        self.progress_frame = ctk.CTkFrame(self.root)
        self.progress_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0.1)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Iniciando procesamiento...")
        self.progress_label.pack()
        
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
        self.progress_bar.set(0.5)
        self.progress_label.configure(text=mensaje)
        self.status_label.configure(text=f"Procesando: {mensaje}")
    
    def _on_process_complete(self, resultado: dict):
        self.current_contract_data = resultado
        self.is_processing = False
        
        self.file_upload.set_success(resultado["nombre_archivo"])
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Indexando...")
        
        try:
            self.status_label.configure(text="Indexando...")
            index_result = self.rag_service.index_contract(resultado)
            
            if index_result.get("estado") == "exito":
                self.progress_label.configure(text="Procesamiento completado!")
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
        
        # Ocultar progreso
        self.root.after(2000, lambda: self.progress_frame.pack_forget())
    
    def _on_process_error(self, error: str):
        self.is_processing = False
        self.file_upload.set_loading(False)
        self.progress_frame.pack_forget()
        self.status_label.configure(text="Error")
        
        if "503" in error or "UNAVAILABLE" in error:
            messagebox.showerror(
                "Servicio No Disponible",
                "El servicio de Gemini esta con alta demanda.\n\nEspera unos minutos o cambia el modelo."
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
        pass  # No necesitamos preview de texto
    
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
            try:
                if self.workflow is None:
                    raise Exception("Sistema no disponible")

                self.root.after(0, lambda: self.qa_progress.set(0.5))

                resultado = self.workflow.ejecutar_sync(
                    self.current_contract_data['texto_completo'],
                    consulta=pregunta,
                    tipo="pregunta"
                )

                if resultado.get("exito"):
                    respuesta = resultado.get("resumen", "No se obtuvo respuesta")
                    self.root.after(0, lambda: self._show_answer(respuesta))
                    return
                else:
                    raise Exception(resultado.get("error", "Error desconocido"))

            except Exception as e:
                error = str(e)
                logger.error(f"Error: {error}")

                if "503" in error or "UNAVAILABLE" in error:
                    respuesta = "Servidor de Gemini saturado. Intenta de nuevo en unos minutos."
                else:
                    respuesta = f"Error: {error[:200]}"

                self.root.after(0, lambda: self._show_answer(respuesta))
            finally:
                self.root.after(0, lambda: self.qa_progress.set(1.0))
                self.root.after(0, lambda: self.qa_progress.pack_forget())
                self.root.after(0, self._reset_ask_button)

        threading.Thread(target=task, daemon=True).start()
    
    def _reset_ask_button(self):
        self.btn_ask.configure(state="normal", text="Preguntar")
        self.status_label.configure(text="Listo")
        self.is_answering = False
    
    def _show_answer(self, respuesta: str):
        self.answer_text.configure(state="normal")
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", respuesta)
        self.answer_text.configure(state="disabled")
    
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
        
        self.answer_text.configure(state="normal")
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", "Las respuestas apareceran aqui...")
        self.answer_text.configure(state="disabled")
        
        self.context_text.configure(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", "El contexto aparecera aqui...")
        self.context_text.configure(state="disabled")
        
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "Los resultados del analisis apareceran aqui...")
        self.analysis_text.configure(state="disabled")
        
        self.question_entry.delete("1.0", "end")
        self.question_entry.insert("1.0", "Ejemplo: Cuanto es el pago mensual?")
        
        self.status_label.configure(text="Sistema listo")
        
        self.btn_ask.configure(state="disabled")
        self.btn_analyze.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        
        self.file_upload.reset_state()
        self.file_upload.set_loading(False)
        
        messagebox.showinfo("Limpieza", "Contrato eliminado. Puedes cargar otro.")
    
    def _on_closing(self):
        if self.is_processing or self.is_analyzing or self.is_answering:
            if messagebox.askyesno("Salir", "Hay procesos en curso. ¿Salir?"):
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()