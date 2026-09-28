# MASTER CONTEXT PROMPT: AI-Driven Satellite Soil Nutrient (NPK) Assessment
## Complete Engineering Project Context, Scientific Foundations, Architecture & Literature

> **How to use this document:** Copy and paste the text below as the initial system prompt or context into any LLM (ChatGPT, Claude, Gemini, DeepSeek, etc.) to immediately bring it up to speed on this project.

---

### 1. Project Identification & Academic Metadata
* **Project Title:** AI-Driven Satellite Remote Sensing for Field-Scale Soil Nutrient (NPK) and Health Assessment
* **Current Phase:** Phase 1 (Research, Feasibility Study, Data Pipeline Prototyping, and Proposal Defense)
* **Academic Level:** Undergraduate Engineering Capstone / Final Year Project
* **Department:** Department of Computer Science & Engineering
* **Project Supervisor / Guide:** Dr. Pramod T. C.
* **Specialization Team Roles (4 Members):**
  * Member 1: Data Engineering & Satellite Preprocessing Lead
  * Member 2: Machine Learning & Predictive Modeling Lead
  * Member 3: Soil Target Chemistry & Advisory System Lead
  * Member 4: Spatial GIS Integration & Inference Pipeline Lead
* **CRITICAL COMPLIANCE RULE:**  
  **Never mention or refer to the name "AgroLens"**. The underlying peer-reviewed research paper is cited strictly as:  
  *Kammerlander, C. et al. (2025). Machine learning models for soil parameter prediction based on satellite, weather, clay and yield data. arXiv:2503.22276.*

---

### 2. Problem Statement & Motivation
* **The Agricultural Crisis:**  
  Conventional laboratory wet-chemical soil testing (Kjeldahl digestion for N, Olsen extraction for P, flame photometry for K) takes **2 to 4 weeks**, costs **₹500 to ₹2,500 ($15–$50) per sample**, and is destructive. Furthermore, a single composite bag collected for a 5-to-10-acre parcel erases intra-field spatial variability.
* **The Consequence:**  
  Farmers resort to indiscriminate blanket fertilizer broadcasting, causing soil acidification, groundwater nitrate contamination, eutrophication, and ballooning input costs.
* **The Project Goal:**  
  Develop an automated, non-invasive cloud-native remote sensing system using free spaceborne multispectral imagery (Copernicus Sentinel-2, 10m resolution) and machine learning regressors (XGBoost, LightGBM, Random Forest) to estimate topsoil **Nitrogen ($N$), Available Phosphorus ($P$), Exchangeable Potassium ($K$), Soil Organic Carbon (SOC), and pH** on demand for any agricultural parcel, generating 2D intra-field fertility heatmaps and tailored fertilizer dosage recommendations.

---

### 3. Scientific & Remote Sensing Foundations (Physics & Spectroscopy)
* **The Optical Skin Depth Paradox & Its Solution:**  
  * Optical remote sensing (VNIR/SWIR, 400–2500 nm) has an optical skin depth of $\delta \le 1.5\text{ mm}$ due to Beer-Lambert attenuation ($I = I_0 e^{-\alpha z}$).  
  * **How we infer the 0–20 cm agricultural plow layer:** In cultivated land, routine mechanical tilling, plowing, and harrowing homogenize the upper Ap horizon (0–20 cm). Therefore, the 1 mm surface skin represents the bulk mineralogy of the plow zone (which is what ground-truth datasets like LUCAS sample).  
  * **How we infer the 20–100 cm root zone:** Crops translocate subsoil nutrients into leaf tissue. Nutrient deficiency causes chlorosis, which shifts the **Sentinel-2 Red Edge (Bands 5, 6, 7: 705–783 nm)**, acting as a physiological bio-indicator of deep root-zone fertility.
* **Nutrient-Specific Spectroscopy & Covariance Mechanics:**  
  * **Nitrogen ($N$):** Over 95% of total soil N is organic (amino acids, proteins, humic matter). It has $N-H$ stretching overtones at 1450 nm, 1510 nm, and combination bands at 2050–2060 nm and 2180 nm. Because soil microbes maintain a strict $C:N$ ratio ($10:1$ to $12:1$), Total N strongly covaries ($r > 0.85$) with Soil Organic Carbon (SOC), causing broad albedo darkening across VIS and strong absorption in SWIR Bands 11 (1610 nm) and 12 (2190 nm). During crop stages, canopy RuBisCO nitrogen is mapped via Red Edge indices (NDRE).  
  * **Phosphorus ($P$):** Orthophosphate ions ($H_2PO_4^-$) do NOT possess discrete optical absorption lines in 400–2500 nm. Estimation relies on **secondary geochemical covariance**: Phosphate binds to iron oxides (Hematite 530/860 nm, Goethite 480/900 nm in Bands 2, 3, 8A) and $Al-OH$ clay mineral lattice bonds at 2200 nm (Band 12).  
  * **Potassium ($K$):** Monovalent cation $K^+$ has no optical resonance. It binds to the interlayers of 2:1 clay minerals (illite, vermiculite, smectite) with hydroxyl vibrations at 1410 nm and 2200 nm, and covaries with Cation Exchange Capacity (CEC). It also covaries with terrain hydrology (DEM Topographic Wetness Index).  
  * **Soil Organic Carbon (SOC):** Direct chromophore causing broad albedo darkening across 400–1200 nm, plus aliphatic $C-H$ stretching at 1600–1720 nm (Band 11) and 2100–2300 nm (Band 12).  
  * **Soil pH:** Calcite ($CaCO_3$) exhibits an asymmetric $C-O$ absorption band at 2340 nm and 2500 nm, suppressing Band 12 relative to Band 11 (Carbonate Index: $B12/B11$).

