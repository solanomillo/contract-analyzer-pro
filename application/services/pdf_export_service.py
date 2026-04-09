"""
Servicio para exportar analisis legales a PDF con formato estructurado.
"""

import logging
import re
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

logger = logging.getLogger(__name__)


class PDFExportService:
    """
    Servicio para exportar analisis de contratos a PDF con formato profesional.
    """
    
    def __init__(self):
        """Inicializa el servicio de exportacion PDF."""
        self.styles = self._crear_estilos()
    
    def _crear_estilos(self):
        """Crea los estilos para el documento PDF."""
        styles = getSampleStyleSheet()
        
        # Estilo para titulo principal
        styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#2ecc71'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtitulos de seccion
        styles.add(ParagraphStyle(
            name='Seccion',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.HexColor('#3498db'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subsecciones
        styles.add(ParagraphStyle(
            name='SubSeccion',
            parent=styles['Heading3'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=8,
            spaceBefore=10,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para texto normal
        styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        # Estilo para items de lista
        styles.add(ParagraphStyle(
            name='ListItem',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=4,
            leftIndent=20,
            fontName='Helvetica'
        ))
        
        # Estilo para texto de recomendacion
        styles.add(ParagraphStyle(
            name='Recomendacion',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leftIndent=30,
            textColor=colors.HexColor('#27ae60'),
            fontName='Helvetica-Oblique'
        ))
        
        # Estilo para texto citado
        styles.add(ParagraphStyle(
            name='TextoCitado',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
            leftIndent=40,
            textColor=colors.HexColor('#7f8c8d'),
            fontName='Helvetica-Oblique'
        ))
        
        # Estilo para metadatos
        styles.add(ParagraphStyle(
            name='Metadata',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            spaceAfter=4,
            textColor=colors.HexColor('#95a5a6'),
            fontName='Helvetica'
        ))
        
        return styles
    
    def exportar_analisis(self, resumen: str, contrato_nombre: str, 
                          archivo_salida: Path = None) -> Path:
        """
        Exporta el analisis legal a un archivo PDF con formato estructurado.
        
        Args:
            resumen: Texto del resumen del analisis
            contrato_nombre: Nombre del contrato analizado
            archivo_salida: Ruta donde guardar el PDF (opcional)
            
        Returns:
            Path del archivo PDF generado
        """
        if archivo_salida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_salida = Path(f"analisis_contrato_{timestamp}.pdf")
        
        logger.info(f"Generando PDF: {archivo_salida}")
        
        # Crear documento
        doc = SimpleDocTemplate(
            str(archivo_salida),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=f"Analisis Legal - {contrato_nombre}",
            author="Contract Analyzer Pro"
        )
        
        # Contenido del PDF
        story = []
        
        # === TITULO ===
        story.append(Paragraph("CONTRACT ANALYZER PRO", self.styles['TituloPrincipal']))
        story.append(Paragraph("Analisis Legal de Contrato", self.styles['Seccion']))
        story.append(Spacer(1, 0.2 * inch))
        
        # === METADATOS ===
        story.append(Paragraph(f"Contrato analizado: {contrato_nombre}", self.styles['Metadata']))
        story.append(Paragraph(f"Fecha de analisis: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                               self.styles['Metadata']))
        story.append(Spacer(1, 0.3 * inch))
        
        # === CONTENIDO DEL ANALISIS ===
        # Procesar el resumen respetando la estructura
        story = self._procesar_contenido(resumen, story)
        
        # Generar PDF
        doc.build(story)
        
        logger.info(f"PDF generado exitosamente: {archivo_salida}")
        return archivo_salida
    
    def _procesar_contenido(self, resumen: str, story: list) -> list:
        """
        Procesa el contenido del resumen respetando la estructura (secciones, items, etc.)
        """
        lineas = resumen.split('\n')
        i = 0
        en_lista = False
        
        while i < len(lineas):
            linea = lineas[i].strip()
            
            if not linea:
                story.append(Spacer(1, 0.1 * inch))
                i += 1
                continue
            
            # Detectar titulo de seccion (ej: "1. FECHAS IMPORTANTES")
            if re.match(r'^\d+\.', linea):
                # Limpiar formato de markdown
                linea_limpia = self._limpiar_formato(linea)
                story.append(Paragraph(linea_limpia, self.styles['Seccion']))
                en_lista = False
                i += 1
                continue
            
            # Detectar subseccion (ej: "2. RIESGOS ALTOS (Requieren atención inmediata)")
            if re.match(r'^\d+\.', linea) or ('RIESGOS' in linea.upper() and '---' not in linea):
                linea_limpia = self._limpiar_formato(linea)
                story.append(Paragraph(linea_limpia, self.styles['SubSeccion']))
                en_lista = False
                i += 1
                continue
            
            # Detectar linea de separacion (---)
            if '---' in linea or '===' in linea or '---' in linea:
                i += 1
                continue
            
            # Detectar item de lista (comienza con • o *)
            if linea.startswith('•') or linea.startswith('*'):
                # Quitar el bullet point
                texto_item = linea[1:].strip()
                texto_limpio = self._limpiar_formato(texto_item)
                story.append(Paragraph(f"• {texto_limpio}", self.styles['ListItem']))
                en_lista = True
                i += 1
                continue
            
            # Detectar texto con "Texto:" (cita)
            if linea.startswith('Texto:') or 'Texto:' in linea[:10]:
                texto_cita = linea.replace('Texto:', '').strip()
                texto_limpio = self._limpiar_formato(texto_cita)
                # Limitar longitud de citas
                if len(texto_limpio) > 200:
                    texto_limpio = texto_limpio[:200] + "..."
                story.append(Paragraph(f'"{texto_limpio}"', self.styles['TextoCitado']))
                i += 1
                continue
            
            # Detectar recomendacion
            if linea.startswith('Recomendacion:') or 'Recomendacion:' in linea[:15]:
                texto_rec = linea.replace('Recomendacion:', '').strip()
                texto_limpio = self._limpiar_formato(texto_rec)
                story.append(Paragraph(f"Recomendacion: {texto_limpio}", self.styles['Recomendacion']))
                i += 1
                continue
            
            # Texto normal
            texto_limpio = self._limpiar_formato(linea)
            if len(texto_limpio) > 80:
                # Texto largo, puede necesitar salto de pagina
                story.append(Paragraph(texto_limpio, self.styles['TextoNormal']))
            elif texto_limpio:
                story.append(Paragraph(texto_limpio, self.styles['TextoNormal']))
            
            i += 1
        
        return story
    
    def _limpiar_formato(self, texto: str) -> str:
        """
        Limpia el texto de caracteres especiales que reportlab no soporta.
        """
        # Reemplazar caracteres especiales
        texto = texto.replace('•', '-')
        texto = texto.replace('*', '-')
        texto = texto.replace('_', '')
        texto = texto.replace('`', '')
        
        # Asegurar que los caracteres sean compatibles con reportlab
        texto = texto.encode('ascii', 'ignore').decode('ascii')
        
        # Escapar caracteres especiales de HTML/XML
        texto = texto.replace('&', '&amp;')
        texto = texto.replace('<', '&lt;')
        texto = texto.replace('>', '&gt;')
        
        return texto