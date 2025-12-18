# core/safety.py
from __future__ import annotations

from .models import ItemClass


def calculate_safety_stock(
    max_daily_demand: float,
    avg_daily_demand: float,
    max_lead_time: float,
    avg_lead_time: float,
    item_class: ItemClass,
) -> float:
    """
    Calcula estoque de segurança (Safety Stock) usando uma fórmula max-max:

    SS = (D_max * LT_max) - (D_avg * LT_avg), ajustado por Curva ABC.

    - D_max / D_avg vêm da série histórica (janela) após limpeza de outliers.
    - LT_max / LT_avg vêm do cadastro de item + fator de variabilidade de fornecedor.
    - Classe A: 100% do risco calculado
    - Classe B: 70%
    - Classe C: 40%
    """
    # Defensive math: não deixa valores negativos entrarem no cálculo
    d_max = max(0.0, max_daily_demand)
    d_avg = max(0.0, avg_daily_demand)
    lt_max = max(0.0, max_lead_time)
    lt_avg = max(0.0, avg_lead_time)

    worst_case = d_max * lt_max
    avg_case = d_avg * lt_avg

    raw_ss = max(0.0, worst_case - avg_case)

    factor_by_class = {
        ItemClass.A: 1.0,   # Alta proteção
        ItemClass.B: 0.70,  # Proteção intermediária
        ItemClass.C: 0.40,  # Aceita mais risco
    }

    factor = factor_by_class.get(item_class, 1.0)

    return raw_ss * factor
