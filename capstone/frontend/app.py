"""
Precision Soil Nutrient Diagnosis - Farmer Web Portal
Frontend application built with Streamlit & Folium.
Connects to Spring Boot 3.3 Backend on Port 9090.
"""

import base64
import json
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- Page Configuration ---
st.set_page_config(
    page_title="Soil Nutrient Diagnosis System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API Configuration (Strictly Port 9090 - NOT 8080 or 8000)
BACKEND_URL = "http://localhost:9090"

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1b5e20;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .metric-box {
        background-color: #f1f8e9;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #2e7d32;
        margin-bottom: 10px;
    }
    .badge-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "farmer" not in st.session_state:
    st.session_state.farmer = None

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = []

if "selected_farm" not in st.session_state:
    st.session_state.selected_farm = None

if "fertility_results" not in st.session_state:
    st.session_state.fertility_results = None

# --- Helper Functions ---
def login_farmer(token: str):
    """Authenticates farmer via Spring Boot backend on port 9090."""
    try:
        resp = requests.post(f"{BACKEND_URL}/api/auth/google", json={"idToken": token}, timeout=10)
        if resp.status_code == 200:
            st.session_state.farmer = resp.json()
            st.rerun()
        else:
            st.sidebar.error(f"Authentication failed: {resp.text}")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("Cannot connect to Spring Boot Backend at port 9090. Please ensure the backend is running.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

def logout_farmer():
    st.session_state.farmer = None
    st.session_state.clicked_coords = []
    st.session_state.selected_farm = None
    st.session_state.fertility_results = None
    st.rerun()

def fetch_farms(farmer_id: int):
    """Fetches all farms saved by this farmer from PostgreSQL/PostGIS."""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/farms?farmerId={farmer_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []

def save_farm(farmer_id: int, farm_name: str, corners: list):
    """Saves a 4-corner quadrilateral farm to Spring Boot -> PostGIS."""
    try:
        payload = {
            "farmerId": farmer_id,
            "farmName": farm_name,
            "corners": corners
        }
        resp = requests.post(f"{BACKEND_URL}/api/farms", json=payload, timeout=10)
        return resp
    except Exception as e:
        st.error(f"Failed to communicate with backend: {e}")
        return None

def trigger_fertility_check(farm_id: int):
    """Triggers Sentinel-2 streaming & XGBoost assessment via Spring Boot."""
    try:
        resp = requests.post(f"{BACKEND_URL}/api/farms/{farm_id}/fertility-check", timeout=120)
        return resp
    except Exception as e:
        st.error(f"Fertility check request failed: {e}")
        return None


# --- Sidebar: Farmer Authentication & Profile ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=600&q=80", use_container_width=True)
    st.markdown("### 🌾 Farmer Account")
    
    if st.session_state.farmer is None:
        st.info("Single Farmer Access: Sign in with your Google account to manage your farm boundaries and run diagnostic checks.")
        
        # Google Sign-In options
        token_input = st.text_input("Google ID Token or Demo Username", placeholder="e.g., farmer_ramesh")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Sign In (Google)", use_container_width=True):
                if token_input.strip():
                    token = token_input.strip() if token_input.startswith("mock_") else f"mock_token_{token_input.strip()}"
                    login_farmer(token)
                else:
                    st.warning("Please provide a demo ID or Google Token.")
        with col_btn2:
            if st.button("Quick Demo Login", use_container_width=True):
                login_farmer("mock_token_farmer_kishan")
        st.caption("Powered by Spring Boot 3.3 (Java 21) & Aiven Cloud PostgreSQL PostGIS.")
    else:
        farmer = st.session_state.farmer
        st.success(f"**Welcome, {farmer.get('fullName', 'Farmer')}!**")
        st.markdown(f"📧 **Email:** `{farmer.get('email')}`")
        st.markdown(f"🆔 **Farmer ID:** `{farmer.get('id')}`")
        
        if st.button("Sign Out", use_container_width=True):
            logout_farmer()
            
        st.divider()
        st.markdown("### 📚 Saved Farms")
        farms_list = fetch_farms(farmer["id"])
        
        if farms_list:
            farm_names = [f"{f['farmName']} ({f['areaAcres']:.2f} ac)" for f in farms_list]
            selected_idx = st.selectbox(
                "Select a farm:",
                range(len(farms_list)),
                format_func=lambda i: farm_names[i],
                key="farm_selector"
            )
            st.session_state.selected_farm = farms_list[selected_idx]
            
            # Button to delete farm
            if st.button("🗑️ Delete Selected Farm"):
                del_resp = requests.delete(f"{BACKEND_URL}/api/farms/{st.session_state.selected_farm['id']}")
                if del_resp.status_code == 200:
                    st.success("Farm deleted successfully.")
                    st.session_state.selected_farm = None
                    st.session_state.fertility_results = None
                    st.rerun()
                else:
                    st.error("Failed to delete farm.")
        else:
            st.info("No farms registered yet. Click 4 corners on the map to define a new quadrilateral farm.")


# --- Main Dashboard ---
st.markdown('<div class="main-header">🌾 Satellite Precision Soil Nutrient Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Copernicus Sentinel-2 L2A Surface Reflectance & AI Multi-Nutrient Assessment (pH, Nitrogen, Phosphorus, Potassium)</div>', unsafe_allow_html=True)

if st.session_state.farmer is None:
    st.warning("🔒 Please sign in using the sidebar to access the interactive farm mapper and fertility analysis tools.")
    st.stop()

# --- Tab Layout ---
tab_map, tab_analysis = st.tabs(["🗺️ 1. Interactive 4-Corner Farm Boundary", "🧪 2. Soil Fertility Diagnostic Heatmaps"])

# ==========================================
# TAB 1: INTERACTIVE 4-CORNER FARM MAPPER
# ==========================================
with tab_map:
    st.markdown("### Define Farm Boundary (Quadrilateral: Exactly 4 Corners)")
    st.markdown(
        "Click on **4 corner points** on the satellite map below to mark the boundary fence of your field. "
        "The coordinates will be recorded in clockwise or counter-clockwise order."
    )

    # Determine default map center
    if st.session_state.selected_farm:
        center_lat = st.session_state.selected_farm["centroidLat"]
        center_lon = st.session_state.selected_farm["centroidLon"]
        zoom_level = 16
    else:
        # Default center: Tumakuru, Karnataka (Siddaganga Institute of Technology region)
        center_lat, center_lon = 13.3409, 77.1009
        zoom_level = 14

    # Build Folium Map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles=None
    )
    # Add Esri Satellite Imagery Layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite Imagery",
        overlay=False,
        control=True
    ).add_to(m)
    # Add OpenStreetMap fallback
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Street Map",
        overlay=False,
        control=True
    ).add_to(m)
    folium.LayerControl().add_to(m)

    # If a farm is selected from dropdown, render its polygon
    if st.session_state.selected_farm:
        farm_info = st.session_state.selected_farm
        corners = farm_info["corners"]
        # Convert [lon, lat] -> [lat, lon] for folium
        latlon_polygon = [[pt[1], pt[0]] for pt in corners]
        folium.Polygon(
            locations=latlon_polygon,
            color="#00e676",
            weight=3,
            fill=True,
            fill_color="#00e676",
            fill_opacity=0.25,
            popup=f"<b>{farm_info['farmName']}</b><br>Area: {farm_info['areaAcres']:.2f} Acres"
        ).add_to(m)
        folium.Marker(
            location=[farm_info['centroidLat'], farm_info['centroidLon']],
            popup=f"<b>{farm_info['farmName']} Center</b>",
            icon=folium.Icon(color="green", icon="leaf")
        ).add_to(m)

    # Render markers for currently clicked points
    current_clicks = st.session_state.clicked_coords
    for idx, pt in enumerate(current_clicks):
        folium.Marker(
            location=[pt[1], pt[0]],  # pt is [lon, lat]
            popup=f"Corner {idx + 1}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    # If 4 points clicked, draw connecting polygon
    if len(current_clicks) == 4:
        latlon_poly = [[pt[1], pt[0]] for pt in current_clicks]
        folium.Polygon(
            locations=latlon_poly,
            color="#ff9100",
            weight=3,
            fill=True,
            fill_color="#ff9100",
            fill_opacity=0.3,
            popup="New Quadrilateral Farm Boundary"
        ).add_to(m)

    # Render map in Streamlit with click listener
    map_data = st_folium(m, width="100%", height=500, key="farm_folium_map")

    # Capture clicked coordinates
    if map_data and map_data.get("last_clicked"):
        click = map_data["last_clicked"]
        new_point = [round(click["lng"], 6), round(click["lat"], 6)]
        
        # Only add if we have fewer than 4 points and it's not a duplicate click
        if len(st.session_state.clicked_coords) < 4:
            if not st.session_state.clicked_coords or st.session_state.clicked_coords[-1] != new_point:
                st.session_state.clicked_coords.append(new_point)
                st.rerun()

    # Form to save farm or reset clicks
    col_ctrl1, col_ctrl2 = st.columns([2, 1])

    with col_ctrl1:
        st.markdown("#### 📍 Selected Coordinates")
        if not st.session_state.clicked_coords:
            st.info("No corners clicked yet. Click on 4 points on the map above.")
        else:
            for i, pt in enumerate(st.session_state.clicked_coords):
                st.write(f"• **Corner {i + 1}:** Longitude `{pt[0]}`, Latitude `{pt[1]}`")

        if len(st.session_state.clicked_coords) == 4:
            st.success("✅ Exactly 4 corners selected! Enter farm name to save.")
            farm_name_input = st.text_input("Enter Farm Name:", placeholder="e.g., North Paddy Field")
            
            if st.button("💾 Save Farm to PostgreSQL (PostGIS)", type="primary"):
                if not farm_name_input.strip():
                    st.error("Please provide a name for your farm.")
                else:
                    with st.spinner("Calculating geodesic area and storing in Aiven PostgreSQL..."):
                        resp = save_farm(
                            farmer_id=st.session_state.farmer["id"],
                            farm_name=farm_name_input.strip(),
                            corners=st.session_state.clicked_coords
                        )
                        if resp and resp.status_code == 201:
                            saved_farm = resp.json()
                            st.success(f"🎉 Farm '{saved_farm['farmName']}' saved successfully! Computed Area: **{saved_farm['areaAcres']:.2f} Acres**.")
                            st.session_state.clicked_coords = []
                            st.session_state.selected_farm = saved_farm
                            st.rerun()
                        elif resp:
                            st.error(f"Error: {resp.text}")

    with col_ctrl2:
        st.markdown("#### Actions")
        if st.button("🔄 Reset Clicked Corners", use_container_width=True):
            st.session_state.clicked_coords = []
            st.rerun()
        
        if st.session_state.selected_farm:
            st.info(f"**Currently Active Farm:** {st.session_state.selected_farm['farmName']}\n\nArea: {st.session_state.selected_farm['areaAcres']:.2f} Acres")


# ==========================================
# TAB 2: SOIL FERTILITY ASSESSMENT & HEATMAPS
# ==========================================
with tab_analysis:
    if not st.session_state.selected_farm:
        st.warning("⚠️ Please select or create a farm in Tab 1 first before running a fertility check.")
    else:
        active_farm = st.session_state.selected_farm
        
        col_top1, col_top2 = st.columns([3, 1])
        with col_top1:
            st.markdown(f"### Diagnostic Soil Assessment: **{active_farm['farmName']}**")
            st.caption(f"PostGIS Geometry: Quadrilateral | Computed Area: {active_farm['areaAcres']:.2f} Acres | Center: ({active_farm['centroidLat']:.5f}, {active_farm['centroidLon']:.5f})")
        with col_top2:
            run_btn = st.button("🚀 Run Fertility Check", type="primary", use_container_width=True)

        if run_btn:
            with st.spinner("Connecting to Microsoft Planetary Computer... Streaming Sentinel-2 L2A Bands & Running 4 XGBoost Models..."):
                resp = trigger_fertility_check(active_farm["id"])
                if resp and resp.status_code == 200:
                    st.session_state.fertility_results = resp.json()
                    st.success("Analysis complete! Heatmaps generated.")
                elif resp:
                    st.error(f"Fertility Check Error: {resp.text}")

        # Render Results if available
        if st.session_state.fertility_results:
            results = st.session_state.fertility_results
            metrics = results.get("metrics", {})
            heatmaps = results.get("heatmaps", {})

            st.divider()

            # Metadata Strip
            col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
            col_meta1.metric("🛰️ Satellite Date", results.get("satellite_date", "N/A"))
            col_meta2.metric("☁️ Cloud Cover", f"{results.get('cloud_cover_pct', 0.0)}%")
            col_meta3.metric("📐 Field Grid Size", f"{results.get('grid_shape', [0, 0])[0]} x {results.get('grid_shape', [0, 0])[1]}")
            col_meta4.metric("🎯 Valid 10m Pixels", results.get("valid_pixels_count", "N/A"))

            st.divider()

            # Soil Nutrient Summary Cards
            st.markdown("#### 🧪 Nutrient Level Breakdown (Field-Wide)")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)

            # pH Card
            with col_m1:
                ph_m = metrics.get("pH", {})
                mean_ph = ph_m.get("mean", 0.0)
                status = "Optimal" if 6.0 <= mean_ph <= 7.5 else ("Acidic" if mean_ph < 6.0 else "Alkaline")
                st.markdown(f"""
                <div class="badge-card">
                    <h4>Soil pH</h4>
                    <h2 style="color: #1b5e20;">{mean_ph}</h2>
                    <p><b>Status:</b> {status}</p>
                    <small>Min: {ph_m.get('min')} | Max: {ph_m.get('max')}</small>
                </div>
                """, unsafe_allow_html=True)

            # Nitrogen Card
            with col_m2:
                n_m = metrics.get("Nitrogen", {})
                st.markdown(f"""
                <div class="badge-card">
                    <h4>Available Nitrogen (N)</h4>
                    <h2 style="color: #2e7d32;">{n_m.get('mean', 0.0)} <span style="font-size: 0.9rem;">mg/kg</span></h2>
                    <p><b>Unit:</b> mg/kg (air-dry soil)</p>
                    <small>Min: {n_m.get('min')} | Max: {n_m.get('max')}</small>
                </div>
                """, unsafe_allow_html=True)

            # Phosphorus Card
            with col_m3:
                p_m = metrics.get("Phosphorus", {})
                st.markdown(f"""
                <div class="badge-card">
                    <h4>Extractable Phosphorus (P)</h4>
                    <h2 style="color: #e65100;">{p_m.get('mean', 0.0)} <span style="font-size: 0.9rem;">mg/kg</span></h2>
                    <p><b>Method:</b> Olsen P</p>
                    <small>Min: {p_m.get('min')} | Max: {p_m.get('max')}</small>
                </div>
                """, unsafe_allow_html=True)

            # Potassium Card
            with col_m4:
                k_m = metrics.get("Potassium", {})
                st.markdown(f"""
                <div class="badge-card">
                    <h4>Exchangeable Potassium (K)</h4>
                    <h2 style="color: #4a148c;">{k_m.get('mean', 0.0)} <span style="font-size: 0.9rem;">mg/kg</span></h2>
                    <p><b>Unit:</b> mg/kg</p>
                    <small>Min: {k_m.get('min')} | Max: {k_m.get('max')}</small>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # 2x2 Spatial Heatmap Grid
            st.markdown("#### 🗺️ High-Resolution 2D Spatial Nutrient Heatmaps")
            st.caption("Each pixel represents a 10m x 10m ground resolution cell clipped strictly within the farmer's 4-corner boundary.")

            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                st.markdown("**Soil Reaction (pH)**")
                if "pH" in heatmaps:
                    st.image(base64.b64decode(heatmaps["pH"]), use_container_width=True)
            with row1_col2:
                st.markdown("**Available Nitrogen (N)**")
                if "Nitrogen" in heatmaps:
                    st.image(base64.b64decode(heatmaps["Nitrogen"]), use_container_width=True)

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                st.markdown("**Extractable Phosphorus (P)**")
                if "Phosphorus" in heatmaps:
                    st.image(base64.b64decode(heatmaps["Phosphorus"]), use_container_width=True)
            with row2_col2:
                st.markdown("**Exchangeable Potassium (K)**")
                if "Potassium" in heatmaps:
                    st.image(base64.b64decode(heatmaps["Potassium"]), use_container_width=True)
