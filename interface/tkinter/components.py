"""
Componentes reutilizables para la interfaz.
"""

import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import Callable, Optional


class FileUploadFrame(ctk.CTkFrame):
    """
    Frame para seleccion de archivos PDF.
    
    Maneja:
    - Seleccion de archivos via dialogo
    - Estados: normal, loading, success
    - Reseteo automatico despues de exito
    """
    
    def __init__(self, parent, on_file_selected: Callable, **kwargs):
        """
        Inicializa el frame de carga.
        
        Args:
            parent: Widget padre
            on_file_selected: Callback cuando se selecciona un archivo
            **kwargs: Argumentos adicionales para CTkFrame
        """
        super().__init__(parent, **kwargs)
        self.on_file_selected = on_file_selected
        self._is_loading = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del componente."""
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
            text="Formatos soportados: PDF (max 50MB)",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.sub_label.pack(pady=(0, 20))
        
        # Boton de seleccion
        self.btn_select = ctk.CTkButton(
            self,
            text="Seleccionar PDF",
            command=self._seleccionar_archivo,
            width=200,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_select.pack(pady=(0, 20))
    
    def _seleccionar_archivo(self):
        """Abre el dialogo para seleccionar archivo."""
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
        Cambia el estado a cargando.
        
        Args:
            loading: True para modo loading, False para normal
        """
        self._is_loading = loading
        
        if loading:
            self.icon_label.configure(text="⏳")
            self.text_label.configure(text="Procesando PDF...")
            self.sub_label.configure(text="Por favor espera")
            self.btn_select.configure(state="disabled", text="Procesando...")
        else:
            self.icon_label.configure(text="📄")
            self.text_label.configure(text="Selecciona un contrato en PDF")
            self.sub_label.configure(text="Formatos soportados: PDF (max 50MB)")
            self.btn_select.configure(state="normal", text="Seleccionar PDF")
    
    def set_success(self, nombre_archivo: str):
        """
        Muestra estado de exito y programa reseteo.
        
        Args:
            nombre_archivo: Nombre del archivo procesado
        """
        self.icon_label.configure(text="✅")
        self.text_label.configure(text=f"PDF cargado: {nombre_archivo}")
        self.sub_label.configure(text="Procesamiento completado")
        self.btn_select.configure(state="normal", text="Seleccionar PDF")
        
        # Resetear despues de 2 segundos
        self.after(2000, self.reset_state)
    
    def reset_state(self):
        """
        Resetea el componente a su estado original.
        Importante: Este metodo es llamado por set_success y por limpieza.
        """
        if not self._is_loading:  # Solo resetear si no esta cargando
            self.icon_label.configure(text="📄")
            self.text_label.configure(text="Selecciona un contrato en PDF")
            self.sub_label.configure(text="Formatos soportados: PDF (max 50MB)")
            self.btn_select.configure(state="normal", text="Seleccionar PDF")
    
    def is_loading(self) -> bool:
        """Retorna True si esta en estado de carga."""
        return self._is_loading


class ProgressCard(ctk.CTkFrame):
    """
    Tarjeta de progreso para mostrar estado de procesamiento.
    
    Maneja:
    - Barra de progreso
    - Mensajes de estado
    - Detalles adicionales
    - Ocultar/mostrar
    """
    
    def __init__(self, parent, **kwargs):
        """
        Inicializa la tarjeta de progreso.
        
        Args:
            parent: Widget padre
            **kwargs: Argumentos adicionales para CTkFrame
        """
        super().__init__(parent, **kwargs)
        self._is_visible = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de la tarjeta."""
        self.configure(fg_color="#2d2d2d", corner_radius=10)
        
        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(self, width=400, height=10)
        self.progress_bar.pack(pady=(15, 10))
        self.progress_bar.set(0)
        
        # Estado
        self.status_label = ctk.CTkLabel(
            self,
            text="Listo",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.status_label.pack()
        
        # Detalle
        self.detail_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.detail_label.pack(pady=(5, 15))
    
    def update_progress(self, valor: float, mensaje: str, detalle: str = ""):
        """
        Actualiza el progreso.
        
        Args:
            valor: Valor entre 0 y 1
            mensaje: Mensaje de estado
            detalle: Detalle adicional (opcional)
        """
        # Asegurar valor entre 0 y 1
        valor = max(0.0, min(1.0, valor))
        
        self.progress_bar.set(valor)
        self.status_label.configure(text=mensaje)
        self.detail_label.configure(text=detalle)
        self.update_idletasks()
    
    def reset(self):
        """Resetea la tarjeta a estado inicial."""
        self.progress_bar.set(0)
        self.status_label.configure(text="Listo")
        self.detail_label.configure(text="")
    
    def show(self):
        """Muestra la tarjeta."""
        if not self._is_visible:
            self.pack(pady=10, fill="x")
            self._is_visible = True
    
    def hide(self):
        """Oculta la tarjeta."""
        if self._is_visible:
            self.pack_forget()
            self._is_visible = False
            self.reset()
    
    def is_visible(self) -> bool:
        """Retorna True si la tarjeta esta visible."""
        return self._is_visible