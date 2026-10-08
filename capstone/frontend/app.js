/**
 * Precision Soil Nutrient Diagnosis - Modern Frontend Application
 * Interacts with Spring Boot 3.3 Backend on Port 9090
 * Uses Leaflet.js, Esri Satellite Imagery, and Turf.js
 */

// Backend API Base URL
// - Cloud/Production (e.g. Vercel, Render, Docker) or direct Spring Boot: Relative ("") prevents Mixed Content and domain issues
// - Local dev server (port 8501, 5500, 3000) or file:// protocol: Explicit "http://localhost:9090"
const API_BASE = (function () {
    if (typeof window !== "undefined" && window.location) {
        const { hostname, port, protocol } = window.location;
        if (protocol === "file:" || ((hostname === "localhost" || hostname === "127.0.0.1") && (port === "8501" || port === "5500" || port === "3000"))) {
            return "http://localhost:9090";
        }
    }
    return "";
})();

// Global Application State
const state = {
    farmer: null,
    isDrawing: false,
    drawnPoints: [], // [[lat, lng], ...]
    markers: [],
    tempPolyline: null,
    fieldPolygon: null,
    savedFarms: [],
    selectedFarm: null,
    map: null
};

// ============================================================================
// 1. Map Initialization (Leaflet + Esri World Imagery)
// ============================================================================
function initMap() {
    if (state.map) {
        setTimeout(() => state.map.invalidateSize(), 150);
        return;
    }
    // Default center: Tumakuru / SIT Region (Lat: 13.3409, Lon: 77.1009)
    state.map = L.map("map", {
        center: [13.3409, 77.1009],
        zoom: 15,
        zoomControl: true
    });

    // Base Layer: Esri World Imagery (High-Res Satellite)
    const esriSatellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
        attribution: "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
        maxZoom: 19
    }).addTo(state.map);

    // Alternative Layer: OpenStreetMap
    const osmStreets = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19
    });

    // Layer control
    L.control.layers({
        "Satellite Imagery (Esri)": esriSatellite,
        "Street Map (OSM)": osmStreets
    }, null, { position: "topright" }).addTo(state.map);

    // Mousemove listener for coordinates display
    state.map.on("mousemove", (e) => {
        const coordsBadge = document.getElementById("mapCoordsBadge");
        if (coordsBadge) {
            coordsBadge.innerText = `Lat: ${e.latlng.lat.toFixed(5)} | Lon: ${e.latlng.lng.toFixed(5)}`;
        }
    });

    // Click listener for drawing quadrilateral field
    state.map.on("click", handleMapClick);
}

