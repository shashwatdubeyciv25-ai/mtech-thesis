# ====================================================================
# modules/carbon.py
# Greenhouse Gas Accounting & Emission Modeling Module
# Based on IPCC 2006 Guidelines and CEA India Baseline v20
# ====================================================================
import pandas as pd
import numpy as np
import os
from .database import get_connection, save_calculated_emissions

DEFAULT_FACTORS = {
    'lpg': 2.984,          # kg CO2e / kg LPG (IPCC 2006)
    'firewood': 1.747,     # kg CO2e / kg wood (IPCC 2006)
    'electricity': 0.820,  # kg CO2e / kWh (CEA India v20 2024)
    'petrol': 2.310,       # kg CO2e / litre (IPCC 2006 mobile combustion)
    'waste': 0.450,        # kg CO2e / kg MSW (IPCC rural solid waste)
    'cow': 980.0,          # kg CO2e / head / yr (enteric + manure, IPCC Indian cattle)
    'goat': 145.6,         # kg CO2e / head / yr (IPCC caprine)
    'sheep': 145.6         # kg CO2e / head / yr (IPCC ovine)
}

def get_emission_factors(db_path=None):
    """Retrieves active emission factors from database or falls back to defaults."""
    factors = DEFAULT_FACTORS.copy()
    if db_path and os.path.exists(db_path):
        try:
            with get_connection(db_path) as conn:
                df = pd.read_sql_query('SELECT activity, emission_factor FROM emission_factors', conn)
                for _, r in df.iterrows():
                    act = str(r['activity']).lower()
                    val = float(r['emission_factor'])
                    if 'lpg' in act:
                        factors['lpg'] = val
                    elif 'firewood' in act:
                        factors['firewood'] = val
                    elif 'electricity' in act:
                        factors['electricity'] = val
                    elif 'fuel' in act or 'petrol' in act:
                        factors['petrol'] = val
                    elif 'waste' in act:
                        factors['waste'] = val
                    elif 'cattle' in act or 'cow' in act:
                        factors['cow'] = val
                    elif 'goat' in act:
                        factors['goat'] = val
                    elif 'sheep' in act:
                        factors['sheep'] = val
        except Exception:
            pass
    return factors

def calculate_single_village(village_dict, factors=None):
    """
    Computes sectoral greenhouse gas emissions for a single village dictionary.
    Activity Data:
      LPG (kg/mo), Firewood (kg/mo), Electricity (kWh/mo)
      Petrol (L/mo), Solid Waste (kg/mo)
      Cows, Goats, Sheep (counts)
    Returns dictionary with all sectoral emissions in tonnes CO2e/year.
    """
    if factors is None:
        factors = DEFAULT_FACTORS
    
    # 1. Energy
    lpg_kg_yr = float(village_dict.get('lpg_monthly_kg', 0) or 0) * 12.0
    firewood_kg_yr = float(village_dict.get('firewood_monthly_kg', 0) or 0) * 12.0
    elec_kwh_yr = float(village_dict.get('electricity_monthly_kwh', 0) or 0) * 12.0
    
    lpg_t = (lpg_kg_yr * factors['lpg']) / 1000.0
    firewood_t = (firewood_kg_yr * factors['firewood']) / 1000.0
    elec_t = (elec_kwh_yr * factors['electricity']) / 1000.0
    energy_t = lpg_t + firewood_t + elec_t
    
    # 2. Transport
    petrol_l_yr = float(village_dict.get('petrol_monthly_litres', 0) or 0) * 12.0
    transport_t = (petrol_l_yr * factors['petrol']) / 1000.0
    
    # 3. Waste
    waste_kg_yr = float(village_dict.get('waste_monthly_kg', 0) or 0) * 12.0
    waste_t = (waste_kg_yr * factors['waste']) / 1000.0
    
    # 4. Livestock
    cows = float(village_dict.get('cows_count', 0) or 0)
    goats = float(village_dict.get('goats_count', 0) or 0)
    sheep = float(village_dict.get('sheep_count', 0) or 0)
    livestock_t = (cows * factors['cow'] + goats * factors['goat'] + sheep * factors['sheep']) / 1000.0
    
    # Total
    total_t = energy_t + transport_t + waste_t + livestock_t
    
    # Per Capita (kg CO2e / person / year)
    pop = float(village_dict.get('total_residents', 0) or 0)
    per_capita_kg = (total_t * 1000.0 / pop) if pop > 0 else 0.0
    
    return {
        'lpg_co2e_t_yr': round(lpg_t, 2),
        'firewood_co2e_t_yr': round(firewood_t, 2),
        'electricity_co2e_t_yr': round(elec_t, 2),
        'energy_total_co2e_t_yr': round(energy_t, 2),
        'transport_co2e_t_yr': round(transport_t, 2),
        'waste_co2e_t_yr': round(waste_t, 2),
        'livestock_co2e_t_yr': round(livestock_t, 2),
        'total_co2e_t_yr': round(total_t, 2),
        'per_capita_co2e_kg_yr': round(per_capita_kg, 2)
    }

def recompute_and_save_all_emissions(db_path=None):
    """Recomputes emissions for every village in the database and updates SQLite."""
    from .database import DEFAULT_DB_PATH
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    factors = get_emission_factors(db_path)
    
    query = """
        SELECT v.village_id, v.village_code, d.total_residents,
               e.lpg_monthly_kg, e.firewood_monthly_kg, e.electricity_monthly_kwh,
               wm.waste_monthly_kg, t.petrol_monthly_litres,
               lp.cows_count, lp.goats_count, lp.sheep_count
        FROM villages v
        LEFT JOIN demographics d ON v.village_id = d.village_id
        LEFT JOIN energy_consumption e ON v.village_id = e.village_id
        LEFT JOIN waste_management wm ON v.village_id = wm.village_id
        LEFT JOIN transport_activity t ON v.village_id = t.village_id
        LEFT JOIN livestock_population lp ON v.village_id = lp.village_id
    """
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    
    emissions_list = []
    for _, row in df.iterrows():
        calc = calculate_single_village(dict(row), factors)
        calc['village_id'] = int(row['village_id'])
        emissions_list.append(calc)
    
    save_calculated_emissions(emissions_list, db_path)
    return len(emissions_list)
