# core/repository_sqlalchemy.py

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple, List, Optional
from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert
from infra.db import SessionLocal
from infra.orm_models import ItemORM, StockLevelORM, SaleORM, DishORM, RecipeORM, AlertSuppressionORM, EngineConfigORM, \
    AlertHistoryORM
from core.models import Item, ItemType, ItemClass, OperationMode, StockLevel, Sale, InventoryState, AnalysisContext, \
    Dish, Recipe


@dataclass
class SqlAlchemyInventoryRepository:
    def load_inventory_state(self, now: datetime | None = None) -> Tuple[InventoryState, AnalysisContext]:
        if now is None: now = datetime.now()
        with SessionLocal() as session:
            items = self._load_items(session)
            stock_levels = self._load_stock_levels(session)
            sales = self._load_sales(session, now)
            dishes = self._load_dishes(session)
            recipes = self._load_recipes(session)
            today_sales = self._load_today_sales(session, now)
            suppressions = self._load_suppressions(session, now)
            engine_cfg = self._load_engine_config(session)
            alert_hist = self._load_alert_history(session)

        state = InventoryState(
            items=items, dishes=dishes, recipes=recipes, stock_levels=stock_levels,
            sales_history=sales, today_sales=today_sales, suppressed_alerts=suppressions,
            alert_history=alert_hist
        )
        ctx = AnalysisContext(
            now=now,
            coverage_days_target_A=engine_cfg.coverage_days_target_A,
            coverage_days_target_B=engine_cfg.coverage_days_target_B,
            coverage_days_target_C=engine_cfg.coverage_days_target_C,
            perishable_risk_threshold_days=engine_cfg.perishable_risk_threshold_days,
            forecast_window_days=engine_cfg.forecast_window_days,
        )
        ctx.profile = engine_cfg.profile
        ctx.supplier_variability_finished = engine_cfg.supplier_variability_finished
        ctx.supplier_variability_ingredient = engine_cfg.supplier_variability_ingredient
        return state, ctx

    def suppress_alert(self, alert_id: str, until: Optional[datetime]):
        with SessionLocal() as session:
            stmt = insert(AlertSuppressionORM).values(alert_id=alert_id, suppress_until=until,
                                                      created_at=datetime.now()).on_conflict_do_update(
                index_elements=['alert_id'], set_=dict(suppress_until=until, created_at=datetime.now()))
            session.execute(stmt)
            session.commit()

    def remove_suppression(self, alert_id: str):
        with SessionLocal() as session:
            stmt = delete(AlertSuppressionORM).where(AlertSuppressionORM.alert_id == alert_id)
            session.execute(stmt)
            session.commit()

    def sync_alert_history(self, current_alert_ids: List[str]):
        """Atualiza a tabela de histórico: insere novos, atualiza last_seen dos existentes."""
        now = datetime.now()
        with SessionLocal() as session:
            for aid in current_alert_ids:
                stmt = insert(AlertHistoryORM).values(alert_id=aid, first_seen_at=now,
                                                      last_seen_at=now).on_conflict_do_update(
                    index_elements=['alert_id'], set_=dict(last_seen_at=now))
                session.execute(stmt)
            session.commit()

    def update_manual_stock(self, item_id: str, quantity: float):
        """Atualiza o estoque manualmente e seta updated_at para AGORA."""
        now = datetime.now()
        with SessionLocal() as session:
            # Estratégia simplificada: Apaga anteriores desse item e insere um novo consolidado
            # Em produção real usaria lotes, mas para MVP manual isso resolve o conflito
            session.query(StockLevelORM).where(StockLevelORM.item_id == item_id).delete()
            session.add(StockLevelORM(item_id=item_id, quantity=quantity, updated_at=now))

            # Atualiza também o last_audit_date do Item para calcular confiabilidade
            item = session.get(ItemORM, item_id)
            if item:
                item.last_audit_date = now.date()

            session.commit()

    # --- Loaders ---
    def _load_items(self, session) -> List[Item]:
        return [Item(id=r.id, name=r.name, item_type=ItemType(r.item_type), unit=r.unit,
                     lead_time_days=float(r.lead_time_days),
                     shelf_life_days=float(r.shelf_life_days) if r.shelf_life_days else None,
                     item_class=ItemClass(r.item_class), operation_mode=OperationMode(r.operation_mode),
                     last_audit_date=r.last_audit_date) for r in session.scalars(select(ItemORM)).all()]

    def _load_stock_levels(self, session) -> List[StockLevel]:
        return [StockLevel(item_id=r.item_id, quantity=float(r.quantity), lot_id=r.lot_id, expires_at=r.expires_at,
                           updated_at=r.updated_at) for r in session.scalars(select(StockLevelORM)).all()]

    def _load_sales(self, session, now: datetime, days: int = 90) -> List[Sale]:
        cutoff = now - timedelta(days=days)
        return [Sale(dish_id=r.dish_id, quantity=float(r.quantity), timestamp=r.timestamp) for r in
                session.scalars(select(SaleORM).where(SaleORM.timestamp >= cutoff)).all()]

    def _load_dishes(self, session) -> list[Dish]:
        return [Dish(id=r.id, name=r.name, prep_time_min=r.prep_time_min, pre_prep_time_min=r.pre_prep_time_min) for r
                in session.scalars(select(DishORM)).all()]

    def _load_recipes(self, session) -> list[Recipe]:
        return [Recipe(parent_item_id=r.parent_item_id, child_item_id=r.child_item_id, quantity=r.quantity) for r in
                session.scalars(select(RecipeORM)).all()]

    def _load_today_sales(self, session, now: datetime) -> list[Sale]:
        today = now.date()
        return [Sale(dish_id=r.dish_id, quantity=float(r.quantity), timestamp=r.timestamp) for r in session.scalars(
            select(SaleORM).where(SaleORM.timestamp >= datetime.combine(today, datetime.min.time())).where(
                SaleORM.timestamp <= datetime.combine(today, datetime.max.time()))).all()]

    def _load_suppressions(self, session, now: datetime) -> dict[str, Optional[datetime]]:
        rows = session.scalars(select(AlertSuppressionORM).where(
            (AlertSuppressionORM.suppress_until == None) | (AlertSuppressionORM.suppress_until > now))).all()
        return {r.alert_id: r.suppress_until for r in rows}

    def _load_engine_config(self, session) -> EngineConfigORM:
        cfg = session.get(EngineConfigORM, 1)
        if cfg is None:
            cfg = EngineConfigORM(id=1)
            session.add(cfg)
            session.commit()
            session.refresh(cfg)
        return cfg

    def _load_alert_history(self, session) -> dict[str, datetime]:
        rows = session.scalars(select(AlertHistoryORM)).all()
        return {r.alert_id: r.first_seen_at for r in rows}
