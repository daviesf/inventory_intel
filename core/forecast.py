# core/forecast.py
"""
Módulo de previsão de demanda (determinístico).

- Usa WMA-DOW (Weighted Moving Average por dia da semana)
- Respeita janela de histórico (ctx.forecast_window_days)
- Pensado inicialmente para itens FINISHED vendidos diretamente.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional

from .models import InventoryState, AnalysisContext, ItemType
from .stats import filter_outliers
from .temporal_adjustments import apply_temporal_adjustments, TemporalBreakdown


@dataclass
class DailyAgg:
    """Agregação diária de vendas por item."""
    date: date
    quantity: float


@dataclass
class DemandStats:
    """
    Estatísticas de demanda para um item:

    - avg_daily_demand: média diária histórica (janela bruta, após limpeza de outliers)
    - max_daily_demand: máximo diário histórico (janela bruta, após limpeza de outliers)
    - wma_forecast: previsão WMA-DOW para o dia da semana atual
    - raw_values: valores diários brutos (após limpeza) para cálculo de CV
    - n_samples: número de dias com dados na janela
    """
    avg_daily_demand: float
    max_daily_demand: float
    wma_forecast: float
    raw_values: List[float] = None
    n_samples: int = 0
    temporal_breakdown: Optional[TemporalBreakdown] = None

    def __post_init__(self):
        if self.raw_values is None:
            self.raw_values = []


def _build_daily_series_for_item(
    state: InventoryState,
    item_id: str,
    ctx: AnalysisContext,
) -> List[DailyAgg]:
    """
    Constrói a série diária de vendas para um item (somando por dia),
    respeitando uma janela de N dias definida em ctx.forecast_window_days.
    """
    if not state.sales_history:
        return []

    window_days = max(1, int(getattr(ctx, "forecast_window_days", 30)))
    now = ctx.now
    min_date = (now - timedelta(days=window_days)).date()
    max_date = now.date()

    qty_by_day: Dict[date, float] = defaultdict(float)

    for sale in state.sales_history:
        # Por enquanto consideramos apenas vendas cujo dish_id == item_id (produto pronto)
        if sale.dish_id != item_id:
            continue

        sale_date = sale.timestamp.date()
        # Ignora vendas fora da janela ou no futuro
        if sale_date < min_date or sale_date > max_date:
            continue

        qty_by_day[sale_date] += sale.quantity

    # Transforma em lista ordenada por data crescente (pode ser invertido depois)
    series = [
        DailyAgg(date=d, quantity=q)
        for d, q in qty_by_day.items()
        if q > 0
    ]
    series.sort(key=lambda x: x.date)  # cronológico

    return series


def _winsorize_high(values: List[float], factor: float = 2.0) -> List[float]:
    """
    Compatível com a assinatura antiga, mas agora:

    - Usa filtro de outliers robusto (MAD/Z-Score).
    - Se ainda quiser, você pode aplicar um "teto" depois
      baseado em mediana + factor * sigma_robusto.

    Aqui, por simplicidade, só filtramos outliers via filter_outliers.
    """
    if not values:
        return []
    clean = filter_outliers(values, threshold=3.5)
    return clean


def _forecast_wma_for_weekday(
    series: List[DailyAgg],
    target_weekday: int,
    max_weeks: int = 4,
) -> float:
    """
    Calcula a demanda prevista para um dia da semana (target_weekday)
    usando WMA (pesos lineares) nas últimas ocorrências daquele dia.

    - Filtra apenas dias do mesmo weekday;
    - Pega até max_weeks ocorrências mais recentes;
    - Aplica limpeza de outliers para evitar picos absurdos contaminando a média.
    """
    if not series:
        return 0.0

    # Filtra só datas com mesmo dia da semana
    same_weekday_points = [
        p for p in series if p.date.weekday() == target_weekday
    ]
    if not same_weekday_points:
        return 0.0

    # Ordena mais recente primeiro
    same_weekday_points.sort(key=lambda x: x.date, reverse=True)

    window = same_weekday_points[:max_weeks]

    # Extrai quantidades e aplica limpeza de outliers
    raw_values = [p.quantity for p in window]
    clipped_values = _winsorize_high(raw_values, factor=2.0)

    if not clipped_values:
        return 0.0

    n = len(clipped_values)
    weights = list(range(n, 0, -1))

    weighted_sum = sum(v * w for v, w in zip(clipped_values, weights))
    sum_weights = sum(weights)

    if sum_weights == 0:
        return 0.0

    return weighted_sum / sum_weights


def _calculate_window_statistics(series: List[DailyAgg]) -> Tuple[float, float, List[float]]:
    """
    Retorna (avg_demand, max_demand, clean_values) da janela histórica bruta.
    Usado para cálculo de Safety Stock (volatilidade).

    Aqui usamos a série diária inteira (não por dia da semana) para capturar picos reais.
    Agora também retorna os valores limpos para cálculo de CV.
    """
    if not series:
        return 0.0, 0.0, []

    values = [p.quantity for p in series]
    clean_values = _winsorize_high(values)

    if not clean_values:
        return 0.0, 0.0, []

    avg_val = sum(clean_values) / len(clean_values)
    max_val = max(clean_values)

    return avg_val, max_val, clean_values


def get_item_demand_data(
    state: InventoryState,
    item_id: str,
    ctx: AnalysisContext,
) -> DemandStats:
    """
    Função unificada que retorna tanto o Forecast (WMA-DOW) quanto as estatísticas
    descritivas históricas (Avg, Max) para um item.

    - avg_daily_demand / max_daily_demand: série bruta (janela) -> para Safety Stock.
    - wma_forecast: previsão específica para o dia da semana atual -> para consumo futuro.
    """
    series = _build_daily_series_for_item(state, item_id, ctx)

    # 1. Estatísticas descritivas (passado)
    avg_hist, max_hist, clean_values = _calculate_window_statistics(series)

    # 2. Forecast WMA-DOW (futuro)
    target_weekday = ctx.now.date().weekday()
    wma_val_base = _forecast_wma_for_weekday(series, target_weekday, max_weeks=4)

    # 3. Apply Temporal Adjustments (Seasonality, Events, etc.)
    # Note: wma_val_base already accounts for DOW implicitly via WMA logic?
    # The user prompt computed DOW factor explicitly: "dow_factor = avg_sales_on_weekday / avg_daily_sales"
    # But `_forecast_wma_for_weekday` already filters by weekday.
    # If the base forecast comes from Same-Weekday-History, adding a DOW factor ON TOP would be double counting 
    # IF the DOW factor represents "Weekday vs Average".
    #
    # However, user explicitly requested:
    # "forecast_final = forecast_base * dow_factor * ..."
    #
    # To follow instructions strictly while being correct:
    # If forecast_base IS ALREADY weekday-specific, then DOW factor should be 1.0 or we should use a global average as base.
    # But `calc_daily_demand_per_item` uses `get_item_demand_data` which uses `_forecast_wma_for_weekday`.
    #
    # DECISION:
    # I will pass `wma_val_base` as `forecast_base`. 
    # And in `compute_dow_factor` in `temporal_adjustments.py`, I implemented a check for `state.dow_factors`.
    # If `state.dow_factors` is empty (default), it returns 1.0.
    # If I were to implement DOW factor calculation from scratch, I would do Global Avg vs Weekday Avg.
    # Sincethe current engine is DOW-aware by design (`_forecast_wma_for_weekday`), 
    # applying an EXTERNAL dow_factor is only necessary if we want to force an override or if the base was not DOW-specific.
    #
    # Given the user instruction "forecast_final = forecast_base * dow_factor ...", i should apply it.
    # If the user populates `dow_factors` table, it will multiply.
    # If not, factor is 1.0.
    
    adjustment = apply_temporal_adjustments(
        item_id=item_id,
        target_date=ctx.now.date(),
        forecast_base=wma_val_base,
        state=state
    )

    return DemandStats(
        avg_daily_demand=avg_hist,
        max_daily_demand=max_hist,
        wma_forecast=adjustment.forecast_final, # Adjusted Value
        raw_values=clean_values,
        n_samples=len(series),
        temporal_breakdown=adjustment
    )


def calc_daily_demand_per_item(
    state: InventoryState,
    ctx: AnalysisContext,
) -> Dict[str, float]:
    """
    Cálculo principal de demanda diária projetada por item_id.

    Mantido para compatibilidade com o motor, mas agora ele
    reutiliza get_item_demand_data internamente.

    - Para cada Item FINISHED:
        - constroi série diária de vendas (últimos N dias)
        - estima a demanda para o dia atual (ctx.now) usando WMA-DOW.
    """
    demand_per_item: Dict[str, float] = {}

    finished_item_ids = [
        item.id for item in state.items if item.item_type == ItemType.FINISHED
    ]

    for item_id in finished_item_ids:
        stats = get_item_demand_data(state, item_id, ctx)
        demand_per_item[item_id] = stats.wma_forecast

    return demand_per_item
