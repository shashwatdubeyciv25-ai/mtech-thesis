# scripts/init_database_and_emissions.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import init_db, load_emission_factors, import_village_excel, get_villages_df
from modules.carbon import recompute_and_save_all_emissions

print("1. Initializing SQLite tables...")
init_db()
print("2. Loading emission factors reference...")
load_emission_factors()
print("3. Importing 1,334 villages from Excel...")
rep = import_village_excel()
print(f"   Import complete: {rep['inserted']} inserted, {rep['updated']} updated, {len(rep['warnings'])} warnings.")
print("4. Calculating greenhouse gas emissions for all villages...")
count = recompute_and_save_all_emissions()
print(f"   Emissions computed for {count} villages.")

df = get_villages_df()
print("5. Verification Sample:")
print(df[['village_code', 'village_name', 'block_name', 'total_residents', 'total_area_ha', 'total_co2e_t_yr', 'per_capita_co2e_kg_yr']].head(5))
print("\nDistrict Emission Summary:")
print(f"   Total Varanasi Emissions: {df['total_co2e_t_yr'].sum():,.2f} t CO2e/year")
print(f"   Average Per Capita Emission: {df['per_capita_co2e_kg_yr'].mean():,.2f} kg CO2e/person/year")
