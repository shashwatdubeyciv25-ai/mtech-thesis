# ====================================================================
# modules/gis.py
# Interactive Folium GIS Map Module for Varanasi Villages
# ====================================================================
import os
import json
import folium
from folium import plugins
import geopandas as gpd
import pandas as pd
import branca.colormap as cm
from .database import get_villages_df, DEFAULT_DB_PATH

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISTRICT_GEOJSON = os.path.join(BASE_DIR, 'data', 'processed', 'varanasi_district.geojson')
BLOCKS_GEOJSON = os.path.join(BASE_DIR, 'data', 'processed', 'varanasi_blocks.geojson')
VILLAGES_GEOJSON = os.path.join(BASE_DIR, 'data', 'processed', 'varanasi_villages_optimized.geojson')

def load_spatial_layers(db_path=DEFAULT_DB_PATH):
    """Loads GeoJSON files and merges live database attributes."""
    if not os.path.exists(VILLAGES_GEOJSON):
        raise FileNotFoundError(f"Village GeoJSON not found at: {VILLAGES_GEOJSON}")
    
    gdf_villages = gpd.read_file(VILLAGES_GEOJSON)
    # Ensure village_code is string
    gdf_villages['village_code'] = gdf_villages['village_code'].astype(str).str.strip()
    
    # Merge with current database attributes
    df_db = get_villages_df(db_path)
    df_db['village_code'] = df_db['village_code'].astype(str).str.strip()
    
    # Drop overlapping columns before merge
    drop_cols = [c for c in ['village_name', 'block_name', 'subdistrict', 'residents', 'area_ha'] if c in df_db.columns and c in gdf_villages.columns]
    gdf_merged = gdf_villages.drop(columns=drop_cols, errors='ignore').merge(df_db, on='village_code', how='left')
    return gdf_merged

