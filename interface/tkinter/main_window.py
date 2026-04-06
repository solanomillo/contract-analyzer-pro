"""
Ventana principal de la aplicacion.
Maneja la carga de PDF, RAG y preguntas sobre el contrato.
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

logger = logging.getLogger(__name__)


class MainWindow:
    """Ventana principal de Contract Analyzer Pro."""
    
    def __init__(self):
        """Inicializa la ventana principal."""
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Analizador de Contratos")
        self.root.geometry("1300x850")
        
        # Configurar tema
        self.colores = configurar_tema()
        
        # Servicios
        self.processing_service = ProcessingService()
        self.config_service = ConfigService()
        self.rag_service = RAGService()
        self.current_contract_data = None
        self.current_pdf_path = None
        
        # Estado
        self.is_processing = False
        self.is_answering = False
        
        # Construir UI
        self._build_ui()
        
        # Centrar ventana
        self._center_window()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1300 // 2)
        y = (self.root.winfo_screenheight() // 2) - (850 // 2)
        self.root.geometry(f"1300x850+{x}+{y}")
    
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
        
        # Boton para generar analisis
        self.btn_analyze_full = ctk.CTkButton(
            parent,
            text="📊 Generar Analisis Completo",
            command=self._generate_full_analysis,
            width=200,
            state="disabled"
        )
        self.btn_analyze_full.pack(anchor="w", pady=(0, 15))
        
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
            text="📎 Exportar Texto",
            command=self._on_export,
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
                
                # Habilitar botones de preguntas
                self.btn_ask.configure(state="normal")
                self.btn_analyze_full.configure(state="normal")
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
        """Maneja error en el procesamiento."""
        self.is_processing = False
        self.file_upload.set_loading(False)
        self.progress_card.hide()
        self.status_label.configure(text="❌ Error en procesamiento")
        messagebox.showerror("Error", f"No se pudo procesar el PDF:\n\n{error}")
    
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
                # Buscar chunks relevantes
                resultados = self.rag_service.search(pregunta, k=4)
                
                if not resultados:
                    respuesta = "No se encontro informacion relevante en el contrato para responder a tu pregunta.\n\nSugerencia: Intenta reformular la pregunta o se mas especifico."
                    contexto_texto = "No se encontraron chunks relevantes."
                else:
                    # Construir contexto
                    contexto_texto = ""
                    for i, res in enumerate(resultados, 1):
                        score = res.get("score", 0)
                        texto = res.get("texto", "")[:500]
                        contexto_texto += f"\n[Chunk {i} - Relevancia: {score:.3f}]\n{texto}\n{'-'*50}\n"
                    
                    # Generar respuesta simple (por ahora mostramos los chunks)
                    # En FASE 4 se integrara con Gemini para respuestas mas naturales
                    respuesta = f"📌 **Informacion encontrada en el contrato:**\n\n"
                    for i, res in enumerate(resultados, 1):
                        score = res.get("score", 0)
                        texto = res.get("texto", "")
                        respuesta += f"\n**Fragmento {i} (relevancia: {score:.2f}):**\n{texto}\n\n"
                    
                    if len(resultados) == 0:
                        respuesta = "No se encontraron clausulas relevantes para tu pregunta."
                
                self.root.after(0, lambda: self._show_answer(respuesta, contexto_texto))
                
            except Exception as e:
                logger.error(f"Error en pregunta: {e}")
                self.root.after(0, lambda: self._show_answer(f"Error al procesar la pregunta: {e}", ""))
        
        threading.Thread(target=task, daemon=True).start()
    
    def _show_answer(self, respuesta: str, contexto: str):
        """Muestra la respuesta en la UI."""
        self.answer_text.configure(state="normal")
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", respuesta)
        self.answer_text.configure(state="disabled")
        
        self.context_text.configure(state="normal")
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", contexto if contexto else "No se encontraron chunks relevantes")
        self.context_text.configure(state="disabled")
        
        self.btn_ask.configure(state="normal", text="🔍 Preguntar")
        self.is_answering = False
    
    def _generate_full_analysis(self):
        """Genera un analisis completo del contrato."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Primero carga un contrato")
            return
        
        self.btn_analyze_full.configure(state="disabled", text="Generando analisis...")
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "🔍 Analizando contrato...\n\nEsto puede tomar unos segundos...")
        self.analysis_text.configure(state="disabled")
        
        def task():
            try:
                # Buscar diferentes tipos de clausulas
                queries = [
                    "penalizacion multa incumplimiento",
                    "rescision terminacion cancelacion",
                    "renovacion automatica prorroga",
                    "exclusividad no competencia",
                    "responsabilidad limitada indemnizacion",
                    "confidencialidad secreto"
                ]
                
                analisis = "=" * 60 + "\n"
                analisis += "ANALISIS LEGAL DEL CONTRATO\n"
                analisis += "=" * 60 + "\n\n"
                
                for query in queries:
                    resultados = self.rag_service.search(query, k=2)
                    if resultados:
                        analisis += f"\n📌 {query.upper()}\n"
                        analisis += "-" * 40 + "\n"
                        for res in resultados:
                            score = res.get("score", 0)
                            texto = res.get("texto", "")[:300]
                            analisis += f"[Relevancia: {score:.2f}]\n{texto}\n\n"
                
                if len(analisis) < 200:
                    analisis += "No se encontraron clausulas especificas en el contrato.\n"
                    analisis += "El contrato puede ser muy corto o no contener clausulas tipicas."
                
                self.root.after(0, lambda: self._show_analysis(analisis))
                
            except Exception as e:
                logger.error(f"Error en analisis: {e}")
                self.root.after(0, lambda: self._show_analysis(f"Error al generar analisis: {e}"))
        
        threading.Thread(target=task, daemon=True).start()
    
    def _show_analysis(self, analisis: str):
        """Muestra el analisis en la UI."""
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", analisis)
        self.analysis_text.configure(state="disabled")
        
        self.btn_analyze_full.configure(state="normal", text="📊 Generar Analisis Completo")
    
    def _on_export(self):
        """Exporta el texto del contrato."""
        if not self.current_contract_data:
            messagebox.showwarning("Sin documento", "Carga un contrato primero")
            return
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("CONTRACT ANALYZER PRO - TEXTO DEL CONTRATO\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"Archivo: {self.current_contract_data['nombre_archivo']}\n")
                    f.write(f"Paginas: {self.current_contract_data['total_paginas']}\n")
                    f.write(f"Caracteres: {self.current_contract_data['total_caracteres']}\n")
                    f.write(f"Chunks: {self.current_contract_data['total_chunks']}\n\n")
                    f.write("=" * 60 + "\n")
                    f.write("TEXTO COMPLETO\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(self.current_contract_data['texto_completo'])
                
                messagebox.showinfo("Exito", f"Texto exportado a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _on_clear(self):
        """Limpia el contrato actual."""
        if self.is_processing:
            messagebox.showwarning("En proceso", "Espera a que termine el procesamiento")
            return
        
        self.current_contract_data = None
        self.current_pdf_path = None
        
        # Limpiar RAG
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
        
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "El analisis legal aparecera aqui...")
        self.analysis_text.configure(state="disabled")
        
        self.stats_label.configure(text="")
        self.status_label.configure(text="✅ Sistema listo")
        
        self.btn_ask.configure(state="disabled")
        self.btn_analyze_full.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        
        self.file_upload._reset_state()
        
        messagebox.showinfo("Limpieza", "Contrato eliminado correctamente")
    
    def _on_closing(self):
        """Maneja el cierre de la ventana."""
        if self.is_processing or self.is_answering:
            respuesta = messagebox.askyesno("Salir", "Hay un proceso en curso. ¿Seguro que quieres salir?")
            if respuesta:
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Ejecuta la ventana."""
        self.root.mainloop()