// ============================================================================
// 2. Interactive 4-Corner Quadrilateral Field Selection (Like Reference)
// ============================================================================
const vertexIcon = L.divIcon({
    className: "vertex-handle",
    html: `<div style="
        width: 14px;
        height: 14px;
        background: #f97316;
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 6px rgba(0,0,0,0.5);
        cursor: pointer;
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
});

function startDrawing() {
    clearField();
    state.isDrawing = true;
    document.getElementById("map").style.cursor = "crosshair";
    updateStatusBanner("<strong>Marking Active:</strong> Click on the map to place Corner 1 of your field.", "#eff6ff", "#3b82f6");
    document.getElementById("btnCompleteField").disabled = true;
}

function handleMapClick(e) {
    if (!state.isDrawing) return;

    if (state.drawnPoints.length >= 4) {
        updateStatusBanner("4 corners marked. Click <strong>'Done Marking'</strong> to calculate area.", "#fef3c7", "#f59e0b");
        return;
    }

    const pt = [e.latlng.lat, e.latlng.lng];
    state.drawnPoints.push(pt);
    const cornerIndex = state.drawnPoints.length;

    // Add orange vertex marker with tooltip
    const marker = L.marker(pt, { icon: vertexIcon })
        .bindTooltip(`Corner ${cornerIndex}`, { permanent: true, direction: "top", offset: [0, -8] })
        .addTo(state.map);
    state.markers.push(marker);

    // Update dynamic polyline
    if (state.tempPolyline) {
        state.map.removeLayer(state.tempPolyline);
    }
    state.tempPolyline = L.polyline(state.drawnPoints, {
        color: "#f97316",
        weight: 2.5,
        dashArray: "5, 5"
    }).addTo(state.map);

    // Update Banner
    if (cornerIndex < 4) {
        updateStatusBanner(`Corner ${cornerIndex} placed. Click map for <strong>Corner ${cornerIndex + 1}</strong>.`, "#eff6ff", "#3b82f6");
    } else if (cornerIndex === 4) {
        updateStatusBanner("<strong>All 4 corners marked!</strong> Click <strong>'Done Marking'</strong> to calculate field area.", "#ecfdf5", "#10b981");
        document.getElementById("btnCompleteField").disabled = false;
    }
}

function completeField() {
    if (state.drawnPoints.length !== 4) {
        alert("Please tap exactly 4 corners on the map to mark your field boundary.");
        return;
    }

    state.isDrawing = false;
    document.getElementById("map").style.cursor = "";

    // Remove dashed polyline
    if (state.tempPolyline) {
        state.map.removeLayer(state.tempPolyline);
        state.tempPolyline = null;
    }

    // Draw completed polygon with solid green styling (just like reference!)
    if (state.fieldPolygon) {
        state.map.removeLayer(state.fieldPolygon);
    }

    state.fieldPolygon = L.polygon(state.drawnPoints, {
        color: "#16a34a",
        fillColor: "#22c55e",
        fillOpacity: 0.35,
        weight: 3
    }).addTo(state.map);

    // Calculate Geodesic Area using Turf.js
    // Turf expects coordinates in [lon, lat] order, closed ring (first == last)
    const turfCoords = state.drawnPoints.map(p => [p[1], p[0]]);
    turfCoords.push(turfCoords[0]); // Close ring

    const geoPoly = turf.polygon([turfCoords]);
    const areaSqMeters = turf.area(geoPoly);
    const areaAcres = areaSqMeters * 0.000247105;
    const areaHectares = areaSqMeters / 10000;

    // Display Area
    document.getElementById("areaDisplay").style.display = "block";
    document.getElementById("areaValue").innerHTML = `${areaAcres.toFixed(2)} <span class="unit">Acres</span>`;
    document.getElementById("areaSubInfo").innerText = `${areaHectares.toFixed(2)} hectares | ${Math.round(areaSqMeters).toLocaleString()} sq. meters`;

    // Show Save Farm Form
    document.getElementById("saveFarmForm").style.display = "flex";
    updateStatusBanner("<strong>Field Boundary Defined.</strong> Enter a name below and click Save Field.", "#ecfdf5", "#10b981");
    document.getElementById("btnCompleteField").disabled = true;
}

function clearField() {
    state.isDrawing = false;
    document.getElementById("map").style.cursor = "";
    state.drawnPoints = [];

    // Remove markers
    state.markers.forEach(m => state.map.removeLayer(m));
    state.markers = [];

    // Remove lines & polygon
    if (state.tempPolyline) {
        state.map.removeLayer(state.tempPolyline);
        state.tempPolyline = null;
    }
    if (state.fieldPolygon) {
        state.map.removeLayer(state.fieldPolygon);
        state.fieldPolygon = null;
    }

    // Hide panels
    document.getElementById("areaDisplay").style.display = "none";
    document.getElementById("saveFarmForm").style.display = "none";
    document.getElementById("btnCompleteField").disabled = true;

    updateStatusBanner("Click <strong>'Mark Field Corners'</strong> and tap 4 corners on the satellite map to define your boundary.", "#eff6ff", "#3b82f6");
}

function updateStatusBanner(message, bg, border) {
    const banner = document.getElementById("statusBanner");
    if (banner) {
        banner.innerHTML = message;
        banner.style.background = bg;
        banner.style.borderLeftColor = border;
    }
}

// ============================================================================
// 3. Save Field via Backend
// ============================================================================
async function saveFarm() {
    if (!state.farmer) {
        alert("Please log in as a farmer first!");
        return;
    }

    const farmNameInput = document.getElementById("farmNameInput");
    const farmName = farmNameInput.value.trim();
    if (!farmName) {
        alert("Please enter a name for your field.");
        return;
    }

    if (state.drawnPoints.length !== 4) {
        alert("Field must have exactly 4 corner points.");
        return;
    }

    // Convert coordinates to [lon, lat]
    const corners = state.drawnPoints.map(p => [Number(p[1].toFixed(6)), Number(p[0].toFixed(6))]);

    const payload = {
        farmerId: state.farmer.id,
        farmName: farmName,
        corners: corners
    };

    const saveBtn = document.getElementById("btnSaveFarm");
    saveBtn.disabled = true;
    saveBtn.innerHTML = `<span>Saving field...</span>`;

    try {
        const resp = await fetch(`${API_BASE}/api/farms`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (resp.status === 201) {
            const newFarm = await resp.json();
            alert(`Field '${newFarm.farmName}' saved successfully!\nTotal Area: ${newFarm.areaAcres.toFixed(2)} Acres.`);
            farmNameInput.value = "";
            clearField();
            await loadSavedFarms();
            // Automatically select new farm
            document.getElementById("savedFarmsSelect").value = newFarm.id;
            selectFarmById(newFarm.id);
        } else {
            const err = await resp.json();
            alert("Failed to save field: " + (err.error || JSON.stringify(err)));
        }
    } catch (e) {
        alert("Cannot connect to backend server. Make sure it is running.");
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg><span>Save Field</span>`;
    }
}

