import unittest
from unittest.mock import MagicMock
from local_api.services.financial_impact_estimator import enrich_with_financial_impact

class TestFinancialImpactEstimator(unittest.TestCase):

    def setUp(self):
        self.mock_state = MagicMock()
        self.mock_state.items = []

    def create_mock_item(self, item_id, price=0.0, cost=0.0):
        item = MagicMock()
        item.id = item_id
        item.price = price
        item.cost = cost
        return item

    def test_rupture_risk_product_with_price(self):
        # Scenario: Product (Sphere 1), Urgent, Price Present
        # Expectation: Financial Impact Calculated
        item = self.create_mock_item("prod_1", price=10.0, cost=5.0)
        self.mock_state.items = [item]

        alert = {
            "sphere": "product",
            "priority": "urgent",
            "meta": {"item_id": "prod_1", "target_stock": 20, "current_stock": 5}
        }
        
        enriched = enrich_with_financial_impact(alert, self.mock_state)
        impact = enriched.get("financial_impact")

        self.assertIsNotNone(impact)
        self.assertEqual(impact["type"], "rupture_risk")
        self.assertEqual(impact["amount"], 150.0) # 15 units * 10.00
        self.assertEqual(impact["description"], "Perda potencial de faturamento")

    def test_rupture_risk_ingredient_should_be_none(self):
        # Scenario: Ingredient (Sphere 1), Urgent
        # Expectation: NO Financial Impact (Strict Rule)
        item = self.create_mock_item("ing_1", price=0.0, cost=5.0)
        self.mock_state.items = [item]

        alert = {
            "sphere": "ingredient",
            "priority": "urgent",
            "meta": {"item_id": "ing_1", "target_stock": 20, "current_stock": 5}
        }
        
        enriched = enrich_with_financial_impact(alert, self.mock_state)
        self.assertIsNone(enriched.get("financial_impact"))

    def test_rupture_risk_product_missing_price(self):
        # Scenario: Product, Urgent, NO Price
        # Expectation: Missing Data Message
        item = self.create_mock_item("prod_no_price", price=0.0, cost=5.0)
        self.mock_state.items = [item]

        alert = {
            "sphere": "product",
            "priority": "urgent",
            "meta": {"item_id": "prod_no_price", "target_stock": 20, "current_stock": 5}
        }
        
        enriched = enrich_with_financial_impact(alert, self.mock_state)
        impact = enriched.get("financial_impact")
        
        self.assertIsNotNone(impact)
        self.assertEqual(impact["type"], "missing_data")
        self.assertEqual(impact["missing_field"], "sale_price")

    def test_waste_risk(self):
        # Scenario: Perishability, Any Priority
        # Expectation: Impact Calculated (using Cost)
        item = self.create_mock_item("perishable_1", price=10.0, cost=4.0)
        self.mock_state.items = [item]

        alert = {
            "sphere": "perishability",
            "priority": "info",
            "meta": {"item_id": "perishable_1", "waste_projected": 5}
        }
        
        enriched = enrich_with_financial_impact(alert, self.mock_state)
        impact = enriched.get("financial_impact")

        self.assertIsNotNone(impact)
        self.assertEqual(impact["type"], "waste_risk")
        self.assertEqual(impact["amount"], 20.0) # 5 * 4.0
        self.assertEqual(impact["description"], "Custo estimado de desperdício")

    def test_idle_capital(self):
        # Scenario: "Sem giro"
        # Expectation: Impact Calculated (using Cost)
        item = self.create_mock_item("dead_stock", price=20.0, cost=8.0)
        self.mock_state.items = [item]

        alert = {
            "title": "Produto sem giro há 30 dias",
            "sphere": "product",
            "priority": "info",
            "meta": {"item_id": "dead_stock", "current_stock": 10}
        }
        
        enriched = enrich_with_financial_impact(alert, self.mock_state)
        impact = enriched.get("financial_impact")

        self.assertIsNotNone(impact)
        self.assertEqual(impact["type"], "idle_capital")
        self.assertEqual(impact["amount"], 80.0) # 10 * 8.0
        self.assertEqual(impact["description"], "Capital imobilizado em estoque")

    def test_planning_alert_should_be_none(self):
        # Scenario: Planning / Suggestion (Not Urgent Rupture)
        # Expectation: NO Impact
        item = self.create_mock_item("prod_plan", price=10.0, cost=5.0)
        self.mock_state.items = [item]

        alert = {
            "sphere": "product",
            "priority": "plan", # NOT urgent
            "meta": {"item_id": "prod_plan", "to_buy": 50}
        }
        
        enriched = enrich_with_financial_impact(alert, self.mock_state)
        self.assertIsNone(enriched.get("financial_impact"))

if __name__ == '__main__':
    unittest.main()