def create_folium_map(gdf, selected_village_code=None, thematic_metric="Total Carbon Emission (t CO2e/yr)", block_filter="All Blocks"):
    """
    Builds a Folium interactive map with thematic layers, tooltips, and selected village highlight.
    """
    # Filter by block if selected
    if block_filter and block_filter != "All Blocks":
        display_gdf = gdf[gdf['block_name'] == block_filter].copy()
    else:
        display_gdf = gdf.copy()
        
    if display_gdf.empty:
        display_gdf = gdf.copy()

    # Determine center coordinates
    center_lat = 25.37
    center_lon = 82.93
    zoom_start = 10 if (not block_filter or block_filter == "All Blocks") else 11
    
    # If a village is selected, center on it
    if selected_village_code:
        sel_row = gdf[gdf['village_code'] == str(selected_village_code)]
        if not sel_row.empty:
            center_lat = float(sel_row['latitude'].iloc[0])
            center_lon = float(sel_row['longitude'].iloc[0])
            zoom_start = 13

    # Initialize Base Map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )

    # Base layers
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://carto.com/">CARTO</a> Positron',
        name='Light Positron (Default GIS)',
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='&copy; OpenStreetMap contributors',
        name='OpenStreetMap',
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Satellite World Imagery',
        name='Satellite Imagery (Esri)',
        control=True
    ).add_to(m)

    # 1. District Outer Boundary Layer
    if os.path.exists(DISTRICT_GEOJSON):
        folium.GeoJson(
            DISTRICT_GEOJSON,
            name='Varanasi District Boundary',
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#1a237e',
                'weight': 3,
                'dashArray': '6, 6'
            },
            control=True
        ).add_to(m)

    # 2. Block Boundaries Layer
    if os.path.exists(BLOCKS_GEOJSON):
        folium.GeoJson(
            BLOCKS_GEOJSON,
            name='Block Boundaries',
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#d84315',
                'weight': 2,
                'dashArray': '3, 4'
            },
            tooltip=folium.GeoJsonTooltip(fields=['block_name'], aliases=['Block:']),
            control=True
        ).add_to(m)

    # 3. Thematic Metric Configuration
    metric_configs = {
        "Total Carbon Emission (t CO2e/yr)": {
            'col': 'total_co2e_t_yr',
            'colors': ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'],
            'caption': 'Total GHG Emission (t CO2e/yr)'
        },
        "Per Capita Emission (kg CO2e/person/yr)": {
            'col': 'per_capita_co2e_kg_yr',
            'colors': ['#e0f3f8', '#99d594', '#fee08b', '#fc8d59', '#d53e4f'],
            'caption': 'Per Capita GHG (kg CO2e/yr)'
        },
        "Agricultural Area (ha)": {
            'col': 'agri_area_ha',
            'colors': ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
            'caption': 'Net Sown Agricultural Area (ha)'
        },
        "Electricity Consumption (kWh/month)": {
            'col': 'electricity_monthly_kwh',
            'colors': ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
            'caption': 'Electricity Consumption (kWh/mo)'
        },
        "Solid Waste Generation (kg/month)": {
            'col': 'waste_monthly_kg',
            'colors': ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
            'caption': 'Solid Waste Generated (kg/mo)'
        },
        "Livestock Population (Count)": {
            'col': 'total_livestock',
            'colors': ['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f'],
            'caption': 'Total Livestock (Cattle/Goats/Sheep)'
        }
    }

    # Color mapping
    cfg = metric_configs.get(thematic_metric)
    color_map = None
    if cfg and cfg['col'] in display_gdf.columns:
        vals = display_gdf[cfg['col']].fillna(0)
        min_v = float(vals.min())
        max_v = float(vals.max())
        if max_v > min_v:
            color_map = cm.LinearColormap(
                colors=cfg['colors'],
                vmin=min_v,
                vmax=max_v,
                caption=cfg['caption']
            )

    # Style function
    sel_code_str = str(selected_village_code) if selected_village_code else None
    
    def get_style(feature):
        props = feature.get('properties', {})
        vcode = str(props.get('village_code', '')).strip()
        
        # Highlight selected village with gold border
        if sel_code_str and vcode == sel_code_str:
            return {
                'fillColor': '#ffd600',
                'color': '#e65100',
                'weight': 4,
                'fillOpacity': 0.85
            }
        
        fill_c = '#a5d6a7'
        if color_map and cfg:
            val = props.get(cfg['col'], 0)
            if val is not None:
                try:
                    fill_c = color_map(float(val))
                except Exception:
                    pass
        
        return {
            'fillColor': fill_c,
            'color': '#37474f',
            'weight': 0.7,
            'fillOpacity': 0.65
        }

    # Prepare GeoJSON string
    village_geojson_data = json.loads(display_gdf.to_json())

    # Add Villages GeoJson layer
    tooltip_fields = ['village_name', 'block_name', 'village_code', 'total_residents', 'total_area_ha']
    tooltip_aliases = ['Village:', 'Block:', 'Census Code:', 'Residents:', 'Area (ha):']
    
    if cfg and cfg['col'] in display_gdf.columns:
        tooltip_fields.append(cfg['col'])
        tooltip_aliases.append(cfg['caption'] + ':')

    villages_layer = folium.GeoJson(
        village_geojson_data,
        name='Varanasi Villages',
        style_function=get_style,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=True
        ),
        popup=folium.GeoJsonPopup(
            fields=['village_name', 'block_name', 'total_residents', 'total_area_ha', 'total_co2e_t_yr'],
            aliases=['Village:', 'Block:', 'Residents:', 'Area (ha):', 'Total CO2e (t/yr):'],
            labels=True
        ),
        control=True
    ).add_to(m)

    # Add colormap legend
    if color_map:
        color_map.add_to(m)

    # Add marker on selected village centroid
    if selected_village_code:
        sel_row = gdf[gdf['village_code'] == str(selected_village_code)]
        if not sel_row.empty:
            v_name = sel_row['village_name'].iloc[0]
            b_name = sel_row['block_name'].iloc[0]
            lat = float(sel_row['latitude'].iloc[0])
            lon = float(sel_row['longitude'].iloc[0])
            co2 = float(sel_row['total_co2e_t_yr'].iloc[0] if 'total_co2e_t_yr' in sel_row.columns else 0)
            
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>Selected: {v_name}</b><br>Block: {b_name}<br>Total CO2e: {co2:,.1f} t/yr",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

    # Add Layer Control and Fullscreen
    folium.LayerControl(position='topright').add_to(m)
    plugins.Fullscreen(position='topleft').add_to(m)
    
    return m
