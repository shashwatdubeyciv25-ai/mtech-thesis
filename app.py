# ====================================================================
# app.py
# VARANASI DISTRICT — VILLAGE ENVIRONMENT & CARBON DASHBOARD
# Master Application (Streamlit + Folium + Plotly + GeoPandas + SQLite)
# ====================================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import io
from datetime import datetime

from modules.database import (
    get_villages_df, get_village_full_details, get_blocks_list,
    import_village_excel, load_emission_factors, init_db, DEFAULT_DB_PATH
)
from modules.carbon import get_emission_factors, calculate_single_village, recompute_and_save_all_emissions
from modules.gis import load_spatial_layers, create_folium_map
from modules.reporting import generate_village_pdf, export_village_csv
from modules.icons import get_lucide_icon
from streamlit_folium import st_folium

# Page Configuration
st.set_page_config(
    page_title="Varanasi Village Environment & Carbon Dashboard",
    page_icon="assets/dashboard_icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title { color: #1b5e20; font-weight: 800; font-size: 26px; margin-bottom: 2px; }
    .sub-title { color: #455a64; font-size: 14px; margin-bottom: 12px; }
    .metric-card {
        background-color: #ffffff; border-radius: 8px; padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid #2e7d32; margin-bottom: 10px;
    }
    .metric-label { font-size: 11px; text-transform: uppercase; color: #546e7a; font-weight: 600; }
    .metric-val { font-size: 22px; font-weight: 700; color: #1b5e20; margin-top: 2px; }
    .metric-sub { font-size: 11px; color: #78909c; }
    .badge-observed { background-color: #e3f2fd; color: #0d47a1; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .badge-derived { background-color: #e8f5e9; color: #1b5e20; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .village-banner {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        color: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 15px;
    }
    /* Sidebar Navigation: Replace radio circle with Lucide arrow-style icons */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 3px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"],
    [data-testid="stSidebar"] div[data-testid="stRadio"] label {
        display: flex !important;
        align-items: center !important;
        padding: 7px 12px !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        transition: all 0.15s ease-in-out !important;
        background-color: transparent !important;
        margin-bottom: 2px !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"]:hover,
    [data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background-color: #f1f8e9 !important;
    }

    /* 1. Ensure the navigation text is ALWAYS explicitly visible and readable */
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
        display: inline-block !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: #263238 !important;
        font-size: 14px !important;
        line-height: 1.4 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 2. Target the radio circle element directly and morph it into an arrow icon */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div:has(+ [data-testid="stMarkdownContainer"]),
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[class*="etak9234"] {
        border-radius: 0 !important;
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        width: 18px !important;
        height: 18px !important;
        min-width: 18px !important;
        margin-right: 8px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 16px 16px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2378909c' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m9 18 6-6-6-6'/%3E%3C/svg%3E") !important;
        transition: transform 0.15s ease, background-image 0.15s ease !important;
    }

    /* Hide inner circle dot inside the radio circle */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div:has(+ [data-testid="stMarkdownContainer"]) *,
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[class*="etak9234"] *,
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[class*="etak9235"] {
        display: none !important;
    }

    /* 3. Hover state: arrow shifts right and turns green */
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"]:hover div:has(+ [data-testid="stMarkdownContainer"]),
    [data-testid="stSidebar"] div[data-testid="stRadio"] label:hover div:has(+ [data-testid="stMarkdownContainer"]),
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"]:hover div[class*="etak9234"] {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%231b5e20' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m9 18 6-6-6-6'/%3E%3C/svg%3E") !important;
        transform: translateX(3px) !important;
    }

    /* 4. Active selected state: green highlight, directional arrow, bold text */
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"]:has(input:checked),
    [data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #e8f5e9 !important;
        border-left: 3px solid #1b5e20 !important;
    }

    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"]:has(input:checked) div:has(+ [data-testid="stMarkdownContainer"]),
    [data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) div:has(+ [data-testid="stMarkdownContainer"]),
    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"]:has(input:checked) div[class*="etak9234"] {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%231b5e20' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14'/%3E%3Cpath d='m12 5 7 7-7 7'/%3E%3C/svg%3E") !important;
        transform: translateX(3px) !important;
    }

    [data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stRadioOption"]:has(input:checked) [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) [data-testid="stMarkdownContainer"] p {
        color: #1b5e20 !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# Database & Spatial Layer Cache
@st.cache_data(show_spinner=False)
def load_data():
    df = get_villages_df()
    blocks = ['All Blocks'] + get_blocks_list()
    return df, blocks

@st.cache_resource(show_spinner=False)
def load_gis():
    return load_spatial_layers()

df_all, block_list = load_data()

if 'selected_village_code' not in st.session_state:
    st.session_state.selected_village_code = "208818"  # Default: Ausanpur
if 'selected_block' not in st.session_state:
    st.session_state.selected_block = "All Blocks"

# Top Header Bar & Global Controls
header_dashboard_icon = get_lucide_icon("layout-dashboard", size=28, color="#1b5e20", stroke_width=2.2, style="vertical-align: -5px; margin-right: 8px; display: inline-block;")
st.markdown(f'<div class="main-title">{header_dashboard_icon}VARANASI DISTRICT — VILLAGE ENVIRONMENT & CARBON DASHBOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">M.Tech Thesis Project: Village-Level Environmental Resource Assessment and Carbon Emission Modeling</div>', unsafe_allow_html=True)

head_col1, head_col2, head_col3, head_col4, head_col5, head_col6 = st.columns([1.5, 1.2, 2.0, 2.8, 1.2, 1.3])

with head_col1:
    current_year = datetime.now().year
    sel_year = st.selectbox("📅 Year", [f"{current_year} (Current)", "2023", "2011 (Baseline)"], index=0)

with head_col2:
    sel_season = st.selectbox("🌦️ Season", ["Annual", "Kharif", "Rabi", "Zaid"], index=0)

with head_col3:
    block_idx = 0
    if st.session_state.selected_block in block_list:
        block_idx = block_list.index(st.session_state.selected_block)
    selected_block = st.selectbox("📍 Select Block", block_list, index=block_idx)
    if selected_block != st.session_state.selected_block:
        st.session_state.selected_block = selected_block
        if selected_block != "All Blocks":
            sub_v = df_all[df_all['block_name'] == selected_block]
            if not sub_v.empty:
                st.session_state.selected_village_code = str(sub_v['village_code'].iloc[0])
        st.rerun()

if st.session_state.selected_block == "All Blocks":
    df_filtered_villages = df_all.copy()
else:
    df_filtered_villages = df_all[df_all['block_name'] == st.session_state.selected_block].copy()

village_options = {}
for _, r in df_filtered_villages.iterrows():
    vcode = str(r['village_code'])
    village_options[vcode] = f"{r['village_name']} ({r['block_name']} - {vcode})"

vcode_list = list(village_options.keys())
current_vcode = st.session_state.selected_village_code
if current_vcode not in vcode_list and vcode_list:
    current_vcode = vcode_list[0]
    st.session_state.selected_village_code = current_vcode

with head_col4:
    selected_vcode = st.selectbox(
        "Select Village",
        options=vcode_list,
        format_func=lambda x: village_options.get(x, x),
        index=vcode_list.index(current_vcode) if current_vcode in vcode_list else 0
    )
    if selected_vcode != st.session_state.selected_village_code:
        st.session_state.selected_village_code = selected_vcode
        st.rerun()

active_village = get_village_full_details(st.session_state.selected_village_code)
if not active_village and not df_all.empty:
    active_village = get_village_full_details(df_all['village_code'].iloc[0])
    st.session_state.selected_village_code = str(active_village['village_code'])

with head_col5:
    st.write("")
    st.write("")
    if st.button("⚖️ Compare", use_container_width=True):
        st.session_state.nav_page = "Village Comparison"

with head_col6:
    st.write("")
    st.write("")
    if active_village:
        pdf_bytes = generate_village_pdf(active_village)
        st.download_button(
            label="📥 Report (PDF)",
            data=pdf_bytes,
            file_name=f"Report_{active_village['village_name']}_{active_village['village_code']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Left Sidebar Navigation
with st.sidebar:
    sidebar_nav_icon = get_lucide_icon("panel-left", size=20, color="#1b5e20", stroke_width=2.2, style="vertical-align: -3px; margin-right: 6px; display: inline-block;")
    st.markdown(f"### {sidebar_nav_icon}Carbon Dashboard", unsafe_allow_html=True)
    pages = [
        "Overview", "Village Map", "Demography", "Land & Water",
        "Energy", "Transport", "Waste", "Livestock",
        "Carbon Emission", "Village Comparison", "Village Ranking",
        "Reports", "Excel Import", "Settings / Methodology"
    ]
    if 'nav_page' not in st.session_state:
        st.session_state.nav_page = "Overview"
    nav_selection = st.radio(
        "Go to Page",
        pages,
        index=pages.index(st.session_state.nav_page) if st.session_state.nav_page in pages else 0,
        label_visibility="collapsed"
    )
    st.session_state.nav_page = nav_selection
    st.markdown("---")
    if active_village:
        st.markdown(f"**Active Village:** {active_village['village_name']}")
        st.markdown(f"**Block:** {active_village['block_name']}")
        st.markdown(f"**Census Code:** `{active_village['village_code']}`")
        st.markdown(f"**Residents:** {active_village.get('total_residents', 0):,}")
        st.markdown(f"**Total Area:** {active_village.get('total_area_ha', 0):,.1f} ha")
        st.markdown(f"**Total Carbon:** **{active_village.get('total_co2e_t_yr', 0):,.1f} t CO2e/yr**")
        st.markdown(f"**Per Capita:** {active_village.get('per_capita_co2e_kg_yr', 0):,.1f} kg/yr")
    st.markdown("---")
    st.caption("Varanasi Village Carbon Dashboard v1.0\nM.Tech Research Project\nSurvey of India & IPCC Tier-1")

if active_village and st.session_state.nav_page not in ["Overview", "Village Ranking", "Excel Import", "Settings / Methodology"]:
    village_home_icon = get_lucide_icon("home", size=20, color="#ffffff", stroke_width=2.2, style="vertical-align: -3px; margin-right: 6px; display: inline-block;")
    st.markdown(f"""
    <div class="village-banner">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:18px; font-weight:700; display:inline-flex; align-items:center;">{village_home_icon}{active_village['village_name']}</span>
                <span style="margin-left:12px; font-size:13px; opacity:0.9;">Block: <b>{active_village['block_name']}</b> | Tehsil: <b>{active_village['subdistrict']}</b> | Code: <b>{active_village['village_code']}</b></span>
            </div>
            <div>
                <span style="font-size:14px; background:rgba(255,255,255,0.2); padding:4px 10px; border-radius:4px;">
                    🌿 <b>{active_village.get('total_co2e_t_yr', 0):,.1f} t CO2e/yr</b> ({active_village.get('per_capita_co2e_kg_yr', 0):,.1f} kg/person)
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==================== PAGE: OVERVIEW ====================
if st.session_state.nav_page == "Overview":
    overview_dash_icon = get_lucide_icon("layout-dashboard", size=24, color="#1b5e20", stroke_width=2.2, style="vertical-align: -4px; margin-right: 8px; display: inline-block;")
    st.markdown(f'<h3 style="color:#1b5e20; display:flex; align-items:center;">{overview_dash_icon}Varanasi District Environmental & Carbon Overview</h3>', unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    tot_villages = len(df_all)
    tot_pop = df_all['total_residents'].sum()
    tot_area_dist = df_all['total_area_ha'].sum()
    tot_emissions = df_all['total_co2e_t_yr'].sum()
    avg_per_cap = df_all['per_capita_co2e_kg_yr'].mean()
    
    with kpi1:
        st.markdown(f'''<div class="metric-card"><div class="metric-label">Total Villages</div><div class="metric-val">{tot_villages:,}</div><div class="metric-sub">Cadastral Polygons</div></div>''', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'''<div class="metric-card"><div class="metric-label">Total Population</div><div class="metric-val">{tot_pop:,.0f}</div><div class="metric-sub">Census / Surveyed</div></div>''', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'''<div class="metric-card"><div class="metric-label">Geographical Area</div><div class="metric-val">{tot_area_dist:,.1f} ha</div><div class="metric-sub">Varanasi District</div></div>''', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #d32f2f;"><div class="metric-label">Total GHG Emissions</div><div class="metric-val">{tot_emissions:,.0f} t</div><div class="metric-sub">t CO2e / yr (IPCC)</div></div>''', unsafe_allow_html=True)
    with kpi5:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #f57c00;"><div class="metric-label">Mean Per Capita GHG</div><div class="metric-val">{avg_per_cap:,.1f} kg</div><div class="metric-sub">kg CO2e / resident / yr</div></div>''', unsafe_allow_html=True)

    st.write("")
    c_left, c_right = st.columns([1.1, 0.9])
    with c_left:
        st.markdown("##### 🏛️ Block-Wise Carbon Emissions (t CO2e/year)")
        df_block_em = df_all.groupby('block_name')['total_co2e_t_yr'].sum().reset_index().sort_values(by='total_co2e_t_yr', ascending=False)
        fig_block = px.bar(df_block_em, x='block_name', y='total_co2e_t_yr', color='total_co2e_t_yr', color_continuous_scale='Greens', text_auto='.2s')
        fig_block.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=40), coloraxis_showscale=False)
        st.plotly_chart(fig_block, use_container_width=True)

    with c_right:
        st.markdown("##### 🍩 District Sectoral GHG Breakdown")
        sec_dict = {
            'LPG Energy': df_all['lpg_co2e_t_yr'].sum() if 'lpg_co2e_t_yr' in df_all.columns else 0,
            'Firewood Energy': df_all['firewood_co2e_t_yr'].sum() if 'firewood_co2e_t_yr' in df_all.columns else 0,
            'Electricity Energy': df_all['electricity_co2e_t_yr'].sum() if 'electricity_co2e_t_yr' in df_all.columns else 0,
            'Transport (Petrol)': df_all['transport_co2e_t_yr'].sum() if 'transport_co2e_t_yr' in df_all.columns else 0,
            'Solid Waste': df_all['waste_co2e_t_yr'].sum() if 'waste_co2e_t_yr' in df_all.columns else 0,
            'Livestock Enteric': df_all['livestock_co2e_t_yr'].sum() if 'livestock_co2e_t_yr' in df_all.columns else 0
        }
        df_sec = pd.DataFrame(list(sec_dict.items()), columns=['Sector', 'Emissions_t'])
        fig_sec = px.pie(df_sec, names='Sector', values='Emissions_t', color_discrete_sequence=px.colors.qualitative.Prism, hole=0.45)
        fig_sec.update_traces(textposition='inside', textinfo='percent+label')
        fig_sec.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=20), showlegend=False)
        st.plotly_chart(fig_sec, use_container_width=True)

# ==================== PAGE: VILLAGE MAP ====================
elif st.session_state.nav_page == "Village Map":
    st.markdown("### 🗺️ Varanasi District Interactive Village GIS Map")
    m_col1, m_col2 = st.columns([3.2, 1])
    with m_col2:
        st.markdown("#### 🎨 Thematic Map Layers")
        thematic_layer = st.selectbox(
            "Select Thematic Metric to Classify:",
            [
                "Total Carbon Emission (t CO2e/yr)",
                "Per Capita Emission (kg CO2e/person/yr)",
                "Agricultural Area (ha)",
                "Electricity Consumption (kWh/month)",
                "Solid Waste Generation (kg/month)",
                "Livestock Population (Count)"
            ]
        )
        st.caption("Color gradient dynamically adjusts based on metric values across village polygons.")
        st.markdown("---")
        if active_village:
            st.markdown(f"**Name:** {active_village['village_name']}")
            st.markdown(f"**Block:** {active_village['block_name']}")
            st.markdown(f"**Code:** `{active_village['village_code']}`")
            st.markdown(f"**Residents:** {active_village['total_residents']:,}")
            st.markdown(f"**Total Area:** {active_village['total_area_ha']:.1f} ha")
            st.markdown(f"**Emissions:** {active_village.get('total_co2e_t_yr', 0):.1f} t CO2e/yr")
            st.markdown(f"**Per Capita:** {active_village.get('per_capita_co2e_kg_yr', 0):.1f} kg/yr")
        st.markdown("---")
        st.info("💡 **Interactive Tip:** Click any village polygon on the map or use the header dropdown to update the active selection.")

    with m_col1:
        gdf_spatial = load_gis()
        with st.spinner("Rendering GIS Map with Village Polygons..."):
            folium_map = create_folium_map(
                gdf_spatial,
                selected_village_code=st.session_state.selected_village_code,
                thematic_metric=thematic_layer,
                block_filter=st.session_state.selected_block
            )
            map_data = st_folium(folium_map, width="100%", height=620, returned_objects=["last_object_clicked"])
            if map_data and map_data.get("last_object_clicked"):
                click_props = map_data["last_object_clicked"].get("properties", {})
                clicked_vcode = str(click_props.get("village_code", "")).strip()
                if clicked_vcode and clicked_vcode != st.session_state.selected_village_code:
                    st.session_state.selected_village_code = clicked_vcode
                    st.rerun()

# ==================== PAGE: DEMOGRAPHY ====================
elif st.session_state.nav_page == "Demography":
    st.markdown("### 👥 Demographic Profile")
    st.markdown('<span class="badge-observed">OBSERVED CENSUS / FIELD SURVEY DATA</span>', unsafe_allow_html=True)
    st.write("")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Residents", f"{active_village.get('total_residents', 0):,}")
    with col2:
        st.metric("Total Households", f"{active_village.get('total_households', 0):,}")
    with col3:
        st.metric("Male Residents", f"{active_village.get('total_male', 0):,}")
    with col4:
        st.metric("Female Residents", f"{active_village.get('total_female', 0):,}")
    st.write("")
    d_left, d_right = st.columns(2)
    with d_left:
        fig_gender = px.pie(names=['Male Residents', 'Female Residents'], values=[active_village.get('total_male', 0), active_village.get('total_female', 0)], title="Gender Composition", color_discrete_sequence=['#1976d2', '#e91e63'], hole=0.4)
        fig_gender.update_layout(height=320)
        st.plotly_chart(fig_gender, use_container_width=True)
    with d_right:
        blk_villages = df_all[df_all['block_name'] == active_village['block_name']]
        avg_pop = blk_villages['total_residents'].mean()
        avg_hh = blk_villages['total_households'].mean()
        comp_df = pd.DataFrame({'Category': ['Residents', 'Households'], 'This Village': [active_village.get('total_residents', 0), active_village.get('total_households', 0)], f"{active_village['block_name']} Mean": [round(avg_pop), round(avg_hh)]})
        fig_comp = px.bar(comp_df, x='Category', y=['This Village', f"{active_village['block_name']} Mean"], barmode='group', title=f"Comparison with {active_village['block_name']} Benchmark", color_discrete_sequence=['#2e7d32', '#90a4ae'])
        fig_comp.update_layout(height=320)
        st.plotly_chart(fig_comp, use_container_width=True)

# ==================== PAGE: LAND & WATER ====================
elif st.session_state.nav_page == "Land & Water":
    st.markdown("### 🌾 Land Use & Water Resources Inventory")
    st.markdown('<span class="badge-observed">OBSERVED CENSUS / GIS SURVEY DATA</span>', unsafe_allow_html=True)
    st.write("")
    lw1, lw2, lw3, lw4 = st.columns(4)
    with lw1:
        st.metric("Total Geographical Area", f"{active_village.get('total_area_ha', 0):,.2f} ha")
    with lw2:
        st.metric("Agricultural Land Area", f"{active_village.get('agri_area_ha', 0):,.2f} ha")
    with lw3:
        st.metric("Built-up / Settlement Area", f"{active_village.get('builtup_area_ha', 0):,.2f} ha")
    with lw4:
        st.metric("Surface Water Bodies", f"{active_village.get('total_water_area_ha', 0):,.2f} ha")
    st.write("")
    lw_left, lw_right = st.columns(2)
    with lw_left:
        land_cats = {'Agricultural': active_village.get('agri_area_ha', 0), 'Built-up': active_village.get('builtup_area_ha', 0), 'Forest': active_village.get('forest_area_ha', 0), 'Barren': active_village.get('barren_area_ha', 0), 'Remaining/Other': active_village.get('remaining_area_ha', 0)}
        df_land = pd.DataFrame(list(land_cats.items()), columns=['Class', 'Area_ha'])
        df_land = df_land[df_land['Area_ha'] > 0]
        fig_land = px.pie(df_land, names='Class', values='Area_ha', title=f"Land Use Distribution ({active_village['village_name']})", color_discrete_sequence=['#4caf50', '#ff9800', '#2e7d32', '#8d6e63', '#90a4ae'], hole=0.45)
        fig_land.update_layout(height=340)
        st.plotly_chart(fig_land, use_container_width=True)
    with lw_right:
        water_cats = {'Ponds / Tanks': active_village.get('pond_area_ha', 0), 'Canals / Drainage': active_village.get('canal_area_ha', 0), 'Rivers / Streams': active_village.get('river_area_ha', 0), 'Tube-wells / Wells': active_village.get('well_irrig_area_ha', 0)}
        df_water = pd.DataFrame(list(water_cats.items()), columns=['Water_Type', 'Area_ha'])
        fig_water = px.bar(df_water, x='Water_Type', y='Area_ha', title="Water Resources Breakdown (Hectares)", color='Water_Type', color_discrete_sequence=['#0288d1', '#0097a7', '#00acc1', '#26c6da'], text_auto='.2f')
        fig_water.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig_water, use_container_width=True)

# ==================== PAGE: ENERGY ====================
elif st.session_state.nav_page == "Energy":
    st.markdown("### ⚡ Household & Agricultural Energy Consumption")
    st.markdown('<span class="badge-observed">OBSERVED ACTIVITY SURVEY DATA</span>', unsafe_allow_html=True)
    st.write("")
    e1, e2, e3 = st.columns(3)
    with e1:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #f57c00;"><div class="metric-label">LPG Consumption</div><div class="metric-val">{active_village.get("lpg_monthly_kg", 0):,.1f} kg</div><div class="metric-sub">Monthly Volume ({active_village.get("lpg_monthly_kg", 0)*12:,.1f} kg/yr)</div></div>''', unsafe_allow_html=True)
    with e2:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #8d6e63;"><div class="metric-label">Firewood / Biomass Burned</div><div class="metric-val">{active_village.get("firewood_monthly_kg", 0):,.1f} kg</div><div class="metric-sub">Monthly Volume ({active_village.get("firewood_monthly_kg", 0)*12:,.1f} kg/yr)</div></div>''', unsafe_allow_html=True)
    with e3:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #0288d1;"><div class="metric-label">Electricity Consumption</div><div class="metric-val">{active_village.get("electricity_monthly_kwh", 0):,.1f} kWh</div><div class="metric-sub">Monthly Grid Usage ({active_village.get("electricity_monthly_kwh", 0)*12:,.1f} kWh/yr)</div></div>''', unsafe_allow_html=True)
    st.write("")
    ec_left, ec_right = st.columns(2)
    with ec_left:
        df_fuels = pd.DataFrame({'Fuel Source': ['LPG (kg/month)', 'Firewood (kg/month)'], 'Consumption': [active_village.get('lpg_monthly_kg', 0), active_village.get('firewood_monthly_kg', 0)]})
        fig_fuels = px.bar(df_fuels, x='Fuel Source', y='Consumption', color='Fuel Source', title="Biomass vs LPG Solid/Gas Fuel Volumes (kg/month)", color_discrete_sequence=['#f57c00', '#8d6e63'], text_auto='.1f')
        fig_fuels.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig_fuels, use_container_width=True)
    with ec_right:
        blk_elec_avg = df_all[df_all['block_name'] == active_village['block_name']]['electricity_monthly_kwh'].mean()
        df_elec = pd.DataFrame({'Scope': [active_village['village_name'], f"{active_village['block_name']} Mean"], 'Electricity_kWh_mo': [active_village.get('electricity_monthly_kwh', 0), round(blk_elec_avg, 1)]})
        fig_elec = px.bar(df_elec, x='Scope', y='Electricity_kWh_mo', color='Scope', title="Electricity Demand vs Block Benchmark (kWh/month)", color_discrete_sequence=['#0288d1', '#78909c'], text_auto='.1f')
        fig_elec.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig_elec, use_container_width=True)

# ==================== PAGE: TRANSPORT ====================
elif st.session_state.nav_page == "Transport":
    st.markdown("### 🛵 Rural Transportation & Fuel Consumption")
    st.markdown('<span class="badge-observed">OBSERVED ACTIVITY SURVEY DATA</span>', unsafe_allow_html=True)
    st.write("")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.metric("2-Wheeler Motorbikes", f"{active_village.get('motorbikes_count', 0):,} vehicles")
    with t2:
        st.metric("Monthly Petrol Consumption", f"{active_village.get('petrol_monthly_litres', 0):,.1f} Litres")
    with t3:
        st.metric("Annual Fuel Volume", f"{(active_village.get('petrol_monthly_litres', 0)*12):,.1f} Litres/yr")
    st.write("")
    bikes = active_village.get('motorbikes_count', 0)
    hh = active_village.get('total_households', 1)
    ratio = (bikes / hh) if hh > 0 else 0
    st.info(f"📊 **Motorization Rate:** {ratio:.2f} registered motorbikes per household in {active_village['village_name']}.")

# ==================== PAGE: WASTE ====================
elif st.session_state.nav_page == "Waste":
    st.markdown("### 🗑️ Solid Waste Generation")
    st.markdown('<span class="badge-observed">OBSERVED ACTIVITY SURVEY DATA</span>', unsafe_allow_html=True)
    st.write("")
    w1, w2, w3 = st.columns(3)
    monthly_w = active_village.get('waste_monthly_kg', 0)
    pop = active_village.get('total_residents', 1)
    per_cap_w = (monthly_w / pop / 30.0) if pop > 0 else 0.0
    with w1:
        st.metric("Monthly Waste Generated", f"{monthly_w:,.1f} kg/month")
    with w2:
        st.metric("Annual Solid Waste", f"{(monthly_w*12/1000):,.2f} Tonnes/yr")
    with w3:
        st.metric("Per Capita Rate", f"{per_cap_w:.3f} kg/capita/day")

# ==================== PAGE: LIVESTOCK ====================
elif st.session_state.nav_page == "Livestock":
    st.markdown("### 🐄 Livestock Population & Ruminant Census")
    st.markdown('<span class="badge-observed">OBSERVED LIVESTOCK SURVEY DATA</span>', unsafe_allow_html=True)
    st.write("")
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        st.metric("Dairy Cattle / Cows", f"{active_village.get('cows_count', 0):,} heads")
    with l2:
        st.metric("Goats (Caprine)", f"{active_village.get('goats_count', 0):,} heads")
    with l3:
        st.metric("Sheep (Ovine)", f"{active_village.get('sheep_count', 0):,} heads")
    with l4:
        st.metric("Total Livestock", f"{active_village.get('total_livestock', 0):,} heads")
    st.write("")
    df_live = pd.DataFrame({'Livestock Species': ['Dairy Cattle / Cows', 'Goats', 'Sheep'], 'Count': [active_village.get('cows_count', 0), active_village.get('goats_count', 0), active_village.get('sheep_count', 0)]})
    fig_live = px.bar(df_live, x='Livestock Species', y='Count', color='Livestock Species', title=f"Livestock Herd Composition ({active_village['village_name']})", color_discrete_sequence=['#4e342e', '#ffb300', '#8d6e63'], text_auto=True)
    fig_live.update_layout(height=340, showlegend=False)
    st.plotly_chart(fig_live, use_container_width=True)

# ==================== PAGE: CARBON EMISSION ====================
elif st.session_state.nav_page == "Carbon Emission":
    st.markdown("### 🌿 Village Greenhouse Gas Accounting & Emission Modeling")
    st.markdown('<span class="badge-derived">DERIVED / CALCULATED SCIENTIFIC OUTPUT</span>', unsafe_allow_html=True)
    st.write("")
    cb1, cb2, cb3, cb4 = st.columns(4)
    tot_co2 = active_village.get('total_co2e_t_yr', 0.0)
    per_cap = active_village.get('per_capita_co2e_kg_yr', 0.0)
    energy_co2 = active_village.get('energy_total_co2e_t_yr', 0.0)
    non_energy_co2 = tot_co2 - energy_co2
    with cb1:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #d32f2f;"><div class="metric-label">Total Village Carbon Footprint</div><div class="metric-val">{tot_co2:,.2f} t</div><div class="metric-sub">Tonnes CO2e / year</div></div>''', unsafe_allow_html=True)
    with cb2:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #f57c00;"><div class="metric-label">Per Capita Footprint</div><div class="metric-val">{per_cap:,.1f} kg</div><div class="metric-sub">kg CO2e / person / year</div></div>''', unsafe_allow_html=True)
    with cb3:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #1976d2;"><div class="metric-label">Energy Sector Emissions</div><div class="metric-val">{energy_co2:,.2f} t</div><div class="metric-sub">LPG + Wood + Electricity</div></div>''', unsafe_allow_html=True)
    with cb4:
        st.markdown(f'''<div class="metric-card" style="border-left-color: #388e3c;"><div class="metric-label">AFOLU & Waste Emissions</div><div class="metric-val">{non_energy_co2:,.2f} t</div><div class="metric-sub">Livestock + Waste + Transport</div></div>''', unsafe_allow_html=True)

    st.write("")
    ce_left, ce_right = st.columns([1.1, 0.9])
    with ce_left:
        st.markdown("##### 📊 Sectoral GHG Emissions Breakdown")
        df_sec_em = pd.DataFrame([
            {'Sector': 'LPG Combustion', 'Emission_tCO2e': active_village.get('lpg_co2e_t_yr', 0)},
            {'Sector': 'Firewood Biomass Burning', 'Emission_tCO2e': active_village.get('firewood_co2e_t_yr', 0)},
            {'Sector': 'Grid Electricity Consumption', 'Emission_tCO2e': active_village.get('electricity_co2e_t_yr', 0)},
            {'Sector': 'Motorbike Petrol Transport', 'Emission_tCO2e': active_village.get('transport_co2e_t_yr', 0)},
            {'Sector': 'Solid Waste Disposal', 'Emission_tCO2e': active_village.get('waste_co2e_t_yr', 0)},
            {'Sector': 'Livestock Enteric Fermentation', 'Emission_tCO2e': active_village.get('livestock_co2e_t_yr', 0)}
        ])
        fig_sec_em = px.bar(df_sec_em, x='Emission_tCO2e', y='Sector', orientation='h', color='Emission_tCO2e', color_continuous_scale='Reds', text_auto='.2f', labels={'Emission_tCO2e': 'Emissions (t CO2e/year)'})
        fig_sec_em.update_layout(height=340, yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig_sec_em, use_container_width=True)
    with ce_right:
        st.markdown("##### 🍩 Sectoral Contribution")
        fig_pie_v = px.pie(df_sec_em, names='Sector', values='Emission_tCO2e', hole=0.45, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_pie_v.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie_v.update_layout(height=340, showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_pie_v, use_container_width=True)
    st.markdown("---")
    st.markdown("##### 📚 Modeling Methodology & IPCC Tier-1 Accounting Formula")
    st.markdown("""
    $$\\text{Total Greenhouse Gas Emission } (\\text{t CO}_2\\text{e/year}) = \\sum_{i} \\left( \\frac{\\text{Annual Activity Data}_i \\times \\text{Emission Factor}_i}{1000} \\right)$$
    * **LPG**: $2.984\\text{ kg CO}_2\\text{e/kg}$ (IPCC 2006 Stationary Combustion).
    * **Firewood**: $1.747\\text{ kg CO}_2\\text{e/kg}$ (MoEFCC & IPCC Biomass default).
    * **Grid Electricity**: $0.820\\text{ kg CO}_2\\text{/kWh}$ (Central Electricity Authority CEA India v20.0).
    * **Transport (Petrol)**: $2.310\\text{ kg CO}_2\\text{e/litre}$ (IPCC 2006 Mobile Road Transport).
    * **Solid Waste**: $0.450\\text{ kg CO}_2\\text{e/kg}$ (IPCC First Order Decay simplified rural factor).
    * **Livestock**: Dairy Cattle $980\\text{ kg CO}_2\\text{e/head/yr}$, Goats/Sheep $145.6\\text{ kg CO}_2\\text{e/head/yr}$ (IPCC Indian Ruminant factors).
    """)

# ==================== PAGE: VILLAGE COMPARISON ====================
elif st.session_state.nav_page == "Village Comparison":
    st.markdown("### ⚖️ Multi-Village Comparative Analysis")
    st.write("Select 2 to 5 villages to evaluate side-by-side across all 12 parameters and total greenhouse gas emissions.")
    compare_codes = st.multiselect(
        "Choose Villages for Comparison (2 to 5):",
        options=list(village_options.keys()),
        default=[st.session_state.selected_village_code, vcode_list[1] if len(vcode_list)>1 else st.session_state.selected_village_code],
        format_func=lambda x: village_options.get(x, x),
        max_selections=5
    )
    if len(compare_codes) >= 2:
        df_cmp = df_all[df_all['village_code'].isin(compare_codes)].copy()
        fig_cmp_em = px.bar(df_cmp, x='village_name', y='total_co2e_t_yr', color='village_name', title="Comparison: Total Carbon Footprint (t CO2e/year)", text_auto='.1f', labels={'total_co2e_t_yr': 'Total Emissions (t CO2e/yr)', 'village_name': 'Village'})
        fig_cmp_em.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig_cmp_em, use_container_width=True)
        st.markdown("##### 📋 Comparative Data Matrix")
        metrics_display = {
            'Village Name': 'village_name', 'Block': 'block_name', 'Residents': 'total_residents', 'Households': 'total_households',
            'Total Area (ha)': 'total_area_ha', 'Built-up (ha)': 'builtup_area_ha', 'Agricultural (ha)': 'agri_area_ha', 'Water Bodies (ha)': 'total_water_area_ha',
            'LPG (kg/mo)': 'lpg_monthly_kg', 'Firewood (kg/mo)': 'firewood_monthly_kg', 'Electricity (kWh/mo)': 'electricity_monthly_kwh',
            'Solid Waste (kg/mo)': 'waste_monthly_kg', 'Motorbikes': 'motorbikes_count', 'Petrol (L/mo)': 'petrol_monthly_litres',
            'Total Livestock': 'total_livestock', 'Total Carbon (t CO2e/yr)': 'total_co2e_t_yr', 'Per Capita (kg CO2e/yr)': 'per_capita_co2e_kg_yr'
        }
        df_cmp_table = df_cmp[list(metrics_display.values())].rename(columns={v: k for k, v in metrics_display.items()})
        st.dataframe(df_cmp_table.set_index('Village Name'), use_container_width=True)
    else:
        st.warning("Please select at least 2 villages to view the comparative matrix.")

# ==================== PAGE: VILLAGE RANKING ====================
elif st.session_state.nav_page == "Village Ranking":
    st.markdown("### 🏆 Village Environmental & Emission Ranking")
    r_col1, r_col2, r_col3 = st.columns([2, 1.5, 1])
    with r_col1:
        metric_choices = {
            'Total Carbon Emission (t CO2e/yr)': 'total_co2e_t_yr',
            'Per Capita Carbon (kg CO2e/yr)': 'per_capita_co2e_kg_yr',
            'Total Population (Residents)': 'total_residents',
            'Agricultural Land Area (ha)': 'agri_area_ha',
            'Electricity Consumption (kWh/mo)': 'electricity_monthly_kwh',
            'Solid Waste Generation (kg/mo)': 'waste_monthly_kg',
            'Total Livestock Count': 'total_livestock'
        }
        sel_rank_metric = st.selectbox("Ranking Metric:", list(metric_choices.keys()))
        rank_col = metric_choices[sel_rank_metric]
    with r_col2:
        sort_order = st.radio("Sort Order:", ["Highest First (Descending)", "Lowest First (Ascending)"], horizontal=True)
        ascending = (sort_order == "Lowest First (Ascending)")
    with r_col3:
        top_n = st.selectbox("Show Top:", [15, 25, 50, 100], index=0)

    df_rank = df_all.copy()
    if st.session_state.selected_block != "All Blocks":
        df_rank = df_rank[df_rank['block_name'] == st.session_state.selected_block]
    df_sorted = df_rank.sort_values(by=rank_col, ascending=ascending).head(top_n).copy()
    df_sorted['Rank'] = range(1, len(df_sorted) + 1)
    
    fig_rank = px.bar(df_sorted, x='Rank', y=rank_col, hover_data=['village_name', 'block_name', 'total_residents'], text='village_name', title=f"Ranked by {sel_rank_metric} ({'Top' if not ascending else 'Bottom'} {top_n})", color=rank_col, color_continuous_scale='Viridis')
    fig_rank.update_layout(height=360)
    st.plotly_chart(fig_rank, use_container_width=True)
    show_cols = ['Rank', 'village_name', 'block_name', 'village_code', rank_col, 'total_residents', 'total_area_ha', 'total_co2e_t_yr']
    st.dataframe(df_sorted[show_cols], use_container_width=True)

# ==================== PAGE: REPORTS ====================
elif st.session_state.nav_page == "Reports":
    st.markdown("### 📑 Village Environmental & Carbon Report Generator")
    st.write(f"Generate and download the complete academic assessment report for **{active_village['village_name']}**.")
    r_left, r_right = st.columns([1.5, 1])
    with r_left:
        st.markdown(f"""
        **Report Contents:**
        1. **Geographic Profile**: Census Code, Block, Sub-district, Coordinates.
        2. **Demographics**: Total Residents, Households, Sex Ratio.
        3. **Land Use & Water Resources**: Total area, built-up, agriculture, ponds, canals.
        4. **Energy**: Monthly LPG, firewood, grid electricity.
        5. **Transport & Waste**: 2-wheelers, fuel, rural solid waste.
        6. **Livestock**: Dairy cattle, goats, sheep counts.
        7. **Greenhouse Gas Modeling**: Comprehensive IPCC Tier-1 and CEA India carbon tables ($t\text{{CO}}_2\text{{e/yr}}$).
        8. **Methodology & Citations**: References for thesis bibliography.
        """)
        pdf_data = generate_village_pdf(active_village)
        st.download_button(
            label="📄 Download Official PDF Report",
            data=pdf_data,
            file_name=f"Varanasi_Carbon_Report_{active_village['village_name']}_{active_village['village_code']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        csv_str = export_village_csv(active_village)
        st.download_button(
            label="📊 Export Village Record as CSV",
            data=csv_str,
            file_name=f"{active_village['village_name']}_{active_village['village_code']}_data.csv",
            mime="text/csv",
            use_container_width=True
        )
    with r_right:
        st.info("💡 **Academic Standard:** Formatted strictly in compliance with MoEFCC and IPCC 2006 guidelines.")

# ==================== PAGE: EXCEL IMPORT ====================
elif st.session_state.nav_page == "Excel Import":
    st.markdown("### 📥 Survey Excel Import & Database Synchronization")
    st.write("Upload a new survey dataset to update village parameters, or download the active survey database.")
    uploaded_file = st.file_uploader("Upload Village Survey Excel File (.xlsx)", type=['xlsx'])
    if uploaded_file is not None:
        try:
            temp_path = os.path.join(os.path.dirname(DEFAULT_DB_PATH), "temp_upload.xlsx")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            report = import_village_excel(temp_path)
            st.success(f"✅ Excel Import Successful! Inserted: {report['inserted']}, Updated: {report['updated']}.")
            if report['warnings']:
                st.warning(f"⚠️ {len(report['warnings'])} warnings encountered during import.")
                st.write(report['warnings'][:10])
            with st.spinner("Re-computing emissions with new data..."):
                recompute_and_save_all_emissions()
                st.success("Greenhouse gas emissions updated successfully!")
                st.cache_data.clear()
        except Exception as e:
            st.error(f"❌ Error during import: {e}")

    st.markdown("---")
    st.markdown("##### 📤 Export Current Survey Database")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_all.to_excel(writer, index=False, sheet_name='Varanasi_Villages')
    st.download_button(
        label="📥 Download Full Database as Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="Varanasi_Village_Environmental_Database_2024.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==================== PAGE: SETTINGS / METHODOLOGY ====================
elif st.session_state.nav_page == "Settings / Methodology":
    st.markdown("### ⚙️ Carbon Emission Factors & Modeling Parameters")
    st.write("Inspect active greenhouse gas emission factors without altering core software code.")
    factors_current = get_emission_factors()
    df_ef = pd.DataFrame([
        {'Activity / Fuel': 'Liquefied Petroleum Gas (LPG)', 'Unit': 'kg', 'Factor': factors_current['lpg'], 'Emission Factor Unit': 'kg CO2e / kg', 'Standard': 'IPCC 2006 Vol 2'},
        {'Activity / Fuel': 'Biomass Firewood Burning', 'Unit': 'kg', 'Factor': factors_current['firewood'], 'Emission Factor Unit': 'kg CO2e / kg', 'Standard': 'MoEFCC / IPCC 2006'},
        {'Activity / Fuel': 'Grid Electricity (UP/NEWNE Grid)', 'Unit': 'kWh', 'Factor': factors_current['electricity'], 'Emission Factor Unit': 'kg CO2 / kWh', 'Standard': 'CEA Baseline v20 2024'},
        {'Activity / Fuel': 'Motorbike Petrol / Gasoline', 'Unit': 'Litre', 'Factor': factors_current['petrol'], 'Emission Factor Unit': 'kg CO2e / Litre', 'Standard': 'IPCC 2006 Vol 2'},
        {'Activity / Fuel': 'Rural Solid Waste Disposal', 'Unit': 'kg', 'Factor': factors_current['waste'], 'Emission Factor Unit': 'kg CO2e / kg', 'Standard': 'IPCC 2006 FOD simplified'},
        {'Activity / Fuel': 'Dairy Cattle / Cows', 'Unit': 'head/year', 'Factor': factors_current['cow'], 'Emission Factor Unit': 'kg CO2e / head / yr', 'Standard': 'IPCC 2006 Vol 4 Indian Cattle'},
        {'Activity / Fuel': 'Goats (Caprine)', 'Unit': 'head/year', 'Factor': factors_current['goat'], 'Emission Factor Unit': 'kg CO2e / head / yr', 'Standard': 'IPCC 2006 Vol 4'},
        {'Activity / Fuel': 'Sheep (Ovine)', 'Unit': 'head/year', 'Factor': factors_current['sheep'], 'Emission Factor Unit': 'kg CO2e / head / yr', 'Standard': 'IPCC 2006 Vol 4'}
    ])
    st.dataframe(df_ef, use_container_width=True)
    if st.button("🔄 Recalculate All District Emissions Now"):
        with st.spinner("Re-calculating emissions across all 1,334 villages..."):
            count = recompute_and_save_all_emissions()
            st.success(f"Recalculated emissions for {count} villages successfully!")
            st.cache_data.clear()
            st.rerun()
