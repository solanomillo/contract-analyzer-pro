# 📄 Contract Analyzer Pro

<div align="center">

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/customtkinter-5.2.0-red.svg)
![Gemini](https://img.shields.io/badge/gemini-2.0--flash-orange.svg)
![FAISS](https://img.shields.io/badge/FAISS-1.7.4-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Sistema de Análisis Legal Inteligente con IA** - Analiza contratos, identifica riesgos y responde preguntas en lenguaje natural

[Características](#características) •
[Instalación](#instalación) •
[Uso](#uso) •
[Arquitectura](#arquitectura) •
[Roadmap](#roadmap) •
[Ejecutable](#crear-ejecutable)

</div>

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Optimizaciones](#optimizaciones)
- [Roadmap](#roadmap)
- [Crear Ejecutable](#crear-ejecutable)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)

## 🎯 Descripción

**Contract Analyzer Pro** es una aplicación de escritorio que permite analizar contratos legales de manera inteligente utilizando técnicas de RAG (Retrieval Augmented Generation) y memoria conversacional. El sistema indexa contratos en PDF, genera embeddings con Gemini, y permite mantener conversaciones contextuales sobre el contenido del documento.

### ¿Qué hace?

- 📄 Carga contratos desde archivos PDF
- 🔍 Extrae y procesa texto legal de manera inteligente
- 🧠 Genera embeddings con Gemini para búsqueda semántica
- 💾 Almacena vectores en FAISS para recuperación eficiente
- 💬 Chat conversacional con memoria de contexto
- ⚠️ Identifica riesgos y cláusulas peligrosas
- 📊 Genera análisis legales completos y estructurados
- 📑 Exporta análisis a PDF profesional

## ✨ Características

### 📄 Procesamiento de Contratos

- Soporte para PDF y TXT
- Extracción de texto con pdfplumber y PyPDF2 (fallback)
- Segmentación inteligente por párrafos y oraciones
- Filtros de limpieza para texto legal

### 💬 Chat Conversacional con IA

| Característica | Descripción |
|----------------|-------------|
| Memoria corto plazo | Últimos 20 mensajes o 8000 tokens |
| Memoria mediano plazo | Resúmenes automáticos cada 10 mensajes |
| Preguntas de seguimiento | "¿Qué dijiste sobre la cláusula X?" |
| Referencias cruzadas | Detección automática de menciones |
| Persistencia | Guardado automático de conversaciones |

### 🔍 Sistema RAG (Gemini + FAISS)

- Embeddings con Gemini (3072 dimensiones)
- Búsqueda semántica con FAISS
- Caché LRU con TTL configurable
- Chunking inteligente por cláusulas

### ⚖️ Análisis Legal

| Tipo | Descripción |
|------|-------------|
| Riesgos | Penalizaciones, rescisión, cláusulas abusivas |
| Fechas | Inicio, término, plazos de pago, preaviso |
| Obligaciones | Pagos, servicios, mantenimiento |

### ⚡ Optimizaciones

- Caché de respuestas (TTL: 1 hora para chat, 24h para embeddings)
- Ventana deslizante de contexto conversacional
- Backoff exponencial con jitter para rate limiting
- Actualización dinámica de modelos (sin reiniciar)

## 🛠️ Tecnologías

| Categoría | Tecnologías |
|-----------|-------------|
| Frontend | CustomTkinter |
| LLM | Google Gemini (2.0 Flash / 2.0 Pro / 2.5 Flash) |
| Embeddings | Gemini Embedding 2 Preview (3072 dim) |
| Vector DB | FAISS |
| Caché | Sistema propio con TTL y LRU |
| PDF | pdfplumber, PyPDF2 |
| Tokens | tiktoken |
| Lenguaje | Python 3.12+ |

## 📦 Instalación

### Requisitos Previos

- Python 3.12 o superior
- API Key de Google Gemini (gratuita en [Google AI Studio](https://aistudio.google.com/))

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/solanomillo/contract-analyzer-pro.git
cd contract-analyzer-pro

# 2. Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate
# Activar en Linux/Mac
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu API key de Gemini

# 5. Crear directorios necesarios
mkdir -p data/cache data/conversations data/vector_store

# 6. Ejecutar la aplicación
python main.py

```

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# Google Gemini API
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2-preview

# Application Configuration
VECTOR_DB_PATH=./data/vector_store
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

```

### Obtener API Key de Gemini

1. Ve a [Google AI Studio](https://aistudio.google.com/)
2. Inicia sesión con tu cuenta Google
3. Haz clic en **"Create API Key"**
4. Copia la clave y pégala en `.env` o ingrésala por la interfaz gráfica

## 🚀 Uso

### 1. Iniciar la Aplicación

```bash
python main.py
```

### 2. Configurar API Key

- Al iniciar, ingresa tu API key de Gemini
- O haz clic en **"Cambiar API Key"** en cualquier momento

### 3. Cargar un Contrato

- Arrastra o selecciona un archivo PDF
- Espera a que el sistema procese e indexe el documento

### 4. Usar el Chat Conversacional

Ve a la pestaña **"Chat con IA"** y haz preguntas como:

| Tipo | Ejemplo |
|------|---------|
| General | "¿De qué trata este contrato?" |
| Obligaciones | "¿Cuáles son las obligaciones del arrendatario?" |
| Fechas | "¿Cuándo termina el contrato?" |
| Riesgos | "¿Hay cláusulas de penalización?" |
| Seguimiento | "¿Qué dijiste sobre los plazos de pago?" |

### 5. Generar Análisis Legal

Ve a la pestaña **"Análisis Legal"** y haz clic en **"Generar Análisis Completo"**

### 6. Exportar Resultados

- Los análisis se pueden exportar a PDF
- Las conversaciones se guardan automáticamente

## 🏗️ Arquitectura

```text
┌─────────────────────────────────────────────────────────────────┐
│                     INTERFAZ (CustomTkinter)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │   Cargar    │ │    Chat     │ │  Análisis   │                │
│  │  Contrato   │ │   con IA    │ │   Legal     │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   APLICACIÓN (Servicios + RAG)                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              ConversationMemory (Chat)                  │    │
│  │  Corto plazo → Resúmenes → Referencias                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │ 
│  │                     RAG Service                         │    │
│  │  Embeddings → FAISS → Recuperación → Gemini             │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Token Optimizer                       │    │
│  │  Conteo → Chunking → Ventana deslizante                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRAESTRUCTURA                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Gemini   │ │  FAISS   │ │  Caché   │ │  PDF     │            │
│  │ LLM/Embed│ │  Vector  │ │  LRU/TTL │ │  Parser  │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## ⚡ Optimizaciones

| Optimización | Descripción | Beneficio |
|--------------|-------------|-----------|
| Caché de respuestas | TTL configurable por tipo de operación | -70% llamadas a API |
| Token counting | Con tiktoken, truncamiento inteligente | Evita errores de contexto |
| Ventana deslizante | Límite de tokens por conversación | Control de costos |
| Chunking inteligente | Por cláusulas, no por caracteres | Mejor precisión |
| Backoff exponencial | Con jitter para rate limiting | Manejo robusto de errores |
| Memoria conversacional | Corto/mediano plazo | Preguntas de seguimiento |
| Actualización dinámica | Modelos sin reiniciar | Flexibilidad |

## 🗺️ Roadmap

### Versión 1.0 (Actual) ✅

- ✅ Carga de contratos PDF
- ✅ Procesamiento y chunking inteligente
- ✅ RAG con Gemini + FAISS
- ✅ Chat conversacional con memoria
- ✅ Análisis legal completo
- ✅ Exportación a PDF
- ✅ Caché y optimización de tokens

### Versión 2.0 (Futuro cercano)

- ⬜ **Múltiples contratos** - Comparar varios contratos simultáneamente
- ⬜ **Exportar conversaciones** - Guardar chat a PDF o TXT
- ⬜ **Sistema de prompts personalizables** - Usuario ajusta el asistente
- ⬜ **Resaltado en contrato** - Mostrar secciones relevantes al preguntar
- ⬜ **Sugerencias automáticas** - Preguntas recomendadas basadas en el contrato

### Versión 3.0 (Futuro lejano)

- ⬜ **Modo oscuro/claro** - Toggle entre temas visuales
- ⬜ **Historial de sesiones** - Ver y cargar conversaciones anteriores
- ⬜ **Notificaciones** - Alertas cuando se completa un análisis
- ⬜ **Plugin para Word/Google Docs** - Integración con editores
- ⬜ **API REST** - Acceso remoto al servicio

## 🏗️ Crear Ejecutable (.exe)

### PyInstaller (Recomendada)

```bash
pyinstaller --onefile --windowed --name="ContractAnalyzerPro" --icon="icon.ico" --add-data "interface;interface" --add-data "application;application" --add-data "infrastructure;infrastructure" --hidden-import="customtkinter" --hidden-import="PIL" --hidden-import="pdfplumber" --hidden-import="pypdf" --hidden-import="langchain" --hidden-import="langgraph" --hidden-import="faiss" --hidden-import="sentence_transformers" --hidden-import="numpy" --hidden-import="google.generativeai" --hidden-import="google.genai" --hidden-import="dotenv" --hidden-import="reportlab" main.py
```

## 📝 Notas importantes para el .exe

- **Primera ejecución**: Puede tardar 30-60 segundos en iniciar
- **Antivirus**: Algunos antivirus pueden marcar falsos positivos
- **Permisos**: Ejecutar como administrador si hay problemas de escritura
- **Datos**: La carpeta `data/` debe tener permisos de escritura

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Convenciones de código

- PEP8 para Python
- Type hints en todas las funciones
- Docstrings en español
- Importaciones ordenadas: estándar → terceros → locales

## 👨‍💻 Autor

**Julio Solano**

- 🔗 GitHub: [https://github.com/solanomillo](https://github.com/solanomillo)
- 🔗 LinkedIn: [https://www.linkedin.com/in/julio-cesar-solano](https://www.linkedin.com/in/julio-cesar-solano)
- 📧 Email: solanomillo144@gmail.com

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- Google Gemini por la API de LLM y embeddings
- FAISS por la búsqueda vectorial eficiente
- CustomTkinter por la interfaz moderna
- pdfplumber por la extracción de texto de PDFs
- tiktoken por el conteo preciso de tokens

<div align="center">

*Hecho con ❤️ para análisis legal inteligente*

</div>