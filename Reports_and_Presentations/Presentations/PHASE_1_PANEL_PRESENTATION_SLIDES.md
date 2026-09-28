# Phase 1 Project Review Presentation Deck (Slide-by-Slide Guide)
## AI-Driven Satellite Remote Sensing for Field-Scale Soil Nutrient (NPK) Assessment

Use this structured deck outline to prepare your PowerPoint (`.pptx`) or Google Slides presentation for your review panel.

---

### Slide 1: Title & Project Identity
- **Title:** Satellite-Based Soil Nutrient (NPK) & Health Assessment Using Machine Learning
- **Subtitle:** Phase 1: Research, Technical Feasibility Study, and System Architecture Proposal
- **Team Members & Designated Roles:**
  1. Member 1: Data Engineering & Preprocessing Lead
  2. Member 2: Machine Learning Model Lead
  3. Member 3: Target Variables & Advisory Lead
  4. Member 4: System Integration & Spatial Mapping Lead
- **Institutional Details:** Department of Computer Science / Information Technology / Agricultural Engineering

---

### Slide 2: Problem Statement & Motivation
- **The Core Problem:**
  - Conventional laboratory soil testing takes 2–4 weeks, costs \$15–\$50 per sample, and fails to capture within-field variability.
  - Farmers resort to indiscriminate NPK fertilizer application $\rightarrow$ soil acidification, groundwater pollution, and reduced profit margins.
- **The Vision:**
  - Empower farmers and agronomists to delineate land boundaries on a map and receive instantaneous, cost-effective soil nutrient estimates (N, P, K, pH, SOC) derived from European Space Agency (ESA) Copernicus Sentinel-2 satellite imagery.

---

### Slide 3: Remote Sensing Fundamentals & Scientific Feasibility
- **Key Question:** *Can optical satellites detect Nitrogen, Phosphorus, and Potassium?*
- **The Scientific Reality:**
  - **Direct Spectral Detection:** Soil Organic Carbon (SOC) and Soil Moisture have strong diagnostic vibrational overtones in the SWIR spectrum (1400 nm – 2200 nm, Sentinel-2 Bands 11 & 12).
  - **Indirect / Proxy Detection:** 
    - **Nitrogen (N):** Directly bound to Soil Organic Matter (~5% of SOM is N) + reflected in vegetative canopy chlorophyll absorption (RedEdge Bands 5–7).
    - **Phosphorus (P) & Potassium (K):** Act via secondary covariance—binding to clay minerals (Al-OH absorption at 2200 nm), iron oxides (450–550 nm), and Cation Exchange Capacity (CEC).
  - **Auxiliary Covariates:** Incorporating Digital Elevation Models (DEM - slope, water flow) and ERA5 climate data compensates for spectral limits.

---

### Slide 4: Overcoming the "Vegetation Canopy & Bare Soil" Challenge
- **The Challenge:** Satellites cannot see the soil if dense green vegetation or crop residue covers the field.
- **The 3-Step Scientific Solution:**
  1. **Multi-Temporal Querying:** Look back across the past 6–12 months of satellite passes.
  2. **Bare-Soil Indexing & Filtering:** Calculate Normalized Difference Vegetation Index ($\text{NDVI} < 0.25$) and Bare Soil Index ($\text{BSI} > 0$) to isolate pixels where the soil was exposed during plowing/tillage.
  3. **Temporal Median Compositing:** Stack cloud-free bare-soil pixels to cancel out temporary atmospheric and surface moisture fluctuations.

---

### Slide 5: Benchmark Case Study — AgroLens (`cvims/AgroLens`)
- **Reference:** Kammerlander et al. (March 2025, arXiv:2503.22276) by CVIMS (TH Ingolstadt) & MI4People.
- **What AgroLens Demonstrated:**
  - Trained on 20,000+ European points from the **LUCAS Soil Database**.
  - Compared Random Forest, XGBoost, and FCNN. Tree-based ensembles outperformed neural networks on raw spectral bands.
  - Successfully integrated **Clay Foundation Model embeddings** (spatial transformers for Earth observation) to boost out-of-distribution generalization.
  - Identified predictable bounds: High performance on SOC and N ($R^2 \approx 0.65–0.78$), moderate on pH ($R^2 \approx 0.50–0.65$), lower on P & K ($R^2 \approx 0.40–0.55$).

