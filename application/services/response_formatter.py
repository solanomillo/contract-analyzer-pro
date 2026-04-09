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
        """Formatea análisis completo."""
        if not hallazgos:
            return "No se encontró información relevante en el contrato."
        
        altos = [h for h in hallazgos if h.get("riesgo") == "ALTO"]
        medios = [h for h in hallazgos if h.get("riesgo") == "MEDIO"]
        bajos = [h for h in hallazgos if h.get("riesgo") == "BAJO"]
        
        lineas = []
        lineas.append("=" * 60)
        lineas.append("ANALISIS LEGAL DEL CONTRATO")
        lineas.append("=" * 60)
        
        lineas.append(f"\nRIESGOS ALTOS ({len(altos)})")
        lineas.append("-" * 40)
        for h in altos[:5]:
            lineas.append(f"* {h.get('descripcion', '')}")
            if h.get('texto_relevante'):
                lineas.append(f"  Texto: \"{h.get('texto_relevante', '')[:150]}...\"")
            if h.get('recomendacion'):
                lineas.append(f"  Recomendacion: {h.get('recomendacion')}")
            lineas.append("")
        
        lineas.append(f"\nRIESGOS MEDIOS ({len(medios)})")
        lineas.append("-" * 40)
        for h in medios[:5]:
            lineas.append(f"* {h.get('descripcion', '')}")
            lineas.append("")
        
        lineas.append(f"\nRIESGOS BAJOS ({len(bajos)})")
        lineas.append("-" * 40)
        for h in bajos[:3]:
            lineas.append(f"* {h.get('descripcion', '')}")
        
        return "\n".join(lineas)