---

### 4. Satellite System Selection & Ingestion Architecture
* **Satellite Selected:** European Space Agency (ESA) **Copernicus Sentinel-2 (MSI)**.  
  * *Why over Hyperspectral (EMIT/PRISMA)?* Hyperspectral sensors operate on targeted tasking modes (revisit 15–45+ days) and coarse resolution (30m–60m). Sentinel-2 provides systematic global coverage every 5 days with 10m resolution (~100 pixels per hectare).  
  * *Why over ISRO Resourcesat-2/2A (LISS-III)?* Resourcesat has only 4 bands (lacks SWIR-2 2190 nm and Red Edge 705–783 nm) and a 24-day revisit cycle. Sentinel-2 carries 13 bands (10 science bands).
* **Cloud Data Ingestion:** **Microsoft Planetary Computer STAC API + Cloud-Optimized GeoTIFFs (COGs)**.  
  * Avoids downloading full 1 GB `.SAFE` tiles.  
  * Uses HTTP Range Requests to read only the farm bounding box pixels (~50 KB) in 1.3 seconds.
* **10 Science Bands Extracted:**  
  * `B02` (Blue 490nm), `B03` (Green 560nm), `B04` (Red 665nm)  
  * `B05` (Red Edge 1, 705nm), `B06` (Red Edge 2, 740nm), `B07` (Red Edge 3, 783nm)  
  * `B08` (Broad NIR 842nm), `B8A` (Narrow NIR 865nm)  
  * `B11` (SWIR-1 1610nm), `B12` (SWIR-2 2190nm)  
  * `SCL` (Scene Classification Layer quality mask: 5 = Bare Soil, 4 = Vegetation, 3/8/9 = Clouds/Shadows).

---

### 5. Preprocessing & Feature Engineering Methodology
* **Reflectance Calibration:** $\text{Surface Reflectance } (\rho) = \frac{\text{DN}}{10000.0}$.
* **Spatial Resampling:** 20m SWIR and Red Edge bands resampled to 10m grid.
* **Date Gap Handling (Multi-Tiered Temporal Search):**  
  * If a soil sample is dated (e.g., `02-02-2025`) and that exact day has no satellite pass or has clouds:  
    1. Tier 1: Query a $\pm 7\text{ day}$ window.  
    2. Tier 2: Expand to a $\pm 30\text{ day}$ seasonal agricultural tillage window.  
    3. Tier 3: Compute a multi-temporal **Barest Earth median composite** across historical passes filtering for bare soil ($\text{NDVI} < 0.25$ and $\text{BSI} > 0.0$).
* **7 Engineered Geochemical Spectral Indices:**  
  1. $\text{Bare Soil Index (BSI)} = \frac{(B_{11} + B_4) - (B_8 + B_2)}{(B_{11} + B_4) + (B_8 + B_2)}$  
  2. $\text{Clay Mineral Ratio (CMR)} = \frac{B_{11}}{B_{12}}$  
  3. $\text{Ferric Iron Index (FII)} = \frac{B_4}{B_2}$  
  4. $\text{Carbonate Index (CI)} = \frac{B_{12}}{B_{11}}$  
  5. $\text{Red Edge Nitrogen (NDRE)} = \frac{B_8 - B_5}{B_8 + B_5}$  
  6. $\text{Soil Brightness Index} = \sqrt{\frac{B_4^2 + B_3^2 + B_8^2}{3}}$  
  7. $\text{NDVI} = \frac{B_8 - B_4}{B_8 + B_4}$

---

### 6. Ground-Truth Datasets & Custom Pipeline
* **European Baseline (LUCAS 2018):** Downloaded and extracted into `data/`:  
  * `LUCAS_Soil_2018.csv` (18,909 rows of laboratory tests: N, P, K, pH, GPS).  
  * `Model_A.csv` (18,471 rows with ground-truth tests already paired with Sentinel-2 bands).
* **Indian Soil Data Sources:**  
  * Mendeley Data: *Soil Nutrient Dataset for Crop Advice* (1,653 samples, Maharashtra, DOI: 10.17632/6n3jjhncbp.1), *AgriNet* (258 samples, UP).  
  * ICAR-NBSS&LUP BHOOMI Geoportal (`bhoomigeoportal-nbsslup.in`), India Data Portal (`indiadataportal.com`), and Soil Health Card Portal (`soilhealth.dac.gov.in`).  
  * Bhargavi & Anitha (2026) Indian soil dataset (408 samples).
