# scripts/init_demo_db.py

from __future__ import annotations

from datetime import datetime, timedelta, time

# Adicionei 'Base' e 'engine' na importação para poder recriar as tabelas
from infra.db import init_db, SessionLocal, DB_PATH, Base, engine
from infra.orm_models import (
    ItemORM,
    StockLevelORM,
    SaleORM,
    DishORM,
    RecipeORM,
    # Importante importar todos os modelos para o metadata reconhecê-los
    AlertSuppressionORM,
    EngineConfigORM,
    AlertHistoryORM
)


def main():
    print(f"Reinicializando banco de dados em: {DB_PATH}")

    # --- PASSO CRÍTICO: DESTRUIR E RECRIAR ESTRUTURA ---
    # Isso garante que novas colunas (como updated_at) sejam criadas
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Schema recriado com sucesso (tabelas limpas e atualizadas).")

    now = datetime.now()
    today = now.date()
    base_date_finished = today - timedelta(days=27)  # 28 dias de histórico

    with SessionLocal() as session:
        # Como demos drop_all, não precisa mais dos delete(),
        # mas mantemos a inserção dos dados:

        # --------------------------------------------------------------------------------
        # 2) ITENS (ESFERA 1 + ESFERA 2)
        # --------------------------------------------------------------------------------
        items = [
            # ---------------------------
            # ESFERA 1 – PRODUTOS PRONTOS
            # ---------------------------
            ItemORM(
                id="item_coca_ks",
                name="Coca-Cola KS",
                item_type="finished",
                unit="un",
                lead_time_days=3.0,
                shelf_life_days=180.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=today,
            ),
            ItemORM(
                id="item_itubaina_ks",
                name="Itubaína KS",
                item_type="finished",
                unit="un",
                lead_time_days=3.0,
                shelf_life_days=365.0,
                item_class="C",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="item_agua_500",
                name="Água Mineral 500ml",
                item_type="finished",
                unit="un",
                lead_time_days=2.0,
                shelf_life_days=365.0,
                item_class="B",
                operation_mode="demand_only",
                last_audit_date=None,
            ),
            ItemORM(
                id="item_cerveja_long_neck",
                name="Cerveja Long Neck",
                item_type="finished",
                unit="un",
                lead_time_days=5.0,
                shelf_life_days=180.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=today,
            ),
            ItemORM(
                id="item_suco_lata",
                name="Suco em Lata",
                item_type="finished",
                unit="un",
                lead_time_days=4.0,
                shelf_life_days=365.0,
                item_class="B",
                operation_mode="strict",
                last_audit_date=today,
            ),

            # ---------------------------
            # ESFERA 2 – SEMI-ACABADOS
            # ---------------------------
            ItemORM(
                id="semi_burger_blend",
                name="Hambúrguer Bovino Moldado",
                item_type="semi_finished",
                unit="kg",
                lead_time_days=0.0,  # produzido na cozinha
                shelf_life_days=2.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=today,
            ),
            ItemORM(
                id="semi_frango_grelhado",
                name="Frango Grelhado em Cubos",
                item_type="semi_finished",
                unit="kg",
                lead_time_days=0.0,
                shelf_life_days=2.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=today,
            ),
            ItemORM(
                id="semi_arroz_cozido",
                name="Arroz Branco Cozido",
                item_type="semi_finished",
                unit="kg",
                lead_time_days=0.0,
                shelf_life_days=1.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=today,
            ),
            ItemORM(
                id="semi_molho_tomate_casa",
                name="Molho de Tomate da Casa",
                item_type="semi_finished",
                unit="kg",
                lead_time_days=0.0,
                shelf_life_days=2.0,
                item_class="B",
                operation_mode="strict",
                last_audit_date=today,
            ),

            # ---------------------------
            # ESFERA 2 – INGREDIENTES
            # ---------------------------
            ItemORM(
                id="ing_carne_moida_bovina",
                name="Carne Moída Bovina",
                item_type="ingredient",
                unit="kg",
                lead_time_days=2.0,
                shelf_life_days=5.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_frango_peito",
                name="Peito de Frango",
                item_type="ingredient",
                unit="kg",
                lead_time_days=2.0,
                shelf_life_days=5.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_arroz_branco",
                name="Arroz Branco Cru",
                item_type="ingredient",
                unit="kg",
                lead_time_days=7.0,
                shelf_life_days=365.0,
                item_class="B",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_tomate",
                name="Tomate In Natura",
                item_type="ingredient",
                unit="kg",
                lead_time_days=2.0,
                shelf_life_days=5.0,
                item_class="B",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_cebola",
                name="Cebola",
                item_type="ingredient",
                unit="kg",
                lead_time_days=2.0,
                shelf_life_days=10.0,
                item_class="C",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_alho",
                name="Alho",
                item_type="ingredient",
                unit="kg",
                lead_time_days=2.0,
                shelf_life_days=30.0,
                item_class="C",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_oleo_soja",
                name="Óleo de Soja",
                item_type="ingredient",
                unit="L",
                lead_time_days=7.0,
                shelf_life_days=365.0,
                item_class="C",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_sal_refinado",
                name="Sal Refinado",
                item_type="ingredient",
                unit="kg",
                lead_time_days=15.0,
                shelf_life_days=365.0,
                item_class="C",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_pao_burger",
                name="Pão de Hambúrguer",
                item_type="ingredient",
                unit="un",
                lead_time_days=2.0,
                shelf_life_days=3.0,
                item_class="A",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_queijo_mussarela_fatia",
                name="Queijo Mussarela (Fatia)",
                item_type="ingredient",
                unit="un",
                lead_time_days=2.0,
                shelf_life_days=10.0,
                item_class="B",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_batata_congelada",
                name="Batata Pré-Frita Congelada",
                item_type="ingredient",
                unit="kg",
                lead_time_days=5.0,
                shelf_life_days=180.0,
                item_class="B",
                operation_mode="strict",
                last_audit_date=None,
            ),
            ItemORM(
                id="ing_alface",
                name="Alface",
                item_type="ingredient",
                unit="kg",
                lead_time_days=2.0,
                shelf_life_days=3.0,
                item_class="B",
                operation_mode="strict",
                last_audit_date=None,
            ),
        ]

        session.add_all(items)
        session.commit()

        # --------------------------------------------------------------------------------
        # 3) DISHES (PRATOS DO SALÃO)
        # --------------------------------------------------------------------------------
        dishes = [
            DishORM(
                id="dish_x_burger",
                name="X-Burger",
                prep_time_min=12.0,
                pre_prep_time_min=20.0,
            ),
            DishORM(
                id="dish_x_salada",
                name="X-Salada",
                prep_time_min=14.0,
                pre_prep_time_min=20.0,
            ),
            DishORM(
                id="dish_prato_frango_grelhado",
                name="Prato Frango Grelhado",
                prep_time_min=15.0,
                pre_prep_time_min=25.0,
            ),
        ]
        session.add_all(dishes)
        session.commit()

        # --------------------------------------------------------------------------------
        # 4) RECEITAS (EXPLOSÃO DE MATERIAIS)
        # --------------------------------------------------------------------------------
        recipes = [
            # Pratos -> Semi-acabados + ingredientes
            RecipeORM(
                parent_item_id="dish_x_burger",
                child_item_id="semi_burger_blend",
                quantity=0.18,  # 180g de blend por X-Burger
            ),
            RecipeORM(
                parent_item_id="dish_x_burger",
                child_item_id="ing_pao_burger",
                quantity=1.0,
            ),
            RecipeORM(
                parent_item_id="dish_x_burger",
                child_item_id="ing_queijo_mussarela_fatia",
                quantity=1.0,
            ),
            RecipeORM(
                parent_item_id="dish_x_burger",
                child_item_id="ing_alface",
                quantity=0.02,
            ),

            RecipeORM(
                parent_item_id="dish_x_salada",
                child_item_id="semi_burger_blend",
                quantity=0.18,
            ),
            RecipeORM(
                parent_item_id="dish_x_salada",
                child_item_id="ing_pao_burger",
                quantity=1.0,
            ),
            RecipeORM(
                parent_item_id="dish_x_salada",
                child_item_id="ing_queijo_mussarela_fatia",
                quantity=1.0,
            ),
            RecipeORM(
                parent_item_id="dish_x_salada",
                child_item_id="ing_alface",
                quantity=0.03,
            ),
            RecipeORM(
                parent_item_id="dish_x_salada",
                child_item_id="ing_tomate",
                quantity=0.03,
            ),

            RecipeORM(
                parent_item_id="dish_prato_frango_grelhado",
                child_item_id="semi_frango_grelhado",
                quantity=0.20,
            ),
            RecipeORM(
                parent_item_id="dish_prato_frango_grelhado",
                child_item_id="semi_arroz_cozido",
                quantity=0.18,
            ),
            RecipeORM(
                parent_item_id="dish_prato_frango_grelhado",
                child_item_id="ing_batata_congelada",
                quantity=0.12,
            ),
            RecipeORM(
                parent_item_id="dish_prato_frango_grelhado",
                child_item_id="ing_alface",
                quantity=0.03,
            ),
            RecipeORM(
                parent_item_id="dish_prato_frango_grelhado",
                child_item_id="ing_tomate",
                quantity=0.03,
            ),

            # Semi-acabados -> Ingredientes
            RecipeORM(
                parent_item_id="semi_burger_blend",
                child_item_id="ing_carne_moida_bovina",
                quantity=1.0,  # 1 kg de carne = 1 kg de blend (simplificado)
            ),
            RecipeORM(
                parent_item_id="semi_burger_blend",
                child_item_id="ing_sal_refinado",
                quantity=0.02,
            ),
            RecipeORM(
                parent_item_id="semi_burger_blend",
                child_item_id="ing_cebola",
                quantity=0.05,
            ),

            RecipeORM(
                parent_item_id="semi_frango_grelhado",
                child_item_id="ing_frango_peito",
                quantity=1.0,
            ),
            RecipeORM(
                parent_item_id="semi_frango_grelhado",
                child_item_id="ing_oleo_soja",
                quantity=0.03,
            ),
            RecipeORM(
                parent_item_id="semi_frango_grelhado",
                child_item_id="ing_sal_refinado",
                quantity=0.02,
            ),

            RecipeORM(
                parent_item_id="semi_arroz_cozido",
                child_item_id="ing_arroz_branco",
                quantity=0.33,  # 1kg arroz cru ~ 3kg cozido (simplificado)
            ),
            RecipeORM(
                parent_item_id="semi_arroz_cozido",
                child_item_id="ing_oleo_soja",
                quantity=0.01,
            ),
            RecipeORM(
                parent_item_id="semi_arroz_cozido",
                child_item_id="ing_sal_refinado",
                quantity=0.01,
            ),

            RecipeORM(
                parent_item_id="semi_molho_tomate_casa",
                child_item_id="ing_tomate",
                quantity=0.80,
            ),
            RecipeORM(
                parent_item_id="semi_molho_tomate_casa",
                child_item_id="ing_cebola",
                quantity=0.05,
            ),
            RecipeORM(
                parent_item_id="semi_molho_tomate_casa",
                child_item_id="ing_alho",
                quantity=0.02,
            ),
            RecipeORM(
                parent_item_id="semi_molho_tomate_casa",
                child_item_id="ing_oleo_soja",
                quantity=0.03,
            ),
            RecipeORM(
                parent_item_id="semi_molho_tomate_casa",
                child_item_id="ing_sal_refinado",
                quantity=0.02,
            ),
        ]
        session.add_all(recipes)
        session.commit()

        # --------------------------------------------------------------------------------
        # 5) ESTOQUE (SALDOS ATUAIS)
        # --------------------------------------------------------------------------------
        stocks = [
            # Esfera 1
            StockLevelORM(item_id="item_coca_ks", quantity=120.0),
            StockLevelORM(item_id="item_itubaina_ks", quantity=80.0),
            StockLevelORM(item_id="item_agua_500", quantity=50.0),
            StockLevelORM(item_id="item_cerveja_long_neck", quantity=-5.0),  # proposital p/ DATA_QUALITY
            StockLevelORM(item_id="item_suco_lata", quantity=40.0),

            # Semi-acabados (produção)
            StockLevelORM(item_id="semi_burger_blend", quantity=3.0),
            StockLevelORM(item_id="semi_frango_grelhado", quantity=1.0),
            StockLevelORM(item_id="semi_arroz_cozido", quantity=2.0),
            StockLevelORM(item_id="semi_molho_tomate_casa", quantity=0.5),

            # Ingredientes (não usados ainda na engine, mas deixam o cenário rico)
            StockLevelORM(item_id="ing_carne_moida_bovina", quantity=8.0),
            StockLevelORM(item_id="ing_frango_peito", quantity=6.0),
            StockLevelORM(item_id="ing_arroz_branco", quantity=10.0),
            StockLevelORM(item_id="ing_tomate", quantity=5.0),
            StockLevelORM(item_id="ing_cebola", quantity=3.0),
            StockLevelORM(item_id="ing_alho", quantity=1.0),
            StockLevelORM(item_id="ing_oleo_soja", quantity=20.0),
            StockLevelORM(item_id="ing_sal_refinado", quantity=2.0),
            StockLevelORM(item_id="ing_pao_burger", quantity=50.0),
            StockLevelORM(item_id="ing_queijo_mussarela_fatia", quantity=80.0),
            StockLevelORM(item_id="ing_batata_congelada", quantity=15.0),
            StockLevelORM(item_id="ing_alface", quantity=4.0),
        ]
        session.add_all(stocks)
        session.commit()

        # --------------------------------------------------------------------------------
        # 6) VENDAS – ESFERA 1 (PRODUTOS PRONTOS) – 28 DIAS
        # --------------------------------------------------------------------------------
        sales_rows: list[SaleORM] = []

        for i in range(28):
            day = base_date_finished + timedelta(days=i)
            ts = datetime.combine(day, time(12, 0))
            wd = day.weekday()  # 0=Seg ... 6=Dom
            is_weekend = wd >= 5

            # Coca: forte em fim de semana
            if wd in (4, 5):  # sexta, sábado
                coca_qty = 90
            elif wd == 6:  # domingo
                coca_qty = 70
            else:
                coca_qty = 50

            # Itubaína: baixo giro
            if is_weekend:
                itubaina_qty = 12
            else:
                itubaina_qty = 8

            # Água: moderado, cresce no fim de semana
            agua_qty = 20 if not is_weekend else 30

            # Cerveja: explode no fim de semana
            cerveja_qty = 30 if not is_weekend else 45

            # Suco: estável, um pouco maior no almoço de família (dom)
            suco_qty = 10
            if wd == 6:
                suco_qty = 15

            sales_rows.extend(
                [
                    SaleORM(
                        dish_id="item_coca_ks",
                        quantity=float(coca_qty),
                        timestamp=ts,
                    ),
                    SaleORM(
                        dish_id="item_itubaina_ks",
                        quantity=float(itubaina_qty),
                        timestamp=ts,
                    ),
                    SaleORM(
                        dish_id="item_agua_500",
                        quantity=float(agua_qty),
                        timestamp=ts,
                    ),
                    SaleORM(
                        dish_id="item_cerveja_long_neck",
                        quantity=float(cerveja_qty),
                        timestamp=ts,
                    ),
                    SaleORM(
                        dish_id="item_suco_lata",
                        quantity=float(suco_qty),
                        timestamp=ts,
                    ),
                ]
            )

        # --------------------------------------------------------------------------------
        # 7) VENDAS – ESFERA 2 (PRATOS) – ÚLTIMOS 7 DIAS + HOJE
        #     -> alimenta today_sales e plano de produção
        # --------------------------------------------------------------------------------
        base_date_dishes = today - timedelta(days=6)

        for i in range(7):
            day = base_date_dishes + timedelta(days=i)
            ts_lunch = datetime.combine(day, time(12, 0))
            ts_dinner = datetime.combine(day, time(20, 0))
            wd = day.weekday()

            # X-Burger: forte sexta/sábado, moderado nos demais
            if wd in (4, 5):
                burger_total = 40
            elif wd == 6:
                burger_total = 30
            else:
                burger_total = 20
            burger_lunch = int(burger_total * 0.4)
            burger_dinner = burger_total - burger_lunch

            # X-Salada: um pouco menos que X-Burger
            xsal_total = int(burger_total * 0.7)
            xsal_lunch = int(xsal_total * 0.45)
            xsal_dinner = xsal_total - xsal_lunch

            # Prato Frango Grelhado: mais forte em dias de semana (almoço executivo)
            if wd in (0, 1, 2, 3, 4):  # seg-sex
                prato_total = 25
            else:
                prato_total = 15
            prato_lunch = int(prato_total * 0.7)
            prato_dinner = prato_total - prato_lunch

            sales_rows.extend(
                [
                    # X-Burger
                    SaleORM(
                        dish_id="dish_x_burger",
                        quantity=float(burger_lunch),
                        timestamp=ts_lunch,
                    ),
                    SaleORM(
                        dish_id="dish_x_burger",
                        quantity=float(burger_dinner),
                        timestamp=ts_dinner,
                    ),
                    # X-Salada
                    SaleORM(
                        dish_id="dish_x_salada",
                        quantity=float(xsal_lunch),
                        timestamp=ts_lunch,
                    ),
                    SaleORM(
                        dish_id="dish_x_salada",
                        quantity=float(xsal_dinner),
                        timestamp=ts_dinner,
                    ),
                    # Prato Frango Grelhado
                    SaleORM(
                        dish_id="dish_prato_frango_grelhado",
                        quantity=float(prato_lunch),
                        timestamp=ts_lunch,
                    ),
                    SaleORM(
                        dish_id="dish_prato_frango_grelhado",
                        quantity=float(prato_dinner),
                        timestamp=ts_dinner,
                    ),
                ]
            )

        # Grava todas as vendas
        session.add_all(sales_rows)
        session.commit()

    print(f"Banco demo inicializado com sucesso ({DB_PATH}).")
    print("Seed inclui:")
    print("- Esfera 1: 5 produtos prontos com 28 dias de histórico (WMA-DOW).")
    print("- Esfera 2: 3 pratos, 4 semi-acabados, ~10 ingredientes.")
    print("- Vendas de pratos nos últimos 7 dias (incluindo hoje) para testar produção.")


if __name__ == "__main__":
    main()
