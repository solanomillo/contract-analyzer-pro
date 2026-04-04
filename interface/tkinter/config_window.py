"""
Ventana de configuracion inicial del sistema.
"""

import threading
import logging
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

from interface.tkinter.styles import configurar_tema, crear_titulo, crear_card
from infrastructure.llm_clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ConfigWindow:

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

        # Variables
        self.api_key_var = ctk.StringVar()
        self.modelo_chat_var = ctk.StringVar(value="gemini-2.5-flash")
        self.modelo_embedding_var = ctk.StringVar(value="gemini-embedding-2-preview")

        self.client = None
        self.api_key_validada = False
        
        # Flag para evitar actualizaciones multiples
        self._is_updating = False

        self._build_ui()

    # =========================
    # UI
    # =========================
    def _build_ui(self):

        # CONTENEDOR PRINCIPAL
        container = ctk.CTkFrame(self.root)
        container.pack(fill="both", expand=True)

        # ================= SCROLL =================
        scroll = ctk.CTkScrollableFrame(container)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        crear_titulo(scroll, "CONTRACT ANALYZER PRO", 28).pack(pady=(10, 10))

        ctk.CTkLabel(
            scroll,
            text="Configuracion inicial - Ingresa tu API key de Gemini",
            text_color="#888888"
        ).pack(pady=(0, 20))

        # ================= API =================
        card_api = crear_card(scroll)
        card_api.pack(fill="x", pady=10)

        ctk.CTkLabel(card_api, text="🔑 Gemini API Key",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        self.api_key_entry = ctk.CTkEntry(
            card_api,
            textvariable=self.api_key_var,
            show="*"
        )
        self.api_key_entry.pack(fill="x", padx=20, pady=(0, 10))

        btn_frame = ctk.CTkFrame(card_api, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=20, pady=(0, 10))

        self.btn_validar = ctk.CTkButton(
            btn_frame,
            text="✓ Validar API Key",
            command=self._validar_api_key
        )
        self.btn_validar.pack(side="left", padx=(0, 10))

        self.btn_toggle = ctk.CTkButton(
            btn_frame,
            text="👁 Mostrar",
            command=self._toggle_api
        )
        self.btn_toggle.pack(side="left")

        self.lbl_estado = ctk.CTkLabel(card_api, text="")
        self.lbl_estado.pack(anchor="w", padx=20, pady=(0, 10))

        # ================= MODELOS =================
        card_modelos = crear_card(scroll)
        card_modelos.pack(fill="x", pady=10)

        ctk.CTkLabel(card_modelos, text="🤖 Modelos",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        self.combo_chat = ctk.CTkComboBox(
            card_modelos,
            values=["Valida primero"],
            variable=self.modelo_chat_var,
            state="disabled"
        )
        self.combo_chat.pack(fill="x", padx=20, pady=5)

        self.combo_embedding = ctk.CTkComboBox(
            card_modelos,
            values=["Valida primero"],
            variable=self.modelo_embedding_var,
            state="disabled"
        )
        self.combo_embedding.pack(fill="x", padx=20, pady=5)

        # ================= RESUMEN =================
        card_resumen = crear_card(scroll)
        card_resumen.pack(fill="x", pady=10)

        ctk.CTkLabel(card_resumen, text="📋 Resumen",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=20, pady=(20, 10))

        self.lbl_resumen = ctk.CTkLabel(
            card_resumen,
            text="Esperando validación...",
            justify="left"
        )
        self.lbl_resumen.pack(anchor="w", padx=20, pady=(0, 20))

        # ================= FOOTER FIJO =================
        footer = ctk.CTkFrame(container)
        footer.pack(fill="x", padx=20, pady=10)

        self.btn_guardar = ctk.CTkButton(
            footer,
            text="💾 Guardar y Continuar",
            state="disabled",
            height=45,
            command=self._guardar
        )
        self.btn_guardar.pack(side="right")

    # =========================
    # FUNCIONES
    # =========================

    def _toggle_api(self):
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.configure(show="")
            self.btn_toggle.configure(text="🙈 Ocultar")
        else:
            self.api_key_entry.configure(show="*")
            self.btn_toggle.configure(text="👁 Mostrar")

    def _safe_update_ui(self, func, *args):
        """Actualiza UI de forma segura desde el hilo principal."""
        if self.root and self.root.winfo_exists():
            self.root.after(0, lambda: func(*args))

    def _validar_api_key(self):

        api_key = self.api_key_var.get().strip()

        if not api_key:
            messagebox.showerror("Error", "Ingresa API key")
            return

        self.lbl_estado.configure(text="Validando...", text_color="#f39c12")
        self.btn_validar.configure(state="disabled")

        def task():
            try:
                client = GeminiClient(api_key)
                ok = client.validar_api_key()

                if ok:
                    self.client = client
                    self._safe_update_ui(self._success)
                else:
                    self._safe_update_ui(self._error, "API key invalida")

            except Exception as e:
                error_msg = str(e)
                if "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                    self._safe_update_ui(self._error, "Cuota de API agotada. Usa otra API key")
                elif "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    self._safe_update_ui(self._error, "API key invalida")
                else:
                    self._safe_update_ui(self._error, f"Error: {error_msg[:100]}")

        threading.Thread(target=task, daemon=True).start()

    def _success(self):
        if not self.root.winfo_exists():
            return
            
        self.api_key_validada = True

        self.lbl_estado.configure(text="✅ API válida", text_color="#2ecc71")
        self.btn_validar.configure(state="normal")

        self.combo_chat.configure(state="readonly")
        self.combo_embedding.configure(state="readonly")
        self.btn_guardar.configure(state="normal")

        self._actualizar_resumen()
        self._cargar_modelos()

    def _error(self, msg="API inválida"):
        if not self.root.winfo_exists():
            return
            
        self.api_key_validada = False
        self.lbl_estado.configure(text=f"❌ {msg}", text_color="#e74c3c")
        self.btn_validar.configure(state="normal")
        self.btn_guardar.configure(state="disabled")

    def _cargar_modelos(self):
        if not self.client:
            return

        def task():
            try:
                chat = self.client.listar_modelos_chat()
                emb = self.client.listar_modelos_embedding()
                self._safe_update_ui(self._set_modelos, chat, emb)
            except Exception as e:
                self._safe_update_ui(self._error, f"Error cargando modelos: {e}")

        threading.Thread(target=task, daemon=True).start()

    def _set_modelos(self, chat, emb):
        if not self.root.winfo_exists():
            return

        if chat:
            nombres = [m.nombre for m in chat]
            self.combo_chat.configure(values=nombres)
            if "gemini-2.5-flash" in nombres:
                self.modelo_chat_var.set("gemini-2.5-flash")
            elif nombres:
                self.modelo_chat_var.set(nombres[0])

        if emb:
            nombres = [m.nombre for m in emb]
            self.combo_embedding.configure(values=nombres)
            if "gemini-embedding-2-preview" in nombres:
                self.modelo_embedding_var.set("gemini-embedding-2-preview")
            elif "gemini-embedding-001" in nombres:
                self.modelo_embedding_var.set("gemini-embedding-001")
            elif nombres:
                self.modelo_embedding_var.set(nombres[0])

        self._actualizar_resumen()

    def _actualizar_resumen(self):
        if not self.root.winfo_exists():
            return
            
        api = self.api_key_var.get()
        if len(api) > 10:
            api_mask = api[:6] + "..." + api[-4:]
        else:
            api_mask = "*" * len(api) if api else "No ingresada"

        texto = f"""
API: {api_mask}
Estado: {'✅ OK' if self.api_key_validada else '⚠️ Pendiente'}

Chat: {self.modelo_chat_var.get()}
Embedding: {self.modelo_embedding_var.get()}
"""
        self.lbl_resumen.configure(text=texto)

    def _guardar(self):
        """Guarda la configuracion REAL en .env y abre la ventana principal"""
        
        if not self.api_key_validada:
            messagebox.showwarning("Advertencia", "Primero valida tu API key")
            return
        
        api_key = self.api_key_var.get().strip()
        modelo_chat = self.modelo_chat_var.get()
        modelo_embedding = self.modelo_embedding_var.get()
        
        try:
            # Guardar configuracion REAL en .env
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
            env_path.write_text(contenido, encoding="utf-8")
            
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
        self.root.mainloop()