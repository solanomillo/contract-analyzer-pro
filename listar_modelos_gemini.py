"""
Script para listar modelos disponibles de Gemini usando solo la API key.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar API key desde .env
load_dotenv()

print("\n" + "="*60)
print("LISTANDO MODELOS DISPONIBLES EN GEMINI API")
print("="*60)

# Obtener API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("\n[ERROR] GEMINI_API_KEY no encontrada en .env")
    print("Crea un archivo .env con:")
    print("GEMINI_API_KEY=tu_api_key_aqui")
    exit(1)

# Configurar Gemini
genai.configure(api_key=api_key)

# Listar modelos
print(f"\n[INFO] API Key configurada. Obteniendo modelos...\n")

try:
    modelos = genai.list_models()
    
    modelos_chat = []
    modelos_embedding = []
    
    for modelo in modelos:
        nombre = modelo.name
        metodos = modelo.supported_generation_methods
        
        if "generateContent" in metodos:
            modelos_chat.append(nombre)
        
        if "embedContent" in metodos:
            modelos_embedding.append(nombre)
    
    print("="*60)
    print("MODELOS PARA CHAT (LLM)")
    print("="*60)
    
    if modelos_chat:
        for i, m in enumerate(modelos_chat, 1):
            nombre_corto = m.replace("models/", "")
            print(f"   {i}. {nombre_corto}")
    else:
        print("   No se encontraron modelos de chat")
    
    print("\n" + "="*60)
    print("MODELOS PARA EMBEDDINGS")
    print("="*60)
    
    if modelos_embedding:
        for i, m in enumerate(modelos_embedding, 1):
            nombre_corto = m.replace("models/", "")
            print(f"   {i}. {nombre_corto}")
    else:
        print("   No se encontraron modelos de embedding")
    
    print("\n" + "="*60)
    print("RECOMENDACIONES PARA CONTRACT ANALYZER PRO")
    print("="*60)
    
    # Recomendar segun lo disponible
    if any("gemini-2.0-flash" in str(m) for m in modelos_chat):
        print("\n   ✅ LLM recomendado: gemini-2.0-flash-exp")
        print("      (Gratuito, rapido, 1M contexto)")
    elif any("gemini-1.5-flash" in str(m) for m in modelos_chat):
        print("\n   ✅ LLM recomendado: gemini-1.5-flash")
        print("      (Gratuito, estable)")
    
    if any("text-embedding-004" in str(m) for m in modelos_embedding):
        print("\n   ✅ Embedding recomendado: models/text-embedding-004")
        print("      (Mejor calidad para RAG)")
    elif any("embedding-001" in str(m) for m in modelos_embedding):
        print("\n   ✅ Embedding recomendado: models/embedding-001")
        print("      (Alternativo confiable)")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\nPosibles causas:")
    print("   1. API key invalida")
    print("   2. Sin acceso a Gemini API")
    print("   3. Problema de red")

print("\n" + "="*60)