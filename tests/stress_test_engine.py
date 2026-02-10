
import unittest
import logging
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# Core Imports assuming the project root is in PYTHONPATH
import sys
import os
sys.path.append(os.getcwd())

from core.models import (
    Item, ItemType, ItemClass, OperationMode, StockLevel, Sale, 
    InventoryState, AnalysisContext, Dish, Recipe, AlertSphere, 
    AlertPriority, StockLot, ReliabilityLevel
)
from core.engine import analyze_inventory

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StressTest")

# --- STRESS TEST CASE ---
class TestEngineStress(unittest.TestCase):
    
    def setUp(self):
        self.now = datetime(2026, 1, 2, 12, 0)
        self.context = AnalysisContext(
            now=self.now,
            coverage_days_target_A=7,
            coverage_days_target_B=5,
            coverage_days_target_C=3,
            perishable_risk_threshold_days=2,
            forecast_window_days=30
        )
        self.items = []
        self.dishes = []
        self.recipes = []
        self.stock_levels = []
        self.lots = []
        self.sales = []
        self.today_sales = []

    def _run_analysis(self):
        state = InventoryState(
            items=self.items, dishes=self.dishes, recipes=self.recipes,
            stock_levels=self.stock_levels, sales_history=self.sales,
            today_sales=self.today_sales, lots=self.lots
        )
        return analyze_inventory(state, self.context)

    # --- HELPERS ---
    def _add_item(self, id, type=ItemType.INGREDIENT, shelf_life=10):
        self.items.append(Item(
            id=id, name=f"Item {id}", item_type=type, unit="kg",
            lead_time_days=1, shelf_life_days=shelf_life, item_class=ItemClass.A
        ))

    def _add_dish(self, id):
        self.dishes.append(Dish(id=id, name=f"Dish {id}"))
        # Add corresponding Finished Product item
        self.items.append(Item(
            id=id, name=f"Dish Item {id}", item_type=ItemType.FINISHED, 
            unit="unit", lead_time_days=0, shelf_life_days=1, item_class=ItemClass.A
        ))

    def _add_recipe(self, dish_id, ingredient_id, qty):
        self.recipes.append(Recipe(parent_item_id=dish_id, child_item_id=ingredient_id, quantity=qty))

    def _add_stock(self, item_id, qty, days_to_expire=None):
        expires = (self.now + timedelta(days=days_to_expire)).date() if days_to_expire is not None else None
        self.stock_levels.append(StockLevel(item_id=item_id, quantity=qty, expires_at=expires))

    def _add_lot(self, item_id, lot_id, qty, days_to_expire):
        expires = (self.now + timedelta(days=days_to_expire)).date()
        self.lots.append(StockLot(lot_id=lot_id, item_id=item_id, quantity=qty, expires_at=expires))

    def _add_sales(self, dish_id, qty_per_day, days_back=30):
        for i in range(1, days_back + 1):
            dt = self.now - timedelta(days=i)
            self.sales.append(Sale(dish_id=dish_id, quantity=qty_per_day, timestamp=dt))

    # --- TESTS ---

    def test_01_volume(self):
        """SCENARIO 1: High Volume (100 items, 50 dishes, deep recipes)"""
        logger.info("[TEST] Volume Stress Test")
        
        # 50 Dishes
        for i in range(50):
            dish_id = f"DISH-{i}"
            self._add_dish(dish_id)
            self._add_sales(dish_id, 10) # 10 sold/day
        
        # 100 Ingredients
        for i in range(100):
            ing_id = f"ING-{i}"
            self._add_item(ing_id, ItemType.INGREDIENT)
            self._add_stock(ing_id, 1000, days_to_expire=30)
            
        # Complex Recipes (Chain)
        for i in range(50):
            dish_id = f"DISH-{i}"
            ing_id_1 = f"ING-{i}"
            ing_id_2 = f"ING-{i+1}"
            self._add_recipe(dish_id, ing_id_1, 0.5)
            self._add_recipe(dish_id, ing_id_2, 0.2)
            
        start = datetime.now()
        alerts = self._run_analysis()
        duration = (datetime.now() - start).total_seconds()
        
        logger.info(f"Analyzed {len(self.items)} items in {duration:.4f}s. Alerts generated: {len(alerts)}")
        
        # Validations
        self.assertLess(duration, 2.0, "Analysis took too long (>2s)")

    def test_02_inconsistent_data_and_loops(self):
        """SCENARIO 2: Bad Data & BOM Loops"""
        logger.info("[TEST] Inconsistent Data & Loops")
        
        # Loop: A -> B -> A
        self._add_dish("DISH-LOOP")
        self._add_item("PREP-A", ItemType.SEMI_FINISHED)
        self._add_item("PREP-B", ItemType.SEMI_FINISHED)
        
        self._add_recipe("DISH-LOOP", "PREP-A", 1)
        self._add_recipe("PREP-A", "PREP-B", 1)
        self._add_recipe("PREP-B", "PREP-A", 1) # EVIL LOOP
        
        try:
            alerts = self._run_analysis()
            logger.info(f"Survived BOM Loop. Alerts: {len(alerts)}")
        except RecursionError:
            self.fail("BOM Loop caused RecursionError! Should be handled gracefully.")
        except Exception as e:
            logger.error(f"Unexpected error in BOM Loop: {e}")

    def test_03_perishability_conflict(self):
        """SCENARIO 3: Perishability vs Purchase Conflict"""
        logger.info("[TEST] Perishability Conflict")
        
        # Item with High Demand but Lots Expiring Soon
        item_id = "RISKY-ITEM"
        self._add_item(item_id, shelf_life=10)
        self._add_stock(item_id, 0) # Zero global stock to force purchase trigger
        
        # Add Expiring Lots specifically (Sphere 4 data)
        # Lot 1: 10 units, expires tomorrow (waste risk)
        self._add_lot(item_id, "L1", 10, days_to_expire=1) 
        # Align stock levels
        self.stock_levels[-1].quantity = 10
        self.stock_levels[-1].expires_at = (self.now + timedelta(days=1)).date()
        
        self._add_dish("DISH-RISK")
        self._add_recipe("DISH-RISK", item_id, 1)
        self._add_sales("DISH-RISK", 5) # 5/day
        
        alerts = self._run_analysis()
        
        purchases = [a for a in alerts if a.sphere == AlertSphere.INGREDIENT and a.priority == AlertPriority.URGENT]
        perish = [a for a in alerts if a.sphere == AlertSphere.PERISHABILITY]
        
        logger.info(f"Purchase alerts: {len(purchases)}")
        logger.info(f"Perishability alerts: {len(perish)}")
        
        for a in alerts:
            logger.info(f"[{a.sphere}] {a.title} - {a.message}")

    def test_04_graceful_degradation(self):
        """SCENARIO 4: Missing Batch Data"""
        logger.info("[TEST] Graceful Degradation")
        
        item_id = "NO-DATA-ITEM"
        self._add_item(item_id, shelf_life=5) 
        self._add_stock(item_id, 20) 
        # NO LOTS added.
        
        # Demand 1/day
        self._add_dish("DISH-NO-DATA")
        self._add_recipe("DISH-NO-DATA", item_id, 1)
        self._add_sales("DISH-NO-DATA", 1)
        
        alerts = self._run_analysis()
        
        waste_alerts = [a for a in alerts if a.sphere == AlertSphere.PERISHABILITY]
        logger.info(f"Degradation Alerts: {len(waste_alerts)}")
        for a in waste_alerts:
            # We expect SOME alert about potential waste if logic assumes existing stock is old?
            # Or assume stock is fresh?
            # Logic: If no lots, get normalised batches.
            # _get_normalized_batches: 
            # If stock_levels has expires_at -> use it.
            # If not, use shelf_life. 
            # If shelf_life, when was it bought? Unknown.
            # Logic typically assumes expiry = now + shelf_life * 0.5 (conservative) or just now + shelf_life.
            # If now + 5 days.
            # 20 units, 1/day -> 20 days coverage.
            # Expires in 5 days. 
            # Waste ~15 units.
            # Should alert.
            logger.info(f"[{a.reliability}] {a.title}: {a.message}")
            if a.reliability == ReliabilityLevel.HIGH:
                 self.fail("Should not be HIGH reliability without lots")

    # --- HELPERS ---
    def _add_item(self, id, type=ItemType.INGREDIENT, shelf_life=10):
        self.items.append(Item(
            id=id, name=f"Item {id}", item_type=type, unit="kg",
            lead_time_days=1, shelf_life_days=shelf_life, item_class=ItemClass.A
        ))

    def _add_dish(self, id):
        self.dishes.append(Dish(id=id, name=f"Dish {id}"))
        # Add corresponding Finished Product item
        self.items.append(Item(
            id=id, name=f"Dish Item {id}", item_type=ItemType.FINISHED, 
            unit="unit", lead_time_days=0, shelf_life_days=1, item_class=ItemClass.A
        ))

    def _add_recipe(self, dish_id, ingredient_id, qty):
        self.recipes.append(Recipe(parent_item_id=dish_id, child_item_id=ingredient_id, quantity=qty))

    def _add_stock(self, item_id, qty, days_to_expire=None):
        expires = (self.now + timedelta(days=days_to_expire)).date() if days_to_expire is not None else None
        self.stock_levels.append(StockLevel(item_id=item_id, quantity=qty, expires_at=expires))

    def _add_lot(self, item_id, lot_id, qty, days_to_expire):
        expires = (self.now + timedelta(days=days_to_expire)).date()
        self.lots.append(StockLot(lot_id=lot_id, item_id=item_id, quantity=qty, expires_at=expires))

    def _add_sales(self, dish_id, qty_per_day, days_back=30):
        for i in range(1, days_back + 1):
            dt = self.now - timedelta(days=i)
            self.sales.append(Sale(dish_id=dish_id, quantity=qty_per_day, timestamp=dt))

    # --- TESTS ---

    def test_01_volume(self):
        """SCENARIO 1: High Volume (100 items, 50 dishes, deep recipes)"""
        logger.info("[TEST] Volume Stress Test")
        
        # 50 Dishes
        for i in range(50):
            dish_id = f"DISH-{i}"
            self._add_dish(dish_id)
            self._add_sales(dish_id, 10) # 10 sold/day
        
        # 100 Ingredients
        for i in range(100):
            ing_id = f"ING-{i}"
            self._add_item(ing_id, ItemType.INGREDIENT)
            self._add_stock(ing_id, 1000, days_to_expire=30)
            
        # Complex Recipes (Chain)
        # Dish-0 needs Ing-0
        # Dish-1 needs Ing-0 and Ing-1
        # ...
        for i in range(50):
            dish_id = f"DISH-{i}"
            ing_id_1 = f"ING-{i}"
            ing_id_2 = f"ING-{i+1}"
            self._add_recipe(dish_id, ing_id_1, 0.5)
            self._add_recipe(dish_id, ing_id_2, 0.2)
            
        engine = None # Not used
        
        start = datetime.now()
        alerts = self._run_analysis()
        duration = (datetime.now() - start).total_seconds()
        
        logger.info(f"Analyzed 150 items in {duration:.4f}s. Alerts generated: {len(alerts)}")
        
        # Validations
        self.assertLess(duration, 2.0, "Analysis took too long (>2s)")
        # Expect alerts for low stock if purchase needed? 
        # With 1000 stock and ~5-15 daily demand (10 * 0.5 + ...), coverage is ~60-200 days. 
        # Should be safe. No PURCHASE alerts expected unless coverage target > stock.
        
    def test_02_inconsistent_data_and_loops(self):
        """SCENARIO 2: Bad Data & BOM Loops"""
        logger.info("[TEST] Inconsistent Data & Loops")
        
        # Loop: A -> B -> A
        self._add_dish("DISH-LOOP")
        self._add_item("PREP-A", ItemType.SEMI_FINISHED)
        self._add_item("PREP-B", ItemType.SEMI_FINISHED)
        
        self._add_recipe("DISH-LOOP", "PREP-A", 1)
        self._add_recipe("PREP-A", "PREP-B", 1)
        self._add_recipe("PREP-B", "PREP-A", 1) # EVIL LOOP
        
        try:
            alerts = self._run_analysis()
            # If we survive, we check for stack overflow or max recursion errors handled
            logger.info(f"Survived BOM Loop. Alerts: {len(alerts)}")
        except RecursionError:
            self.fail("BOM Loop caused RecursionError! Should be handled gracefully.")
        except Exception as e:
            logger.error(f"Unexpected error in BOM Loop: {e}")
            # Depending on implementation, it might raise InventoryEngineError or just log and ignore
            # We want graceful degradation.

    def test_03_perishability_conflict(self):
        """SCENARIO 3: Perishability vs Purchase Conflict"""
        logger.info("[TEST] Perishability Conflict")
        
        # Item with High Demand but Lots Expiring Soon
        item_id = "RISKY-ITEM"
        self._add_item(item_id, shelf_life=10)
        self._add_stock(item_id, 0) # Zero global stock to force purchase trigger
        
        # Add Expiring Lots specifically (Sphere 4 data)
        # Lot 1: 10 units, expires tomorrow (waste risk)
        self._add_lot(item_id, "L1", 10, days_to_expire=1) 
        # Note: Global stock is 0 in stock_levels? 
        # Engine behavior: stock_levels is authoritative for qty. Lots are consultative. 
        # If stock_levels says 0, we have 0. Lots might be ghost data.
        # Let's align them: stock_levels has 10.
        self.stock_levels[-1].quantity = 10
        self.stock_levels[-1].expires_at = (self.now + timedelta(days=1)).date()
        
        # Demand: 5/day. 
        # Coverage: 2 days (10 units / 5/day). Target: 7 days.
        # Sphere 2 says: BUY MORE (need ~35 units).
        # Sphere 4 says: 10 units expiring in 1 day. consumption 5/day. 
        #   Day 1: consume 5. Remainder 5. Expire 5. Waste 5.
        #   Buying more helps? If we buy fresh, we might use fresh instead of old? FEFO says no.
        #   Trigger: "Purchase Aggravates Waste"? 
        #   If we buy 30 units (fresh), total 40. Demand 5.
        #   Waste is still 5 from L1. Does buying fresh INCREASE waste? No.
        #   Unless storage limit? We don't model storage limit.
        
        # Let's create a scenario where buying increases waste? 
        # Perhaps if demand was low?
        
        self._add_dish("DISH-RISK")
        self._add_recipe("DISH-RISK", item_id, 1)
        self._add_sales("DISH-RISK", 5) # 5/day
        
        alerts = self._run_analysis()
        
        purchases = [a for a in alerts if a.sphere == AlertSphere.INGREDIENT and a.priority == AlertPriority.URGENT]
        perish = [a for a in alerts if a.sphere == AlertSphere.PERISHABILITY]
        
        logger.info(f"Purchase alerts: {len(purchases)}")
        logger.info(f"Perishability alerts: {len(perish)}")
        
        # Iterate and print titles
        for a in alerts:
            logger.info(f"[{a.sphere}] {a.title} - {a.message}")

    def test_04_graceful_degradation(self):
        """SCENARIO 4: Missing Batch Data"""
        logger.info("[TEST] Graceful Degradation")
        
        item_id = "NO-DATA-ITEM"
        self._add_item(item_id, shelf_life=5) # 5 days shelf life
        self._add_stock(item_id, 20) # 20 units
        # NO LOTS added.
        # NO EXPIRES_AT in stock level.
        
        # Demand 1/day from sales
        self._add_dish("DISH-NO-DATA")
        self._add_recipe("DISH-NO-DATA", item_id, 1)
        self._add_sales("DISH-NO-DATA", 1)
        
        alerts = self._run_analysis()
        
        # Core checks: 
        # Sphere 4 should try to estimate waste.
        # 20 units, 1/day -> 20 days coverage.
        # Shelf life 5 days.
        # "Estimated" start date? Assume 50% shelf life? 2.5 days left?
        # If 2.5 days left, we waste units after day 3.
        # Should generate LOW reliability waste alert.
        
        waste_alerts = [a for a in alerts if a.sphere == AlertSphere.PERISHABILITY]
        logger.info(f"Degradation Alerts: {len(waste_alerts)}")
        for a in waste_alerts:
            logger.info(f"[{a.reliability}] {a.title}: {a.message}")
            self.assertNotEqual(a.reliability, ReliabilityLevel.HIGH, "Should not be HIGH reliability without lots")

if __name__ == '__main__':
    unittest.main()
