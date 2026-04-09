"""
Servicio para formatear respuestas.
"""

from typing import List, Dict, Any


class ResponseFormatter:
    
    @staticmethod
    def format_respuesta_concreta(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuesta concreta para preguntas."""
        if not hallazgos:
            return "No se encontró información relevante."
        
        if hallazgos[0].get("tipo") == "error":
            return hallazgos[0].get("descripcion", "Error desconocido")
        
        return hallazgos[0].get("descripcion", "Sin respuesta")
    
    @staticmethod
    def format_completo(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea análisis completo con estructura clara."""
        if not hallazgos:
            return "No se encontró información relevante en el contrato."
        
        # Clasificar hallazgos por tipo
        fechas = []
        riesgos_altos = []
        riesgos_medios = []
        obligaciones = []
        otros = []
        
        for h in hallazgos:
            tipo = h.get("tipo", "")
            riesgo = h.get("riesgo", "MEDIO")
            
            if "fecha" in tipo:
                fechas.append(h)
            elif riesgo == "ALTO":
                riesgos_altos.append(h)
            elif riesgo == "MEDIO":
                riesgos_medios.append(h)
            elif "obligacion" in tipo or "pago" in tipo or "servicios" in tipo:
                obligaciones.append(h)
            else:
                otros.append(h)
        
        lineas = []
        lineas.append("=" * 60)
        lineas.append("ANALISIS LEGAL DEL CONTRATO")
        lineas.append("=" * 60)
        
        # Sección 1: Fechas Importantes
        if fechas:
            lineas.append("\n1. FECHAS IMPORTANTES")
            lineas.append("-" * 40)
            for h in fechas:
                desc = h.get('descripcion', '')
                texto = h.get('texto_relevante', '')
                lineas.append(f"• {desc}")
                if texto:
                    lineas.append(f"  Texto: \"{texto[:100]}...\"")
            lineas.append("")
        
        # Sección 2: Riesgos Altos
        if riesgos_altos:
            lineas.append("2. RIESGOS ALTOS (Requieren atención inmediata)")
            lineas.append("-" * 40)
            for h in riesgos_altos:
                desc = h.get('descripcion', '')
                texto = h.get('texto_relevante', '')
                rec = h.get('recomendacion', '')
                lineas.append(f"• {desc}")
                if texto:
                    lineas.append(f"  Texto: \"{texto[:150]}...\"")
                if rec:
                    lineas.append(f"  Recomendacion: {rec}")
            lineas.append("")
        
        # Sección 3: Riesgos Medios
        if riesgos_medios:
            lineas.append("3. RIESGOS MEDIOS (Requieren atención)")
            lineas.append("-" * 40)
            for h in riesgos_medios:
                desc = h.get('descripcion', '')
                texto = h.get('texto_relevante', '')
                lineas.append(f"• {desc}")
                if texto:
                    lineas.append(f"  Texto: \"{texto[:150]}...\"")
            lineas.append("")
        
        # Sección 4: Obligaciones de las Partes
        if obligaciones:
            lineas.append("4. OBLIGACIONES DE LAS PARTES")
            lineas.append("-" * 40)
            for h in obligaciones:
                desc = h.get('descripcion', '')
                rec = h.get('recomendacion', '')
                lineas.append(f"• {desc}")
                if rec:
                    lineas.append(f"  Recomendacion: {rec}")
            lineas.append("")
        
        # Sección 5: Otros hallazgos
        if otros:
            lineas.append("5. INFORMACION ADICIONAL")
            lineas.append("-" * 40)
            for h in otros:
                desc = h.get('descripcion', '')
                lineas.append(f"• {desc}")
        
        return "\n".join(lineas)