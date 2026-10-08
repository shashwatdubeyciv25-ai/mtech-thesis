# VARANASI DISTRICT — VILLAGE ENVIRONMENT & CARBON DASHBOARD

### *M.Tech Thesis Research Project*
**Village-Level Environmental Resource Assessment and Carbon Emission Modeling in Varanasi District, Uttar Pradesh, India**

---

## 🌿 1. Overview
This application is a specialized Geographic Information System (GIS) and Environmental Database Dashboard built specifically for **Varanasi District** and its **1,334 revenue villages**.

The system integrates:
* **Spatial Cadastral Boundaries** from the **Survey of India (SOI)**
* **Census 2011 & Field Survey Database** (demographics, land use, water bodies, household energy, transportation, municipal solid waste, and livestock)
* **IPCC Tier-1 & Central Electricity Authority (CEA) GHG Accounting Models**
* **Interactive Web GIS (Folium/Leaflet)** with synchronized village selectors and thematic choropleth layers
* **Comparative Analytics & Ranking** across all Community Development Blocks
* **Academic PDF Reporting** (ReportLab) adhering to MoEFCC reporting standards

---

## 🏛️ 2. Administrative Hierarchy & Coverage
* **Country:** India
* **State:** Uttar Pradesh
* **District:** Varanasi (`dtcode: 187`)
* **Community Development Blocks (8 Blocks + Sadar Peri-Urban):**
  1. Arajiline (220 villages)
  2. Pindra (191 villages)
  3. Sevapuri (185 villages)
  4. Harahua (173 villages)
  5. Cholapur (148 villages)
  6. Baragaon (139 villages)
  7. Chiraigaon (133 villages)
  8. Kashi Vidyapeeth (106 villages)
  9. Sadar Peri-Urban / ULB (39 mauzas)
* **Total Village Polygons:** **1,334 features**

---

## 📂 3. Project Directory Structure
```text
dashboard main/
│
├── app.py                         # Master Streamlit Application
├── requirements.txt               # Python package dependencies
├── README.md                      # Project thesis documentation
│
├── VARANASI_VILLages/
│   └── VARANASI_VILL.gpkg         # Primary Survey of India Cadastral GPKG
│
├── data/
│   ├── raw/
│   │   └── village_data.xlsx      # Master survey database (1,334 villages)
│   └── processed/
│       ├── varanasi_district.geojson # Dissolved District Boundary
│       ├── varanasi_blocks.geojson   # Dissolved 8 Block Boundaries
│       └── varanasi_villages_optimized.geojson # Fast Web GIS Polygons
│
├── database/
│   ├── database.db                # SQLite Relational Database (10 tables)
│   └── schema.sql                 # DDL Schema with Foreign Keys & Indexes
│
├── config/
│   └── emission_factors.csv       # Configurable IPCC & CEA Emission Factors
│
├── modules/
│   ├── database.py                # Database connection, queries & Excel upserts
│   ├── carbon.py                  # GHG emissions accounting engine
│   ├── gis.py                     # Folium mapping & thematic styling
│   └── reporting.py               # ReportLab Academic PDF generator
│
└── scripts/
    └── init_database_and_emissions.py # Database & Carbon pipeline initializer
```

---

## 🔬 4. Methodology & Accounting Standards
The application enforces a rigorous distinction between:
1. **Observed Survey / Census Data**: Physical measurements (kg LPG, kWh electricity, hectares of cropped land, head count of livestock).
2. **Derived Output**: Mathematical greenhouse gas emissions ($t\text{CO}_2\text{e/year}$) computed via:

$$\text{Emissions } (\text{t CO}_2\text{e/year}) = \frac{\text{Annual Activity Data} \times \text{Emission Factor}}{1000}$$

### Emission Factor Reference Standards:
* **Grid Electricity:** $0.820 \text{ kg CO}_2/\text{kWh}$ (*Central Electricity Authority CEA CO2 Baseline Database for Indian Power Sector Version 20.0, 2024*).
* **LPG Domestic:** $2.984 \text{ kg CO}_2\text{e/kg}$ (*IPCC 2006 Guidelines for National GHG Inventories, Vol 2 Energy*).
* **Biomass Firewood:** $1.747 \text{ kg CO}_2\text{e/kg}$ (*MoEFCC & IPCC Biomass default combustion baseline*).
* **2-Wheeler Petrol:** $2.310 \text{ kg CO}_2\text{e/Litre}$ (*IPCC 2006 Mobile Road Transport*).
* **Rural Solid Waste:** $0.450 \text{ kg CO}_2\text{e/kg}$ (*IPCC 2006 First Order Decay model simplified default*).
* **Dairy Cattle / Cows:** $980.0 \text{ kg CO}_2\text{e/head/yr}$ (*IPCC 2006 Vol 4 AFOLU Indian Cattle Enteric + Manure*).
* **Goats & Sheep:** $145.6 \text{ kg CO}_2\text{e/head/yr}$ (*IPCC 2006 Vol 4 AFOLU Small Ruminants*).

---

## 🚀 5. Execution on Windows

Open PowerShell or Command Prompt in the project folder:

```powershell
# 1. (Optional) Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Dashboard
streamlit run app.py
```
The browser will automatically open at `http://localhost:8501`.