// ============================================================================
// 4. Saved Farms Management
// ============================================================================
async function loadSavedFarms() {
    if (!state.farmer) return;

    try {
        const resp = await fetch(`${API_BASE}/api/farms?farmerId=${state.farmer.id}`);
        if (resp.ok) {
            state.savedFarms = await resp.json();
            renderFarmsDropdown();
        }
    } catch (e) {
        console.error("Failed to fetch farms:", e);
    }
}

function renderFarmsDropdown() {
    const select = document.getElementById("savedFarmsSelect");
    const countBadge = document.getElementById("farmsCountBadge");
    select.innerHTML = '<option value="">-- Choose a registered farm --</option>';

    countBadge.innerText = `${state.savedFarms.length} Farms`;

    state.savedFarms.forEach(f => {
        const opt = document.createElement("option");
        opt.value = f.id;
        opt.innerText = `${f.farmName} (${f.areaAcres.toFixed(2)} Acres)`;
        select.appendChild(opt);
    });

    document.getElementById("savedFarmsSection").style.display = "block";
}

function selectFarmById(farmId) {
    if (!farmId) {
        state.selectedFarm = null;
        const select = document.getElementById("savedFarmsSelect");
        if (select) select.value = "";
        document.getElementById("farmActionsGroup").style.display = "none";
        document.getElementById("fertilitySection").style.display = "none";
        const results = document.getElementById("resultsContainer");
        if (results) results.style.display = "none";
        const loader = document.getElementById("loadingContainer");
        if (loader) loader.style.display = "none";
        const floatingBtn = document.getElementById("btnFloatingBackToDashboard");
        if (floatingBtn) floatingBtn.style.display = "none";
        clearField();
        return;
    }

    const farm = state.savedFarms.find(f => f.id == farmId);
    if (!farm) return;

    state.selectedFarm = farm;
    clearField();

    // Convert [lon, lat] back to [lat, lon] for Leaflet
    const latlngs = farm.corners.map(c => [c[1], c[0]]);

    // Render polygon on satellite map
    state.fieldPolygon = L.polygon(latlngs, {
        color: "#10b981",
        fillColor: "#059669",
        fillOpacity: 0.35,
        weight: 3
    }).addTo(state.map);

    // Add vertex markers
    latlngs.forEach((pt, i) => {
        const m = L.marker(pt, { icon: vertexIcon })
            .bindTooltip(`Corner ${i + 1}`, { permanent: false })
            .addTo(state.map);
        state.markers.push(m);
    });

    // Zoom map to field
    state.map.fitBounds(state.fieldPolygon.getBounds(), { padding: [40, 40] });

    // Show actions and fertility assessment panel
    document.getElementById("farmActionsGroup").style.display = "block";
    document.getElementById("fertilitySection").style.display = "block";
    document.getElementById("activeFarmBadge").innerText = `${farm.farmName} (${farm.areaAcres.toFixed(2)} ac)`;

    const resultsFarmTitle = document.getElementById("resultsFarmTitle");
    if (resultsFarmTitle) {
        resultsFarmTitle.innerText = `${farm.farmName} — Crop Health & Soil Nutrients (${farm.areaAcres.toFixed(2)} Acres)`;
    }

    // Reset results if farm changes
    document.getElementById("resultsContainer").style.display = "none";
    document.getElementById("loadingContainer").style.display = "none";
    const floatingBtn = document.getElementById("btnFloatingBackToDashboard");
    if (floatingBtn) floatingBtn.style.display = "none";
}

