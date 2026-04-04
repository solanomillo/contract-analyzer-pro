"""
Componentes reutilizables para la interfaz.
"""

import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import Optional, Callable


class FileUploadFrame(ctk.CTkFrame):
    """
    Frame para seleccion y carga de archivos PDF.
    """
    
    def __init__(self, parent, on_file_selected: Callable, **kwargs):
        """
        Inicializa el frame de carga de archivos.
        
        Args:
            parent: Widget padre
            on_file_selected: Callback cuando se selecciona un archivo
            **kwargs: Argumentos de CTkFrame
        """
        super().__init__(parent, **kwargs)
        self.on_file_selected = on_file_selected
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del area de carga."""
        # Icono
        self.icon_label = ctk.CTkLabel(
            self,
            text="📄",
            font=ctk.CTkFont(size=48)
        )
        self.icon_label.pack(pady=(20, 10))
        
        # Texto principal
        self.text_label = ctk.CTkLabel(
            self,
            text="Selecciona un contrato en PDF",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.text_label.pack(pady=(0, 5))
        
        # Texto secundario
        self.sub_label = ctk.CTkLabel(
            self,
            text="Formatos soportados: PDF",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.sub_label.pack(pady=(0, 20))
        
        # Boton selector
        self.btn_select = ctk.CTkButton(
            self,
            text="Seleccionar PDF",
            command=self._seleccionar_archivo,
            width=200,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.btn_select.pack(pady=(0, 20))
    
    def _seleccionar_archivo(self):
        """Abre dialogo para seleccionar archivo."""
        archivo = filedialog.askopenfilename(
            title="Seleccionar contrato PDF",
            filetypes=[
                ("Documentos PDF", "*.pdf"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if archivo:
            self.on_file_selected(Path(archivo))
    
    def set_loading(self, loading: bool):
        """
        Cambia el estado del componente a cargando.
        
        Args:
            loading: True si esta cargando
        """
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
        """
        Muestra estado de exito.
        
        Args:
            nombre_archivo: Nombre del archivo procesado
        """
        self.icon_label.configure(text="✅")
        self.text_label.configure(text=f"PDF cargado: {nombre_archivo}")
        self.sub_label.configure(text="Procesamiento completado")
        
        # Resetear despues de 2 segundos
        self.after(2000, self._reset_state)
    
    def _reset_state(self):
        """Resetea el estado normal."""
        if not hasattr(self, '_processing') or not self._processing:
            self.icon_label.configure(text="📄")
            self.text_label.configure(text="Selecciona un contrato en PDF")
            self.sub_label.configure(text="Formatos soportados: PDF")


class ProgressCard(ctk.CTkFrame):
    """
    Tarjeta de progreso para mostrar estado de procesamiento.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Inicializa la tarjeta de progreso.
        
        Args:
            parent: Widget padre
            **kwargs: Argumentos de CTkFrame
        """
        super().__init__(parent, **kwargs)
        
        self.configure(fg_color="#2d2d2d", corner_radius=10)
        
        self.progress_bar = ctk.CTkProgressBar(self, width=400, height=10)
        self.progress_bar.pack(pady=(15, 10))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            self,
            text="Listo para procesar",
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
        """
        Actualiza el progreso.
        
        Args:
            valor: Valor entre 0 y 1
            mensaje: Mensaje de estado
            detalle: Detalle adicional
        """
        self.progress_bar.set(valor)
        self.status_label.configure(text=mensaje)
        self.detail_label.configure(text=detalle)
        
        # Forzar actualizacion de la UI
        self.update_idletasks()
    
    def reset(self):
        """Resetea el progreso."""
        self.progress_bar.set(0)
        self.status_label.configure(text="Listo para procesar")
        self.detail_label.configure(text="")
    
    def hide(self):
        """Oculta la tarjeta."""
        self.pack_forget()
    
    def show(self):
        """Muestra la tarjeta."""
        self.pack(pady=10, fill="x")