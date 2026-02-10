# local_api/services/business_translator.py
"""
Serviço de Tradução de Linguagem Comercial.

Responsável por converter termos técnicos do sistema (ex: "Forecast")
em linguagem de negócio (ex: "Demanda Prevista") na camada de apresentação.
"""

from __future__ import annotations
from typing import Dict, Any
import re

# Dicionário de Mapeamento de Títulos
# Chave: Padrão Regex ou String exata (Técnico)
# Valor: Template de Negócio (pode usar {item} se extraído)

MAPPINGS = [
    # Esfera 1: Compras
    (r"Comprar agora – (.+)", "Risco de Ruptura: {}"),
    (r"Planejar compra – (.+)", "Sugestão de Reposição: {}"),
    (r"Produto sem giro – (.+)", "Capital Parado (Sem Giro): {}"),
    # Esfera 1 (Críticos)
    (r"Estoque negativo – (.+)", "Erro de Inventário: {}"),
    
    # Esfera 2: Ingredientes
    (r"Crítico – (.+)", "Insumo Crítico (Risco de Parada): {}"),
    (r"Repor imediatamente – (.+)", "Ação Imediata Necessária: {}"),
    (r"Ingrediente sem giro – (.+)", "Insumo Obsoleto: {}"),
    
    # Esfera 3: Produção
    (r"Produzir agora – (.+)", "Demanda Imediata (Cliente Esperando): {}"),
    (r"Planejar produção – (.+)", "Programação de Produção: {}"),
    
    # Esfera 4: Perecibilidade
    (r"⚠️ (.+) VENCIDOS", "PERDA SANITÁRIA CONFIRMADA: {}"), # O regex aqui precisa ser mais flexível se o nome do item estiver no final
    (r"Risco de vencimento – (.+)", "Alerta Prévio de Desperdício: {}"),
    (r"⚠️ Compra agrava desperdício – (.+)", "Decisão de Compra Ineficiente: {}"),
]

# Caso especial para "⚠️ {qty} {unit} VENCIDOS" onde o item não está no título explicitamente as vezes, 
# mas o padrão do sistema é "⚠️ {qty} {unit} VENCIDOS" no title e o item está no data.
# O regex acima assume que o título contenha o nome. 
# Vamos ajustar a lógica para usar dados estruturados se disponíveis.

def translate_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriquece o alerta com 'title_business' e 'title_technical'.
    Preserva o 'title' original como técnico.
    """
    original_title = alert_data.get("title", "")
    
    # Default: Business title = Technical title (fallback)
    business_title = original_title
    
    # Tenta casar padrões conhecidos
    for pattern, template in MAPPINGS:
        match = re.search(pattern, original_title)
        if match:
            # Se houver grupos de captura (ex: nome do item), usa no format
            if match.groups():
                business_title = template.format(*match.groups())
            else:
                business_title = template
            break
            
    # Tratamentos Especiais (Regras de Negócio de Apresentação)
    
    # Caso de Vencidos (que tem formato variável)
    if "VENCIDOS" in original_title and "PERDA SANITÁRIA" not in business_title:
         # Tenta extrair contexto mais amigável
         business_title = f"Perda Sanitária (Vencimento)"
    
    alert_data["title_business"] = business_title
    alert_data["title_technical"] = original_title
    
    return alert_data
