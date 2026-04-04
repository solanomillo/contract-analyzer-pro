"""
Servicio de procesamiento de PDF para extraccion de contratos.

Este servicio maneja la extraccion de texto de PDF, limpieza y segmentacion.
Utiliza pdfplumber como extractor principal y pypdf como respaldo.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading

import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFService:
    """
    Servicio para procesar contratos en PDF o archivos de texto.
    
    Maneja la extraccion de texto, limpieza y segmentacion inteligente
    para el posterior procesamiento RAG.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Inicializa el servicio de PDF.
        
        Args:
            chunk_size: Tamaño maximo de cada chunk en caracteres
            chunk_overlap: Superposicion entre chunks para mantener contexto
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._processing_lock = threading.Lock()
        logger.info(f"PDFService inicializado: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrae texto del archivo (PDF o TXT).
        
        Args:
            file_path: Ruta al archivo (PDF o TXT)
            
        Returns:
            Diccionario con el texto extraido y metadatos
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo esta vacio o no se puede extraer texto
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        logger.info(f"Extrayendo texto del archivo: {file_path}")
        
        # Si es archivo de texto, procesar directamente
        if file_path.suffix.lower() == '.txt':
            return self._extract_from_text(file_path)
        
        # Si es PDF, usar los metodos de PDF
        if file_path.suffix.lower() == '.pdf':
            return self._extract_from_pdf(file_path)
        
        raise ValueError(f"Formato no soportado: {file_path.suffix}. Use .pdf o .txt")
    
    def _extract_from_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrae texto de un archivo de texto plano.
        
        Args:
            file_path: Ruta al archivo de texto
            
        Returns:
            Diccionario con el texto extraido y metadatos
        """
        resultado = {
            "texto_completo": "",
            "paginas": [],
            "metadatos": {},
            "total_paginas": 1,
            "exito": False
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                texto_raw = f.read()
            
            texto_limpio = self._limpiar_texto(texto_raw)
            resultado["texto_completo"] = texto_limpio
            resultado["paginas"].append({
                "pagina": 1,
                "texto": texto_limpio
            })
            resultado["metadatos"] = {
                "titulo": file_path.stem,
                "autor": "",
                "tipo": "texto_plano"
            }
            resultado["exito"] = bool(resultado["texto_completo"].strip())
            
            logger.info(f"Texto extraido de archivo TXT: {len(resultado['texto_completo'])} caracteres")
            
        except Exception as e:
            logger.error(f"Error al leer archivo de texto: {e}")
            raise ValueError(f"No se pudo leer el archivo de texto: {e}")
        
        return resultado
    
    def _extract_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extrae texto de un archivo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con el texto extraido y metadatos
        """
        resultado = {
            "texto_completo": "",
            "paginas": [],
            "metadatos": {},
            "total_paginas": 0,
            "exito": False
        }
        
        # Intentar primero con pdfplumber (mejor para texto formateado)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                resultado["total_paginas"] = len(pdf.pages)
                resultado["metadatos"] = {
                    "titulo": pdf.metadata.get("Title", "") if pdf.metadata else "",
                    "autor": pdf.metadata.get("Author", "") if pdf.metadata else "",
                    "fecha_creacion": pdf.metadata.get("CreationDate", "") if pdf.metadata else ""
                }
                
                for num_pagina, pagina in enumerate(pdf.pages, 1):
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_limpio = self._limpiar_texto(texto_pagina)
                        resultado["paginas"].append({
                            "pagina": num_pagina,
                            "texto": texto_limpio
                        })
                        resultado["texto_completo"] += texto_limpio + "\n\n"
                
                resultado["exito"] = bool(resultado["texto_completo"].strip())
                
                if not resultado["exito"]:
                    logger.warning("pdfplumber no extrajo texto, el PDF podria estar vacio o ser una imagen")
                    
        except Exception as e:
            logger.warning(f"pdfplumber fallo: {e}, intentando con pypdf")
            resultado = self._extract_with_pypdf(pdf_path)
        
        if not resultado["exito"]:
            # Si no se pudo extraer texto, verificar si es un PDF vacio
            if resultado["total_paginas"] > 0:
                logger.warning(f"El PDF tiene {resultado['total_paginas']} paginas pero no contiene texto extraible")
                resultado["texto_completo"] = "[PDF SIN TEXTO EXTRAIBLE - POSIBLEMENTE ESCANEADO]"
            else:
                raise ValueError(f"No se pudo extraer texto del PDF: {pdf_path}")
        
        logger.info(f"Texto extraido del PDF: {len(resultado['texto_completo'])} caracteres de {resultado['total_paginas']} paginas")
        return resultado
    
    def _extract_with_pypdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extraccion de respaldo usando pypdf.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con texto extraido y metadatos
        """
        resultado = {
            "texto_completo": "",
            "paginas": [],
            "metadatos": {},
            "total_paginas": 0,
            "exito": False
        }
        
        try:
            lector = PdfReader(pdf_path)
            resultado["total_paginas"] = len(lector.pages)
            
            for num_pagina, pagina in enumerate(lector.pages, 1):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_limpio = self._limpiar_texto(texto_pagina)
                    resultado["paginas"].append({
                        "pagina": num_pagina,
                        "texto": texto_limpio
                    })
                    resultado["texto_completo"] += texto_limpio + "\n\n"
            
            resultado["metadatos"] = {
                "titulo": lector.metadata.get("/Title", "") if lector.metadata else "",
                "autor": lector.metadata.get("/Author", "") if lector.metadata else "",
                "creador": lector.metadata.get("/Creator", "") if lector.metadata else ""
            }
            resultado["exito"] = bool(resultado["texto_completo"].strip())
            
        except Exception as e:
            logger.error(f"Extraccion con pypdf fallo: {e}")
            raise ValueError(f"Ambos metodos de extraccion fallaron: {e}")
        
        return resultado
    
    def _limpiar_texto(self, texto: str) -> str:
        """
        Limpia el texto extraido normalizando espacios y eliminando artefactos.
        
        Args:
            texto: Texto crudo extraido
            
        Returns:
            Texto limpio
        """
        if not texto:
            return ""
        
        # Reemplazar multiples saltos de linea con doble salto
        texto = re.sub(r'\n\s*\n', '\n\n', texto)
        
        # Reemplazar multiples espacios con un solo espacio
        texto = re.sub(r' +', ' ', texto)
        
        # Eliminar caracteres raros pero mantener acentos del español
        texto = re.sub(r'[^\w\s\u00C0-\u00FF.,;:()\-¿?¡!%$€£]', '', texto)
        
        # Normalizar saltos de linea
        texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
        
        # Eliminar espacios al inicio y final
        texto = texto.strip()
        
        return texto
    
    def segmentar_texto(self, texto: str) -> List[Dict[str, Any]]:
        """
        Divide el texto en chunks inteligentes para procesamiento RAG.
        
        Divide por parrafos primero, luego combina hasta alcanzar el tamaño del chunk.
        
        Args:
            texto: Texto completo a segmentar
            
        Returns:
            Lista de chunks con metadatos
        """
        logger.info("Segmentando texto para procesamiento RAG")
        
        if not texto or len(texto.strip()) == 0:
            logger.warning("Texto vacio para segmentar")
            return []
        
        # Dividir por parrafos
        parrafos = [p.strip() for p in texto.split('\n\n') if p.strip()]
        
        if not parrafos:
            # Si no hay parrafos, dividir por oraciones
            parrafos = [p.strip() for p in texto.split('. ') if p.strip()]
            parrafos = [p + '.' for p in parrafos[:-1]] + [parrafos[-1]] if parrafos else []
        
        chunks = []
        chunk_actual = []
        tamanio_actual = 0
        
        for parrafo in parrafos:
            tamanio_parrafo = len(parrafo)
            
            if tamanio_actual + tamanio_parrafo > self.chunk_size and chunk_actual:
                # Guardar chunk actual
                texto_chunk = '\n\n'.join(chunk_actual)
                chunks.append({
                    "texto": texto_chunk,
                    "tamanio": len(texto_chunk),
                    "parrafos": len(chunk_actual),
                    "indice": len(chunks)
                })
                
                # Iniciar nuevo chunk con superposicion
                texto_superposicion = chunk_actual[-1] if self.chunk_overlap > 0 else ""
                chunk_actual = [texto_superposicion] if texto_superposicion else []
                tamanio_actual = len(texto_superposicion)
            
            chunk_actual.append(parrafo)
            tamanio_actual += tamanio_parrafo
        
        # Agregar ultimo chunk
        if chunk_actual:
            texto_chunk = '\n\n'.join(chunk_actual)
            chunks.append({
                "texto": texto_chunk,
                "tamanio": len(texto_chunk),
                "parrafos": len(chunk_actual),
                "indice": len(chunks)
            })
        
        logger.info(f"Creados {len(chunks)} chunks desde {len(parrafos)} parrafos")
        return chunks
    
    def procesar_archivo(self, file_path: Path) -> Dict[str, Any]:
        """
        Pipeline completo de procesamiento de archivo (PDF o TXT).
        
        Args:
            file_path: Ruta al archivo (PDF o TXT)
            
        Returns:
            Resultado completo del procesamiento con texto y chunks
        """
        logger.info(f"Procesando archivo: {file_path.name}")
        
        # Extraer texto
        extraccion = self.extract_text(file_path)
        
        # Crear chunks
        chunks = self.segmentar_texto(extraccion["texto_completo"])
        
        resultado = {
            "nombre_archivo": file_path.name,
            "texto_completo": extraccion["texto_completo"],
            "chunks": chunks,
            "metadatos": extraccion["metadatos"],
            "total_paginas": extraccion["total_paginas"],
            "total_chunks": len(chunks),
            "total_caracteres": len(extraccion["texto_completo"])
        }
        
        logger.info(f"Procesamiento completado: {resultado['total_caracteres']} caracteres, {resultado['total_chunks']} chunks")
        return resultado
    
    def procesar_async(self, file_path: Path, callback: Optional[callable] = None):
        """
        Procesa archivo de forma asincrona usando threading.
        
        Args:
            file_path: Ruta al archivo (PDF o TXT)
            callback: Funcion a llamar con el resultado cuando termine
        """
        def _procesar():
            try:
                resultado = self.procesar_archivo(file_path)
                if callback:
                    callback(resultado, None)
            except Exception as e:
                logger.error(f"Procesamiento asincrono fallo: {e}")
                if callback:
                    callback(None, str(e))
        
        hilo = threading.Thread(target=_procesar, daemon=True)
        hilo.start()
        return hilo