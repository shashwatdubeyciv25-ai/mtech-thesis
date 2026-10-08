# ====================================================================
# modules/database.py
# Database Management Module for Varanasi Village Dashboard
# ====================================================================
import sqlite3
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')
DEFAULT_SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')
DEFAULT_FACTORS_PATH = os.path.join(BASE_DIR, 'config', 'emission_factors.csv')
DEFAULT_EXCEL_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'village_data.xlsx')

def get_connection(db_path=DEFAULT_DB_PATH):
    """Establishes SQLite connection with foreign keys enabled."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH, schema_path=DEFAULT_SCHEMA_PATH):
    """Initializes tables from schema.sql."""
    with get_connection(db_path) as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()

def load_emission_factors(db_path=DEFAULT_DB_PATH, factors_csv=DEFAULT_FACTORS_PATH):
    """Loads emission factors reference table."""
    if not os.path.exists(factors_csv):
        return
    df = pd.read_csv(factors_csv)
    # Normalize column names to lowercase
    df.columns = [c.lower() for c in df.columns]
    with get_connection(db_path) as conn:
        for _, row in df.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO emission_factors 
                (factor_id, sector, activity, fuel_or_source, unit, emission_factor, gas, co2e_factor, reference_source, publication_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(row['factor_id']), str(row['sector']), str(row['activity']),
                str(row['fuel_or_source']), str(row['unit']), float(row['emission_factor']),
                str(row['gas']), float(row.get('co2e_factor', 1.0)), str(row['reference']), int(row['year'])
            ))
        conn.commit()

def import_village_excel(excel_path=DEFAULT_EXCEL_PATH, db_path=DEFAULT_DB_PATH):
    """
    Imports Excel survey data into normalized SQLite tables.
    Performs data integrity and range validation.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found at: {excel_path}")
    
    df = pd.read_excel(excel_path)
    report = {
        'total_rows': len(df),
        'inserted': 0,
        'updated': 0,
        'warnings': []
    }
    
    req_cols = ['village_code', 'village_name', 'block_name', 'total_residents', 'total_area_ha']
    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing mandatory columns in Excel: {missing}")

    with get_connection(db_path) as conn:
        for idx, row in df.iterrows():
            vcode = str(row['village_code']).strip()
            vname = str(row['village_name']).strip()
            bname = str(row['block_name']).strip()
            sdist = str(row.get('subdistrict', 'Varanasi')).strip()
            lat = float(row.get('latitude', 25.3))
            lon = float(row.get('longitude', 82.9))
            
            # Validation checks
            pop = max(0, int(row.get('total_residents', 0)))
            hh = max(0, int(row.get('total_households', round(pop/6.0) if pop > 0 else 0)))
            tot_area = max(0.0, float(row.get('total_area_ha', 0.0)))
            builtup = max(0.0, float(row.get('builtup_area_ha', 0.0)))
            agri = max(0.0, float(row.get('agri_area_ha', 0.0)))
            
            if builtup + agri > tot_area * 1.05 and tot_area > 0:
                report['warnings'].append(f"Village {vname} ({vcode}): Built-up + Agri ({builtup + agri:.1f} ha) exceeds total area ({tot_area:.1f} ha).")

            # 1. Upsert Village Core
            cur = conn.cursor()
            cur.execute('SELECT village_id FROM villages WHERE village_code = ?', (vcode,))
            existing = cur.fetchone()
            
            if existing:
                village_id = existing['village_id']
                conn.execute("""
                    UPDATE villages 
                    SET village_name = ?, block_name = ?, subdistrict = ?, latitude = ?, longitude = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE village_id = ?
                """, (vname, bname, sdist, lat, lon, village_id))
                report['updated'] += 1
            else:
                cur.execute("""
                    INSERT INTO villages (village_code, village_name, block_name, subdistrict, latitude, longitude)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vcode, vname, bname, sdist, lat, lon))
                village_id = cur.lastrowid
                report['inserted'] += 1

            # 2. Demographics
            conn.execute("""
                INSERT OR REPLACE INTO demographics (village_id, total_residents, total_households, total_male, total_female)
                VALUES (?, ?, ?, ?, ?)
            """, (village_id, pop, hh, int(row.get('total_male', 0)), int(row.get('total_female', 0))))

            # 3. Land Use
            forest = max(0.0, float(row.get('forest_area_ha', 0.0)))
            barren = max(0.0, float(row.get('barren_area_ha', 0.0)))
            culturable = max(0.0, float(row.get('culturable_waste_ha', 0.0)))
            fallow = max(0.0, float(row.get('fallow_land_ha', 0.0)))
            remaining = max(0.0, float(row.get('remaining_area_ha', max(0.0, tot_area - (builtup + agri + forest)))))
            
            conn.execute("""
                INSERT OR REPLACE INTO land_use 
                (village_id, total_area_ha, builtup_area_ha, agri_area_ha, forest_area_ha, barren_area_ha, culturable_waste_ha, fallow_land_ha, remaining_area_ha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (village_id, tot_area, builtup, agri, forest, barren, culturable, fallow, remaining))

            # 4. Water Resources
            pond = max(0.0, float(row.get('pond_area_ha', 0.0)))
            river = max(0.0, float(row.get('river_area_ha', 0.0)))
            canal = max(0.0, float(row.get('canal_area_ha', 0.0)))
            well = max(0.0, float(row.get('well_irrig_area_ha', 0.0)))
            tot_water = max(0.0, float(row.get('total_water_area_ha', pond + river + canal)))
            
            conn.execute("""
                INSERT OR REPLACE INTO water_resources 
                (village_id, pond_area_ha, river_area_ha, canal_area_ha, well_irrig_area_ha, other_water_ha, total_water_area_ha)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (village_id, pond, river, canal, well, 0.0, tot_water))

            # 5. Energy
            lpg = max(0.0, float(row.get('lpg_monthly_kg', 0.0)))
            firewood = max(0.0, float(row.get('firewood_monthly_kg', 0.0)))
            elec = max(0.0, float(row.get('electricity_monthly_kwh', 0.0)))
            conn.execute("""
                INSERT OR REPLACE INTO energy_consumption (village_id, lpg_monthly_kg, firewood_monthly_kg, electricity_monthly_kwh)
                VALUES (?, ?, ?, ?)
            """, (village_id, lpg, firewood, elec))

            # 6. Waste
            waste = max(0.0, float(row.get('waste_monthly_kg', 0.0)))
            conn.execute("""
                INSERT OR REPLACE INTO waste_management (village_id, waste_monthly_kg)
                VALUES (?, ?)
            """, (village_id, waste))

            # 7. Transport
            motorbikes = max(0, int(row.get('motorbikes_count', 0)))
            petrol = max(0.0, float(row.get('petrol_monthly_litres', 0.0)))
            conn.execute("""
                INSERT OR REPLACE INTO transport_activity (village_id, motorbikes_count, petrol_monthly_litres)
                VALUES (?, ?, ?)
            """, (village_id, motorbikes, petrol))

            # 8. Livestock
            cows = max(0, int(row.get('cows_count', 0)))
            goats = max(0, int(row.get('goats_count', 0)))
            sheep = max(0, int(row.get('sheep_count', 0)))
            tot_live = max(0, int(row.get('total_livestock', cows + goats + sheep)))
            conn.execute("""
                INSERT OR REPLACE INTO livestock_population (village_id, cows_count, goats_count, sheep_count, total_livestock)
                VALUES (?, ?, ?, ?, ?)
            """, (village_id, cows, goats, sheep, tot_live))

        conn.commit()
    return report

def get_blocks_list(db_path=DEFAULT_DB_PATH):
    """Returns sorted list of distinct block names."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query('SELECT DISTINCT block_name FROM villages ORDER BY block_name', conn)
    return df['block_name'].tolist()

def get_villages_df(db_path=DEFAULT_DB_PATH, block_name=None):
    """Returns complete dataframe of villages and parameters."""
    query = """
        SELECT v.village_id, v.village_code, v.village_name, v.block_name, v.subdistrict, v.latitude, v.longitude,
               d.total_residents, d.total_households,
               l.total_area_ha, l.builtup_area_ha, l.agri_area_ha,
               w.total_water_area_ha,
               e.lpg_monthly_kg, e.firewood_monthly_kg, e.electricity_monthly_kwh,
               wm.waste_monthly_kg,
               t.motorbikes_count, t.petrol_monthly_litres,
               lp.cows_count, lp.goats_count, lp.sheep_count, lp.total_livestock,
               ve.lpg_co2e_t_yr, ve.firewood_co2e_t_yr, ve.electricity_co2e_t_yr, ve.energy_total_co2e_t_yr,
               ve.transport_co2e_t_yr, ve.waste_co2e_t_yr, ve.livestock_co2e_t_yr,
               ve.total_co2e_t_yr, ve.per_capita_co2e_kg_yr
        FROM villages v
        LEFT JOIN demographics d ON v.village_id = d.village_id
        LEFT JOIN land_use l ON v.village_id = l.village_id
        LEFT JOIN water_resources w ON v.village_id = w.village_id
        LEFT JOIN energy_consumption e ON v.village_id = e.village_id
        LEFT JOIN waste_management wm ON v.village_id = wm.village_id
        LEFT JOIN transport_activity t ON v.village_id = t.village_id
        LEFT JOIN livestock_population lp ON v.village_id = lp.village_id
        LEFT JOIN village_emissions ve ON v.village_id = ve.village_id
    """
    params = []
    if block_name and block_name != 'All Blocks':
        query += ' WHERE v.block_name = ?'
        params.append(block_name)
    query += ' ORDER BY v.village_name'
    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)

def get_village_full_details(village_code_or_id, db_path=DEFAULT_DB_PATH):
    """Fetches complete record of all 12 parameters and emissions for a single village."""
    query = """
        SELECT v.*, 
               d.total_residents, d.total_households, d.total_male, d.total_female,
               l.total_area_ha, l.builtup_area_ha, l.agri_area_ha, l.forest_area_ha, l.barren_area_ha, l.culturable_waste_ha, l.fallow_land_ha, l.remaining_area_ha,
               w.pond_area_ha, w.river_area_ha, w.canal_area_ha, w.well_irrig_area_ha, w.other_water_ha, w.total_water_area_ha,
               e.lpg_monthly_kg, e.firewood_monthly_kg, e.electricity_monthly_kwh,
               wm.waste_monthly_kg,
               t.motorbikes_count, t.petrol_monthly_litres,
               lp.cows_count, lp.goats_count, lp.sheep_count, lp.total_livestock,
               ve.lpg_co2e_t_yr, ve.firewood_co2e_t_yr, ve.electricity_co2e_t_yr, ve.energy_total_co2e_t_yr,
               ve.transport_co2e_t_yr, ve.waste_co2e_t_yr, ve.livestock_co2e_t_yr, ve.total_co2e_t_yr, ve.per_capita_co2e_kg_yr
        FROM villages v
        LEFT JOIN demographics d ON v.village_id = d.village_id
        LEFT JOIN land_use l ON v.village_id = l.village_id
        LEFT JOIN water_resources w ON v.village_id = w.village_id
        LEFT JOIN energy_consumption e ON v.village_id = e.village_id
        LEFT JOIN waste_management wm ON v.village_id = wm.village_id
        LEFT JOIN transport_activity t ON v.village_id = t.village_id
        LEFT JOIN livestock_population lp ON v.village_id = lp.village_id
        LEFT JOIN village_emissions ve ON v.village_id = ve.village_id
        WHERE v.village_code = ? OR v.village_id = ?
    """
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(query, (str(village_code_or_id), str(village_code_or_id)))
        row = cur.fetchone()
        return dict(row) if row else None

def save_calculated_emissions(emissions_list, db_path=DEFAULT_DB_PATH):
    """Batch updates/inserts emissions into village_emissions table."""
    with get_connection(db_path) as conn:
        for item in emissions_list:
            conn.execute("""
                INSERT OR REPLACE INTO village_emissions
                (village_id, lpg_co2e_t_yr, firewood_co2e_t_yr, electricity_co2e_t_yr, energy_total_co2e_t_yr,
                 transport_co2e_t_yr, waste_co2e_t_yr, livestock_co2e_t_yr, total_co2e_t_yr, per_capita_co2e_kg_yr, calculation_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                int(item['village_id']),
                float(item['lpg_co2e_t_yr']),
                float(item['firewood_co2e_t_yr']),
                float(item['electricity_co2e_t_yr']),
                float(item['energy_total_co2e_t_yr']),
                float(item['transport_co2e_t_yr']),
                float(item['waste_co2e_t_yr']),
                float(item['livestock_co2e_t_yr']),
                float(item['total_co2e_t_yr']),
                float(item['per_capita_co2e_kg_yr'])
            ))
        conn.commit()
