"""
Servicio centralizado para formatear respuestas de los agentes.
Elimina duplicacion de codigo en el formateo de hallazgos.
"""

import re
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
        
        respuestas = []
        for h in hallazgos:
            tipo = h.get("tipo", "")
            descripcion = h.get("descripcion", "")
            
            if tipo == "inicio":
                respuestas.append(f"El contrato comienza el {descripcion}")
            elif tipo == "termino":
                respuestas.append(f"El contrato termina el {descripcion}")
            elif tipo == "plazo_pago":
                respuestas.append(f"Plazo de pago: {descripcion}")
            elif tipo == "preaviso":
                respuestas.append(f"Preaviso requerido: {descripcion}")
            else:
                respuestas.append(descripcion)
        
        if len(respuestas) == 1:
            return respuestas[0]
        return "\n".join(respuestas)
    
    @staticmethod
    def format_riesgos(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de riesgos."""
        if not hallazgos:
            return "No se encontraron clausulas de riesgo en el contrato."
        
        # Primero buscar penalizaciones
        for h in hallazgos:
            if "penalizacion" in h.get("tipo", "").lower():
                desc = h.get('descripcion', '')
                # Extraer el porcentaje si existe
                porcentaje = re.search(r'(\d+)%', desc)
                if porcentaje:
                    return f"{porcentaje.group()} del valor total del contrato"
                return desc
        
        # Buscar rescision
        for h in hallazgos:
            if "rescision" in h.get("tipo", "").lower():
                desc = h.get('descripcion', '')
                # Extraer los dias
                dias = re.search(r'(\d+)\s*dias', desc.lower())
                if dias:
                    return f"{dias.group()}"
                return desc
        
        # Si no, devolver el primer riesgo
        return hallazgos[0].get('descripcion', '')
    
    @staticmethod
    def format_obligaciones(hallazgos: List[Dict[str, Any]]) -> str:
        """Formatea respuestas del agente de obligaciones."""
        if not hallazgos:
            return "No se encontraron obligaciones en el contrato."
        
        respuestas = []
        
        for h in hallazgos:
            tipo = h.get("tipo", "")
            descripcion = h.get("descripcion", "")
            
            # Buscar informacion de pago (monto)
            if "pago" in tipo.lower() or "$" in descripcion:
                monto = re.search(r'\$\s*[\d,]+\.?\d*', descripcion)
                if monto:
                    respuestas.append(f"{monto.group()} mensuales")
                else:
                    respuestas.append(descripcion)
            
            # Buscar obligaciones de servicios
            elif "servicio" in descripcion.lower() or "luz" in descripcion.lower():
                respuestas.append(f"Servicios a cargo: {descripcion}")
            
            # Buscar obligaciones de mantenimiento
            elif "mantener" in descripcion.lower():
                respuestas.append(f"Obligacion: {descripcion}")
            
            # Otras obligaciones
            else:
                respuestas.append(descripcion)
        
        if len(respuestas) == 1:
            return respuestas[0]
        return "\n".join(respuestas)
    
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