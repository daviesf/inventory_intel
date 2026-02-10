# core/perishability.py
from __future__ import annotations

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from .models import (
    InventoryState,
    AnalysisContext,
    Alert,
    AlertSphere,
    AlertPersona,
    AlertPriority,
    ReliabilityLevel,
    ItemType,
    StockLot,
)
from .demand_cache import DemandCache


@dataclass
class VirtualBatch:
    """Representação normalizada de um lote para simulação."""
    quantity: float
    expires_at: date
    source: str  # 'real_lot', 'stock_level', 'estimated', 'virtual_purchase'


def analyze_perishability_sphere(
    state: InventoryState,
    ctx: AnalysisContext,
    cache: DemandCache,
    generated_alerts: List[Alert],
) -> List[Alert]:
    """
    ESFERA 4: Perecibilidade Inteligente (FEFO Real).
    
    Analisa risco de desperdício usando lotes (se disponíveis) ou estimativas.
    """
    alerts: List[Alert] = []
    
    # 1. Mapear compras sugeridas
    purchase_suggestions: Dict[str, Alert] = {}
    for alert in generated_alerts:
        if alert.sphere in [AlertSphere.PRODUCT, AlertSphere.INGREDIENT] and "buy" in alert.id:
            item_id = alert.data.get("item_id")
            if item_id:
                purchase_suggestions[item_id] = alert

    today = ctx.now.date()

    # 2. Analisar cada item
    for item in state.items:
        # Pular itens sem validade relevante (ex: embalagens s/ validade cadastrada)
        # Assumiremos que se shelf_life_days for None ou 0, não é perecível crítico ou não geramos alerta
        if not item.shelf_life_days:
            continue

        stats = cache.get_demand_stats(item.id)
        avg_demand = stats.avg_daily_demand
        
        # Obter lotes normalizados (Degradação Graciosa)
        batches, reliability = _get_normalized_batches(state, item.id, today, item.shelf_life_days)
        
        if not batches:
            continue
            
        total_stock = sum(b.quantity for b in batches)
        if total_stock <= 0:
            continue

        # 3. Detectar VENCIDOS (Expired)
        expired_qty = sum(b.quantity for b in batches if b.expires_at < today)
        if expired_qty > 0:
            alerts.append(Alert(
                id=f"perishability_expired_{item.id}",
                sphere=AlertSphere.PERISHABILITY,
                persona=AlertPersona.MANAGEMENT,
                priority=AlertPriority.URGENT, # Sanitário
                title=f"⚠️ {expired_qty:.0f} {item.unit} VENCIDOS",
                message=f"Produto vencido em estoque ({reliability.value} confidence). Descartar.",
                created_at=ctx.now,
                reliability=ReliabilityLevel.HIGH if reliability == ReliabilityLevel.HIGH else ReliabilityLevel.MEDIUM,
                data={
                    "item_id": item.id,
                    "quantity_expired": expired_qty,
                    "action": "discard",
                    "data_source": reliability.value
                }
            ))

        # 4. Simulação FEFO (Baseline)
        # Filtra vencidos para simulação futura
        valid_batches = [b for b in batches if b.expires_at >= today]
        if not valid_batches:
             continue # Tudo vencido, já alertado

        waste_baseline, days_to_waste = _simulate_fefo_consumption(valid_batches, avg_demand, today)
        
        days_of_coverage = total_stock / avg_demand if avg_demand > 0 else 999.0

        # Alerta de Risco Futuro (sem considerar compra ainda)
        if waste_baseline > 0:
             # Só alerta se o desperdício for relevante (> 1 unidade ou > 5% do estoque)
             if waste_baseline > 1.0 or (waste_baseline / total_stock) > 0.05:
                 alerts.append(Alert(
                    id=f"perishability_risk_stock_{item.id}",
                    sphere=AlertSphere.PERISHABILITY,
                    persona=AlertPersona.MANAGEMENT,
                    priority=AlertPriority.INFO,
                    title=f"Risco de vencimento – {item.name}",
                    message=f"O estoque atual duraria {days_of_coverage:.1f} dias, mas {waste_baseline:.1f} {item.unit} devem vencer antes do consumo.",
                    created_at=ctx.now,
                    reliability=reliability,
                    data={
                        "item_id": item.id,
                        "waste_projected": waste_baseline,
                        "days_until_first_waste": days_to_waste,
                        "action": "promote_consumption"
                    }
                ))

        # 5. Impacto da Compra Sugerida
        if item.id in purchase_suggestions:
            buy_alert = purchase_suggestions[item.id]
            to_buy = buy_alert.data.get("to_buy", 0.0)
            
            if to_buy > 0:
                # Criar lote virtual de compra
                # Validade = Hoje + Shelf Life
                virtual_expiry = today + timedelta(days=int(item.shelf_life_days))
                virtual_batch = VirtualBatch(
                    quantity=to_buy,
                    expires_at=virtual_expiry,
                    source='virtual_purchase'
                )
                
                # Simular com o novo lote
                simulation_batches = valid_batches + [virtual_batch]
                waste_new, _ = _simulate_fefo_consumption(simulation_batches, avg_demand, today)
                
                waste_increase = waste_new - waste_baseline
                
                # Se a compra aumenta o desperdício significativamente
                if waste_increase > 1.0: # Threshold mínimo
                     msg = (
                        f"Risco de desperdício: Comprar {to_buy:.0f} {item.unit} "
                        f"pode gerar {waste_increase:.1f} {item.unit} de perda futura."
                    )
                     alerts.append(Alert(
                        id=f"perishability_impact_buy_{item.id}",
                        sphere=AlertSphere.PERISHABILITY,
                        persona=AlertPersona.MANAGEMENT,
                        priority=AlertPriority.PLAN,
                        title=f"⚠️ Compra agrava desperdício – {item.name}",
                        message=msg,
                        created_at=ctx.now,
                        reliability=reliability,
                        data={
                            "item_id": item.id,
                            "waste_increase": waste_increase,
                            "suggestion": "Avalie reduzir volume ou postergar"
                        }
                    ))

    return alerts