* **Automated Data Preparation Pipeline (`build_custom_soil_dataset.py`):**  
  * Fully working script in workspace. Takes any CSV with `[Lat, Lon, N, P, K, pH]`, automatically queries Sentinel-2 COGs, extracts 10 bands and 7 indices, and outputs a 29-column ML-ready dataset. Verified on 5 Indian states (AP, KA, MH, PB, TN).

---

### 7. Machine Learning & Spatial Validation Strategy
* **Algorithms:** Extreme Gradient Boosting (**XGBoost**), **LightGBM**, and **Random Forest Regressors**. Tree ensembles outperform neural networks on tabular spectral features due to collinearity robustness.
* **Target Scaling:** Logarithmic transform applied to right-skewed Available P and K ($y' = \ln(y + 1)$).
* **Spatial Autocorrelation Hazard & Solution:**  
  * Random k-fold cross-validation is **invalid** for geospatial data because neighboring pixels share identical soil, falsely inflating $R^2 > 0.90$.  
  * **Mandatory Validation:** **Spatial Block Cross-Validation (Spatial GroupKFold)** using regional administrative clusters (e.g. `NUTS_2` or district blocks) to evaluate genuine out-of-field generalization.

---

### 8. The 16 Peer-Reviewed Research Papers (Syllabus Literature)
1. **Castaldi et al. (2019):** Remote Sensing of Environment ([DOI: 10.1016/j.rse.2019.01.011](https://doi.org/10.1016/j.rse.2019.01.011))
2. **Gholizadeh et al. (2021):** MDPI Remote Sensing ([DOI: 10.3390/rs13101952](https://doi.org/10.3390/rs13101952))
3. **Piccoli et al. (2023):** MDPI Sensors ([DOI: 10.3390/s23041845](https://doi.org/10.3390/s23041845))
4. **Demattê et al. (2018):** Revista Ciência Agronômica ([PDF Link](https://www.redalyc.org/pdf/687/68759600010.pdf))
5. **Kammerlander et al. (2025):** arXiv:2503.22276 ([arXiv Link](https://arxiv.org/abs/2503.22276)) *(Core peer benchmark paper)*
6. **Vohland et al. (2018):** MDPI Remote Sensing ([DOI: 10.3390/rs10081236](https://doi.org/10.3390/rs10081236))
7. **Frontiers in Remote Sensing (2024):** Systematic Review ([DOI: 10.3389/frsen.2024.1342115](https://doi.org/10.3389/frsen.2024.1342115))
8. **Dotto et al. (2018):** Geoderma / ScienceDirect ([DOI: 10.1016/j.geoderma.2018.01.037](https://doi.org/10.1016/j.geoderma.2018.01.037))
9. **Charishma et al. (2024):** Taylor & Francis / Geocarto ([DOI: 10.1080/10106049.2024.2319623](https://doi.org/10.1080/10106049.2024.2319623))
10. **Ng et al. (2019):** Geoderma / ScienceDirect ([DOI: 10.1016/j.geoderma.2019.06.012](https://doi.org/10.1016/j.geoderma.2019.06.012))
11. **Bhargavi & Anitha (2026):** IJSET ([Journal Link](https://www.ijset.in))
12. **CIGR Journal (2025):** Deep Learning Framework ([Journal Link](https://cigrjournal.org))
13. **Taghizadeh-Mehrjardi et al. (2020):** Geoderma ([DOI: 10.1016/j.geoderma.2020.114251](https://doi.org/10.1016/j.geoderma.2020.114251))
14. **IEEE Access (2021):** Soil Organic Matter ([DOI: 10.1109/ACCESS.2021.3083561](https://doi.org/10.1109/ACCESS.2021.3083561))
15. **MDPI Sensors (2021):** Spectroscopic ML Strategy ([DOI: 10.3390/s21186088](https://doi.org/10.3390/s21186088))
16. **Wang et al. (2021):** MDPI Remote Sensing ([DOI: 10.3390/rs13071312](https://doi.org/10.3390/rs13071312))

---

### 9. Current Status of Codebase & Deliverables (All Built & Verified)
* `Phase_1_Interactive_Presentation.pptx`: Official 15-slide presentation with clickable links and flowcharts.
* `PHASE_1_OFFICIAL_PRESENTATION_DECK.md`: Complete word-for-word speaker notes for presentation defense.
* `PHASE_1_RESEARCH_REPORT_SOIL_NUTRIENTS_REMOTE_SENSING.md`: Formal written academic proposal report.
* `SOIL_NUTRIENTS_REMOTE_SENSING_COMPREHENSIVE_SCIENTIFIC_DOSSIER.md`: 50-page equivalent scientific master dossier.
* `build_custom_soil_dataset.py`: Operational Python script to generate custom ML-ready datasets for any country.
* `data/Model_A.csv`: Preprocessed 18,471-row training dataset (Sentinel-2 bands + ground truth NPK).
