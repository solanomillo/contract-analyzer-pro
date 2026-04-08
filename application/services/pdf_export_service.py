"""
Servicio para exportar analisis legales a PDF.
"""

import logging
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


class PDFExportService:
    """
    Servicio para exportar analisis de contratos a PDF.
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
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtitulos
        styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=10,
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
        
        # Estilo para texto de recomendaciones
        styles.add(ParagraphStyle(
            name='Recomendacion',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leftIndent=20,
            fontName='Helvetica'
        ))
        
        # Estilo para secciones
        styles.add(ParagraphStyle(
            name='Seccion',
            parent=styles['Heading3'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        return styles
    
    def exportar_analisis(self, resumen: str, contrato_nombre: str, 
                          archivo_salida: Path = None) -> Path:
        """
        Exporta el analisis legal a un archivo PDF.
        
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
            bottomMargin=72
        )
        
        # Contenido del PDF
        story = []
        
        # Titulo
        story.append(Paragraph("CONTRACT ANALYZER PRO", self.styles['TituloPrincipal']))
        story.append(Paragraph("Analisis Legal de Contrato", self.styles['Subtitulo']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Informacion del documento
        story.append(Paragraph(f"Contrato analizado: {contrato_nombre}", self.styles['TextoNormal']))
        story.append(Paragraph(f"Fecha de analisis: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                               self.styles['TextoNormal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Procesar el resumen (eliminar emojis y formatear)
        resumen_limpio = self._limpiar_texto(resumen)
        
        # Dividir el resumen en secciones y agregar al PDF
        lineas = resumen_limpio.split('\n')
        
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                story.append(Spacer(1, 0.1 * inch))
                continue
            
            # Detectar secciones por palabras clave
            if 'RIESGOS ALTOS' in linea.upper():
                story.append(Paragraph("RIESGOS ALTOS", self.styles['Seccion']))
            elif 'RIESGOS MEDIOS' in linea.upper():
                story.append(PageBreak())
                story.append(Paragraph("RIESGOS MEDIOS", self.styles['Seccion']))
            elif 'RIESGOS BAJOS' in linea.upper() or 'RIESGOS BAJOS / INFORMATIVOS' in linea.upper():
                story.append(PageBreak())
                story.append(Paragraph("RIESGOS BAJOS / INFORMATIVOS", self.styles['Seccion']))
            elif 'RECOMENDACIONES' in linea.upper():
                story.append(Spacer(1, 0.2 * inch))
                story.append(Paragraph("RECOMENDACIONES PRIORITARIAS", self.styles['Seccion']))
            elif linea.startswith('•') or linea.startswith('-'):
                # Es un item de lista
                texto_item = linea[1:].strip()
                story.append(Paragraph(f"• {texto_item}", self.styles['TextoNormal']))
            elif linea.startswith('  '):
                # Es subitem (texto o recomendacion)
                texto_sub = linea.strip()
                if 'recomendacion' in texto_sub.lower() or 'recomendación' in texto_sub.lower():
                    story.append(Paragraph(texto_sub, self.styles['Recomendacion']))
                else:
                    story.append(Paragraph(texto_sub, self.styles['TextoNormal']))
            else:
                # Texto normal
                if '=' in linea or '-' * 10 in linea:
                    continue  # Saltar lineas de separacion
                story.append(Paragraph(linea, self.styles['TextoNormal']))
        
        # Generar PDF
        doc.build(story)
        
        logger.info(f"PDF generado exitosamente: {archivo_salida}")
        return archivo_salida
    
    def _limpiar_texto(self, texto: str) -> str:
        """
        Elimina emojis, markdown y formateo especial del texto.
        
        Args:
            texto: Texto original con posibles emojis y markdown
            
        Returns:
            Texto limpio sin emojis ni formateo
        """
        # Eliminar emojis (rango Unicode de emojis)
        import re
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001F900-\U0001F9FF"  # supplemental symbols
            u"\U0001FA70-\U0001FAFF"  # more symbols
            "]+",
            flags=re.UNICODE
        )
        texto = emoji_pattern.sub('', texto)
        
        # Eliminar markdown bold (**texto**)
        texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
        
        # Eliminar markdown italic (*texto*)
        texto = re.sub(r'\*(.*?)\*', r'\1', texto)
        
        # Eliminar otros caracteres especiales comunes
        texto = texto.replace('```', '').replace('`', '')
        
        # Limpiar multiples espacios
        texto = re.sub(r'\s+', ' ', texto)
        
        # Restaurar saltos de linea donde corresponde
        texto = texto.replace('. ', '.\n')
        
        return texto.strip()