def _get_normalized_batches(
    state: InventoryState, 
    item_id: str, 
    today: date,
    shelf_life: float
) -> Tuple[List[VirtualBatch], ReliabilityLevel]:
    """
    Retorna lista de lotes normalizada (VirtualBatch) e nível de confiabilidade.
    Prioridade: State.lots -> StockLevels com exp -> Estimativa (Fallback)
    """
    # 1. Tentar Lotes Reais (High Fidelity)
    item_lots = [l for l in state.lots if l.item_id == item_id]
    if item_lots:
        batches = [
            VirtualBatch(l.quantity, l.expires_at, 'real_lot')
            for l in item_lots
        ]
        return batches, ReliabilityLevel.HIGH
    
    # 2. Tentar StockLevels com validade (Medium Fidelity)
    item_stock_levels = [sl for sl in state.stock_levels if sl.item_id == item_id]
    
    # Se algum stock level tiver data de validade, usamos
    levels_with_expiry = [
        sl for sl in item_stock_levels 
        if sl.expires_at is not None
    ]
    
    if levels_with_expiry:
        batches = []
        for sl in levels_with_expiry:
             exp = sl.expires_at.date() if isinstance(sl.expires_at, datetime) else sl.expires_at
             batches.append(VirtualBatch(sl.quantity, exp, 'stock_level'))
        
        # Adiciona também os sem validade como "estimados"? 
        # Risco: Misturar dados. Melhor: se tem validade parcial, assume o resto com shelf life "novo"?
        # Simplificação Canônica: Usa o que tem validade. O resto assume validade "longa" ou "estimada".
        # Vamos assumir validade estimada para os sem data para não ignorar estoque.
        levels_no_expiry = [sl for sl in item_stock_levels if sl.expires_at is None]
        if levels_no_expiry:
             qty_no_exp = sum(sl.quantity for sl in levels_no_expiry)
             # Estimativa conservadora: validade média (50% do shelf life?) ou item novo?
             # Vamos assumir item novo (shelf_life total) a partir de hoje.
             est_exp = today + timedelta(days=int(shelf_life))
             batches.append(VirtualBatch(qty_no_exp, est_exp, 'estimated_mixed'))
             
        return batches, ReliabilityLevel.MEDIUM

    # 3. Fallback Total (Low Fidelity)
    total_qty = sum(sl.quantity for sl in item_stock_levels)
    if total_qty > 0:
        # Assume que todo o estoque tem validade de (Hoje + 50% do Shelf Life)
        # Por que 50%? Média estatística de estoque em andamento.
        est_days = max(1, int(shelf_life * 0.5))
        est_exp = today + timedelta(days=est_days)
        return [VirtualBatch(total_qty, est_exp, 'estimated_fallback')], ReliabilityLevel.LOW

    return [], ReliabilityLevel.LOW


