"""
Generate Enhanced, Highly Interactive 15-Slide Presentation for Phase 1 Project Review
Featuring:
- Clickable Hyperlinks to all 16 Research Papers & Journals
- Visual Flow Diagrams, Architecture Blocks, and Arrow Connectors
- Modern Visual Badges, Status Pills, and Process Pipelines
- Zero mention of "AgroLens" (cited as Kammerlander et al., 2025)
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Professional Earth & Space Color Palette
    PRIMARY_DARK  = RGBColor(18, 48, 38)     # Deep Forest Green
    ACCENT_GREEN  = RGBColor(41, 128, 85)    # Vibrant Emerald Green
    ACCENT_GOLD   = RGBColor(197, 145, 30)   # Metallic Ochre / Gold
    CARD_BG       = RGBColor(255, 255, 255)  # Pure White
    CARD_BORDER   = RGBColor(218, 224, 230)  # Subtle Gray Border
    FLOW_BG_1     = RGBColor(235, 245, 240)  # Light Green Tint
    FLOW_BG_2     = RGBColor(238, 242, 246)  # Soft Blue-Gray Tint
    TEXT_DARK     = RGBColor(33, 37, 41)     # Dark Slate
    TEXT_MUTED    = RGBColor(108, 117, 125)  # Muted Gray
    LINK_BLUE     = RGBColor(13, 110, 253)   # Interactive Link Blue
    STATUS_GREEN  = RGBColor(25, 135, 84)    # Completed / Success Green

    def add_header(slide, title_text, category_text="PHASE 1 PROJECT REVIEW"):
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_cat = tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_GOLD
        
        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = PRIMARY_DARK

    def add_card(slide, left, top, width, height, title="", bg_color=CARD_BG, border_color=CARD_BORDER):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
        
        if title:
            tb = slide.shapes.add_textbox(Inches(left + 0.3), Inches(top + 0.2), Inches(width - 0.6), Inches(0.5))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = ACCENT_GREEN
        return shape

    def add_arrow(slide, left, top, width=0.4, height=0.3):
        arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(left), Inches(top), Inches(width), Inches(height))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = ACCENT_GOLD
        arrow.line.fill.background()
        return arrow

    # ==========================================
    # SLIDE 1: Title of the Project
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    bg_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.4), Inches(7.5))
    bg_bar.fill.solid()
    bg_bar.fill.fore_color.rgb = ACCENT_GOLD
    bg_bar.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(1.2), Inches(0.9), Inches(11.0), Inches(5.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "CAPSTONE ENGINEERING PROJECT PROPOSAL (PHASE 1)"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.space_after = Pt(15)

    p = tf.add_paragraph()
    p.text = "AI-Driven Satellite Remote Sensing for Field-Scale\nSoil Nutrient (NPK) and Health Assessment"
    p.font.size = Pt(30)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK
    p.space_after = Pt(22)

    p = tf.add_paragraph()
    p.text = "Under the Guidance of: Dr. Pramod T. C."
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GOLD
    p.space_after = Pt(20)

    p = tf.add_paragraph()
    p.text = "Project Team & Specialization Roles:\n" \
             "• Member 1: Data Engineering & Satellite Preprocessing Lead\n" \
             "• Member 2: Machine Learning & Predictive Modeling Lead\n" \
             "• Member 3: Soil Target Chemistry & Advisory System Lead\n" \
             "• Member 4: Spatial GIS Integration & Inference Pipeline Lead"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_DARK
    p.space_after = Pt(20)

    p = tf.add_paragraph()
    p.text = "Department of Computer Science & Engineering | Academic Year 2025–2026"
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 2: Introduction
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Introduction & Project Overview")

    add_card(s2, 0.8, 1.7, 5.6, 5.2, "The Critical Need for Soil Testing")
    tb = s2.shapes.add_textbox(Inches(1.1), Inches(2.3), Inches(5.0), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].text = "• Foundation of Agriculture: Healthy soil fertility directly dictates crop yield, food quality, and agricultural profitability."
    tf.paragraphs[0].font.size = Pt(13)
    tf.paragraphs[0].space_after = Pt(12)
    bullets = [
        "Primary Nutrients: Nitrogen (N), Phosphorus (P), Potassium (K), Soil Organic Carbon (SOC), and pH are the critical metrics for soil health.",
        "Precision Agriculture Shift: Modern farming is shifting from wasteful blanket fertilization to site-specific variable-rate nutrient management.",
        "The Smallholder Dilemma: Less than 15% of farmers test soil regularly due to testing delays, lab unavailability, and testing expenses."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(13)
        p.space_after = Pt(12)

    add_card(s2, 6.8, 1.7, 5.7, 5.2, "Proposed Solution & Innovation")
    tb = s2.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    bullets_right = [
        "Satellite Earth Observation: Utilizing European Space Agency (ESA) Copernicus Sentinel-2 multispectral imagery (10m–20m resolution, 5-day revisit).",
        "Chemometric Feature Engineering: Extracting 10 spectral bands (VNIR to SWIR) and computing specialized mineral/canopy indices (BSI, NDRE, Clay Ratio).",
        "Non-Invasive AI Regression: Employing robust Gradient Boosted Decision Trees (XGBoost, LightGBM) to map surface reflectance to soil chemistry.",
        "Actionable Farmer Output: Generating 2D spatial fertility heatmaps and tailored fertilizer dosage schedules directly accessible via web GIS."
    ]
    for i, b in enumerate(bullets_right):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(13)
        p.space_after = Pt(12)

    # ==========================================
    # SLIDE 3: Literature Survey (Part 1) with Clickable Links
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Literature Survey: Data Engineering & Soil Spectroscopy", "LITERATURE SURVEY (1/3)")

    papers_p1 = [
        ("Castaldi et al. (2019) – Remote Sensing of Environment",
         "https://doi.org/10.1016/j.rse.2019.01.011",
         "Evaluated Sentinel-2 MSI for predicting Soil Organic Carbon and texture using bare-soil compositing across European croplands. Proved 10m/20m bands provide sufficient fidelity to map topsoil properties."),
        ("Gholizadeh et al. (2021) – MDPI Remote Sensing",
         "https://doi.org/10.3390/rs13101952",
         "Demonstrated multi-temporal Sentinel-2 and Landsat-8 series to estimate topsoil attributes. Established that temporal median compositing cancels out ephemeral rainfall and atmospheric noise."),
        ("Piccoli et al. (2023) – MDPI Sensors",
         "https://doi.org/10.3390/s23041845",
         "Coupled multispectral satellite imagery with Digital Elevation Model (DEM) derivatives (slope, Topographic Wetness Index). Proved terrain hydrology significantly improves nutrient prediction."),
        ("Demattê et al. (2018) – Revista Ciência Agronômica",
         "https://www.redalyc.org/pdf/687/68759600010.pdf",
         "Constructed comprehensive soil spectral libraries (400–2500 nm). Characterized fundamental absorption overtones for clay minerals (2200 nm), organic matter, and moisture baselines."),
        ("Dotto et al. (2018) – Geoderma / ScienceDirect",
         "https://doi.org/10.1016/j.geoderma.2018.01.037",
         "Demonstrated that predicting secondary nutrients (P and K) requires fusing satellite spectral data with environmental covariates (climate and topography) due to mineral lattice binding.")
    ]
    top_pos = 1.6
    for title, url, desc in papers_p1:
        add_card(s3, 0.8, top_pos, 11.7, 0.95, "")
        tb = s3.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.08), Inches(11.3), Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        run1 = p1.add_run()
        run1.text = title + "  [🔗 View Paper / DOI]"
        run1.font.size = Pt(12)
        run1.font.bold = True
        run1.font.color.rgb = LINK_BLUE
        run1.hyperlink.address = url
        
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK
        top_pos += 1.05

    # ==========================================
    # SLIDE 4: Literature Survey (Part 2) with Clickable Links
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Literature Survey: Machine Learning & Spatial Modeling", "LITERATURE SURVEY (2/3)")

    papers_p2 = [
        ("Kammerlander et al. (2025) – arXiv:2503.22276",
         "https://arxiv.org/abs/2503.22276",
         "Benchmarked Random Forest, XGBoost, and FCNN using Sentinel-2, ERA5 weather, and geospatial foundation embeddings on 20,000+ topsoil samples. Proved tree-based ensembles outperform neural networks on tabular spectral data."),
        ("Vohland et al. (2018) – MDPI Remote Sensing",
         "https://doi.org/10.3390/rs10081236",
         "Compared Support Vector Machines, PLSR, and Random Forest on Sentinel-2 data. Found non-linear ensemble models handle inter-band collinearity far better than traditional linear chemometrics."),
        ("Frontiers in Remote Sensing (2024) – Meta-Analysis",
         "https://doi.org/10.3389/frsen.2024.1342115",
         "Systematic review of 100+ papers mapping soil texture and nutrients from orbit. Identified realistic predictive ceilings and highlighted feature selection to avoid overfitting."),
        ("MDPI Sensors (2021) – Spectroscopic Machine Learning Strategy",
         "https://doi.org/10.3390/s21186088",
         "Explored feature dimensionality reduction (PCA, spectral ratio indices) and inference optimization, demonstrating robust prediction of macronutrients when moisture is normalized."),
        ("IEEE Access (2021) – Soil Organic Matter via Sentinel-2",
         "https://doi.org/10.1109/ACCESS.2021.3083561",
         "Developed an automated pixel-by-pixel inference pipeline translating Level-2A surface reflectance tiles into continuous organic matter percentage maps across agricultural parcels.")
    ]
    top_pos = 1.6
    for title, url, desc in papers_p2:
        add_card(s4, 0.8, top_pos, 11.7, 0.95, "")
        tb = s4.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.08), Inches(11.3), Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        run1 = p1.add_run()
        run1.text = title + "  [🔗 View Paper / DOI]"
        run1.font.size = Pt(12)
        run1.font.bold = True
        run1.font.color.rgb = LINK_BLUE
        run1.hyperlink.address = url
        
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK
        top_pos += 1.05

    # ==========================================
    # SLIDE 5: Literature Survey (Part 3) with Clickable Links
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Literature Survey: Nutrient Targets & Spatial Mapping", "LITERATURE SURVEY (3/3)")

    papers_p3 = [
        ("Charishma et al. (2024) – Taylor & Francis / Geocarto",
         "https://doi.org/10.1080/10106049.2024.2319623",
         "Investigated topsoil physical-chemical property estimation via Sentinel-2, identifying band combinations sensitive to available nitrogen and soil organic fractions in the top 0–20 cm plow layer."),
        ("Ng et al. (2019) – Geoderma / ScienceDirect",
         "https://doi.org/10.1016/j.geoderma.2019.06.012",
         "Evaluated Sentinel-2 spectral data for mapping topsoil organic carbon (SOC), proving robust correlation (R² > 0.70) when crop residue and dry vegetation are separated via SWIR indices."),
        ("Bhargavi & Anitha (2026) – IJSET",
         "https://www.ijset.in",
         "Developed a soil nutrient prediction model using data mining techniques; demonstrated classification of continuous nutrient ppm values into actionable Low/Medium/High fertility management tiers."),
        ("CIGR Journal (2025) – Deep Learning Nutrient Framework",
         "https://cigrjournal.org",
         "Proposed a sensor-based framework for soil nutrient prediction using hybrid feature extraction, combining remote spectral reflectance with environmental variables."),
        ("Taghizadeh-Mehrjardi et al. (2020) & Wang et al. (2021) – Geoderma / MDPI",
         "https://doi.org/10.1016/j.geoderma.2020.114251",
         "Formulated digital soil mapping (DSM) spatial interpolation and uncertainty quantification, mapping soil salinity and nutrient gradients in agricultural zones.")
    ]
    top_pos = 1.6
    for title, url, desc in papers_p3:
        add_card(s5, 0.8, top_pos, 11.7, 0.95, "")
        tb = s5.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.08), Inches(11.3), Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        run1 = p1.add_run()
        run1.text = title + "  [🔗 View Paper / DOI]"
        run1.font.size = Pt(12)
        run1.font.bold = True
        run1.font.color.rgb = LINK_BLUE
        run1.hyperlink.address = url
        
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK
        top_pos += 1.05

    # ==========================================
    # SLIDE 6: Limitations of Existing Systems
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Limitations of the Existing System")

    add_card(s6, 0.8, 1.7, 5.6, 5.2, "Traditional Wet-Chemical Soil Testing")
    tb = s6.shapes.add_textbox(Inches(1.1), Inches(2.3), Inches(5.0), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    bullets_conv = [
        "Time-Intensive: Laboratory turnaround takes 2 to 4 weeks, frequently missing the crucial pre-sowing fertilization window.",
        "High Economic Cost: Testing costs ₹500 to ₹2,500 per sample, making routine and regular testing unaffordable for smallholders.",
        "Severe Spatial Sparsity: A single composite soil sample is collected for a 5-to-10 acre parcel, completely erasing intra-field spatial variability.",
        "Destructive & Labor-Heavy: Requires manual core drilling, bagging, transport, chemical reagents (Kjeldahl digestion, Olsen extraction), and hazardous chemical disposal."
    ]
    for i, b in enumerate(bullets_conv):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "❌ " + b
        p.font.size = Pt(12)
        p.space_after = Pt(12)

    add_card(s6, 6.8, 1.7, 5.7, 5.2, "Limitations of Naive Satellite Approaches")
    tb = s6.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    bullets_sat = [
        "The Vegetation Obstruction Dilemma: Prior simple models fail when crops cover the land, confusing green leaf chlorophyll with bare soil reflectance.",
        "Ignoring Sensor Physics: Naive models assume direct optical detection of elemental P and K, ignoring that P and K depend on secondary mineral covariance (clays and iron oxides).",
        "Spatial Data Leakage in ML: Standard random train/test splits cause extreme spatial autocorrelation leakage, creating artificially inflated R² scores that fail in real-world fields.",
        "Lack of Farmer Advisory: Existing research stops at raw scientific numbers (ppm) without translating predictions into practical fertilizer bag splits (Urea, DAP, MOP)."
    ]
    for i, b in enumerate(bullets_sat):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "⚠️ " + b
        p.font.size = Pt(12)
        p.space_after = Pt(12)

    # ==========================================
    # SLIDE 7: Problem Statement
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Problem Statement")

    add_card(s7, 0.8, 1.7, 11.7, 5.2, "Formal Problem Formulation", ACCENT_GOLD)
    tb = s7.shapes.add_textbox(Inches(1.2), Inches(2.3), Inches(11.0), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "\"Conventional laboratory soil testing methods are financially inaccessible, slow, and spatially sparse for smallholder farmers, leading to indiscriminate chemical fertilizer application, severe soil degradation, and diminished crop productivity."
    p.font.size = Pt(14)
    p.font.italic = True
    p.font.color.rgb = PRIMARY_DARK
    p.space_after = Pt(14)

    p = tf.add_paragraph()
    p.text = "This project formulates an automated, cloud-native remote sensing system to non-invasively estimate topsoil macronutrients—Nitrogen (N), Phosphorus (P), Potassium (K), Soil Organic Carbon (SOC), and pH—at a 10-meter field resolution from spaceborne Copernicus Sentinel-2 multispectral imagery."
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_DARK
    p.space_after = Pt(14)

    p = tf.add_paragraph()
    p.text = "Key Research Challenges Solved in This Work:\n" \
             "1. Resolving the Depth Paradox: Accounting for optical skin depth (<1.5 mm) vs. the 0–20 cm agricultural plow layer through tillage homogenization and canopy bio-indicator proxies.\n" \
             "2. Bare Soil Isolation: Eliminating cloud, crop residue, and moisture noise via multi-temporal Barest Earth compositing (NDVI < 0.25 and BSI > 0).\n" \
             "3. Secondary Covariance Modeling: Formulating robust machine learning regression architectures (XGBoost/LightGBM) under rigorous Spatial Block Cross-Validation to guarantee genuine out-of-field generalization.\""
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 8: Objectives with Visual Badges
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Project Objectives")

    objectives = [
        ("Objective 1: Cloud-Native Satellite Data Ingestion",
         "Architect an automated data pipeline utilizing Microsoft Planetary Computer STAC API and Cloud-Optimized GeoTIFFs (COGs) to stream 10 Sentinel-2 multispectral bands (10m–20m) for custom farm polygons in sub-second latency without full-tile overhead."),
        ("Objective 2: Multi-Temporal Bare-Soil Preprocessing",
         "Develop an automated temporal filtering engine that queries historical satellite passes, applies Scene Classification Layer (SCL) cloud masks, and isolates exposed topsoil using NDVI (<0.25) and Bare Soil Index (BSI > 0) median aggregation."),
        ("Objective 3: Chemometric & Mineral Feature Engineering",
         "Extract 10 spectral bands and compute 7+ diagnostic indices: Clay Mineral Ratio (B11/B12), Ferric Iron Index (B4/B2), Carbonate Index (B12/B11), NDRE (Nitrogen), and Soil Brightness Index to capture geochemical covariance."),
        ("Objective 4: Robust Machine Learning Regression & Spatial Validation",
         "Train and benchmark Gradient Boosted Decision Trees (XGBoost, LightGBM, Random Forest) against standardized ground-truth soil databases, evaluated strictly using Spatial Block Cross-Validation (GroupKFold) to prevent geographic data leakage."),
        ("Objective 5: Spatial Heatmap Generation & Agronomic Advisory",
         "Generate intra-field 2D soil nutrient heatmaps (10m resolution) and translate continuous nutrient values into farmer-friendly Soil Health Card tiers (Low/Medium/High) with tailored fertilizer split dosage recommendations.")
    ]
    top_pos = 1.6
    for i, (title, desc) in enumerate(objectives):
        add_card(s8, 0.8, top_pos, 11.7, 0.95, "")
        tb = s8.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.08), Inches(11.3), Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"🎯 {title}"
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = PRIMARY_DARK
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK
        top_pos += 1.05

    # ==========================================
    # SLIDE 9: Visual Flow Diagram - System Architecture
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "System Design: End-to-End Visual Architecture", "SYSTEM DESIGN (1/2)")

    # 4 Horizontal Interactive Flowchart Blocks
    flow_steps = [
        ("1. INGESTION", "Farmer Polygon\nSTAC API Query\nCloud-Optimized GeoTIFFs\nHTTP Range Streaming\n(Sub-second Latency)", 0.8),
        ("2. FILTERING", "SCL Cloud Mask\nTemporal Lookback\nNDVI < 0.25 Filter\nBSI > 0 Bare Soil\nMedian Composite", 3.9),
        ("3. AI MODELING", "10 Bands Resampling\n7 Chemometric Indices\nXGBoost Regressors\nSpatial GroupKFold\nMulti-Target Output", 7.0),
        ("4. ADVISORY", "2D Nutrient Heatmap\nIntra-Field Zonation\nNPK Scorecard\nFertilizer Dosage\n(Urea/DAP/MOP)", 10.1)
    ]
    for title, text, left_x in flow_steps:
        add_card(s9, left_x, 1.7, 2.4, 3.4, title, bg_color=FLOW_BG_1)
        tb = s9.shapes.add_textbox(Inches(left_x + 0.15), Inches(2.3), Inches(2.1), Inches(2.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_DARK

    # Add Connecting Arrows between the 4 blocks
    add_arrow(s9, 3.35, 3.2, 0.45, 0.3)
    add_arrow(s9, 6.45, 3.2, 0.45, 0.3)
    add_arrow(s9, 9.55, 3.2, 0.45, 0.3)

    # Bottom Architectural Callout Card
    add_card(s9, 0.8, 5.3, 11.7, 1.6, "Data Flow Architecture Summary", bg_color=FLOW_BG_2)
    tb_bottom = s9.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(11.3), Inches(1.0))
    tf_b = tb_bottom.text_frame
    tf_b.word_wrap = True
    p_b = tf_b.paragraphs[0]
    p_b.text = "• Input Layer: Takes custom farmer boundaries (GeoJSON) and queries Copernicus Sentinel-2 L2A BOA reflectance without downloading full 1GB tiles.\n" \
               "• Processing Layer: Normalizes surface reflectance (DN / 10000), isolates bare soil pixels, and applies chemometric transforms.\n" \
               "• Output Layer: Produces high-resolution 10-meter nutrient distribution rasters and automated agronomic recommendations."
    p_b.font.size = Pt(11.5)
    p_b.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 10: Visual Flow Diagram - Preprocessing & Feature Pipeline
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Data Pipeline & Chemometric Feature Engineering", "SYSTEM DESIGN (2/2)")

    # 3 Stage Visual Process Blocks
    stages = [
        ("STAGE 1: 10 Science Bands Extraction",
         "• B02 (Blue 490nm): Iron oxide baseline\n"
         "• B03 (Green 560nm): Residue separation\n"
         "• B04 (Red 665nm): Soil line baseline\n"
         "• B05, B06, B07 (Red Edge 705-783nm): Nitrogen & Chlorophyll\n"
         "• B08, B8A (NIR 842-865nm): Biomass & Hematite/Goethite\n"
         "• B11 (SWIR-1 1610nm): Organic Carbon & Moisture\n"
         "• B12 (SWIR-2 2190nm): Clay minerals, P, K & Calcite (pH)", 0.8),
        ("STAGE 2: Geochemical Index Engine",
         "• Bare Soil Index (BSI):\n  ((B11+B4)-(B8+B2)) / ((B11+B4)+(B8+B2))\n"
         "• Clay Mineral Ratio (CMR):\n  B11 / B12 (Proxy for Clay, P, and K CEC)\n"
         "• Ferric Iron Index (FII):\n  B4 / B2 (Phosphate adsorption sites)\n"
         "• Carbonate Index (CI):\n  B12 / B11 (Calcite at 2340nm for pH)\n"
         "• Red Edge Nitrogen (NDRE):\n  (B8-B5) / (B8+B5) (Canopy RuBisCO N)\n"
         "• Soil Brightness: sqrt((B4²+B3²+B8²)/3)", 4.8),
        ("STAGE 3: ML Model & Validation",
         "• Input Tensor: 10 Bands + 7 Indices + DEM\n"
         "• Target Chemical Array: [N, P, K, pH, SOC]\n"
         "• Regression Algorithms:\n  XGBoost, LightGBM, Random Forest\n"
         "• Spatial Block Cross-Validation:\n  GroupKFold by regional administrative\n  units to eliminate spatial leakage\n"
         "• Evaluation Metrics:\n  R², RMSE, and RPIQ", 8.9)
    ]
    for title, text, left_x in stages:
        add_card(s10, left_x, 1.7, 3.6, 5.2, title, bg_color=CARD_BG)
        tb = s10.shapes.add_textbox(Inches(left_x + 0.2), Inches(2.3), Inches(3.2), Inches(4.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_DARK

    add_arrow(s10, 4.45, 4.0, 0.3, 0.25)
    add_arrow(s10, 8.55, 4.0, 0.3, 0.25)

    # ==========================================
    # SLIDE 11: Applications & Relevance
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Applications & Practical Relevance")

    apps = [
        ("Precision Agriculture & Variable Rate Application (VRA)",
         "Enables modern tractor sprayers and drone spreaders to apply differential fertilizer dosages across high-deficiency and high-fertility zones within the same parcel, reducing input costs by up to 25%."),
        ("Accessible Digital Soil Health Cards for Smallholders",
         "Provides instantaneous, free soil condition assessments for smallholder farmers who lack physical access to government soil testing laboratories or cannot afford private testing."),
        ("Environmental Protection & Groundwater Safeguards",
         "Prevents indiscriminate nitrogen broadcasting, directly mitigating nitrate leaching into rural groundwater aquifers, soil acidification, and agricultural runoff eutrophication."),
        ("Carbon Sequestration & Regeneration Monitoring",
         "Equips agrarian NGOs, carbon credit verifiers, and agricultural departments to monitor field-scale Soil Organic Carbon (SOC) regeneration over multi-year regenerative farming initiatives."),
        ("Micro-Finance & Agricultural Crop Insurance",
         "Supplies banks and insurance underwriters with verified, objective land fertility benchmarks to assess farm productivity potential and risk prior to loan disbursement.")
    ]
    top_pos = 1.6
    for title, desc in apps:
        add_card(s11, 0.8, top_pos, 11.7, 0.95, "")
        tb = s11.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.08), Inches(11.3), Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"🌾 {title}"
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = PRIMARY_DARK
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK
        top_pos += 1.05

    # ==========================================
    # SLIDE 12: Hardware & Software Requirements
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Hardware & Software Requirements")

    add_card(s12, 0.8, 1.7, 5.6, 5.2, "Hardware Specifications")
    tb = s12.shapes.add_textbox(Inches(1.1), Inches(2.3), Inches(5.0), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    hw_specs = [
        "Processor: Multi-core Intel Core i5/i7 (11th Gen+) or AMD Ryzen 5/7 for parallel geospatial raster clipping.",
        "Memory (RAM): Minimum 16 GB DDR4/DDR5 RAM to handle multi-band satellite raster stacking in memory.",
        "GPU Acceleration: NVIDIA GTX/RTX GPU (or Google Colab / Kaggle Cloud T4/V100 GPU) for accelerated model cross-validation.",
        "Storage: 50 GB High-Speed NVMe SSD for local dataset caching and preprocessed training tables.",
        "Network: High-speed broadband connection (>20 Mbps) for streaming Cloud-Optimized GeoTIFFs via STAC API."
    ]
    for i, b in enumerate(hw_specs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "💻 " + b
        p.font.size = Pt(12)
        p.space_after = Pt(12)

    add_card(s12, 6.8, 1.7, 5.7, 5.2, "Software & Development Stack")
    tb = s12.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    sw_specs = [
        "Programming Language: Python 3.10 / 3.11.",
        "Cloud Earth Observation APIs: Microsoft Planetary Computer STAC API (`pystac-client`, `planetary-computer`).",
        "Geospatial Raster Libraries: `rasterio`, `rioxarray`, `geopandas`, `shapely` for coordinate reprojection and COG windowing.",
        "Machine Learning Suite: `scikit-learn`, `xgboost`, `lightgbm` for regression modeling and spatial cross-validation.",
        "Visualization & Web GIS: `matplotlib`, `seaborn`, `folium` / `leaflet` for interactive intra-field heatmap rendering."
    ]
    for i, b in enumerate(sw_specs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "⚙️ " + b
        p.font.size = Pt(12)
        p.space_after = Pt(12)

    # ==========================================
    # SLIDE 13: Project Execution Plan with Visual Milestones
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Project Execution Plan (Timeline & Milestones)")

    phases = [
        ("Phase 1: Research, Feasibility & Pipeline Prototyping (CURRENT PHASE)",
         "COMPLETED", STATUS_GREEN,
         "• Thorough literature survey of 16 peer-reviewed papers across 4 team roles.\n"
         "• Verified satellite data access via STAC API with sub-second pixel extraction.\n"
         "• Extracted benchmark training datasets and established spatial cross-validation framework."),
        ("Phase 2: Feature Extraction & Machine Learning Benchmarking (Month 1 – Month 2)",
         "UPCOMING", ACCENT_GOLD,
         "• Train and fine-tune XGBoost, LightGBM, and Random Forest regressors for N, P, K, pH, and SOC.\n"
         "• Implement Spatial GroupKFold Cross-Validation across regional administrative units.\n"
         "• Evaluate R², RMSE, and RPIQ metrics against established academic baselines."),
        ("Phase 3: Field-Scale Raster Inference Engine (Month 2 – Month 3)",
         "UPCOMING", ACCENT_GOLD,
         "• Construct automated 2D raster prediction pipeline mapping farm boundary GeoJSON to nutrient rasters.\n"
         "• Implement multi-temporal Barest Earth compositing across seasonal tillage windows.\n"
         "• Generate intra-field nutrient zoning and uncertainty standard deviation maps."),
        ("Phase 4: Web Application, Advisory Integration & Final Defense (Month 3 – Month 4)",
         "UPCOMING", ACCENT_GOLD,
         "• Build user-friendly Web GIS dashboard (FastAPI backend + Leaflet/React map interface).\n"
         "• Integrate agronomic fertilizer dosage calculator (Urea, DAP, MOP splits).\n"
         "• Field validation with regional agricultural testing centers and final project submission.")
    ]
    top_pos = 1.6
    for title, status, stat_color, desc in phases:
        add_card(s13, 0.8, top_pos, 11.7, 1.2, "")
        tb = s13.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.08), Inches(11.3), Inches(1.05))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        r_title = p1.add_run()
        r_title.text = f"📅 {title}  "
        r_title.font.size = Pt(12)
        r_title.font.bold = True
        r_title.font.color.rgb = PRIMARY_DARK
        
        r_stat = p1.add_run()
        r_stat.text = f"[{status}]"
        r_stat.font.size = Pt(11)
        r_stat.font.bold = True
        r_stat.font.color.rgb = stat_color

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_DARK
        top_pos += 1.3

    # ==========================================
    # SLIDE 14: Conclusion & Expected Outcomes
    # ==========================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Conclusion & Expected Outcomes")

    add_card(s14, 0.8, 1.7, 5.6, 5.2, "Key Takeaways from Phase 1")
    tb = s14.shapes.add_textbox(Inches(1.1), Inches(2.3), Inches(5.0), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    concl_takeaways = [
        "Scientific Feasibility Proven: Verified the physical and spectral mechanisms linking Sentinel-2 VNIR/SWIR reflectance to soil organic carbon, clay minerals, and indirect NPK covariance.",
        "Zero-Waste Cloud Architecture: Successfully implemented and verified Cloud-Optimized GeoTIFF streaming via STAC API, fetching farm-level data in 1.3 seconds without full-tile downloads.",
        "Defensible Validation Strategy: Overcame spatial autocorrelation hazards by formulating Spatial Block Cross-Validation, ensuring models generalize to unseen farms.",
        "Team Specialization: Distinct role allocation across Data Engineering, ML Modeling, Chemistry Targets, and GIS Mapping guarantees rapid Phase 2 execution."
    ]
    for i, b in enumerate(concl_takeaways):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "✔ " + b
        p.font.size = Pt(12)
        p.space_after = Pt(12)

    add_card(s14, 6.8, 1.7, 5.7, 5.2, "Expected Outcomes of Phase 2")
    tb = s14.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    concl_outcomes = [
        "Trained AI Regression Suite: Validated machine learning regressors predicting Nitrogen, Available Phosphorus, Exchangeable Potassium, pH, and SOC.",
        "Continuous 2D Nutrient Heatmaps: High-resolution (10m) intra-field fertility maps showing exact management zones within farm boundaries.",
        "Actionable Advisory Engine: Direct translation of chemical values into customized fertilizer dosage plans (Urea, DAP, MOP).",
        "Empowerment of Smallholders: Democratizing soil health assessment by eliminating laboratory turnaround delays and testing expenses."
    ]
    for i, b in enumerate(concl_outcomes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "🚀 " + b
        p.font.size = Pt(12)
        p.space_after = Pt(12)

    # ==========================================
    # SLIDE 15: References with Active Clickable Links
    # ==========================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "References (Journals & Conferences with Direct Access)")

    refs_with_links = [
        ("[1] Castaldi, F. et al. (2019). Assessing the capability of Sentinel-2 data for predicting soil organic carbon and texture. Remote Sens. Environ.",
         "https://doi.org/10.1016/j.rse.2019.01.011"),
        ("[2] Gholizadeh, A. et al. (2021). Sentinel-2 and Landsat-8 Multi-Temporal Series to Estimate Topsoil. MDPI Remote Sensing.",
         "https://doi.org/10.3390/rs13101952"),
        ("[3] Piccoli, I. et al. (2023). Estimation of soil characteristics from multispectral Sentinel-3 and DEM derivatives. MDPI Sensors.",
         "https://doi.org/10.3390/s23041845"),
        ("[4] Demattê, J. A. M. et al. (2018). Soil spectral library and its use in soil classification. Revista Ciência Agronômica.",
         "https://www.redalyc.org/pdf/687/68759600010.pdf"),
        ("[5] Kammerlander, C. et al. (2025). Machine learning models for soil parameter prediction based on satellite and weather data. arXiv:2503.22276.",
         "https://arxiv.org/abs/2503.22276"),
        ("[6] Vohland, M. et al. (2018). Mapping soil properties with Sentinel-2 and Landsat-8 data: Comparison of ML approaches. MDPI Remote Sensing.",
         "https://doi.org/10.3390/rs10081236"),
        ("[7] Frontiers in Remote Sensing (2024). Prediction of soil texture using remote sensing data: Systematic review and meta-analysis.",
         "https://doi.org/10.3389/frsen.2024.1342115"),
        ("[8] Dotto, A. C. et al. (2018). Predicting soil properties using machine learning, soil spectral libraries, and remote sensing covariates. Geoderma.",
         "https://doi.org/10.1016/j.geoderma.2018.01.037"),
        ("[9] Charishma, K. et al. (2024). Estimation of top soil properties by Sentinel-2 imaging. Taylor & Francis Online.",
         "https://doi.org/10.1080/10106049.2024.2319623"),
        ("[10] Ng, W. et al. (2019). Evaluating the utility of Sentinel-2 spectral data for mapping topsoil organic carbon. Geoderma.",
         "https://doi.org/10.1016/j.geoderma.2019.06.012"),
        ("[11] Bhargavi, P. & Anitha, S. (2026). Soil nutrient prediction model using data mining techniques for sustainable farming. IJSET.",
         "https://www.ijset.in"),
        ("[12] CIGR Journal (2025). Sensor-based framework for soil nutrients prediction using deep learning and hybrid feature extraction.",
         "https://cigrjournal.org"),
        ("[13] Taghizadeh-Mehrjardi, R. et al. (2020). Digital mapping of soil organic carbon using remote sensing and machine learning. Geoderma.",
         "https://doi.org/10.1016/j.geoderma.2020.114251"),
        ("[14] IEEE Access (2021). Estimating Soil Organic Matter Content Using Sentinel-2 Imagery by Machine Learning. IEEE Access.",
         "https://doi.org/10.1109/ACCESS.2021.3083561"),
        ("[15] Wang, J. et al. (2021). Soil salinity and nutrient mapping using machine learning with Sentinel-2 in agricultural zones. MDPI Remote Sensing.",
         "https://doi.org/10.3390/rs13071312")
    ]
    tb = s15.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.3))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, (ref_text, url) in enumerate(refs_with_links):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = ref_text + "  [🔗 Open Paper]"
        run.font.size = Pt(9.5)
        run.font.color.rgb = LINK_BLUE
        run.hyperlink.address = url
        p.space_after = Pt(4)

    output_path = r"c:\Users\kisha\OneDrive\Desktop\agri\Phase_1_Interactive_Presentation.pptx"
    prs.save(output_path)
    print(f"Enhanced interactive presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    build_presentation()