---

### Slide 6: Literature Survey Synthesis (16 Papers Mapped)
- **Member 1 (Data Engineering):** Castaldi (2019), Gholizadeh (2021), Piccoli (2023), Demattê (2018)
  - *Key Takeaway:* Sentinel-2 L2A (10m/20m) + DEM derivatives provide sufficient spectral-spatial resolution; multi-temporal compositing eliminates single-date noise.
- **Member 2 (Machine Learning):** Kammerlander (2025), Vohland (2018), Frontiers Remote Sensing (2024), Dotto (2018)
  - *Key Takeaway:* Gradient Boosted Trees (XGBoost/LightGBM) are optimal; spatial block cross-validation is mandatory to prevent geographic data leakage.
- **Member 3 (Target Variables & LLM):** Charishma (2024), Ng (2019), Bhargavi & Anitha (2026), CIGR Journal (2025)
  - *Key Takeaway:* Harmonized chemical target scales (N in g/kg, P and K in mg/kg); integrating LLMs to translate raw numbers into practical fertilizer schedules.
- **Member 4 (System Integration):** Taghizadeh-Mehrjardi (2020), IEEE Access (2021), MDPI Sensors (2021), Wang (2021)
  - *Key Takeaway:* Pixel-by-pixel 2D digital soil mapping; generating continuous nutrient heatmaps and confidence intervals across custom farmer polygons.

---

### Slide 7: Ground Truth Dataset & Training Strategy
- **Primary Training Source:** **LUCAS Soil Dataset** (European Joint Research Centre)
  - 22,000+ laboratory-tested topsoil points across Europe.
  - Measured parameters: Total Nitrogen, Available Phosphorus, Extractable Potassium, pH, Organic Carbon, Texture (Clay/Silt/Sand).
- **Regional Adaptation (Phase 2):**
  - Use transfer learning: Pre-train the model on LUCAS + Earth Foundation Model embeddings, then fine-tune using regional soil survey data / national agricultural health cards.

---

### Slide 8: Proposed Phase 2 System Architecture
- **User Flow:**
  1. Farmer enters coordinates or draws field boundary (GeoJSON).
  2. Cloud backend queries Sentinel-2 L2A via Planetary Computer / Copernicus STAC.
  3. Preprocessing engine filters bare-soil pixels and calculates spectral indices (BSI, NDWI).
  4. ML Regression Model outputs nutrient rasters.
  5. LLM Advisory Engine translates values into customized crop-specific fertilizer plans (Urea, DAP, MOP splits).
  6. Frontend displays interactive nutrient heatmaps and downloadable PDF report.

---

### Slide 9: Risk Analysis & Mitigation Strategy
| Risk Identified | Potential Impact | Mitigation Strategy Planned |
| :--- | :--- | :--- |
| Cloud cover / dense vegetation | Missing soil surface reflectance | Multi-temporal compositing (6-month lookback) + canopy proxy modeling |
| Spatial data leakage in ML | Artificially inflated $R^2$, fails in wild | Mandatory **Spatial Block Cross-Validation** (GroupKFold by region) |
| Low direct absorption of P and K | Weak predictive power | Integrate auxiliary DEM topography + climate covariates + Clay AI embeddings |

---

### Slide 10: Phase 2 Roadmap & Milestones (Post-Approval)
- **Month 1:** Data Ingestion Pipeline (Sentinel-2 STAC + LUCAS Dataset matching).
- **Month 2:** Feature Engineering & ML Model Training (XGBoost, LightGBM, Random Forest benchmarking).
- **Month 3:** Digital Soil Mapping & Raster Inference API (FastAPI + GDAL/Rasterio).
- **Month 4:** Web GIS UI, LLM Advisory Integration, Field Validation, and Final Review.

---

### Slide 11: Summary & Panel Q&A
- **Key Takeaways:**
  - Clear scientific understanding: Not direct spectroscopy, but validated proxy and secondary covariance modeling.
  - Solid peer benchmark established via AgroLens and 16 international research papers.
  - Zero trial-and-error: Defensible cross-validation, clear dataset acquisition, and modular team ownership.
- **Open for Questions from the Respected Panel!**
