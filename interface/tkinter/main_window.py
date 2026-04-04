"""
Ventana principal de la aplicacion.
Maneja la carga de PDF y visualizacion de resultados.
"""

import logging
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

from interface.tkinter.components import FileUploadFrame, ProgressCard
from interface.tkinter.styles import configurar_tema, crear_titulo, crear_card
from application.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Ventana principal de Contract Analyzer Pro.
    """
    
    def __init__(self):
        """Inicializa la ventana principal."""
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Analizador de Contratos")
        self.root.geometry("1200x800")
        
        # Configurar tema
        self.colores = configurar_tema()
        
        # Servicios
        self.processing_service = ProcessingService()
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
        
        # Frame principal con padding
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header con titulo
        self._build_header(main_frame)
        
        # Contenido principal (2 columnas)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=20)
        
        # Columna izquierda - Carga de PDF
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self._build_upload_area(left_column)
        
        # Columna derecha - Visualizacion
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self._build_preview_area(right_column)
        
        # Footer con botones de accion
        self._build_footer(main_frame)
    
    def _build_header(self, parent):
        """Construye el header de la aplicacion."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x")
        
        titulo = crear_titulo(header_frame, "CONTRACT ANALYZER PRO", 24)
        titulo.pack(side="left")
        
        # Info de estado
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="✅ Sistema listo",
            font=ctk.CTkFont(size=12),
            text_color="#2ecc71"
        )
        self.status_label.pack(side="right")
    
    def _build_upload_area(self, parent):
        """Construye el area de carga de PDF."""
        
        # Card de carga
        upload_card = crear_card(parent)
        upload_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            upload_card,
            text="📁 Cargar Contrato",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Area de carga de archivos
        self.file_upload = FileUploadFrame(
            upload_card,
            on_file_selected=self._on_file_selected,
            height=250,
            corner_radius=10,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.file_upload.pack(fill="x", padx=20, pady=(0, 20))
        
        # Card de informacion del contrato
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
    
    def _build_preview_area(self, parent):
        """Construye el area de previsualizacion del texto."""
        
        preview_card = crear_card(parent)
        preview_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            preview_card,
            text="📄 Vista Previa del Texto",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Barra de progreso
        self.progress_card = ProgressCard(preview_card)
        self.progress_card.hide()
        
        # Area de texto
        self.preview_text = ctk.CTkTextbox(preview_card, wrap="word")
        self.preview_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.preview_text.insert("1.0", "El texto del contrato aparecera aqui despues de procesar el PDF...")
        self.preview_text.configure(state="disabled")
        
        # Estadisticas
        stats_frame = ctk.CTkFrame(preview_card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.stats_label.pack()
    
    def _build_footer(self, parent):
        """Construye el footer con botones de accion."""
        
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
        # Separador
        separator = ctk.CTkFrame(footer_frame, height=1, fg_color="#3d3d3d")
        separator.pack(fill="x", pady=(0, 15))
        
        # Botones
        buttons_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        self.btn_analyze = ctk.CTkButton(
            buttons_frame,
            text="🔍 Analizar Riesgos",
            command=self._on_analyze,
            width=180,
            height=40,
            fg_color=self.colores["secondary"],
            hover_color=self.colores["secondary_hover"],
            state="disabled",
            font=ctk.CTkFont(size=13, weight="bold")
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
            border_color="#555555",
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
            border_width=1,
            border_color="#555555"
        )
        self.btn_clear.pack(side="left", padx=(10, 0))
    
    def _on_file_selected(self, pdf_path: Path):
        """
        Maneja la seleccion de un archivo PDF.
        
        Args:
            pdf_path: Ruta al PDF seleccionado
        """
        if self.is_processing:
            messagebox.showwarning("En proceso", "Ya hay un documento en procesamiento")
            return
        
        # Validar extension
        if pdf_path.suffix.lower() != '.pdf':
            messagebox.showerror("Error", "Solo se permiten archivos PDF")
            return
        
        # Validar tamaño (max 50MB)
        if pdf_path.stat().st_size > 50 * 1024 * 1024:
            messagebox.showerror("Error", "El archivo es demasiado grande (max 50MB)")
            return
        
        self.current_pdf_path = pdf_path
        self._procesar_pdf()
    
    def _procesar_pdf(self):
        """Procesa el PDF en segundo plano."""
        self.is_processing = True
        self.file_upload.set_loading(True)
        self.progress_card.show()
        self.progress_card.update_progress(0.1, "Iniciando procesamiento...", "")
        
        def on_progress(mensaje: str):
            """Actualiza progreso desde el hilo."""
            self.root.after(0, lambda: self._update_progress(mensaje))
        
        def on_complete(resultado: dict):
            """Completado desde el hilo."""
            self.root.after(0, lambda: self._on_process_complete(resultado))
        
        def on_error(error: str):
            """Error desde el hilo."""
            self.root.after(0, lambda: self._on_process_error(error))
        
        # Iniciar procesamiento
        self.processing_service.procesar_pdf(
            self.current_pdf_path,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error
        )
    
    def _update_progress(self, mensaje: str):
        """Actualiza la UI con el progreso."""
        self.progress_card.update_progress(0.5, mensaje, "")
        self.status_label.configure(text=f"🔄 {mensaje}")
    
    def _on_process_complete(self, resultado: dict):
        """Maneja la finalizacion del procesamiento."""
        self.current_contract_data = resultado
        self.is_processing = False
        
        # Actualizar UI
        self.file_upload.set_success(resultado["nombre_archivo"])
        self.progress_card.update_progress(1.0, "Procesamiento completado!", "")
        self.status_label.configure(text="✅ Documento procesado")
        
        # Actualizar informacion del contrato
        self._update_contract_info(resultado)
        
        # Actualizar preview de texto
        self._update_preview(resultado)
        
        # Habilitar botones
        self.btn_analyze.configure(state="normal")
        self.btn_export.configure(state="normal")
        
        # Ocultar progreso despues de 2 segundos
        self.root.after(2000, self.progress_card.hide)
    
    def _on_process_error(self, error: str):
        """Maneja error en el procesamiento."""
        self.is_processing = False
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        self.status_label.configure(text="❌ Error en procesamiento")
        
        messagebox.showerror("Error de Procesamiento", f"No se pudo procesar el PDF:\n\n{error}")
    
    def _update_contract_info(self, resultado: dict):
        """Actualiza la informacion del contrato."""
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        
        info = f"""Nombre: {resultado['nombre_archivo']}
Paginas: {resultado['total_paginas']}
Caracteres: {resultado['total_caracteres']:,}
Chunks: {resultado['total_chunks']}

Metadatos:
- Titulo: {resultado['metadatos'].get('titulo', 'N/A')}
- Autor: {resultado['metadatos'].get('autor', 'N/A')}"""
        
        self.info_text.insert("1.0", info)
        self.info_text.configure(state="disabled")
    
    def _update_preview(self, resultado: dict):
        """Actualiza el preview del texto."""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        
        # Mostrar primeros 2000 caracteres
        texto_preview = resultado['texto_completo'][:2000]
        if len(resultado['texto_completo']) > 2000:
            texto_preview += "\n\n... [texto truncado, usar analisis para ver completo]"
        
        self.preview_text.insert("1.0", texto_preview)
        self.preview_text.configure(state="disabled")
        
        # Actualizar estadisticas
        self.stats_label.configure(
            text=f"Total: {resultado['total_caracteres']} caracteres | {resultado['total_chunks']} chunks"
        )
    
    def _on_analyze(self):
        """Inicia el analisis de riesgos (FASE 4)."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Primero carga un contrato")
            return
        
        messagebox.showinfo("Analisis de Riesgos", 
            "El analisis de riesgos se implementara en la FASE 4\n\n"
            f"Contrato: {self.current_contract_data['nombre_archivo']}\n"
            f"Chunks: {self.current_contract_data['total_chunks']}\n"
            f"Caracteres: {self.current_contract_data['total_caracteres']:,}")
    
    def _on_export(self):
        """Exporta el analisis."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Primero carga un contrato")
            return
        
        from tkinter import filedialog
        archivo = filedialog.asksaveasfilename(
            title="Guardar analisis",
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("CONTRACT ANALYZER PRO - ANALISIS DE CONTRATO\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"Archivo: {self.current_contract_data['nombre_archivo']}\n")
                    f.write(f"Paginas: {self.current_contract_data['total_paginas']}\n")
                    f.write(f"Caracteres: {self.current_contract_data['total_caracteres']}\n")
                    f.write(f"Chunks: {self.current_contract_data['total_chunks']}\n\n")
                    f.write("=" * 60 + "\n")
                    f.write("TEXTO DEL CONTRATO\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(self.current_contract_data['texto_completo'])
                
                messagebox.showinfo("Exito", f"Analisis exportado a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
    
    def _on_clear(self):
        """Limpia el contrato actual."""
        if self.is_processing:
            messagebox.showwarning("En proceso", "Espera a que termine el procesamiento")
            return
        
        self.current_contract_data = None
        self.current_pdf_path = None
        
        # Limpiar UI
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", "Esperando carga de documento...")
        self.info_text.configure(state="disabled")
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "El texto del contrato aparecera aqui despues de procesar el PDF...")
        self.preview_text.configure(state="disabled")
        
        self.stats_label.configure(text="")
        self.status_label.configure(text="✅ Sistema listo")
        
        # Deshabilitar botones
        self.btn_analyze.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        
        # Resetear area de carga
        self.file_upload._reset_state()
        
        messagebox.showinfo("Limpieza", "Contrato eliminado correctamente")
    
    def _on_closing(self):
        """Maneja el cierre de la ventana."""
        if self.is_processing:
            respuesta = messagebox.askyesno("Salir", "Hay un procesamiento en curso. ¿Seguro que quieres salir?")
            if respuesta:
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Ejecuta la ventana principal."""
        self.root.mainloop()