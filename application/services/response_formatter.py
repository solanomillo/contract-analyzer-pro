"""
Servicio centralizado para formatear respuestas de los agentes.
Elimina duplicacion de codigo en el formateo de hallazgos.
"""

from typing import List, Dict, Any


class ResponseFormatter:
    """
    Formatea respuestas para mostrar al usuario.
    Unico lugar donde se maneja el formato de salida.
    """
    
    @staticmethod
    def format_fechas(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de fechas."""
        if not hallazgos:
            return "No se encontraron fechas importantes en el contrato."
        
        respuesta = "Respuesta:\n\n"
        
        for h in hallazgos:
            tipo = h.get("tipo", "")
            descripcion = h.get("descripcion", "")
            
            if tipo == "inicio":
                respuesta += f"Fecha de inicio: {descripcion}\n"
            elif tipo == "termino":
                respuesta += f"Fecha de termino: {descripcion}\n"
            elif tipo == "plazo_pago":
                respuesta += f"Plazo de pago: {descripcion}\n"
            elif tipo == "preaviso":
                respuesta += f"Preaviso requerido: {descripcion}\n"
            else:
                respuesta += f"• {descripcion}\n"
            
            if h.get("recomendacion"):
                respuesta += f"   Recomendacion: {h.get('recomendacion')}\n"
        
        return respuesta
    
    @staticmethod
    def format_riesgos(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de riesgos."""
        if not hallazgos:
            return "No se encontraron clausulas de riesgo en el contrato."
        
        altos = [h for h in hallazgos if h.get("riesgo") == "ALTO"]
        medios = [h for h in hallazgos if h.get("riesgo") == "MEDIO"]
        bajos = [h for h in hallazgos if h.get("riesgo") == "BAJO"]
        
        respuesta = "Respuesta:\n\n"
        
        if altos:
            respuesta += "RIESGOS ALTOS:\n"
            for h in altos:
                respuesta += f"  • {h.get('descripcion', '')}\n"
                if h.get('recomendacion'):
                    respuesta += f"    Recomendacion: {h.get('recomendacion')}\n"
            respuesta += "\n"
        
        if medios:
            respuesta += "RIESGOS MEDIOS:\n"
            for h in medios:
                respuesta += f"  • {h.get('descripcion', '')}\n"
                if h.get('recomendacion'):
                    respuesta += f"    Recomendacion: {h.get('recomendacion')}\n"
            respuesta += "\n"
        
        if bajos and not altos and not medios:
            respuesta += "RIESGOS BAJOS:\n"
            for h in bajos[:3]:
                respuesta += f"  • {h.get('descripcion', '')}\n"
        
        return respuesta.strip()
    
    @staticmethod
    def format_obligaciones(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de obligaciones."""
        if not hallazgos:
            return "No se encontraron obligaciones en el contrato."
        
        respuesta = "Respuesta:\n\n"
        
        for h in hallazgos:
            tipo = h.get("tipo", "")
            descripcion = h.get("descripcion", "")
            
            if tipo == "pago":
                respuesta += f"Obligacion de pago: {descripcion}\n"
            elif tipo == "plazo":
                respuesta += f"Plazo: {descripcion}\n"
            else:
                respuesta += f"• {descripcion}\n"
            
            if h.get("recomendacion"):
                respuesta += f"   Recomendacion: {h.get('recomendacion')}\n"
        
        return respuesta
    
    @staticmethod
    def format_completo(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de analisis completo."""
        if not hallazgos:
            return "No se encontro informacion relevante en el contrato."
        
        altos = [h for h in hallazgos if h.get("riesgo") == "ALTO"]
        medios = [h for h in hallazgos if h.get("riesgo") == "MEDIO"]
        bajos = [h for h in hallazgos if h.get("riesgo") == "BAJO"]
        
        lineas = []
        lineas.append("=" * 60)
        lineas.append("RESULTADOS DEL ANALISIS LEGAL")
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
            if h.get('texto_relevante'):
                lineas.append(f"  Texto: \"{h.get('texto_relevante', '')[:150]}...\"")
            lineas.append("")
        
        lineas.append(f"\nRIESGOS BAJOS / INFORMATIVOS ({len(bajos)})")
        lineas.append("-" * 40)
        for h in bajos[:3]:
            lineas.append(f"* {h.get('descripcion', '')}")
        
        if altos:
            lineas.append("\n" + "!" * 60)
            lineas.append("RECOMENDACIONES PRIORITARIAS:")
            lineas.append("!" * 60)
            for h in altos[:3]:
                if h.get('recomendacion'):
                    lineas.append(f"* {h.get('recomendacion')}")
        
        return "\n".join(lineas)
    
    @staticmethod
    def format_error(mensaje: str) -> str:
        """Formatea mensajes de error."""
        return f"ERROR:\n\n{mensaje}"