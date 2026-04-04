"""
Ventana de configuracion inicial del sistema.
Permite ingresar API key y seleccionar modelos.
"""

import threading
import logging
import os
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

from interface.tkinter.styles import configurar_tema, crear_titulo, crear_card
from infrastructure.llm_clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ConfigWindow:
    """
    Ventana de configuracion de la aplicacion.
    
    Permite al usuario:
    - Ingresar API key de Gemini
    - Ver modelos disponibles
    - Seleccionar modelo de chat y embedding
    - Guardar configuracion y continuar
    """
    
    def __init__(self):
        """Inicializa la ventana de configuracion."""
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Configuracion Inicial")
        self.root.geometry("750x700")
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"750x700+{x}+{y}")
        
        # Configurar tema
        self.colores = configurar_tema()
        
        # Variables
        self.api_key_var = ctk.StringVar()
        self.modelo_chat_var = ctk.StringVar(value="gemini-2.5-flash")
        self.modelo_embedding_var = ctk.StringVar(value="gemini-embedding-2-preview")
        self.client = None
        self.modelos_chat = []
        self.modelos_embedding = []
        self.api_key_validada = False
        
        # Construir UI
        self._build_ui()
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Titulo
        titulo = crear_titulo(main_frame, "CONTRACT ANALYZER PRO", 28)
        titulo.pack(pady=(0, 10))
        
        subtitulo = ctk.CTkLabel(
            main_frame,
            text="Configuracion inicial - Ingresa tu API key de Gemini",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        subtitulo.pack(pady=(0, 30))
        
        # Card de API Key
        card_api = crear_card(main_frame)
        card_api.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            card_api,
            text="🔑 Gemini API Key",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            card_api,
            text="Obtén tu API key gratis en: https://makersuite.google.com/app/apikey",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        self.api_key_entry = ctk.CTkEntry(
            card_api,
            textvariable=self.api_key_var,
            placeholder_text="Ingresa tu API key",
            width=450,
            show="*"
        )
        self.api_key_entry.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Frame para botones de API key
        btn_frame = ctk.CTkFrame(card_api, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_validar = ctk.CTkButton(
            btn_frame,
            text="✓ Validar API Key",
            command=self._validar_api_key,
            width=150,
            fg_color=self.colores["secondary"],
            hover_color=self.colores["secondary_hover"]
        )
        self.btn_validar.pack(side="left", padx=(0, 10))
        
        self.btn_mostrar = ctk.CTkButton(
            btn_frame,
            text="👁️ Mostrar",
            command=self._toggle_mostrar_api_key,
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="#555555"
        )
        self.btn_mostrar.pack(side="left")
        
        # Estado de validacion
        self.lbl_estado = ctk.CTkLabel(
            card_api,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_estado.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Card de Modelos (inicialmente deshabilitada)
        self.card_modelos = crear_card(main_frame)
        self.card_modelos.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            self.card_modelos,
            text="🤖 Seleccion de Modelos",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Modelo de Chat
        ctk.CTkLabel(
            self.card_modelos,
            text="Modelo de Chat (LLM):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.combo_chat = ctk.CTkComboBox(
            self.card_modelos,
            values=["Primero valida tu API key"],
            variable=self.modelo_chat_var,
            width=450,
            state="disabled"
        )
        self.combo_chat.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Modelo de Embedding
        ctk.CTkLabel(
            self.card_modelos,
            text="Modelo de Embedding (Vectores):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.combo_embedding = ctk.CTkComboBox(
            self.card_modelos,
            values=["Primero valida tu API key"],
            variable=self.modelo_embedding_var,
            width=450,
            state="disabled"
        )
        self.combo_embedding.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Boton para refrescar modelos
        self.btn_refrescar = ctk.CTkButton(
            self.card_modelos,
            text="🔄 Refrescar Modelos",
            command=self._refrescar_modelos,
            width=150,
            fg_color=self.colores["secondary"],
            hover_color=self.colores["secondary_hover"],
            state="disabled"
        )
        self.btn_refrescar.pack(anchor="w", padx=20, pady=(10, 20))
        
        # Card de Resumen
        self.card_resumen = crear_card(main_frame)
        
        ctk.CTkLabel(
            self.card_resumen,
            text="📋 Resumen de Configuracion",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.lbl_resumen = ctk.CTkLabel(
            self.card_resumen,
            text="Esperando validacion de API key...",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
            justify="left"
        )
        self.lbl_resumen.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Botones finales
        btn_final_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_final_frame.pack(fill="x", pady=(10, 0))
        
        self.btn_guardar = ctk.CTkButton(
            btn_final_frame,
            text="💾 Guardar y Continuar",
            command=self._guardar_y_continuar,
            width=200,
            height=45,
            fg_color=self.colores["primary"],
            hover_color=self.colores["primary_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.btn_guardar.pack(side="right")
        
        self.btn_salir = ctk.CTkButton(
            btn_final_frame,
            text="Salir",
            command=self.root.quit,
            width=100,
            height=45,
            fg_color="transparent",
            border_width=1,
            border_color="#555555"
        )
        self.btn_salir.pack(side="right", padx=(0, 10))
    
    def _toggle_mostrar_api_key(self):
        """Muestra u oculta la API key."""
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.configure(show="")
            self.btn_mostrar.configure(text="🙈 Ocultar")
        else:
            self.api_key_entry.configure(show="*")
            self.btn_mostrar.configure(text="👁️ Mostrar")
    
    def _validar_api_key(self):
        """Valida la API key en segundo plano."""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Ingresa una API key")
            return
        
        # Deshabilitar boton durante validacion
        self.btn_validar.configure(state="disabled", text="Validando...")
        self.lbl_estado.configure(text="🔄 Validando API key...", text_color="#f39c12")
        
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
        self.btn_validar.configure(state="normal", text="✓ Validar API Key")
        self.lbl_estado.configure(text="✅ API key valida", text_color="#2ecc71")
        
        # Habilitar seleccion de modelos
        self.combo_chat.configure(state="readonly")
        self.combo_embedding.configure(state="readonly")
        self.btn_refrescar.configure(state="normal")
        
        # Habilitar boton guardar
        self.btn_guardar.configure(state="normal")
        
        # Cargar modelos disponibles
        self._cargar_modelos()
    
    def _on_validacion_fallida(self, error):
        """Maneja validacion fallida."""
        self.api_key_validada = False
        self.btn_validar.configure(state="normal", text="✓ Validar API Key")
        self.lbl_estado.configure(text=f"❌ Error: {error}", text_color="#e74c3c")
        
        self.combo_chat.configure(values=["Valida tu API key primero"], state="disabled")
        self.combo_embedding.configure(values=["Valida tu API key primero"], state="disabled")
        self.btn_refrescar.configure(state="disabled")
        self.btn_guardar.configure(state="disabled")
    
    def _refrescar_modelos(self):
        """Refresca la lista de modelos."""
        if not self.client:
            messagebox.showwarning("Advertencia", "Primero valida tu API key")
            return
        
        self.lbl_estado.configure(text="🔄 Refrescando modelos...", text_color="#f39c12")
        self._cargar_modelos()
    
    def _cargar_modelos(self):
        """Carga los modelos disponibles en segundo plano."""
        def cargar():
            try:
                modelos_chat = self.client.listar_modelos_chat()
                modelos_embedding = self.client.listar_modelos_embedding()
                
                self.root.after(0, self._actualizar_modelos, modelos_chat, modelos_embedding)
                
            except Exception as e:
                self.root.after(0, self._on_validacion_fallida, f"Error cargando modelos: {e}")
        
        threading.Thread(target=cargar, daemon=True).start()
    
    def _actualizar_modelos(self, modelos_chat, modelos_embedding):
        """Actualiza los combobox con los modelos disponibles."""
        self.modelos_chat = modelos_chat
        self.modelos_embedding = modelos_embedding
        
        # Actualizar combo chat
        nombres_chat = [m.nombre for m in modelos_chat]
        if nombres_chat:
            self.combo_chat.configure(values=nombres_chat)
            # Seleccionar gemini-2.5-flash por defecto
            if "gemini-2.5-flash" in nombres_chat:
                self.modelo_chat_var.set("gemini-2.5-flash")
            else:
                self.modelo_chat_var.set(nombres_chat[0])
        else:
            self.combo_chat.configure(values=["No se encontraron modelos"])
        
        # Actualizar combo embedding
        nombres_embedding = [m.nombre for m in modelos_embedding]
        if nombres_embedding:
            self.combo_embedding.configure(values=nombres_embedding)
            # Seleccionar gemini-embedding-2-preview por defecto
            if "gemini-embedding-2-preview" in nombres_embedding:
                self.modelo_embedding_var.set("gemini-embedding-2-preview")
            elif "gemini-embedding-001" in nombres_embedding:
                self.modelo_embedding_var.set("gemini-embedding-001")
            else:
                self.modelo_embedding_var.set(nombres_embedding[0])
        else:
            self.combo_embedding.configure(values=["No se encontraron modelos"])
        
        # Actualizar resumen
        self._actualizar_resumen()
        
        self.lbl_estado.configure(text="✅ Modelos cargados correctamente", text_color="#2ecc71")
    
    def _actualizar_resumen(self):
        """Actualiza el resumen de configuracion."""
        api_key = self.api_key_var.get()
        api_key_masked = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else api_key
        
        resumen = f"""
API Key: {api_key_masked}
Estado: ✅ Valida

Modelo Chat: {self.modelo_chat_var.get()}
Modelo Embedding: {self.modelo_embedding_var.get()}
"""
        self.lbl_resumen.configure(text=resumen, text_color="#ffffff")
    
    def _guardar_y_continuar(self):
        """Guarda configuracion y continua a la ventana principal."""
        if not self.api_key_validada:
            messagebox.showwarning("Advertencia", "Primero valida tu API key")
            return
        
        api_key = self.api_key_var.get().strip()
        modelo_chat = self.modelo_chat_var.get()
        modelo_embedding = self.modelo_embedding_var.get()
        
        # Guardar configuracion en .env
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
        """Ejecuta la ventana de configuracion."""
        self.root.mainloop()