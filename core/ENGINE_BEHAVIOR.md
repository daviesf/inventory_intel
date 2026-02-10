# IntelliStock Engine Behavior (Frozen Core)

Este documento define o comportamento canônico consolidado das Esferas 1, 2 e 3.
Qualquer alteração neste comportamento requer revisão explícita.

## Ordem de Execução

1. **Esfera 1 (Produtos Prontos)**
   - Analisa itens comprados e revendidos.
   - Gera alertas de compra baseados em forecast e estoque de segurança.

2. **Esfera 2 (Ingredientes)**
   - Explode receitas de produtos planejados.
   - Gera alertas de compra para insumos.
   - Protegida contra loops de BOM (Depth Limit = 10).

3. **Esfera 3 (Produção)**
   - Analisa semi-acabados.
   - **Reativa**: Vendas do dia → Alerta urgente.
   - **Planejada**: Forecast → Alerta de planejamento.
   - *Precedência*: Se houver alerta Reativo, o Planejado é suprimido.

4. **Esfera 4 (Perecibilidade Inteligente)**
   - Camada de gestão superior.
   - Observa o estado e alertas anteriores.
   - Pode sugerir NÃO COMPRAR, mas não bloqueia alertas operacionais.

## Regras Canônicas de Precedência

1. **Abastecimento > Perecibilidade (Operação)**
   - A operação sempre recebe o alerta de "Comprar".
   - A perecibilidade adiciona um alerta de "Risco" ou "Cuidado", mas não remove a instrução de compra.

2. **Produção > Compra de Ingrediente**
   - Se a produção de um semi-acabado é sugerida, ela deve ocorrer antes da compra de seus ingredientes (ingredientes são consumidos pela produção).

3. **Lead Time Zero**
   - É suportado e válido.
   - Resulta em Safety Stock = 0.
   - Ponto de Reposição = Forecast * LeadTime (0) + Safety (0) = 0.
   - Gera compra agressiva (Just-in-Time imediato).

4. **Forecast Zero**
   - **Com Estoque > 0**: Gera alerta de produto parado (INFO).
   - **Com Estoque = 0**: Silêncio correto (item inativo).

5. **Semi-Acabados vs Ingredientes**
   - Semi-acabados são produzidos (Esfera 3).
   - Nunca são tratados como compra na Esfera 2.

## Estados Válidos vs Silêncio Inexplicável

| Estado | Comportamento Esperado |
|--------|------------------------|
| Forecast > 0, Estoque < ROP | Alerta de Compra (URGENT) |
| Forecast > 0, Estoque < Target | Alerta de Planejamento (PLAN) |
| Forecast = 0, Estoque > 0 | Alerta de Estagnação (INFO) |
| Forecast = 0, Estoque = 0 | Silêncio (Correto) |
| Lead Time = 0 | Alertas JIT (Correto) |

## Alertas por Esfera

- **Esfera 1**: `buy_*`, `neg_stock_*`, `stagnant_*`
- **Esfera 2**: `ingredient_*`, `ingredient_stagnant_*`
- **Esfera 3**: `prod_reactive_*`, `prod_plan_*`
- **Esfera 4**: `perishability_risk_*` (Plan/Info apenas)
