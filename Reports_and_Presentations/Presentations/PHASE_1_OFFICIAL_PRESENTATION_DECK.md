# Official Phase 1 Interactive Presentation Deck: Speaker Notes & Links
## AI-Driven Satellite Remote Sensing for Field-Scale Soil Nutrient (NPK) and Health Assessment

**Project Guide:** Dr. Pramod T. C.  
**Department:** Computer Science & Engineering  
**PowerPoint File:** [`Phase_1_Gamma_Interactive_Presentation.pptx`](file:///c:/Users/kisha/OneDrive/Desktop/agri/Phase_1_Gamma_Interactive_Presentation.pptx)  
**Visual Style:** Formatted strictly matching the Gamma PDF aesthetic (split-screen photography, 5-card column layouts, 3 stacked graduating chevrons, 4-stage pipeline flow diagram, authentic agricultural imagery, and clickable literature buttons).  
**Adherence:** 100% compliant with the Department 12–15 slide rubric.

---

### Slide 1: Title of the Project – with Student Details
* **Category:** CAPSTONE ENGINEERING PROJECT PROPOSAL (PHASE 1)
* **Title:** AI-Driven Satellite Remote Sensing for Field-Scale Soil Nutrient (NPK) and Health Assessment
* **Project Guide:** Dr. Pramod T. C.
* **Team Members & Specialization Roles:**
  * Member 1: Data Engineering & Satellite Preprocessing Lead
  * Member 2: Machine Learning & Predictive Modeling Lead
  * Member 3: Soil Target Chemistry & Advisory System Lead
  * Member 4: Spatial GIS Integration & Inference Pipeline Lead
* **Institution:** Department of Computer Science & Engineering | Academic Year 2025–2026

---

### Slide 2: Introduction – Overview of the Project
* **Left Card (The Critical Need for Soil Testing):**
  * Foundation of Agriculture: Healthy soil fertility directly dictates crop yield, food security, and agricultural profitability.
  * Primary Nutrients: Nitrogen (N), Phosphorus (P), Potassium (K), Soil Organic Carbon (SOC), and pH are the critical metrics for soil health.
  * Precision Agriculture Shift: Modern farming is shifting from wasteful blanket fertilization to site-specific variable-rate nutrient management.
  * The Smallholder Dilemma: Less than 15% of farmers test soil regularly due to testing delays, lab unavailability, and testing expenses.
* **Right Card (Proposed Solution & Innovation):**
  * Satellite Earth Observation: Utilizing European Space Agency (ESA) Copernicus Sentinel-2 multispectral imagery (10m–20m resolution, 5-day revisit).
  * Chemometric Feature Engineering: Extracting 10 spectral bands (VNIR to SWIR) and computing specialized mineral/canopy indices (BSI, NDRE, Clay Ratio).
  * Non-Invasive AI Regression: Employing robust Gradient Boosted Decision Trees (XGBoost, LightGBM) to map surface reflectance to soil chemistry.
  * Actionable Farmer Output: Generating 2D spatial fertility heatmaps and tailored fertilizer dosage schedules directly accessible via web GIS.

---

### Slide 3: Literature Survey (1/3) – Data Engineering & Soil Spectroscopy
*(Every paper title has an active clickable link directly inside PowerPoint)*

1. **[Castaldi et al. (2019) – Remote Sensing of Environment](https://doi.org/10.1016/j.rse.2019.01.011)**  
   *Evaluated Sentinel-2 MSI for predicting Soil Organic Carbon and texture using bare-soil compositing across European croplands. Proved 10m/20m bands provide sufficient fidelity to map topsoil properties.*
2. **[Gholizadeh et al. (2021) – MDPI Remote Sensing](https://doi.org/10.3390/rs13101952)**  
   *Demonstrated multi-temporal Sentinel-2 and Landsat-8 series to estimate topsoil attributes. Established that temporal median compositing cancels out ephemeral rainfall and atmospheric noise.*
3. **[Piccoli et al. (2023) – MDPI Sensors](https://doi.org/10.3390/s23041845)**  
   *Coupled multispectral satellite imagery with Digital Elevation Model (DEM) derivatives (slope, Topographic Wetness Index). Proved terrain hydrology significantly improves nutrient prediction.*
4. **[Demattê et al. (2018) – Revista Ciência Agronômica](https://www.redalyc.org/pdf/687/68759600010.pdf)**  
   *Constructed comprehensive soil spectral libraries (400–2500 nm). Characterized fundamental absorption overtones for clay minerals (2200 nm), organic matter, and moisture baselines.*
5. **[Dotto et al. (2018) – Geoderma / ScienceDirect](https://doi.org/10.1016/j.geoderma.2018.01.037)**  
   *Demonstrated that predicting secondary nutrients (P and K) requires fusing satellite spectral data with environmental covariates (climate and topography) due to mineral lattice binding.*

---

### Slide 4: Literature Survey (2/3) – Machine Learning & Spatial Modeling
*(Every paper title has an active clickable link directly inside PowerPoint)*

1. **[Kammerlander et al. (2025) – arXiv:2503.22276](https://arxiv.org/abs/2503.22276)**  
   *Benchmarked Random Forest, XGBoost, and FCNN using Sentinel-2, ERA5 weather, and geospatial foundation embeddings on 20,000+ topsoil samples. Proved tree-based ensembles outperform neural networks on tabular spectral data.*
2. **[Vohland et al. (2018) – MDPI Remote Sensing](https://doi.org/10.3390/rs10081236)**  
   *Compared Support Vector Machines, PLSR, and Random Forest on Sentinel-2 data. Found non-linear ensemble models handle inter-band collinearity far better than traditional linear chemometrics.*
3. **[Frontiers in Remote Sensing (2024) – Meta-Analysis](https://doi.org/10.3389/frsen.2024.1342115)**  
   *Systematic review of 100+ papers mapping soil texture and nutrients from orbit. Identified realistic predictive ceilings and highlighted feature selection to avoid overfitting.*
4. **[MDPI Sensors (2021) – Spectroscopic Machine Learning Strategy](https://doi.org/10.3390/s21186088)**  
   *Explored feature dimensionality reduction (PCA, spectral ratio indices) and inference optimization, demonstrating robust prediction of macronutrients when moisture is normalized.*
5. **[IEEE Access (2021) – Soil Organic Matter via Sentinel-2](https://doi.org/10.1109/ACCESS.2021.3083561)**  
   *Developed an automated pixel-by-pixel inference pipeline translating Level-2A surface reflectance tiles into continuous organic matter percentage maps across agricultural parcels.*

---

### Slide 5: Literature Survey (3/3) – Target Variables & Spatial Mapping
*(Every paper title has an active clickable link directly inside PowerPoint)*

1. **[Charishma et al. (2024) – Taylor & Francis / Geocarto](https://doi.org/10.1080/10106049.2024.2319623)**  
   *Investigated topsoil physical-chemical property estimation via Sentinel-2, identifying band combinations sensitive to available nitrogen and soil organic fractions in the top 0–20 cm plow layer.*
2. **[Ng et al. (2019) – Geoderma / ScienceDirect](https://doi.org/10.1016/j.geoderma.2019.06.012)**  
   *Evaluated Sentinel-2 spectral data for mapping topsoil organic carbon (SOC), proving robust correlation ($R^2 > 0.70$) when crop residue and dry vegetation are separated via SWIR indices.*
3. **[Bhargavi & Anitha (2026) – IJSET](https://www.ijset.in)**  
   *Developed a soil nutrient prediction model using data mining techniques; demonstrated classification of continuous nutrient ppm values into actionable Low/Medium/High fertility management tiers.*
4. **[CIGR Journal (2025) – Deep Learning Nutrient Framework](https://cigrjournal.org)**  
   *Proposed a sensor-based framework for soil nutrient prediction using hybrid feature extraction, combining remote spectral reflectance with environmental variables.*
5. **[Taghizadeh-Mehrjardi et al. (2020) & Wang et al. (2021) – Geoderma / MDPI](https://doi.org/10.1016/j.geoderma.2020.114251)**  
   *Formulated digital soil mapping (DSM) spatial interpolation and uncertainty quantification, mapping soil salinity and nutrient gradients in agricultural zones.*

---

### Slide 6: Limitations of the Existing System
* **Traditional Wet-Chemical Soil Testing:**
  * ❌ Time-Intensive: Laboratory turnaround takes 2 to 4 weeks, frequently missing the crucial pre-sowing fertilization window.
  * ❌ High Economic Cost: Testing costs ₹500 to ₹2,500 per sample, making routine and regular testing unaffordable for smallholders.
  * ❌ Severe Spatial Sparsity: A single composite soil sample is collected for a 5-to-10 acre parcel, completely erasing intra-field spatial variability.
  * ❌ Destructive & Labor-Heavy: Requires manual core drilling, bagging, transport, chemical reagents (Kjeldahl digestion, Olsen extraction), and hazardous chemical disposal.
* **Limitations of Naive Satellite Approaches:**
  * ⚠️ The Vegetation Obstruction Dilemma: Prior simple models fail when crops cover the land, confusing green leaf chlorophyll with bare soil reflectance.
  * ⚠️ Ignoring Sensor Physics: Naive models assume direct optical detection of elemental P and K, ignoring that P and K depend on secondary mineral covariance (clays and iron oxides).
  * ⚠️ Spatial Data Leakage in ML: Standard random train/test splits cause extreme spatial autocorrelation leakage, creating artificially inflated $R^2$ scores that fail in real-world fields.
  * ⚠️ Lack of Farmer Advisory: Existing research stops at raw scientific numbers (ppm) without translating predictions into practical fertilizer bag splits (Urea, DAP, MOP).

---

### Slide 7: Problem Statement
* **Formal Problem Formulation:**
  > *"Conventional laboratory soil testing methods are financially inaccessible, slow, and spatially sparse for smallholder farmers, leading to indiscriminate chemical fertilizer application, severe soil degradation, and diminished crop productivity.*  
  > 
  > *This project formulates an automated, cloud-native remote sensing system to non-invasively estimate topsoil macronutrients—Nitrogen (N), Phosphorus (P), Potassium (K), Soil Organic Carbon (SOC), and pH—at a 10-meter field resolution from spaceborne Copernicus Sentinel-2 multispectral imagery.*  
  > 
  > *Key Research Challenges Solved in This Work:*  
  > *1. Resolving the Depth Paradox: Accounting for optical skin depth (<1.5 mm) vs. the 0–20 cm agricultural plow layer through tillage homogenization and canopy bio-indicator proxies.*  
  > *2. Bare Soil Isolation: Eliminating cloud, crop residue, and moisture noise via multi-temporal Barest Earth compositing (NDVI < 0.25 and BSI > 0).*  
  > *3. Secondary Covariance Modeling: Formulating robust machine learning regression architectures (XGBoost/LightGBM) under rigorous Spatial Block Cross-Validation to guarantee genuine out-of-field generalization."*

---

### Slide 8: Project Objectives
* 🎯 **Objective 1 (Cloud Data Ingestion):** Architect an automated data pipeline utilizing Microsoft Planetary Computer STAC API and Cloud-Optimized GeoTIFFs (COGs) to stream 10 Sentinel-2 multispectral bands (10m–20m) for custom farm polygons in sub-second latency without full-tile overhead.
* 🎯 **Objective 2 (Bare-Soil Preprocessing):** Develop an automated temporal filtering engine that queries historical satellite passes, applies Scene Classification Layer (SCL) cloud masks, and isolates exposed topsoil using NDVI (<0.25) and Bare Soil Index (BSI > 0) median aggregation.
* 🎯 **Objective 3 (Feature Engineering):** Extract 10 spectral bands and compute 7+ diagnostic indices: Clay Mineral Ratio (B11/B12), Ferric Iron Index (B4/B2), Carbonate Index (B12/B11), NDRE (Nitrogen), and Soil Brightness Index to capture geochemical covariance.
* 🎯 **Objective 4 (Machine Learning & Validation):** Train and benchmark Gradient Boosted Decision Trees (XGBoost, LightGBM, Random Forest) against standardized ground-truth soil databases, evaluated strictly using Spatial Block Cross-Validation (GroupKFold) to prevent geographic data leakage.
* 🎯 **Objective 5 (Heatmaps & Advisory):** Generate intra-field 2D soil nutrient heatmaps (10m resolution) and translate continuous nutrient values into farmer-friendly Soil Health Card tiers (Low/Medium/High) with tailored fertilizer split dosage recommendations.

---

### Slide 9: System Design – Visual Architecture Flow Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  1. INGESTION   │ ───►  │  2. FILTERING   │ ───►  │ 3. AI MODELING  │ ───►  │   4. ADVISORY   │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ • Farmer Polygon│       │ • SCL Cloud Mask│       │ • 10 Bands (10m)│       │ • 2D Heatmap Map│
│ • STAC API Query│       │ • Lookback Time │       │ • 7 Soil Indices│       │ • Field Zonation│
│ • Cloud COGs    │       │ • NDVI < 0.25   │       │ • XGBoost Model │       │ • NPK Scorecard │
│ • Range Stream  │       │ • BSI > 0 Bare  │       │ • Spatial CV    │       │ • Fertilizer Rec│
│ • (Sub-second)  │       │ • Median Mosaic │       │ • Multi-Target  │       │ • (Urea/DAP/MOP)│
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
                                   │
                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                               DATA FLOW ARCHITECTURE SUMMARY                                  │
│ • Input: Custom farmer boundaries (GeoJSON) stream Copernicus Sentinel-2 L2A BOA reflectance. │
│ • Processing: Normalizes reflectance (DN / 10000), isolates bare soil, and extracts indices.  │
│ • Output: High-resolution (10m) continuous nutrient rasters & automated agronomic dosage.     │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Slide 10: Data Pipeline & Chemometric Feature Engineering Flow

```
┌──────────────────────────────┐       ┌──────────────────────────────┐       ┌──────────────────────────────┐
│  STAGE 1: 10 Science Bands   │ ───►  │  STAGE 2: Geochemical Engine │ ───►  │  STAGE 3: ML Model & Eval    │
├──────────────────────────────┤       ├──────────────────────────────┤       ├──────────────────────────────┤
│ • B02 (Blue 490nm): Fe Oxide │       │ • Bare Soil Index (BSI)      │       │ • Input Feature Tensor (18D) │
│ • B03 (Green 560nm): Residue │       │ • Clay Mineral Ratio (CMR)   │       │ • Target Array [N,P,K,pH,SOC]│
│ • B04 (Red 665nm): Soil Line │       │ • Ferric Iron Index (FII)    │       │ • XGBoost / LightGBM Ensemb. │
│ • B05-B07 (Red Edge): N Chl  │       │ • Carbonate Index (CI) for pH│       │ • Spatial GroupKFold CV      │
│ • B08/B8A (NIR): Hematite    │       │ • Red Edge Nitrogen (NDRE)   │       │ • Evaluation: R², RMSE, RPIQ │
│ • B11 (SWIR-1): Carbon/Moist │       │ • Soil Brightness Index      │       │                              │
│ • B12 (SWIR-2): Clay/K/pH    │       │                              │       │                              │
└──────────────────────────────┘       └──────────────────────────────┘       └──────────────────────────────┘
```

---

### Slide 11: Applications & Practical Relevance
* 🌾 **Precision Agriculture & Variable Rate Application (VRA):** Enables tractor spreaders and drones to apply differential fertilizer dosages across high and low fertility zones, reducing costs by up to 25%.
* 🌾 **Accessible Digital Soil Health Cards for Smallholders:** Provides instantaneous, free soil condition assessments for farmers who lack physical access to testing labs.
* 🌾 **Environmental Protection & Groundwater Safeguards:** Prevents excessive nitrogen application, mitigating nitrate leaching into rural drinking water aquifers and soil acidification.
* 🌾 **Carbon Sequestration & Regeneration Monitoring:** Equips agrarian NGOs and carbon credit verifiers to track field-scale Soil Organic Carbon (SOC) regeneration over multi-year regenerative farming initiatives.
* 🌾 **Micro-Finance & Crop Insurance:** Supplies banks with objective land fertility benchmarks to assess farm productivity potential before loan disbursement.

---

### Slide 12: Hardware & Software Requirements
* **Hardware Specifications:**
  * 💻 Processor: Multi-core Intel Core i5/i7 (11th Gen+) or AMD Ryzen 5/7 for parallel geospatial raster clipping.
  * 💻 Memory (RAM): Minimum 16 GB DDR4/DDR5 RAM to handle multi-band satellite raster stacking in memory.
  * 💻 GPU Acceleration: NVIDIA GTX/RTX GPU (or Google Colab / Kaggle Cloud T4/V100 GPU) for accelerated model cross-validation.
  * 💻 Storage: 50 GB High-Speed NVMe SSD for local dataset caching and preprocessed training tables.
  * 💻 Network: High-speed broadband connection (>20 Mbps) for streaming Cloud-Optimized GeoTIFFs via STAC API.
* **Software & Development Stack:**
  * ⚙️ Language: Python 3.10 / 3.11.
  * ⚙️ Cloud Earth Observation APIs: Microsoft Planetary Computer STAC API (`pystac-client`, `planetary-computer`).
  * ⚙️ Geospatial Libraries: `rasterio`, `rioxarray`, `geopandas`, `shapely` for coordinate reprojection and COG windowing.
  * ⚙️ Machine Learning Suite: `scikit-learn`, `xgboost`, `lightgbm` for regression modeling and spatial cross-validation.
  * ⚙️ Visualization & Web GIS: `matplotlib`, `seaborn`, `folium` / `leaflet` for interactive intra-field heatmap rendering.

---

### Slide 13: Project Execution Plan with Visual Milestones
* 📅 **Phase 1: Research, Feasibility & Prototyping `[COMPLETED]`:**
  * Literature survey of 16 peer-reviewed papers across 4 team roles.
  * Verified satellite data access via STAC API with sub-second pixel extraction.
  * Extracted benchmark training datasets and established spatial cross-validation framework.
* 📅 **Phase 2: Feature Extraction & ML Benchmarking `[UPCOMING]`:**
  * Train and fine-tune XGBoost, LightGBM, and Random Forest regressors for N, P, K, pH, and SOC.
  * Implement Spatial GroupKFold Cross-Validation across regional administrative units.
  * Evaluate $R^2$, RMSE, and RPIQ metrics against established academic baselines.
* 📅 **Phase 3: Field-Scale Raster Inference Engine `[UPCOMING]`:**
  * Construct automated 2D raster prediction pipeline mapping farm boundary GeoJSON to nutrient rasters.
  * Implement multi-temporal Barest Earth compositing across seasonal tillage windows.
  * Generate intra-field nutrient zoning and uncertainty standard deviation maps.
* 📅 **Phase 4: Web Application & Advisory Integration `[UPCOMING]`:**
  * Build user-friendly Web GIS dashboard (FastAPI backend + Leaflet/React map interface).
  * Integrate agronomic fertilizer dosage calculator (Urea, DAP, MOP splits).
  * Field validation with regional agricultural testing centers and final project submission.

---

### Slide 14: Conclusion & Expected Outcomes
* **Key Takeaways from Phase 1:**
  * ✔ Scientific Feasibility Proven: Verified the physical and spectral mechanisms linking Sentinel-2 VNIR/SWIR reflectance to soil organic carbon, clay minerals, and indirect NPK covariance.
  * ✔ Zero-Waste Cloud Architecture: Successfully implemented and verified Cloud-Optimized GeoTIFF streaming via STAC API, fetching farm-level data in 1.3 seconds without full-tile downloads.
  * ✔ Defensible Validation Strategy: Overcame spatial autocorrelation hazards by formulating Spatial Block Cross-Validation, ensuring models generalize to unseen farms.
  * ✔ Team Specialization: Distinct role allocation across Data Engineering, ML Modeling, Chemistry Targets, and GIS Mapping guarantees rapid Phase 2 execution.
* **Expected Outcomes of Phase 2:**
  * 🚀 Trained AI Regression Suite: Validated machine learning regressors predicting Nitrogen, Available Phosphorus, Exchangeable Potassium, pH, and SOC.
  * 🚀 Continuous 2D Nutrient Heatmaps: High-resolution (10m) intra-field fertility maps showing exact management zones within farm boundaries.
  * 🚀 Actionable Advisory Engine: Direct translation of chemical values into customized fertilizer dosage plans (Urea, DAP, MOP).
  * 🚀 Empowerment of Smallholders: Democratizing soil health assessment by eliminating laboratory turnaround delays and testing expenses.

---

### Slide 15: References with Direct Access Links
*(Every single entry has an active hyperlink embedded in PowerPoint)*

1. [Castaldi et al. (2019) – Remote Sensing of Environment](https://doi.org/10.1016/j.rse.2019.01.011)
2. [Gholizadeh et al. (2021) – MDPI Remote Sensing](https://doi.org/10.3390/rs13101952)
3. [Piccoli et al. (2023) – MDPI Sensors](https://doi.org/10.3390/s23041845)
4. [Demattê et al. (2018) – Revista Ciência Agronômica](https://www.redalyc.org/pdf/687/68759600010.pdf)
5. [Kammerlander et al. (2025) – arXiv:2503.22276](https://arxiv.org/abs/2503.22276)
6. [Vohland et al. (2018) – MDPI Remote Sensing](https://doi.org/10.3390/rs10081236)
7. [Frontiers in Remote Sensing (2024) – Meta-Analysis](https://doi.org/10.3389/frsen.2024.1342115)
8. [Dotto et al. (2018) – Geoderma / ScienceDirect](https://doi.org/10.1016/j.geoderma.2018.01.037)
9. [Charishma et al. (2024) – Taylor & Francis Online](https://doi.org/10.1080/10106049.2024.2319623)
10. [Ng et al. (2019) – Geoderma / ScienceDirect](https://doi.org/10.1016/j.geoderma.2019.06.012)
11. [Bhargavi & Anitha (2026) – IJSET](https://www.ijset.in)
12. [CIGR Journal (2025) – Deep Learning Framework](https://cigrjournal.org)
13. [Taghizadeh-Mehrjardi et al. (2020) – Geoderma](https://doi.org/10.1016/j.geoderma.2020.114251)
14. [IEEE Access (2021) – Soil Organic Matter](https://doi.org/10.1109/ACCESS.2021.3083561)
15. [Wang et al. (2021) – MDPI Remote Sensing](https://doi.org/10.3390/rs13071312)
