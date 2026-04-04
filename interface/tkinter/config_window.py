"""
Ventana de configuracion inicial del sistema.
Permite ingresar API key y seleccionar modelos.
"""

import threading
import logging
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

from infrastructure.llm_clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ConfigWindow:
    """
    Ventana de configuracion de la aplicacion.
    """
    
    def __init__(self):
        """Inicializa la ventana de configuracion."""
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Configuracion Inicial")
        self.root.geometry("600x550")
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (550 // 2)
        self.root.geometry(f"600x550+{x}+{y}")
        
        # Variables
        self.api_key_var = ctk.StringVar()
        self.modelo_chat_var = ctk.StringVar(value="gemini-2.5-flash")
        self.modelo_embedding_var = ctk.StringVar(value="gemini-embedding-2-preview")
        self.client = None
        self.api_key_validada = False
        
        # Construir UI
        self._build_ui()
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Titulo
        titulo = ctk.CTkLabel(
            main_frame,
            text="CONTRACT ANALYZER PRO",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2ecc71"
        )
        titulo.pack(pady=(10, 5))
        
        subtitulo = ctk.CTkLabel(
            main_frame,
            text="Configuracion inicial",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        subtitulo.pack(pady=(0, 20))
        
        # Separador
        separator = ctk.CTkFrame(main_frame, height=1, fg_color="#3d3d3d")
        separator.pack(fill="x", pady=(0, 20))
        
        # Seccion API Key
        ctk.CTkLabel(
            main_frame,
            text="🔑 Gemini API Key",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            main_frame,
            text="Obtén tu API key gratis en: https://makersuite.google.com/app/apikey",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        ).pack(anchor="w", pady=(0, 10))
        
        self.api_key_entry = ctk.CTkEntry(
            main_frame,
            textvariable=self.api_key_var,
            placeholder_text="Ingresa tu API key",
            width=400,
            height=40,
            show="*"
        )
        self.api_key_entry.pack(fill="x", pady=(0, 10))
        
        # Botones de API key
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))
        
        self.btn_validar = ctk.CTkButton(
            btn_frame,
            text="Validar API Key",
            command=self._validar_api_key,
            width=150,
            height=35,
            fg_color="#3498db"
        )
        self.btn_validar.pack(side="left", padx=(0, 10))
        
        self.btn_mostrar = ctk.CTkButton(
            btn_frame,
            text="Mostrar",
            command=self._toggle_mostrar_api_key,
            width=100,
            height=35,
            fg_color="transparent",
            border_width=1,
            border_color="#555555"
        )
        self.btn_mostrar.pack(side="left")
        
        # Estado
        self.lbl_estado = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_estado.pack(anchor="w", pady=(0, 15))
        
        # Separador
        separator2 = ctk.CTkFrame(main_frame, height=1, fg_color="#3d3d3d")
        separator2.pack(fill="x", pady=(0, 15))
        
        # Seccion Modelos
        ctk.CTkLabel(
            main_frame,
            text="🤖 Seleccion de Modelos",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Modelo Chat
        ctk.CTkLabel(
            main_frame,
            text="Modelo de Chat:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", pady=(5, 0))
        
        self.combo_chat = ctk.CTkComboBox(
            main_frame,
            values=["Valida tu API key primero"],
            variable=self.modelo_chat_var,
            width=400,
            state="readonly"
        )
        self.combo_chat.pack(fill="x", pady=(5, 10))
        
        # Modelo Embedding
        ctk.CTkLabel(
            main_frame,
            text="Modelo de Embedding:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", pady=(5, 0))
        
        self.combo_embedding = ctk.CTkComboBox(
            main_frame,
            values=["Valida tu API key primero"],
            variable=self.modelo_embedding_var,
            width=400,
            state="readonly"
        )
        self.combo_embedding.pack(fill="x", pady=(5, 10))
        
        # Separador
        separator3 = ctk.CTkFrame(main_frame, height=1, fg_color="#3d3d3d")
        separator3.pack(fill="x", pady=(15, 15))
        
        # BOTONES FINALES - AQUI ESTA EL BOTON GUARDAR
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 10))
        
        self.btn_guardar = ctk.CTkButton(
            buttons_frame,
            text="💾 GUARDAR Y CONTINUAR",
            command=self._guardar_y_continuar,
            width=200,
            height=45,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.btn_guardar.pack(side="right", padx=(10, 0))
        
        self.btn_salir = ctk.CTkButton(
            buttons_frame,
            text="Salir",
            command=self.root.quit,
            width=100,
            height=45,
            fg_color="transparent",
            border_width=1,
            border_color="#555555"
        )
        self.btn_salir.pack(side="right")
    
    def _toggle_mostrar_api_key(self):
        """Muestra u oculta la API key."""
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.configure(show="")
            self.btn_mostrar.configure(text="Ocultar")
        else:
            self.api_key_entry.configure(show="*")
            self.btn_mostrar.configure(text="Mostrar")
    
    def _validar_api_key(self):
        """Valida la API key."""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Ingresa una API key")
            return
        
        # Deshabilitar boton durante validacion
        self.btn_validar.configure(state="disabled", text="Validando...")
        self.lbl_estado.configure(text="Validando API key...", text_color="#f39c12")
        
        def validar():
            try:
                client = GeminiClient(api_key=api_key)
                
                if client.validar_api_key():
                    self.client = client
                    self.root.after(0, self._on_validacion_exitosa)
                else:
                    self.root.after(0, self._on_validacion_fallida, "API key invalida")
                    
            except Exception as e:
                self.root.after(0, self._on_validacion_fallida, str(e))
        
        threading.Thread(target=validar, daemon=True).start()
    
    def _on_validacion_exitosa(self):
        """Maneja validacion exitosa."""
        self.api_key_validada = True
        self.btn_validar.configure(state="normal", text="Validar API Key")
        self.lbl_estado.configure(text="✅ API key valida", text_color="#2ecc71")
        
        # HABILITAR EL BOTON GUARDAR - ESTA ES LA LINEA CLAVE
        self.btn_guardar.configure(state="normal")
        
        # Cambiar texto del boton para confirmar
        self.btn_guardar.configure(fg_color="#2ecc71")
        
        # Actualizar combos
        self.combo_chat.configure(values=["Cargando modelos..."])
        self.combo_embedding.configure(values=["Cargando modelos..."])
        
        # Cargar modelos
        self._cargar_modelos()
    
    def _on_validacion_fallida(self, error):
        """Maneja validacion fallida."""
        self.api_key_validada = False
        self.btn_validar.configure(state="normal", text="Validar API Key")
        self.lbl_estado.configure(text=f"❌ {error}", text_color="#e74c3c")
        
        # DESHABILITAR EL BOTON GUARDAR
        self.btn_guardar.configure(state="disabled")
        
        # Resetear combos
        self.combo_chat.configure(values=["Valida tu API key primero"])
        self.combo_embedding.configure(values=["Valida tu API key primero"])
    
    def _cargar_modelos(self):
        """Carga los modelos disponibles."""
        def cargar():
            try:
                modelos_chat = self.client.listar_modelos_chat()
                modelos_embedding = self.client.listar_modelos_embedding()
                
                self.root.after(0, self._actualizar_modelos, modelos_chat, modelos_embedding)
                
            except Exception as e:
                self.root.after(0, self._on_error_modelos, str(e))
        
        threading.Thread(target=cargar, daemon=True).start()
    
    def _actualizar_modelos(self, modelos_chat, modelos_embedding):
        """Actualiza los combos con los modelos."""
        # Actualizar combo chat
        if modelos_chat:
            nombres_chat = [m.nombre for m in modelos_chat]
            self.combo_chat.configure(values=nombres_chat)
            if "gemini-2.5-flash" in nombres_chat:
                self.modelo_chat_var.set("gemini-2.5-flash")
            elif nombres_chat:
                self.modelo_chat_var.set(nombres_chat[0])
        
        # Actualizar combo embedding
        if modelos_embedding:
            nombres_embedding = [m.nombre for m in modelos_embedding]
            self.combo_embedding.configure(values=nombres_embedding)
            if "gemini-embedding-2-preview" in nombres_embedding:
                self.modelo_embedding_var.set("gemini-embedding-2-preview")
            elif "gemini-embedding-001" in nombres_embedding:
                self.modelo_embedding_var.set("gemini-embedding-001")
            elif nombres_embedding:
                self.modelo_embedding_var.set(nombres_embedding[0])
        
        self.lbl_estado.configure(text="✅ API key valida - Modelos cargados", text_color="#2ecc71")
    
    def _on_error_modelos(self, error):
        """Maneja error cargando modelos."""
        self.lbl_estado.configure(text=f"⚠️ Error cargando modelos: {error}", text_color="#f39c12")
    
    def _guardar_y_continuar(self):
        """Guarda configuracion y continua."""
        if not self.api_key_validada:
            messagebox.showwarning("Advertencia", "Primero valida tu API key")
            return
        
        api_key = self.api_key_var.get().strip()
        modelo_chat = self.modelo_chat_var.get()
        modelo_embedding = self.modelo_embedding_var.get()
        
        # Guardar en .env
        try:
            env_path = Path(".env")
            contenido = f"""# Google Gemini API Configuration
GEMINI_API_KEY={api_key}
GEMINI_MODEL={modelo_chat}
GEMINI_EMBEDDING_MODEL={modelo_embedding}

# Application Configuration
VECTOR_DB_PATH=./data/vector_store
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
"""
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(contenido.strip())
            
            messagebox.showinfo(
                "Exito", 
                "✅ Configuracion guardada correctamente\n\nLa aplicacion se iniciara con los modelos seleccionados."
            )
            
            # Cerrar ventana de configuracion
            self.root.destroy()
            
            # Iniciar ventana principal
            from interface.tkinter.main_window import MainWindow
            app = MainWindow()
            app.run()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuracion:\n{e}")
    
    def run(self):
        """Ejecuta la ventana."""
        self.root.mainloop()