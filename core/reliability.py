# core/reliability.py
"""
Módulo consolidado para cálculo de confiabilidade (reliability).
Unifica a lógica que antes estava espalhada em engine.py e ingredients.py.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Tuple, List, Dict

from .models import ReliabilityLevel, Item
from .stats import calculate_coefficient_of_variation, calculate_reliability_from_cv


# Constantes para thresholds de auditoria
AUDIT_DAYS_CRITICAL = 15
AUDIT_DAYS_MODERATE = 3
MIN_DRIVERS_FOR_BONUS = 3
DRIVER_BONUS = 0.1


def calculate_item_reliability(
    item: Item,
    raw_values: List[float],
    n_samples: int,
    now: datetime,
    drivers: Optional[Dict[str, float]] = None,
) -> Tuple[float, ReliabilityLevel]:
    """
    Calcula reliability score e nível para um item.
    
    Args:
        item: O item sendo analisado
        raw_values: Valores históricos de demanda (já limpos de outliers)
        n_samples: Número de amostras no período
        now: Timestamp atual para calcular dias desde última auditoria
        drivers: Opcional - dict de drivers (para ingredientes)
    
    Returns:
        Tuple (score: 0.0-1.0, level: ReliabilityLevel)
    """
    # Base: CV + volume de dados
    cv = calculate_coefficient_of_variation(raw_values)
    rel_score, rel_level = calculate_reliability_from_cv(cv, n_samples)
    
    # Ajuste por última auditoria
    if item.last_audit_date is None:
        rel_score = min(rel_score, 0.4)
        reliability = ReliabilityLevel.LOW
    else:
        days_since_audit = (now.date() - item.last_audit_date).days
        if days_since_audit > AUDIT_DAYS_CRITICAL:
            rel_score = min(rel_score, 0.5)
            reliability = ReliabilityLevel.LOW
        elif days_since_audit > AUDIT_DAYS_MODERATE:
            reliability = ReliabilityLevel(rel_level)
        else:
            reliability = ReliabilityLevel.HIGH if rel_score >= 0.8 else ReliabilityLevel(rel_level)
    
    # Bônus por múltiplos drivers (ingredientes)
    if drivers and len(drivers) >= MIN_DRIVERS_FOR_BONUS:
        rel_score = min(1.0, rel_score + DRIVER_BONUS)
    
    return rel_score, reliability


def calculate_ingredient_reliability(
    all_driver_values: List[float],
    n_drivers: int,
) -> Tuple[float, ReliabilityLevel]:
    """
    Calcula reliability para ingrediente baseado nos valores dos drivers.
    Versão simplificada para quando não temos o Item diretamente.
    
    Args:
        all_driver_values: Valores agregados de todos os drivers
        n_drivers: Número de drivers
    
    Returns:
        Tuple (score: 0.0-1.0, level: ReliabilityLevel)
    """
    if not all_driver_values:
        return 0.4, ReliabilityLevel.LOW
    
    cv = calculate_coefficient_of_variation(all_driver_values)
    rel_score, rel_level = calculate_reliability_from_cv(cv, len(all_driver_values))
    reliability = ReliabilityLevel(rel_level)
    
    # Bônus por múltiplos drivers
    if n_drivers >= MIN_DRIVERS_FOR_BONUS:
        rel_score = min(1.0, rel_score + DRIVER_BONUS)
    
    return rel_score, reliability