async function deleteSelectedFarm() {
    if (!state.selectedFarm) {
        alert("No field is currently selected to remove.");
        return;
    }
    const farmName = state.selectedFarm.farmName;
    const farmId = state.selectedFarm.id;
    if (!confirm(`Are you sure you want to remove the field '${farmName}'?`)) return;

    const deleteBtn = document.getElementById("btnDeleteFarm");
    if (deleteBtn) {
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = `<span>Removing...</span>`;
    }

    try {
        const resp = await fetch(`${API_BASE}/api/farms/${farmId}`, { method: "DELETE" });
        if (resp.ok) {
            alert(`Field '${farmName}' removed successfully.`);
            selectFarmById(null);
            await loadSavedFarms();
        } else {
            const errData = await resp.json().catch(() => ({}));
            alert(errData.error || "Failed to remove field from server.");
        }
    } catch (e) {
        alert("Error connecting to backend: " + e.message);
    } finally {
        if (deleteBtn) {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg><span>Remove Field</span>`;
        }
    }
}

// ============================================================================
// 5. Diagnostic Soil Nutrient Assessment & 2D Spatial Heatmaps
// ============================================================================
async function runFertilityCheck() {
    if (!state.selectedFarm) {
        alert("Please select one of your saved fields first.");
        return;
    }

    const runBtn = document.getElementById("btnRunFertility");
    const loader = document.getElementById("loadingContainer");
    const results = document.getElementById("resultsContainer");
    const loadTitle = document.getElementById("loadingTitle");
    const loadSubtitle = document.getElementById("loadingSubtitle");

    runBtn.disabled = true;
    loader.style.display = "block";
    results.style.display = "none";

    // Dynamic progress indicators
    loadTitle.innerText = "Finding Latest Satellite Image...";
    loadSubtitle.innerText = "Checking clearest, cloud-free satellite view over your field...";

    const progressTimer = setTimeout(() => {
        loadTitle.innerText = "Scanning Soil & Crop Health...";
        loadSubtitle.innerText = "Analyzing ground reflection and crop vigor across your field...";
    }, 3500);

    const modelTimer = setTimeout(() => {
        loadTitle.innerText = "Calculating Soil Nutrients...";
        loadSubtitle.innerText = "Estimating Soil pH, Nitrogen (N), Phosphorus (P), and Potassium (K)...";
    }, 12000);

    try {
        const resp = await fetch(`${API_BASE}/api/farms/${state.selectedFarm.id}/fertility-check`, {
            method: "POST"
        });

        clearTimeout(progressTimer);
        clearTimeout(modelTimer);

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || `Server responded with ${resp.status}`);
        }

        const data = await resp.json();
        renderFertilityResults(data);
    } catch (e) {
        clearTimeout(progressTimer);
        clearTimeout(modelTimer);
        alert("Soil Test Notice: " + e.message);
    } finally {
        loader.style.display = "none";
        runBtn.disabled = false;
    }
}

function renderFertilityResults(data) {
    const results = document.getElementById("resultsContainer");
    results.style.display = "block";

    // Metadata
    document.getElementById("metaDate").innerText = data.satellite_date || "N/A";
    document.getElementById("metaCloud").innerText = `${data.cloud_cover_pct || 0}%`;
    document.getElementById("metaPixels").innerText = (data.valid_pixels_count || 0).toLocaleString();

    // Acquisition & Season Note
    const seasonBox = document.getElementById("seasonNoteBox");
    const seasonText = document.getElementById("seasonNoteText");
    if (data.season_context) {
        seasonBox.style.display = "flex";
        seasonText.innerHTML = `<strong>Satellite Scan Note (${data.satellite_date}):</strong> ${data.season_context}`;
    } else {
        seasonBox.style.display = "none";
    }

    // Land-Cover Surface Validation Alert
    const alertBox = document.getElementById("surfaceAlertBox");
    const alertIcon = document.getElementById("surfaceAlertIcon");
    const alertTitle = document.getElementById("surfaceAlertTitle");
    const alertMsg = document.getElementById("surfaceAlertMsg");

    if (data.surface_validation) {
        alertBox.style.display = "block";
        const sv = data.surface_validation;
        if (sv.is_soil_valid) {
            alertBox.className = "surface-alert valid-soil";
            alertIcon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>`;
            alertTitle.innerText = "Field Verified: Agricultural Land";
            alertMsg.innerHTML = `Satellite reflection confirms natural farmland. Soil nutrient levels are ready for your review below.`;
        } else {
            alertBox.className = "surface-alert warning-roof";
            alertIcon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
            alertTitle.innerText = `Structure Detected: ${sv.surface_type}`;
            alertMsg.innerHTML = `<strong>Note:</strong> ${sv.warning}<br><span style="display:inline-block; margin-top:4px;">Tip: For best accuracy, make sure your marked boundary only covers soil or crops.</span>`;
        }
    } else {
        alertBox.style.display = "none";
    }

    const m = data.metrics || {};

    // 1. pH
    if (m.pH) {
        const ph = m.pH.mean;
        document.getElementById("valPh").innerText = ph;
        const statusEl = document.getElementById("statusPh");
        if (ph < 6.0) {
            statusEl.innerText = "Acidic Soil (Low pH)";
            statusEl.style.color = "#dc2626";
        } else if (ph > 7.5) {
            statusEl.innerText = "Alkaline Soil (High pH)";
            statusEl.style.color = "#d97706";
        } else {
            statusEl.innerText = "Normal / Good pH";
            statusEl.style.color = "#16a34a";
        }
        document.getElementById("rangePh").innerText = `Min: ${m.pH.min} | Max: ${m.pH.max}`;
    }

    // 2. Nitrogen
    if (m.Nitrogen) {
        document.getElementById("valN").innerHTML = `${m.Nitrogen.mean} <span class="sub-unit">mg/kg</span>`;
        document.getElementById("statusN").innerText = m.Nitrogen.mean < 15 ? "Low Nitrogen (Needs Fertilizer)" : "Good Nitrogen Level";
        document.getElementById("statusN").style.color = m.Nitrogen.mean < 15 ? "#d97706" : "#16a34a";
        document.getElementById("rangeN").innerText = `Min: ${m.Nitrogen.min} | Max: ${m.Nitrogen.max}`;
    }

    // 3. Phosphorus
    if (m.Phosphorus) {
        document.getElementById("valP").innerHTML = `${m.Phosphorus.mean} <span class="sub-unit">mg/kg</span>`;
        document.getElementById("statusP").innerText = m.Phosphorus.mean < 12 ? "Low Phosphorus (Needs DAP/Manure)" : "Good Phosphorus Level";
        document.getElementById("statusP").style.color = m.Phosphorus.mean < 12 ? "#d97706" : "#16a34a";
        document.getElementById("rangeP").innerText = `Min: ${m.Phosphorus.min} | Max: ${m.Phosphorus.max}`;
    }

    // 4. Potassium
    if (m.Potassium) {
        document.getElementById("valK").innerHTML = `${m.Potassium.mean} <span class="sub-unit">mg/kg</span>`;
        document.getElementById("statusK").innerText = m.Potassium.mean < 120 ? "Low Potassium (Needs Potash)" : "Healthy Potassium Level";
        document.getElementById("statusK").style.color = m.Potassium.mean < 120 ? "#d97706" : "#16a34a";
        document.getElementById("rangeK").innerText = `Min: ${m.Potassium.min} | Max: ${m.Potassium.max}`;
    }

    // Field Nutrient Distribution Heatmaps
    const heatmaps = data.heatmaps || {};
    if (heatmaps.pH) document.getElementById("imgHeatmapPh").src = heatmaps.pH;
    if (heatmaps.Nitrogen) document.getElementById("imgHeatmapN").src = heatmaps.Nitrogen;
    if (heatmaps.Phosphorus) document.getElementById("imgHeatmapP").src = heatmaps.Phosphorus;
    if (heatmaps.Potassium) document.getElementById("imgHeatmapK").src = heatmaps.Potassium;

    // Crop & Soil Indicator Metrics (NDVI, NDBI, BSI, UI)
    const sm = data.spectral_metrics || {};
    if (sm.NDVI) {
        document.getElementById("valNdvi").innerText = sm.NDVI.mean;
        document.getElementById("statusNdvi").innerText = sm.NDVI.mean > 0.25 ? "Good Green Canopy" : "Dry / Sparse Field";
        document.getElementById("statusNdvi").style.color = sm.NDVI.mean > 0.25 ? "#16a34a" : "#d97706";
        document.getElementById("rangeNdvi").innerText = `Min: ${sm.NDVI.min} | Max: ${sm.NDVI.max}`;
    }
    if (sm.NDBI) {
        document.getElementById("valNdbi").innerText = sm.NDBI.mean;
        document.getElementById("statusNdbi").innerText = sm.NDBI.mean > 0 ? "Dry Ground / Fallow" : "Moist Soil";
        document.getElementById("statusNdbi").style.color = sm.NDBI.mean > 0 ? "#ea580c" : "#2563eb";
        document.getElementById("rangeNdbi").innerText = `Min: ${sm.NDBI.min} | Max: ${sm.NDBI.max}`;
    }
    if (sm.BSI) {
        document.getElementById("valBsi").innerText = sm.BSI.mean;
        document.getElementById("statusBsi").innerText = sm.BSI.mean > 0 ? "Open Bare Soil" : "Dense Crop Cover";
        document.getElementById("statusBsi").style.color = sm.BSI.mean > 0 ? "#b45309" : "#16a34a";
        document.getElementById("rangeBsi").innerText = `Min: ${sm.BSI.min} | Max: ${sm.BSI.max}`;
    }
    if (sm.UI) {
        document.getElementById("valUi").innerText = sm.UI.mean;
        document.getElementById("statusUi").innerText = sm.UI.mean > 0 ? "Firm Ground" : "Soft Soil";
        document.getElementById("statusUi").style.color = "#7c3aed";
        document.getElementById("rangeUi").innerText = `Min: ${sm.UI.min} | Max: ${sm.UI.max}`;
    }

    // Diagnostic Multispectral Heatmaps
    const shm = data.spectral_heatmaps || {};
    if (shm.NDVI) document.getElementById("imgHeatmapNdvi").src = shm.NDVI;
    if (shm.NDBI) document.getElementById("imgHeatmapNdbi").src = shm.NDBI;
    if (shm.BSI) document.getElementById("imgHeatmapBsi").src = shm.BSI;
    if (shm.UI) document.getElementById("imgHeatmapUi").src = shm.UI;

    // Update Field Title in Results Bar
    const resultsFarmTitle = document.getElementById("resultsFarmTitle");
    if (resultsFarmTitle && state.selectedFarm) {
        resultsFarmTitle.innerText = `${state.selectedFarm.farmName} — Crop Health & Soil Nutrients (${state.selectedFarm.areaAcres.toFixed(2)} Acres)`;
    }

    // Ensure both sections are visible for continuous scrolling (Section 1: Indicators first, Section 2: Soil Nutrients second)
    const viewSpectral = document.getElementById("viewSpectral");
    const viewNutrients = document.getElementById("viewNutrients");
    if (viewSpectral) viewSpectral.style.display = "block";
    if (viewNutrients) viewNutrients.style.display = "block";

    // Scroll smoothly to full-width results below dashboard
    setTimeout(() => {
        results.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 200);
}

// ============================================================================
// Scroll to Dashboard (Change Field) & Floating Button Logic
// ============================================================================
function scrollToDashboard() {
    window.scrollTo({ top: 0, behavior: "smooth" });
}
window.scrollToDashboard = scrollToDashboard;

window.addEventListener("scroll", () => {
    const floatingBtn = document.getElementById("btnFloatingBackToDashboard");
    const resultsContainer = document.getElementById("resultsContainer");
    if (!floatingBtn || !resultsContainer || resultsContainer.style.display === "none") {
        if (floatingBtn) floatingBtn.style.display = "none";
        return;
    }
    if (window.scrollY > 350) {
        floatingBtn.style.display = "flex";
    } else {
        floatingBtn.style.display = "none";
    }
});

// ============================================================================
// Fullscreen Image Modal Functions
// ============================================================================
function openFullscreenModal(imgElementId, title) {
    const imgEl = document.getElementById(imgElementId);
    if (!imgEl || !imgEl.src) return;
    const modal = document.getElementById("fullscreenModal");
    const modalImg = document.getElementById("fullscreenModalImg");
    const modalTitle = document.getElementById("fullscreenModalTitle");
    if (modal && modalImg && modalTitle) {
        modalImg.src = imgEl.src;
        modalTitle.innerText = title || "Map View";
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
    }
}
window.openFullscreenModal = openFullscreenModal;

function closeFullscreenModal() {
    const modal = document.getElementById("fullscreenModal");
    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = "";
    }
}
window.closeFullscreenModal = closeFullscreenModal;

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeFullscreenModal();
    }
});

