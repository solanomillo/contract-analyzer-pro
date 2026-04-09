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
        """Formatea respuestas del agente de fechas - SOLO TEXTO CONCRETO."""
        if not hallazgos:
            return "No se encontraron fechas importantes en el contrato."
        
        # Buscar la fecha mas relevante segun la pregunta implicita
        for h in hallazgos:
            tipo = h.get("tipo", "")
            descripcion = h.get("descripcion", "")
            
            if tipo == "inicio":
                return f"{descripcion}"
            elif tipo == "termino":
                return f"{descripcion}"
            elif tipo == "plazo_pago":
                return f"{descripcion}"
        
        # Si no encuentra tipo especifico, devolver el primero
        return f"{hallazgos[0].get('descripcion', '')}"
    
    @staticmethod
    def format_riesgos(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de riesgos - SOLO TEXTO CONCRETO."""
        if not hallazgos:
            return "No se encontraron clausulas de riesgo en el contrato."
        
        # Buscar riesgo ALTO primero
        for h in hallazgos:
            if h.get("riesgo") == "ALTO":
                return f"{h.get('descripcion', '')}"
        
        # Si no hay riesgo ALTO, devolver el primero
        return f"{hallazgos[0].get('descripcion', '')}"
    
    @staticmethod
    def format_obligaciones(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de obligaciones - SOLO TEXTO CONCRETO."""
        if not hallazgos:
            return "No se encontraron obligaciones en el contrato."
        
        # Buscar informacion de pago (monto)
        for h in hallazgos:
            tipo = h.get("tipo", "")
            descripcion = h.get("descripcion", "")
            
            # Buscar el monto exacto
            if "$" in descripcion or "pesos" in descripcion.lower():
                # Extraer solo el monto
                if "$" in descripcion:
                    import re
                    monto_match = re.search(r'\$\s*[\d,]+\.?\d*', descripcion)
                    if monto_match:
                        return f"{monto_match.group()}"
                return f"{descripcion}"
        
        # Si no encuentra monto, devolver la primera obligacion
        return f"{hallazgos[0].get('descripcion', '')}"
    
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
        return f"ERROR: {mensaje}"