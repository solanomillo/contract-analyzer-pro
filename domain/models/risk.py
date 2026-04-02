"""
Risk domain model.

Represents a detected risk or clause in a contract.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    """Risk levels for contract clauses."""
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"


class RiskType(Enum):
    """Types of risks that can be detected."""
    PENALIZACION = "penalizacion"
    RESCISION_UNILATERAL = "rescision_unilateral"
    CLAUSULA_ABUSIVA = "clausula_abusiva"
    RENOVACION_AUTOMATICA = "renovacion_automatica"
    EXCLUSIVIDAD = "exclusividad"
    LIMITACION_RESPONSABILIDAD = "limitacion_responsabilidad"
    MULTA = "multa"
    INTERES_ELEVADO = "interes_elevado"
    OBLIGACION_PAGO = "obligacion_pago"
    FECHA_CRITICA = "fecha_critica"


@dataclass
class Risk:
    """
    Domain model representing a detected risk in a contract.

    Attributes:
        tipo: Type of risk (from RiskType enum)
        descripcion: Human-readable description of the risk
        riesgo: Risk level (ALTO, MEDIO, BAJO)
        texto_relevante: The exact text snippet where the risk was found
        recomendacion: Suggested action or recommendation
        ubicacion: Optional location (page, section) in the contract
    """
    tipo: RiskType
    descripcion: str
    riesgo: RiskLevel
    texto_relevante: str
    recomendacion: str
    ubicacion: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert risk to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the risk.
        """
        return {
            "tipo": self.tipo.value,
            "descripcion": self.descripcion,
            "riesgo": self.riesgo.value,
            "texto_relevante": self.texto_relevante,
            "recomendacion": self.recomendacion,
            "ubicacion": self.ubicacion
        }