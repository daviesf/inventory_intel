# tests/test_business_translator.py

from local_api.services.business_translator import translate_alert

def test_translation_exact_match():
    alert = {"title": "Comprar agora – Arroz", "alert_id": "1"}
    result = translate_alert(alert)
    assert result["title_business"] == "Risco de Ruptura: Arroz"
    assert result["title_technical"] == "Comprar agora – Arroz"

def test_translation_fallback():
    alert = {"title": "Título Desconhecido", "alert_id": "2"}
    result = translate_alert(alert)
    assert result["title_business"] == "Título Desconhecido"
    assert result["title_technical"] == "Título Desconhecido"

def test_translation_vencidos():
    alert = {"title": "⚠️ 5.0 kg VENCIDOS", "alert_id": "3"}
    result = translate_alert(alert)
    # The current regex expects "PERDA SANITÁRIA CONFIRMADA: {}"
    # But let's check what our implementation does with regex
    assert "PERDA SANITÁRIA CONFIRMADA" in result["title_business"]
    assert "5.0 kg" in result["title_business"]

def test_translation_planning():
    alert = {"title": "Planejar compra – Feijão", "alert_id": "4"}
    result = translate_alert(alert)
    assert result["title_business"] == "Sugestão de Reposição: Feijão"

def test_translation_sem_giro():
    alert = {"title": "Produto sem giro – Trufas", "alert_id": "5"}
    result = translate_alert(alert)
    assert result["title_business"] == "Capital Parado (Sem Giro): Trufas"

def test_translation_producao_imediata():
    alert = {"title": "Produzir agora – Molho Tomate", "alert_id": "6"}
    result = translate_alert(alert)
    assert result["title_business"] == "Demanda Imediata (Cliente Esperando): Molho Tomate"
