"""
Ventana principal de la aplicacion.
Maneja la carga de PDF y visualizacion de resultados.
"""

import logging
import os
import sys
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox, filedialog

from interface.tkinter.components import FileUploadFrame, ProgressCard
from interface.tkinter.styles import configurar_tema, crear_titulo, crear_card
from application.services.processing_service import ProcessingService
from application.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class MainWindow:
    """Ventana principal de Contract Analyzer Pro."""
    
    def __init__(self):
        """Inicializa la ventana principal."""
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Analizador de Contratos")
        self.root.geometry("1200x800")
        
        # Configurar tema
        self.colores = configurar_tema()
        
        # Servicios
        self.processing_service = ProcessingService()
        self.config_service = ConfigService()
        self.current_contract_data = None
        self.current_pdf_path = None
        
        # Estado
        self.is_processing = False
        
        # Construir UI
        self._build_ui()
        
        # Centrar ventana
        self._center_window()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self._build_header(main_frame)
        
        # Contenido principal (2 columnas)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=20)
        
        # Columna izquierda
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._build_upload_area(left_column)
        
        # Columna derecha
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self._build_preview_area(right_column)
        
        # Footer
        self._build_footer(main_frame)
    
    def _build_header(self, parent):
        """Construye el header."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x")
        
        titulo = crear_titulo(header_frame, "CONTRACT ANALYZER PRO", 24)
        titulo.pack(side="left")
        
        # Botones header
        header_buttons = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_buttons.pack(side="right")
        
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
        upload_card = crear_card(parent)
        upload_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            upload_card,
            text="📁 Cargar Contrato",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.file_upload = FileUploadFrame(
            upload_card,
            on_file_selected=self._on_file_selected,
            height=250,
            corner_radius=10,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.file_upload.pack(fill="x", padx=20, pady=(0, 20))
        
        # Info contrato
        info_card = crear_card(parent)
        info_card.pack(fill="x")
        
        ctk.CTkLabel(
            info_card,
            text="📋 Informacion del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.info_text = ctk.CTkTextbox(info_card, height=150, wrap="word")
        self.info_text.pack(fill="both", padx=20, pady=(0, 20))
        self.info_text.insert("1.0", "Esperando carga de documento...")
        self.info_text.configure(state="disabled")
    
    # En _build_preview_area, agregar seccion de preguntas

    def _build_preview_area(self, parent):
        """Construye el area de preview y preguntas."""
        
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
        
        self.answer_text = ctk.CTkTextbox(parent, wrap="word")
        self.answer_text.pack(fill="both", expand=True)
        self.answer_text.insert("1.0", "Las respuestas apareceran aqui...")
        self.answer_text.configure(state="disabled")
        
        # Contexto usado
        ctk.CTkLabel(
            parent,
            text="Contexto utilizado:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.context_text = ctk.CTkTextbox(parent, height=100, wrap="word")
        self.context_text.pack(fill="x")
        self.context_text.insert("1.0", "El contexto usado para generar la respuesta...")
        self.context_text.configure(state="disabled")

    def _build_analysis_tab(self, parent):
        """Construye la pestaña de analisis legal."""
        ctk.CTkLabel(
            parent,
            text="Analisis Legal del Contrato",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.analysis_text = ctk.CTkTextbox(parent, wrap="word")
        self.analysis_text.pack(fill="both", expand=True)
        self.analysis_text.insert("1.0", "El analisis legal aparecera aqui...")
        self.analysis_text.configure(state="disabled")
    
    def _build_footer(self, parent):
        """Construye el footer."""
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
        separator = ctk.CTkFrame(footer_frame, height=1, fg_color="#3d3d3d")
        separator.pack(fill="x", pady=(0, 15))
        
        buttons_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        self.btn_analyze = ctk.CTkButton(
            buttons_frame,
            text="🔍 Analizar Riesgos",
            command=self._on_analyze,
            width=180,
            height=40,
            fg_color="#3498db",
            state="disabled"
        )
        self.btn_analyze.pack(side="left", padx=(0, 10))
        
        self.btn_export = ctk.CTkButton(
            buttons_frame,
            text="📎 Exportar Analisis",
            command=self._on_export,
            width=150,
            height=40,
            fg_color="transparent",
            border_width=1,
            state="disabled"
        )
        self.btn_export.pack(side="left")
        
        self.btn_clear = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Limpiar",
            command=self._on_clear,
            width=120,
            height=40,
            fg_color="transparent",
            border_width=1
        )
        self.btn_clear.pack(side="left", padx=(10, 0))
    
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
        """Procesa el PDF."""
        self.is_processing = True
        self.file_upload.set_loading(True)
        self.progress_card.show()
        self.progress_card.update_progress(0.1, "Iniciando...", "")
        
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
        self.status_label.configure(text=f"🔄 {mensaje}")
    
    def _on_process_complete(self, resultado: dict):
        self.current_contract_data = resultado
        self.is_processing = False
        
        self.file_upload.set_success(resultado["nombre_archivo"])
        self.progress_card.update_progress(1.0, "Completado!", "")
        self.status_label.configure(text="✅ Documento procesado")
        
        self._update_contract_info(resultado)
        self._update_preview(resultado)
        
        self.btn_analyze.configure(state="normal")
        self.btn_export.configure(state="normal")
        
        self.root.after(2000, self.progress_card.hide)
    
    def _on_process_error(self, error: str):
        self.is_processing = False
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        self.status_label.configure(text="❌ Error")
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
        
        texto = resultado['texto_completo'][:2000]
        if len(resultado['texto_completo']) > 2000:
            texto += "\n\n... [texto truncado]"
        
        self.preview_text.insert("1.0", texto)
        self.preview_text.configure(state="disabled")
        
        self.stats_label.configure(
            text=f"Total: {resultado['total_caracteres']} caracteres | {resultado['total_chunks']} chunks"
        )
    
    def _on_analyze(self):
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Carga un contrato primero")
            return
        
        messagebox.showinfo("Analisis", f"Analizando: {self.current_contract_data['nombre_archivo']}")
    
    def _on_export(self):
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Carga un contrato primero")
            return
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write(self.current_contract_data['texto_completo'])
                messagebox.showinfo("Exito", f"Guardado en:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _on_clear(self):
        if self.is_processing:
            messagebox.showwarning("En proceso", "Espera a que termine")
            return
        
        self.current_contract_data = None
        self.current_pdf_path = None
        
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", "Esperando carga...")
        self.info_text.configure(state="disabled")
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "El texto aparecera aqui...")
        self.preview_text.configure(state="disabled")
        
        self.stats_label.configure(text="")
        self.status_label.configure(text="✅ Sistema listo")
        self.btn_analyze.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        self.file_upload._reset_state()
    
    def _on_closing(self):
        if self.is_processing:
            if messagebox.askyesno("Salir", "Procesamiento en curso. ¿Salir?"):
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Ejecuta la ventana."""
        self.root.mainloop()