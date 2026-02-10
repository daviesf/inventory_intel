# core/demand_cache.py
"""
Cache de demanda para evitar recálculos O(n²).
Pré-computa demand stats para todos os items uma vez por request.
"""

from __future__ import annotations

from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import InventoryState, AnalysisContext, Item
    from .forecast import DemandStats


class DemandCache:
    """
    Cache que pré-computa demand data para todos os items.
    Evita o problema N+1 de chamar get_item_demand_data repetidamente.
    """
    
    def __init__(self, state: "InventoryState", ctx: "AnalysisContext"):
        from .forecast import get_item_demand_data
        
        self._cache: Dict[str, "DemandStats"] = {}
        self._item_by_id: Dict[str, "Item"] = {item.id: item for item in state.items}
        self._stock_map: Dict[str, float] = {}
        
        # Pré-computa stock map
        for sl in state.stock_levels:
            self._stock_map[sl.item_id] = self._stock_map.get(sl.item_id, 0.0) + sl.quantity
        
        # Pré-computa demand data para todos os items
        all_item_ids = set(item.id for item in state.items)
        
        # Adiciona dishes das receitas (podem não estar em items)
        for recipe in state.recipes:
            all_item_ids.add(recipe.parent_item_id)
        
        for item_id in all_item_ids:
            self._cache[item_id] = get_item_demand_data(state, item_id, ctx)
    
    def get_demand_stats(self, item_id: str) -> "DemandStats":
        """Retorna demand stats do cache. O(1)."""
        from .forecast import DemandStats
        
        if item_id in self._cache:
            return self._cache[item_id]
        
        # Fallback para item não cacheado (não deveria acontecer)
        return DemandStats(
            avg_daily_demand=0.0,
            max_daily_demand=0.0,
            wma_forecast=0.0,
            raw_values=[],
            n_samples=0,
        )
    
    def get_item(self, item_id: str) -> "Item | None":
        """Retorna item por ID. O(1) ao invés de O(n)."""
        return self._item_by_id.get(item_id)
    
    def get_stock(self, item_id: str) -> float:
        """Retorna estoque total por item. O(1)."""
        return self._stock_map.get(item_id, 0.0)
    
    @property
    def item_by_id(self) -> Dict[str, "Item"]:
        """Acesso direto ao dict de items."""
        return self._item_by_id
    
    @property
    def stock_map(self) -> Dict[str, float]:
        """Acesso direto ao stock map."""
        return self._stock_map
