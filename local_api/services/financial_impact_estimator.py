# local_api/services/financial_impact_estimator.py
"""
Service to estimate the financial impact of inventory alerts.
Calculates potential losses or waste based on current stock, demand, and item costs/prices.

Strictly conservative estimates.
"""

from typing import Dict, Any, Optional
from core.models import InventoryState

def enrich_with_financial_impact(alert_dict: Dict[str, Any], state: InventoryState) -> Dict[str, Any]:
    """
    Enriches an alert dictionary with estimated financial impact data.
    
    Args:
        alert_dict: The dictionary representation of the alert (task).
        state: The full inventory state to access item details (cost, price).
        
    Returns:
        The alert dictionary enriched with 'financial_impact' key if applicable.
    """
    
    # 1. Identify the item in the state
    # The alert_dict usually has 'meta' -> 'item_id' or we might need to find it by name if ID is missing
    # But usually 'meta' contains 'item_id'.
    
    meta = alert_dict.get("meta", {})
    item_id = meta.get("item_id")
    
    if not item_id:
        return alert_dict
        
    # Find the item in state
    # InventoryState uses a list 'items', so we need to find it.
    # Optimization: ideally this map is passed or cached, but for now we iterate or build map.
    # Given the scale (local), building a quick lookup or just searching is fine.
    item = next((i for i in state.items if i.id == item_id), None)
    
    if not item:
        return alert_dict
        
    impact = None
    
    # Extract key values safely
    cost = getattr(item, 'cost', 0.0) or 0.0
    price = getattr(item, 'price', 0.0) or 0.0
    
    # 2. Logic per Sphere/Type
    
    impact = None
    sphere = alert_dict.get("sphere")
    priority = alert_dict.get("priority")
    title = alert_dict.get("title", "").lower()
    anomaly = str(alert_dict.get("anomaly", "")).lower()

    # --- A) RUPTURA / FALTA (Profit Loss) ---
    # Rules: Urgent, Product Only (Final Sale Item). Uses SALE PRICE.
    # Excludes Ingredients.
    if sphere == "product" and priority == "urgent":
        suggestion_qty = 0
        if meta.get("to_buy"):
             suggestion_qty = meta["to_buy"]
        elif meta.get("target_stock") and meta.get("current_stock") is not None:
             suggestion_qty = max(0, meta["target_stock"] - meta["current_stock"])
             
        if price > 0:
             if suggestion_qty > 0:
                impact = {
                    "type": "rupture_risk",
                    "amount": round(suggestion_qty * price, 2),
                    "currency": "BRL",
                    "description": "Perda potencial de faturamento",
                    "reliability": "MEDIUM"
                }
        else:
            # Eligible (Product Rupture) but missing price
            impact = {"type": "missing_data", "missing_field": "sale_price"}

    # --- B) DESPERDÍCIO / PERECIBILIDADE (Cost Loss) ---
    # Rules: Any priority (Info/Urgent) in Perishability sphere. Uses PURCHASE COST.
    elif sphere in ["perishability", "perishable"]:
        qty_at_risk = meta.get("waste_projected") or meta.get("expiring_quantity") or meta.get("quantity", 0)
        
        if cost > 0:
            if qty_at_risk > 0:
                impact = {
                    "type": "waste_risk",
                    "amount": round(qty_at_risk * cost, 2),
                    "currency": "BRL",
                    "description": "Custo estimado de desperdício",
                    "reliability": "HIGH"
                }
        else:
            # Eligible but missing cost
            impact = {"type": "missing_data", "missing_field": "purchase_cost"}

    # --- C) ESTOQUE PARADO / SEM GIRO (Idle Capital) ---
    # Rules: "sem giro" or overstock. Uses PURCHASE COST.
    elif "sem giro" in title or "overstock" in anomaly:
         stock_qty = meta.get("current_stock", 0)
         if cost > 0:
             if stock_qty > 0:
                 impact = {
                     "type": "idle_capital",
                     "amount": round(stock_qty * cost, 2),
                     "currency": "BRL",
                     "description": "Capital imobilizado em estoque",
                     "reliability": "HIGH"
                 }
         else:
             # Eligible but missing cost
             impact = {"type": "missing_data", "missing_field": "purchase_cost"}

    # --- D) & E) PLANNING / INFO / INGREDIENT RUPTURE ---
    # Explicitly fall through (impact = None).
    # - Planning priorities are usually 'plan' or 'info' (except perishability).
    # - Ingredients in 'purchasing' sphere are ignored for financial impact.
    
    # --- D) DATA QUALITY (Negative Stock) ---
    # FIX [UX-001]: Estoque negativo agora gera impacto financeiro.
    elif sphere == "data_quality" and "neg_stock" in alert_dict.get("id", ""):
         current = meta.get("current_stock", 0)
         if current < 0:
             qty_missing = abs(current)
             # Se tiver cost ou price, usamos. data_quality geralmente é sério.
             # Usar Cost como conservador (custo de reposição 'fantasma' ou perda desconhecida)
             base_val = cost if cost > 0 else (price * 0.5 if price > 0 else 0)
             
             if base_val > 0:
                 impact = {
                    "type": "audit_risk",
                    "amount": round(qty_missing * base_val, 2),
                    "currency": "BRL",
                    "description": "Furo de estoque (Valor Estimado)",
                    "reliability": "LOW"
                 }
             else:
                 impact = {"type": "missing_data", "missing_field": "cost_or_price"}

    if impact:
        alert_dict["financial_impact"] = impact
        
    return alert_dict