function switchLayerTab(layer) {
    // Both sections are now visible continuously in one unified view
}
window.switchLayerTab = switchLayerTab;

// ============================================================================
// 6. Farmer Authentication & Session (Username & Password Only)
// ============================================================================
function showLoginScreen() {
    const loginScreen = document.getElementById("loginScreen");
    const mainApp = document.getElementById("mainAppScreen");
    if (loginScreen) loginScreen.style.display = "flex";
    if (mainApp) mainApp.style.display = "none";

    showLoginStatus("", "");
}

function showLoginStatus(message, type) {
    const statusBox = document.getElementById("loginStatusMessage");
    if (!statusBox) return;
    if (!message) {
        statusBox.style.display = "none";
        statusBox.innerText = "";
        return;
    }
    statusBox.style.display = "block";
    statusBox.innerText = message;
    statusBox.className = "login-status-msg " + (type || "");
}

async function handleLoginSubmit(e) {
    if (e && e.preventDefault) e.preventDefault();
    const usernameInput = document.getElementById("loginUsername");
    const passwordInput = document.getElementById("loginPassword");
    const btnSubmit = document.getElementById("btnLoginSubmit");

    const username = usernameInput ? usernameInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value.trim() : "";

    if (!username || !password) {
        showLoginStatus("Please enter both username and password.", "error");
        return;
    }

    showLoginStatus("Authenticating...", "loading");
    if (btnSubmit) btnSubmit.disabled = true;

    try {
        const resp = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        if (resp.ok) {
            const farmer = await resp.json();
            showLoginStatus("Login successful! Loading dashboard...", "loading");
            setTimeout(() => loginSuccess(farmer), 300);
        } else {
            const err = await resp.json().catch(() => ({}));
            showLoginStatus(err.error || "Invalid username or password.", "error");
        }
    } catch (e) {
        console.error("Login connection failure:", e);
        const serverHint = API_BASE ? ` (${API_BASE})` : "";
        showLoginStatus(`Unable to connect to backend server${serverHint}. Please ensure the Spring Boot service is running.`, "error");
    } finally {
        if (btnSubmit) btnSubmit.disabled = false;
    }
}

