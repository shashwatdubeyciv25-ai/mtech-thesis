-- ====================================================================
-- VARANASI DISTRICT VILLAGE-LEVEL ENVIRONMENTAL & CARBON DATABASE
-- Academic M.Tech Thesis Database Schema (SQLite)
-- ====================================================================

PRAGMA foreign_keys = ON;

-- 1. Core Village Master Table
CREATE TABLE IF NOT EXISTS villages (
    village_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_code TEXT UNIQUE NOT NULL,
    village_name TEXT NOT NULL,
    block_name TEXT NOT NULL,
    subdistrict TEXT,
    district TEXT NOT NULL DEFAULT 'Varanasi',
    state TEXT NOT NULL DEFAULT 'Uttar Pradesh',
    latitude REAL,
    longitude REAL,
    data_status TEXT DEFAULT 'BASELINE_SURVEY_DATA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_villages_code ON villages(village_code);
CREATE INDEX IF NOT EXISTS idx_villages_block ON villages(block_name);
CREATE INDEX IF NOT EXISTS idx_villages_name ON villages(village_name);

-- 2. Demographics Table
CREATE TABLE IF NOT EXISTS demographics (
    demography_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    total_residents INTEGER NOT NULL DEFAULT 0,
    total_households INTEGER DEFAULT 0,
    total_male INTEGER DEFAULT 0,
    total_female INTEGER DEFAULT 0,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);

-- 3. Land Use Table (Hectares)
CREATE TABLE IF NOT EXISTS land_use (
    land_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    total_area_ha REAL NOT NULL DEFAULT 0.0,
    builtup_area_ha REAL NOT NULL DEFAULT 0.0,
    agri_area_ha REAL NOT NULL DEFAULT 0.0,
    forest_area_ha REAL DEFAULT 0.0,
    barren_area_ha REAL DEFAULT 0.0,
    culturable_waste_ha REAL DEFAULT 0.0,
    fallow_land_ha REAL DEFAULT 0.0,
    remaining_area_ha REAL DEFAULT 0.0,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);

-- 4. Water Resources Table (Hectares)
CREATE TABLE IF NOT EXISTS water_resources (
    water_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    pond_area_ha REAL NOT NULL DEFAULT 0.0,
    river_area_ha REAL NOT NULL DEFAULT 0.0,
    canal_area_ha REAL NOT NULL DEFAULT 0.0,
    well_irrig_area_ha REAL DEFAULT 0.0,
    other_water_ha REAL DEFAULT 0.0,
    total_water_area_ha REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);

-- 5. Energy Consumption Table (Monthly)
CREATE TABLE IF NOT EXISTS energy_consumption (
    energy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    lpg_monthly_kg REAL NOT NULL DEFAULT 0.0,
    firewood_monthly_kg REAL NOT NULL DEFAULT 0.0,
    electricity_monthly_kwh REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);

-- 6. Solid Waste Table (Monthly)
CREATE TABLE IF NOT EXISTS waste_management (
    waste_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    waste_monthly_kg REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);

-- 7. Transport Activity Table
CREATE TABLE IF NOT EXISTS transport_activity (
    transport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    motorbikes_count INTEGER NOT NULL DEFAULT 0,
    petrol_monthly_litres REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);

-- 8. Livestock Population Table
CREATE TABLE IF NOT EXISTS livestock_population (
    livestock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    cows_count INTEGER NOT NULL DEFAULT 0,
    goats_count INTEGER NOT NULL DEFAULT 0,
    sheep_count INTEGER NOT NULL DEFAULT 0,
    total_livestock INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);

-- 9. Emission Factors Reference Table
CREATE TABLE IF NOT EXISTS emission_factors (
    factor_id INTEGER PRIMARY KEY,
    sector TEXT NOT NULL,
    activity TEXT NOT NULL,
    fuel_or_source TEXT NOT NULL,
    unit TEXT NOT NULL,
    emission_factor REAL NOT NULL,
    gas TEXT NOT NULL,
    co2e_factor REAL NOT NULL DEFAULT 1.0,
    reference_source TEXT,
    publication_year INTEGER
);

-- 10. Calculated GHG Emissions Table (Derived Values - t CO2e/year)
CREATE TABLE IF NOT EXISTS village_emissions (
    emission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL UNIQUE,
    lpg_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    firewood_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    electricity_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    energy_total_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    transport_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    waste_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    livestock_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    total_co2e_t_yr REAL NOT NULL DEFAULT 0.0,
    per_capita_co2e_kg_yr REAL NOT NULL DEFAULT 0.0,
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (village_id) REFERENCES villages(village_id) ON DELETE CASCADE
);