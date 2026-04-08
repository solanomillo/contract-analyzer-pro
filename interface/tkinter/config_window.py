"""
Ventana de configuracion inicial del sistema.
"""

import threading
import customtkinter as ctk
from tkinter import messagebox

from interface.tkinter.styles import configurar_tema, crear_titulo, crear_card
from application.services.config_service import ConfigService


class ConfigWindow:
    """Ventana de configuracion de la aplicacion."""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Contract Analyzer Pro - Configuracion Inicial")
        self.root.geometry("750x700")
        self.root.resizable(False, False)

        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"750x700+{x}+{y}")

        self.colores = configurar_tema()
        
        # Servicio de configuracion
        self.config_service = ConfigService()

        # Variables
        self.api_key_var = ctk.StringVar()
        self.modelo_chat_var = ctk.StringVar(value="gemini-2.5-flash")
        self.modelo_embedding_var = ctk.StringVar(value="gemini-embedding-2-preview")

        self.api_key_validada = False
        self.modelos_chat = []
        self.modelos_embedding = []

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz."""
        container = ctk.CTkFrame(self.root)
        container.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(container)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        crear_titulo(scroll, "CONTRACT ANALYZER PRO", 28).pack(pady=(10, 10))

        ctk.CTkLabel(
            scroll,
            text="Configuracion inicial - Ingresa tu API key de Gemini",
            text_color="#888888"
        ).pack(pady=(0, 20))

        # Card API Key
        card_api = crear_card(scroll)
        card_api.pack(fill="x", pady=10)

        ctk.CTkLabel(card_api, text="Gemini API Key",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            card_api,
            text="Obtén tu API key gratis en: https://makersuite.google.com/app/apikey",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self.api_key_entry = ctk.CTkEntry(
            card_api,
            textvariable=self.api_key_var,
            show="*",
            height=40
        )
        self.api_key_entry.pack(fill="x", padx=20, pady=(0, 10))

        btn_frame = ctk.CTkFrame(card_api, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=20, pady=(0, 10))

        self.btn_validar = ctk.CTkButton(
            btn_frame,
            text="Validar API Key",
            command=self._validar_api_key,
            width=150
        )
        self.btn_validar.pack(side="left", padx=(0, 10))

        self.btn_toggle = ctk.CTkButton(
            btn_frame,
            text="Mostrar",
            command=self._toggle_api,
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="#555555"
        )
        self.btn_toggle.pack(side="left")

        self.lbl_estado = ctk.CTkLabel(card_api, text="")
        self.lbl_estado.pack(anchor="w", padx=20, pady=(0, 10))

        # Card Modelos
        card_modelos = crear_card(scroll)
        card_modelos.pack(fill="x", pady=10)

        ctk.CTkLabel(card_modelos, text="Seleccion de Modelos",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            card_modelos,
            text="Modelo de Chat (LLM):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.combo_chat = ctk.CTkComboBox(
            card_modelos,
            values=["Valida tu API key primero"],
            variable=self.modelo_chat_var,
            width=450,
            state="disabled"
        )
        self.combo_chat.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            card_modelos,
            text="Modelo de Embedding (Vectores):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.combo_embedding = ctk.CTkComboBox(
            card_modelos,
            values=["Valida tu API key primero"],
            variable=self.modelo_embedding_var,
            width=450,
            state="disabled"
        )
        self.combo_embedding.pack(fill="x", padx=20, pady=5)

        # Card Resumen
        card_resumen = crear_card(scroll)
        card_resumen.pack(fill="x", pady=10)

        ctk.CTkLabel(card_resumen, text="Resumen de Configuracion",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        self.lbl_resumen = ctk.CTkLabel(
            card_resumen,
            text="Esperando validacion de API key...",
            justify="left"
        )
        self.lbl_resumen.pack(anchor="w", padx=20, pady=(0, 20))

        # Footer
        footer = ctk.CTkFrame(container)
        footer.pack(fill="x", padx=20, pady=10)

        self.btn_guardar = ctk.CTkButton(
            footer,
            text="Guardar y Continuar",
            state="disabled",
            height=45,
            width=200,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._guardar
        )
        self.btn_guardar.pack(side="right")

        self.btn_salir = ctk.CTkButton(
            footer,
            text="Salir",
            command=self.root.quit,
            width=100,
            height=45,
            fg_color="transparent",
            border_width=1,
            border_color="#555555"
        )
        self.btn_salir.pack(side="right", padx=(0, 10))

    def _toggle_api(self):
        """Muestra u oculta la API key."""
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.configure(show="")
            self.btn_toggle.configure(text="Ocultar")
        else:
            self.api_key_entry.configure(show="*")
            self.btn_toggle.configure(text="Mostrar")

    def _validar_api_key(self):
        """Valida la API key en segundo plano."""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Ingresa una API key")
            return

        self.lbl_estado.configure(text="Validando API key...", text_color="#f39c12")
        self.btn_validar.configure(state="disabled")

        def task():
            es_valida, mensaje = self.config_service.validar_api_key(api_key)
            if es_valida:
                self.root.after(0, self._success)
            else:
                self.root.after(0, lambda: self._error(mensaje))

        threading.Thread(target=task, daemon=True).start()

    def _success(self):
        """Maneja validacion exitosa."""
        self.api_key_validada = True
        self.lbl_estado.configure(text="API key valida", text_color="#2ecc71")
        self.btn_validar.configure(state="normal")
        self.btn_guardar.configure(state="normal")
        self.combo_chat.configure(state="readonly")
        self.combo_embedding.configure(state="readonly")
        self._actualizar_resumen()
        self._cargar_modelos()

    def _error(self, msg="API invalida"):
        """Maneja validacion fallida."""
        self.api_key_validada = False
        self.lbl_estado.configure(text=f"Error: {msg}", text_color="#e74c3c")
        self.btn_validar.configure(state="normal")
        self.btn_guardar.configure(state="disabled")
        self.combo_chat.configure(state="disabled")
        self.combo_embedding.configure(state="disabled")

    def _cargar_modelos(self):
        """Carga los modelos disponibles."""
        def task():
            try:
                chat, emb = self.config_service.cargar_modelos_disponibles()
                self.root.after(0, lambda: self._set_modelos(chat, emb))
            except Exception as e:
                error_msg = str(e)
                if "API key" in error_msg or "key" in error_msg.lower():
                    self.root.after(0, lambda: self._error("API key invalida o no configurada"))
                else:
                    self.root.after(0, lambda: self._error(f"Error cargando modelos: {error_msg[:100]}"))

        threading.Thread(target=task, daemon=True).start()

    def _set_modelos(self, chat, emb):
        """Actualiza los combos con los modelos."""
        if chat:
            nombres = [m.nombre for m in chat]
            self.combo_chat.configure(values=nombres)
            self.modelos_chat = chat
            if "gemini-2.5-flash" in nombres:
                self.modelo_chat_var.set("gemini-2.5-flash")
            elif "gemini-2.0-flash" in nombres:
                self.modelo_chat_var.set("gemini-2.0-flash")
            elif nombres:
                self.modelo_chat_var.set(nombres[0])

        if emb:
            nombres = [m.nombre for m in emb]
            self.combo_embedding.configure(values=nombres)
            self.modelos_embedding = emb
            if "gemini-embedding-2-preview" in nombres:
                self.modelo_embedding_var.set("gemini-embedding-2-preview")
            elif "gemini-embedding-001" in nombres:
                self.modelo_embedding_var.set("gemini-embedding-001")
            elif nombres:
                self.modelo_embedding_var.set(nombres[0])

        self._actualizar_resumen()
        self.lbl_estado.configure(text="API key valida - Modelos cargados", text_color="#2ecc71")

    def _actualizar_resumen(self):
        """Actualiza el resumen de configuracion."""
        api = self.api_key_var.get()
        if len(api) > 10:
            api_mask = api[:6] + "..." + api[-4:]
        else:
            api_mask = "*" * len(api) if api else "No ingresada"

        texto = f"""
API Key: {api_mask}
Estado: {'Valida' if self.api_key_validada else 'Pendiente'}

Modelo Chat: {self.modelo_chat_var.get()}
Modelo Embedding: {self.modelo_embedding_var.get()}
"""
        self.lbl_resumen.configure(text=texto)

    def _guardar(self):
        """Guarda la configuracion y abre la ventana principal."""
        if not self.api_key_validada:
            messagebox.showwarning("Advertencia", "Primero valida tu API key")
            return

        api_key = self.api_key_var.get().strip()
        modelo_chat = self.modelo_chat_var.get()
        modelo_embedding = self.modelo_embedding_var.get()

        if self.config_service.guardar_configuracion(api_key, modelo_chat, modelo_embedding):
            messagebox.showinfo("Exito", "Configuracion guardada correctamente")
            self.root.destroy()
            
            from interface.tkinter.main_window import MainWindow
            app = MainWindow()
            app.run()
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuracion")

    def run(self):
        """Ejecuta la ventana."""
        self.root.mainloop()