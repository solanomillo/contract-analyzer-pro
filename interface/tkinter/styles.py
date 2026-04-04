"""
Estilos y temas para la interfaz CustomTkinter.
"""

import customtkinter as ctk


def configurar_tema():
    """Configura el tema global."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    return {
        "primary": "#2ecc71",
        "primary_hover": "#27ae60",
        "secondary": "#3498db",
        "secondary_hover": "#2980b9",
        "danger": "#e74c3c",
        "warning": "#f39c12",
        "dark_bg": "#1e1e1e",
        "card_bg": "#2d2d2d",
        "text": "#ffffff",
        "text_secondary": "#b0b0b0"
    }


def crear_titulo(parent, texto, tamanio=24):
    """Crea un titulo estilizado."""
    return ctk.CTkLabel(
        parent,
        text=texto,
        font=ctk.CTkFont(size=tamanio, weight="bold"),
        text_color="#2ecc71"
    )


def crear_card(parent, **kwargs):
    """Crea una tarjeta estilizada."""
    return ctk.CTkFrame(
        parent,
        fg_color="#2d2d2d",
        corner_radius=15,
        border_width=1,
        border_color="#3d3d3d",
        **kwargs
    )