def _simulate_fefo_consumption(
    batches: List[VirtualBatch], 
    daily_demand: float,
    today: date
) -> Tuple[float, int]:
    """
    Simula consumo FEFO dia a dia.
    Retorna (total_waste, days_until_first_waste).
    """
    if daily_demand <= 0:
        # Se não há demanda, TUDO vai vencer (a menos que validade seja infinita, mas assumimos perecíveis)
        # Retorna soma total como waste
        total = sum(b.quantity for b in batches)
        # Dias até primeiro vencimento
        if not batches: return 0.0, 999
        sorted_batches = sorted(batches, key=lambda b: b.expires_at)
        first_waste_days = (sorted_batches[0].expires_at - today).days
        return total, max(0, first_waste_days)

    # Clonar lotes para não alterar originais (simulação)
    # Precisamos ser cuidadosos com performance aqui se forem muitos dias.
    # Mas estoque geralmente gira em 30-90 dias. Loop diário é aceitável.
    
    # Ordenar FEFO
    sim_batches = sorted([
        VirtualBatch(b.quantity, b.expires_at, b.source) 
        for b in batches
    ], key=lambda b: b.expires_at)
    
    total_waste = 0.0
    first_waste_day_offset = 999
    
    # O horizonte de simulação precisa ir até o último lote vencer ou acabar o estoque
    if not sim_batches:
        return 0.0, 999
        
    last_expiry = sim_batches[-1].expires_at
    max_days = (last_expiry - today).days + 1
    
    # Otimização: Se max_days for muito grande (ex: 2 anos), limitar a 365 dias
    max_days = min(max_days, 365)
    
    current_day_offset = 0
    
    while sim_batches and current_day_offset <= max_days:
        # Demanda do dia
        demand_remaining = daily_demand
        
        # Verificar vencimentos do dia (Início do dia: remove vencidos ONTEM/HOJE que não foram consumidos)
        # Regra: Consumo acontece durante o dia. Vencimento acontece ao final do dia (ou inicio do próximo).
        # Vamos assumir: Se expires_at == today, ainda pode consumir Hoje?
        # Geralmente validade é "até dia X inclusivo". Então vence amanhã (day + 1).
        # Vamos checar batches que expiraram (expires_at < today + offset)
        
        # Melhor abordagem:
        # 1. Consumir
        # 2. Checkar expiração dos sobrando
        
        current_date = today + timedelta(days=current_day_offset)
        
        # Tentar satisfazer demanda com lotes válidos
        # Lotes válidos: expires_at >= current_date
        
        # Precisamos iterar sobre batches e consumir
        # batches já estão ordenados por expiry
        
        # Remover lotes já exauridos (qty <= 0) - limpeza prévia
        sim_batches = [b for b in sim_batches if b.quantity > 0.001]
        
        # Verificar waste ANTES do consumo? (Se já venceu ontem)
        # Se expires_at < current_date -> WASTE
        active_batches = []
        for b in sim_batches:
            if b.expires_at < current_date:
                total_waste += b.quantity
                if first_waste_day_offset == 999:
                    first_waste_day_offset = current_day_offset
                # b.quantity = 0 # Mark as wasted (nao adiciona em active)
            else:
                active_batches.append(b)
        
        sim_batches = active_batches
        if not sim_batches:
            break
            
        # Consumir (FEFO)
        for b in sim_batches:
            if demand_remaining <= 0:
                break
            
            # Consumir deste lote
            consumed = min(b.quantity, demand_remaining)
            b.quantity -= consumed
            demand_remaining -= consumed
            
        current_day_offset += 1
        
    # Se sobrou algo após max loop (ex: itens com shelf life > 1 ano), não é waste por enquanto.
    
    return total_waste, first_waste_day_offset
