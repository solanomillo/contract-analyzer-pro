"""
Componentes reutilizables para la interfaz.
"""

import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import Callable


class FileUploadFrame(ctk.CTkFrame):
    """Frame para seleccion de archivos PDF."""
    
    def __init__(self, parent, on_file_selected: Callable, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_file_selected = on_file_selected
        self._setup_ui()
    
    def _setup_ui(self):
        self.icon_label = ctk.CTkLabel(self, text="📄", font=ctk.CTkFont(size=48))
        self.icon_label.pack(pady=(20, 10))
        
        self.text_label = ctk.CTkLabel(
            self,
            text="Selecciona un contrato en PDF",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.text_label.pack(pady=(0, 5))
        
        self.sub_label = ctk.CTkLabel(
            self,
            text="Formatos soportados: PDF",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.sub_label.pack(pady=(0, 20))
        
        self.btn_select = ctk.CTkButton(
            self,
            text="Seleccionar PDF",
            command=self._seleccionar_archivo,
            width=200,
            height=40
        )
        self.btn_select.pack(pady=(0, 20))
    
    def _seleccionar_archivo(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar contrato PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if archivo:
            self.on_file_selected(Path(archivo))
    
    def set_loading(self, loading: bool):
        if loading:
            self.icon_label.configure(text="⏳")
            self.text_label.configure(text="Procesando PDF...")
            self.sub_label.configure(text="Por favor espera")
            self.btn_select.configure(state="disabled")
        else:
            self.icon_label.configure(text="📄")
            self.text_label.configure(text="Selecciona un contrato en PDF")
            self.sub_label.configure(text="Formatos soportados: PDF")
            self.btn_select.configure(state="normal")
    
    def set_success(self, nombre_archivo: str):
        self.icon_label.configure(text="✅")
        self.text_label.configure(text=f"PDF cargado: {nombre_archivo}")
        self.sub_label.configure(text="Procesamiento completado")
        self.after(2000, self._reset_state)
    
    def _reset_state(self):
        self.icon_label.configure(text="📄")
        self.text_label.configure(text="Selecciona un contrato en PDF")
        self.sub_label.configure(text="Formatos soportados: PDF")


class ProgressCard(ctk.CTkFrame):
    """Tarjeta de progreso."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="#2d2d2d", corner_radius=10)
        
        self.progress_bar = ctk.CTkProgressBar(self, width=400, height=10)
        self.progress_bar.pack(pady=(15, 10))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            self,
            text="Listo",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.status_label.pack()
        
        self.detail_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.detail_label.pack(pady=(5, 15))
        
        self.pack(pady=10, fill="x")
    
    def update_progress(self, valor: float, mensaje: str, detalle: str = ""):
        self.progress_bar.set(valor)
        self.status_label.configure(text=mensaje)
        self.detail_label.configure(text=detalle)
        self.update_idletasks()
    
    def reset(self):
        self.progress_bar.set(0)
        self.status_label.configure(text="Listo")
        self.detail_label.configure(text="")
    
    def hide(self):
        self.pack_forget()
    
    def show(self):
        self.pack(pady=10, fill="x")