function loginSuccess(farmer) {
    state.farmer = farmer;
    localStorage.setItem("farmer_session", JSON.stringify(farmer));

    // Hide Login Page, Show Main Application
    const loginScreen = document.getElementById("loginScreen");
    const mainApp = document.getElementById("mainAppScreen");
    if (loginScreen) loginScreen.style.display = "none";
    if (mainApp) mainApp.style.display = "flex";

    // Update Header Profile
    const nameEl = document.getElementById("headerUserName");
    const emailEl = document.getElementById("headerUserEmail");
    const avatarEl = document.getElementById("headerAvatar");

    if (nameEl) nameEl.innerText = farmer.fullName || farmer.username || "Farmer";
    if (emailEl) emailEl.innerText = farmer.email || `@${farmer.username}`;
    if (avatarEl) {
        avatarEl.src = farmer.pictureUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(farmer.fullName || farmer.username)}&background=10b981&color=fff`;
    }

    // Initialize or resize map
    initMap();
    setTimeout(() => {
        if (state.map) state.map.invalidateSize();
    }, 250);

    // Load Farmer's Saved Fields
    loadSavedFarms();
}

function logoutFarmer() {
    state.farmer = null;
    localStorage.removeItem("farmer_session");
    clearField();
    state.savedFarms = [];
    state.selectedFarm = null;

    const savedSelect = document.getElementById("savedFarmsSelect");
    if (savedSelect) savedSelect.innerHTML = '<option value="">-- Choose a registered farm --</option>';

    const savedSection = document.getElementById("savedFarmsSection");
    if (savedSection) savedSection.style.display = "none";
    const fertSection = document.getElementById("fertilitySection");
    if (fertSection) fertSection.style.display = "none";

    showLoginScreen();
}

// ============================================================================
// 7. Event Listeners & Bootstrap
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
    // 1. Auth Listeners
    const loginForm = document.getElementById("loginForm");
    if (loginForm) loginForm.addEventListener("submit", handleLoginSubmit);

    const btnLogoutHeader = document.getElementById("btnLogoutHeader");
    if (btnLogoutHeader) {
        btnLogoutHeader.addEventListener("click", logoutFarmer);
    }

    // 2. Mapping Buttons
    document.getElementById("btnStartDraw").addEventListener("click", startDrawing);
    document.getElementById("btnClearField").addEventListener("click", clearField);
    document.getElementById("btnCompleteField").addEventListener("click", completeField);
    document.getElementById("btnSaveFarm").addEventListener("click", saveFarm);

    // 3. Farm Selector
    document.getElementById("savedFarmsSelect").addEventListener("change", (e) => {
        selectFarmById(e.target.value);
    });
    document.getElementById("btnDeleteFarm").addEventListener("click", deleteSelectedFarm);

    // 4. Fertility Check
    document.getElementById("btnRunFertility").addEventListener("click", runFertilityCheck);

    // 5. Initial Session Check: Check if user already logged in
    const saved = localStorage.getItem("farmer_session");
    if (saved) {
        try {
            const farmer = JSON.parse(saved);
            loginSuccess(farmer);
        } catch (e) {
            localStorage.removeItem("farmer_session");
            showLoginScreen();
        }
    } else {
        // Show Simple Login Page by default!
        showLoginScreen();
    }

    // Handle Window Resize for Map
    window.addEventListener("resize", () => {
        if (state.map) state.map.invalidateSize();
    });
});
