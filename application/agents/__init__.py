"""Modulo de agentes para analisis de contratos."""

from application.agents.base_agent import BaseAgent, Hallazgo
from application.agents.risk_agent import RiskDetectionAgent
from application.agents.date_agent import DateExtractionAgent
from application.agents.obligation_agent import ObligationAgent
from application.agents.complete_analysis_agent import CompleteAnalysisAgent

__all__ = [
    "BaseAgent", 
    "Hallazgo", 
    "RiskDetectionAgent", 
    "DateExtractionAgent", 
    "ObligationAgent",
    "CompleteAnalysisAgent"
]