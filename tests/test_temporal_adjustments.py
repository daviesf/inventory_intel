import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import date
from core.models import InventoryState, DowFactor, MonthFactor, Event, BridgeRule, PaydayRule, TemporalBreakdown
from core.temporal_adjustments import (
    compute_dow_factor, compute_month_factor, get_event_on_date,
    compute_bridge_factor, compute_payday_factor, apply_temporal_adjustments
)

class TestTemporalAdjustments(unittest.TestCase):
    def setUp(self):
        self.state = InventoryState(
            items=[], dishes=[], recipes=[], stock_levels=[], sales_history=[], today_sales=[],
            dow_factors={
                "item1": {
                    0: 1.1, # Mon
                    1: 0.9, # Tue
                    4: 1.5  # Fri
                }
            },
            month_factors={
                "item1": {
                    1: 0.8, # Jan
                    12: 1.2 # Dec
                }
            },
            events=[
                Event(id=1, name="Natal", date=date(2025, 12, 25), factor=2.0),
                Event(id=2, name="Feriado Fraco", date=date(2025, 5, 1), factor=0.5)
            ],
            bridge_rules=[
                BridgeRule(id=1, name="Ponte Padrão", multiplier=0.5, lookback_days=True, enabled=True)
            ],
            payday_rules=[
                PaydayRule(id=1, name="Quinto Dia Útil", day_of_month=None, rule_type="fifth_business_day", multiplier=1.1, enabled=True),
                PaydayRule(id=2, name="Dia 20", day_of_month=20, rule_type="fixed_day", multiplier=1.05, enabled=True)
            ]
        )

    def test_dow_factor(self):
        # Mon
        self.assertEqual(compute_dow_factor("item1", date(2025, 1, 6), self.state), 1.1)
        # Tue
        self.assertEqual(compute_dow_factor("item1", date(2025, 1, 7), self.state), 0.9)
        # Wed (Default)
        self.assertEqual(compute_dow_factor("item1", date(2025, 1, 8), self.state), 1.0)
        # Unknown item
        self.assertEqual(compute_dow_factor("itemX", date(2025, 1, 6), self.state), 1.0)

    def test_month_factor(self):
        # Jan
        self.assertEqual(compute_month_factor("item1", date(2025, 1, 15), self.state), 0.8)
        # Dec
        self.assertEqual(compute_month_factor("item1", date(2025, 12, 10), self.state), 1.2)
        # Feb (Default)
        self.assertEqual(compute_month_factor("item1", date(2025, 2, 10), self.state), 1.0)

    def test_get_event(self):
        evt = get_event_on_date(date(2025, 12, 25), self.state.events)
        self.assertIsNotNone(evt)
        self.assertEqual(evt.name, "Natal")
        self.assertEqual(evt.factor, 2.0)
        
        self.assertIsNone(get_event_on_date(date(2025, 1, 1), self.state.events))

    def test_bridge_factor(self):
        # 2025-12-25 is Event (2.0)
        # 2025-12-24 is Bridge Day (Previous) because lookback=True
        # Formula: 1 + (Event.factor - 1) * BridgeMult
        # 1 + (2.0 - 1) * 0.5 = 1.5
        
        # Check 24th (Wednesday)
        f_prev = compute_bridge_factor(date(2025, 12, 24), self.state.events, self.state.bridge_rules)
        self.assertEqual(f_prev, 1.5)
        
        # Check 26th (Friday) - Next Day
        f_next = compute_bridge_factor(date(2025, 12, 26), self.state.events, self.state.bridge_rules)
        self.assertEqual(f_next, 1.5)
        
        # Check 23rd (No bridge)
        self.assertEqual(compute_bridge_factor(date(2025, 12, 23), self.state.events, self.state.bridge_rules), 1.0)

    def test_payday_factor(self):
        # Fixed Day 20
        # Only pass the fixed day rule (index 1) to ensure it's evaluated
        self.assertEqual(compute_payday_factor(date(2025, 1, 20), [self.state.payday_rules[1]]), 1.05)
        
        # Fifth Local Business Day of Jan 2025
        # Pass only the 5th BD rule (index 0)
        # Assuming simple Mon-Fri business days, Jan 1 is Wed.
        # Jan 1 (Wed) - 1, Jan 2 (Thu) - 2, Jan 3 (Fri) - 3, Jan 6 (Mon) - 4, Jan 7 (Tue) - 5
        self.assertEqual(compute_payday_factor(date(2025, 1, 7), [self.state.payday_rules[0]]), 1.1)
        
        # Other day - check valid rule but wrong day
        self.assertEqual(compute_payday_factor(date(2025, 1, 10), [self.state.payday_rules[0]]), 1.0)

    def test_apply_temporal_adjustments(self):
        # Test combination for Item1 on Dec 24, 2025 (Wed)
        # Base = 100
        # DOW (Wed) = 1.0 (Default for item1 is 1.0 on Wed)
        # Month (Dec) = 1.2
        # Event = None (Dec 24 is not event)
        # Bridge = 1.5 (Bridge to Natal)
        # Payday = 1.0 (Not payday)
        
        # Total = 100 * 1.0 * 1.2 * 1.5 * 1.0 = 180
        
        res = apply_temporal_adjustments("item1", date(2025, 12, 24), 100.0, self.state)
        self.assertAlmostEqual(res.forecast_final, 180.0, delta=0.1)
        self.assertAlmostEqual(res.total_factor, 1.8, delta=0.001)
        self.assertTrue(len(res.components) > 0)

    def test_clamping(self):
        # Test crazy factors
        # Force mock
        self.state.dow_factors["item1"][2] = 10.0 # Wed
        
        res = apply_temporal_adjustments("item1", date(2025, 1, 8), 100.0, self.state)
        # 10.0 * 0.8 (Jan) = 8.0. Clamped to 3.0
        self.assertAlmostEqual(res.total_factor, 3.0, delta=0.001)
        self.assertAlmostEqual(res.forecast_final, 300.0, delta=0.1)

if __name__ == "__main__":
    unittest.main()
