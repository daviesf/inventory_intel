import sys
import os
from datetime import datetime, timedelta
import statistics

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from infra.db import SessionLocal
from core.models import InventoryState, AnalysisContext, ItemType
from core.repository_sqlalchemy import SqlAlchemyInventoryRepository
from core.forecast import get_item_demand_data, _forecast_wma_for_weekday, _build_daily_series_for_item
from core.temporal_adjustments import apply_temporal_adjustments

def run_backtest(days_to_test=30):
    repo = SqlAlchemyInventoryRepository()
    
    # Load state as of NOW (to get items/history)
    # Ideally we would load state as of T-30, but for simplicity we use current history 
    # and just cut off the last 30 days for "truth" and simulate forecast from T-31.
    real_now = datetime.now()
    state, _ = repo.load_inventory_state(now=real_now)
    
    finished_items = [i for i in state.items if i.item_type == ItemType.FINISHED]
    print(f"Running backtest for {len(finished_items)} items over last {days_to_test} days...")
    
    metrics = {"baseline_mae": [], "seasonal_mae": []}
    
    for item in finished_items:
        # Get full history series
        # We need a dummy context to build series
        ctx_dummy = AnalysisContext(now=real_now)
        series = _build_daily_series_for_item(state, item.id, ctx_dummy)
        
        if len(series) < days_to_test + 14: # Need at least some history before test period
            continue
            
        # Split series
        # History for training: up to T - days_to_test
        # Test truth: T - days_to_test to T
        
        # Actually proper backtest iterates day by day.
        # Let's do a simpler "one-shot" or "rolling" backtest?
        # Rolling is better.
        
        item_maes_base = []
        item_maes_seas = []
        
        # Rolling forecast for the last N days
        for i in range(days_to_test):
            # Simulation Date: T - (days_to_test - i)
            sim_date = real_now - timedelta(days=(days_to_test - i))
            
            # Known history at sim_date
            # We filter series to only include dates < sim_date.date()
            # series is list of (date, qty)
            history_subset = [s for s in series if s[0] < sim_date.date()]
            
            if len(history_subset) < 14: continue
            
            # Actual value on sim_date
            actual_sales = next((s[1] for s in series if s[0] == sim_date.date()), 0.0)
            
            # 1. Baseline Forecast (WMA-DOW)
            # logic from _forecast_wma_for_weekday
            target_weekday = sim_date.weekday()
            # We need to pass ONLY the history subset to wma
            forecast_base = _forecast_wma_for_weekday(history_subset, target_weekday)
            
            # 2. Seasonal Forecast
            # Apply adjustments to the base forecast
            # We use the FULL state rules (assuming rules don't change over time for this backtest)
            adj = apply_temporal_adjustments(
                 item_id=item.id,
                 target_date=sim_date.date(),
                 forecast_base=forecast_base,
                 state=state
            )
            forecast_seasonal = adj.forecast_final
            
            # Calculate Error
            item_maes_base.append(abs(forecast_base - actual_sales))
            item_maes_seas.append(abs(forecast_seasonal - actual_sales))
            
        if item_maes_base:
            mae_b = statistics.mean(item_maes_base)
            mae_s = statistics.mean(item_maes_seas)
            metrics["baseline_mae"].append(mae_b)
            metrics["seasonal_mae"].append(mae_s)
            
            # print(f"Item {item.name}: Base MAE={mae_b:.2f}, Seasonal MAE={mae_s:.2f}")

    if not metrics["baseline_mae"]:
        print("Not enough data for backtest.")
        return

    avg_base_mae = statistics.mean(metrics["baseline_mae"])
    avg_seas_mae = statistics.mean(metrics["seasonal_mae"])
    improvement = ((avg_base_mae - avg_seas_mae) / avg_base_mae) * 100 if avg_base_mae > 0 else 0
    
    print("-" * 40)
    print(f"RESULTS (Average across {len(metrics['baseline_mae'])} items)")
    print(f"Baseline MAE: {avg_base_mae:.4f}")
    print(f"Seasonal MAE: {avg_seas_mae:.4f}")
    print(f"Improvement:  {improvement:+.2f}%")
    print("-" * 40)

if __name__ == "__main__":
    run_backtest()
