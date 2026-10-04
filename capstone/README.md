# Precision Soil Nutrient Diagnosis Web Platform
### 5th Semester Capstone Engineering Project | Dept. of CSE (AI & ML), SIT Tumakuru

An end-to-end, decoupled precision agriculture system for diagnosing soil macronutrients (**Soil pH**, **Available Nitrogen [N]**, **Extractable Phosphorus [P]**, and **Exchangeable Potassium [K]**) from Copernicus Sentinel-2 L2A satellite remote sensing imagery using 4 trained **XGBoost regression models**.

---

## Architecture Overview & Port Allocations

The project is split into three decoupled services. As instructed, **ports 8080 and 8000 are not used**:

```
+-------------------------------------------------------------+
|        Modern Farmer Web Portal (HTML5 / CSS3 / JS)         |
|        Port: 8501 (and served on Port: 9090)                |
|   • Simple Farmer Sign-In (SHA-256 Auth)                    |
|   • Leaflet & Esri World Imagery Satellite Map              |
|   • Interactive 4-Corner Quadrilateral Field Selection      |
|   • Full-Width 2D Spatial Heatmaps (pH, N, P, K)            |
+------------------------------+------------------------------+
                               | REST (JSON)
                               v
+-------------------------------------------------------------+
|            Backend Enterprise API (Spring Boot 3.3)         |
|            Runtime: Java 21 LTS | Port: 9090                |
|   • Custom SHA-256 Credential Authentication                |
|   • JTS Polygon / Geodesic Field Area Calculation (Acres)   |
|   • Fertility Assessment Persistence                        |
+--------------+-------------------------------+--------------+
               | JDBC (SSL)                    | REST (JSON)
               v                               v
+-------------------------------+ +---------------------------+
| Aiven Cloud PostgreSQL       | | Python AI Microservice    |
| • Cloud-hosted (No local PG)  | | Port: 7000                |
| • PostGIS Geospatial Engine   | | • Microsoft STAC Streamer |
| • Spatial Indexing (GiST)     | | • 18 Diagnostic Features  |
+-------------------------------+ | • 4 XGBoost Models        |
                                  | • Polygon-Masked PNGs     |
                                  +---------------------------+
```

---

## 1. Cloud Database Setup (Aiven PostgreSQL with PostGIS)

> **Important:** No local PostgreSQL installation is required. Everything runs in the cloud on [Aiven.io](https://aiven.io).

### Step 1: Enable PostGIS on your Aiven PostgreSQL Database
1. Go to your **Aiven Web Console** and open your PostgreSQL service.
2. Open the **Query** tab or connect using DBeaver / pgAdmin / psql using your Aiven service URI.
3. Run the script located at `capstone/database/init_aiven_postgis.sql`:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
4. Verify PostGIS is active:
   ```sql
   SELECT PostGIS_Full_Version();
   ```

### Step 2: Configure Credentials in Spring Boot
Open `capstone/backend-spring/src/main/resources/application.properties` and paste your Aiven connection parameters:
```properties
server.port=9090

# Replace with your actual Aiven host, port, user, and password:
spring.datasource.url=jdbc:postgresql://<AIVEN_HOST>:<AIVEN_PORT>/defaultdb?sslmode=require
spring.datasource.username=avnadmin
spring.datasource.password=<YOUR_AIVEN_PASSWORD>
spring.datasource.driver-class-name=org.postgresql.Driver

spring.jpa.hibernate.ddl-auto=update
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect

# Python AI Service
python.ai.service.url=http://localhost:7000
```
*(Alternatively, you can set the environment variables `AIVEN_PG_URL`, `AIVEN_PG_USER`, and `AIVEN_PG_PASSWORD` without editing the file).*

---

## 2. Launching the Services

You can launch all services in 1-click using the provided script or start each one individually:

### Option A: Launch All (Recommended)
Double-click:
```bash
capstone\start_all.bat
```

### Option B: Launch Manually in Separate Terminals

#### Terminal 1: Python AI Satellite Microservice (Port 7000)
```powershell
cd c:\Users\kisha\OneDrive\Desktop\agri\capstone\ai-service
python -m uvicorn app:app --host 127.0.0.1 --port 7000 --reload
```
*Health Check:* `http://localhost:7000/health`

#### Terminal 2: Spring Boot 3.3 Backend (Port 9090)
```powershell
cd c:\Users\kisha\OneDrive\Desktop\agri\capstone\backend-spring
mvn spring-boot:run
```
*API Base:* `http://localhost:9090/api`

#### Terminal 3: Modern Farmer Web Portal (Port 8501)
```powershell
cd c:\Users\kisha\OneDrive\Desktop\agri\capstone\frontend
python -m http.server 8501
```
*Open Browser:* `http://localhost:8501` *(Also accessible directly at `http://localhost:9090`)*

---

## 3. How to Use the Application

1. **Farmer Authentication:**
   - Sign in using your registered username and password (e.g. `farmer_kishan` / `farmer123`).
   - Authenticated session ensures each farmer only accesses their own registered fields.

2. **Interactive 4-Corner Quadrilateral Mapping:**
   - Click **"Mark Field Corners"** and tap **4 corner points** on the high-resolution satellite map around your agricultural field.
   - The map automatically draws the quadrilateral polygon and calculates the geodesic surface area in acres.
   - Enter your Field Name (e.g., `Rice Plot`) and click **"Save Field"**.

3. **Fertility Check & 2D Spatial Heatmaps:**
   - Select your saved field from the dropdown.
   - Click **"🔍 Check Soil Nutrients"**.
   - The system streams the latest cloud-free Copernicus Sentinel-2 L2A scene, calculates the spectral indices, and runs the 4 trained XGBoost models.
   - View the results below the map:
     - Acquisition scan date, cloud level, and land surface verification check.
     - **Crop Health & Satellite Indicators:** NDVI, NDBI, BSI, UI metrics and heatmaps.
     - **Soil Nutrients & Fertility Levels:** Soil pH, Nitrogen (N), Phosphorus (P), and Potassium (K) metrics and heatmaps.
     - Dedicated **"Full Screen"** viewing on every heatmap.
     - Scroll up anytime to return to the dashboard and switch fields.

---

## 4. Tech Stack Summary

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (Leaflet.js & Turf.js) | Farmer UI, 4-corner boundary marking, full-width heatmap viewer |
| **Backend** | Spring Boot 3.3.3, Java 21 LTS, Maven | REST API, SHA-256 Auth, JTS geometry processing |
| **Database** | PostgreSQL with PostGIS on Aiven Cloud | Cloud spatial database, geodesic acreage, spatial indexing |
| **AI / Satellite Engine** | Python 3.12, FastAPI, XGBoost, Element84 STAC, RioXarray | Remote sensing band streaming, polygon masking, ML inference |
| **Satellite Data** | Copernicus Sentinel-2 L2A (10m - 20m) | Multi-spectral surface reflectance |
| **Machine Learning** | 4 Trained XGBoost Regressors | Trained on LUCAS benchmark dataset (Kammerlander et al., 2025) |
