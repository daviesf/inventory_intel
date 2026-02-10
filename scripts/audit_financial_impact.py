import sys
import unittest
from unittest.mock import MagicMock
from local_api.services.financial_impact_estimator import enrich_with_financial_impact

def run_audit():
    print("="*60)
    print("AUDITORIA DE IMPACTO FINANCEIRO - INTELLISTOCK")
    print("="*60)
    
    mock_item = MagicMock()
    mock_item.id = "audit_item"
    mock_item.price = 20.0  # Sale Price
    mock_item.cost = 10.0   # Purchase Cost
    
    mock_state = MagicMock()
    mock_state.items = [mock_item]
    
    scenarios = [
        {
            "name": "A) RUPTURA - PRODUTO FINAL (Com Preço)",
            "alert": {"sphere": "product", "priority": "urgent", "meta": {"item_id": "audit_item", "target_stock": 10, "current_stock": 0}},
            "expect": "SHOW",
            "type": "rupture_risk",
            "val_check": 200.0 # 10 * 20.0
        },
        {
            "name": "B) RUPTURA - INGREDIENTE (Com Preço/Custo)",
            "alert": {"sphere": "ingredient", "priority": "urgent", "meta": {"item_id": "audit_item", "target_stock": 10, "current_stock": 0}},
            "expect": "NONE",
        },
        {
            "name": "C) DESPERDÍCIO (Perecível)",
            "alert": {"sphere": "perishability", "priority": "urgent", "meta": {"item_id": "audit_item", "waste_projected": 5}},
            "expect": "SHOW",
            "type": "waste_risk",
            "val_check": 50.0 # 5 * 10.0 (Cost)
        },
        {
            "name": "D) CAPITAL PARADO (Sem Giro)",
            "alert": {"title": "Produto sem giro", "sphere": "product", "priority": "info", "meta": {"item_id": "audit_item", "current_stock": 10}},
            "expect": "SHOW",
            "type": "idle_capital",
            "val_check": 100.0 # 10 * 10.0 (Cost)
        },
        {
            "name": "E) PLANEJAMENTO / SUGESTÃO",
            "alert": {"sphere": "product", "priority": "plan", "meta": {"item_id": "audit_item", "to_buy": 50}},
            "expect": "NONE",
        },
        {
            "name": "F) RUPTURA - PRODUTO (Sem Preço -> Missing Data)",
            "setup_override": lambda i: setattr(i, 'price', 0.0),
            "alert": {"sphere": "product", "priority": "urgent", "meta": {"item_id": "audit_item", "target_stock": 10, "current_stock": 0}},
            "expect": "MISSING_DATA",
        },
    ]

    all_passed = True

    for s in scenarios:
        # Reset Item
        mock_item.price = 20.0
        mock_item.cost = 10.0
        if "setup_override" in s:
            s["setup_override"](mock_item)
            
        enriched = enrich_with_financial_impact(s["alert"], mock_state)
        impact = enriched.get("financial_impact")
        
        status = "FAIL"
        
        if s["expect"] == "NONE":
            success = (impact is None)
            display = "NENHUM"
        elif s["expect"] == "MISSING_DATA":
            success = (impact is not None and impact["type"] == "missing_data")
            display = "MENSAGEM AVISO"
        else:
            success = (impact is not None and impact["type"] == s["type"] and impact["amount"] == s["val_check"])
            display = f"{impact['type']} | R$ {impact.get('amount')}" if impact else "None"

        if success:
            status = "PASS"
        else:
            all_passed = False
            
        print(f"[{status}] {s['name']}")
        print(f"      Esperado: {s['expect']} -> Obtido: {display}")
        print("-" * 40)

    if all_passed:
        print("\n✅ AUDITORIA CONCLUÍDA: TODOS OS CENÁRIOS FORAM VALIDADOS.")
    else:
        print("\n❌ FALHA NA AUDITORIA.")

if __name__ == "__main__":
    run_audit()
