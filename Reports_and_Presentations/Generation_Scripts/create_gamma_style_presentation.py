"""
Generate a Premium, Highly Interactive Presentation Matching the Gamma PDF Design:
- Uses authentic high-resolution images extracted directly from the user's Gamma PDF
- Split-screen hero layouts with authentic field photography
- 5-card horizontal column grids with miniature photo headers
- 3 stacked horizontal process chevrons with graduating lengths (Resolve Depth Paradox, Isolate Bare Soil, Model Covariance)
- 4-stage pipeline architecture flow diagram with visual connecting flow
- Mathematical formulas for chemometric indices (BSI, CMR, FII, CI, NDRE)
- 4-phase execution roadmap with numbered footer columns and agricultural photography
- Active, clickable paper hyperlinks on all literature cards and references
- 100% compliant with the 12-15 slide department rubric
- Non-commercial, strictly academic tone; peer benchmark cited strictly as Kammerlander et al. (2025)
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

img_dir = r"c:\Users\kisha\OneDrive\Desktop\agri\assets\pdf_images"

def get_img(name):
    base = os.path.splitext(name)[0]
    for f in os.listdir(img_dir):
        if f.startswith(base):
            return os.path.join(img_dir, f)
    return None

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette matching Gamma PDF
    BG_MAIN       = RGBColor(252, 252, 250)  # Subtle warm off-white
    PRIMARY_DARK  = RGBColor(28, 30, 28)     # Deep Charcoal
    ACCENT_BROWN  = RGBColor(92, 58, 33)     # Rich Dark Brown / Soil Sienna
    ACCENT_TERRA  = RGBColor(156, 82, 38)    # Medium Terracotta
    ACCENT_GOLD   = RGBColor(196, 126, 48)   # Warm Ochre / Amber
    ACCENT_GREEN  = RGBColor(46, 90, 68)     # Forest Green
    CARD_BG       = RGBColor(255, 255, 255)  # Pure White
    CARD_BORDER   = RGBColor(228, 230, 226)  # Subtle border gray
    TEXT_DARK     = RGBColor(40, 44, 42)     # Readable Body Text
    TEXT_MUTED    = RGBColor(110, 115, 112)  # Muted secondary text
    LINK_BLUE     = RGBColor(24, 100, 185)   # Interactive hyperlink blue
    LINE_GRAY     = RGBColor(215, 218, 214)  # Thin separator line

    FONT_TITLE = "Georgia"
    FONT_BODY  = "Calibri"
    FONT_CODE  = "Consolas"

    def set_slide_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_MAIN
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="PHASE 1 PROJECT REVIEW"):
        # Category Pill
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(7.5), Inches(0.3))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = FONT_BODY
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_GOLD

        # Title
        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.7), Inches(0.65))
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = FONT_TITLE
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = PRIMARY_DARK

        # Top-right interactive navigation pill badge
        nav_tb = slide.shapes.add_textbox(Inches(8.5), Inches(0.35), Inches(4.0), Inches(0.3))
        nav_tf = nav_tb.text_frame
        nav_tf.word_wrap = True
        nav_tf.margin_left = nav_tf.margin_top = nav_tf.margin_right = nav_tf.margin_bottom = 0
        p_nav = nav_tf.paragraphs[0]
        p_nav.text = "CAPSTONE 2025–26 | DR. PRAMOD T. C."
        p_nav.font.name = FONT_BODY
        p_nav.font.size = Pt(9.5)
        p_nav.font.bold = True
        p_nav.font.color.rgb = TEXT_MUTED
        p_nav.alignment = PP_ALIGN.RIGHT

    def add_card(slide, left, top, width, height, title="", bg_color=CARD_BG, border_color=CARD_BORDER, left_bar_color=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)
        
        # Optional vertical left accent bar (matching Page 3 bottom cards)
        if left_bar_color:
            bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(0.12), Inches(height))
            bar.fill.solid()
            bar.fill.fore_color.rgb = left_bar_color
            bar.line.fill.background()

        if title:
            tb = slide.shapes.add_textbox(Inches(left + 0.18), Inches(top + 0.14), Inches(width - 0.36), Inches(0.42))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = title
            p.font.name = FONT_TITLE
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = PRIMARY_DARK
        return card

    # =========================================================================
    # SLIDE 1: Title (Split-Screen Hero Matching Gamma PDF Page 1)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1)

    s1_img = get_img("page_01_img_01")
    if s1_img:
        s1.shapes.add_picture(s1_img, Inches(8.3), Inches(0), Inches(5.033), Inches(7.5))

    tb = s1.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(7.1), Inches(6.3))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = "AI-Driven Satellite Remote\nSensing for Field-Scale Soil\nNutrient (NPK) and Health\nAssessment"
    p.font.name = FONT_TITLE
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_DARK
    p.space_after = Pt(14)

    p = tf.add_paragraph()
    p.text = "CAPSTONE ENGINEERING PROJECT PROPOSAL (PHASE 1) — Department of Computer Science & Engineering, Academic Year 2025–2026.\nProject Guide: Dr. Pramod T. C. | Team: 4 Specialized Roles (Data Engineering, ML Modeling, Soil Chemistry, Web GIS)."
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_after = Pt(14)

    # Divider line
    line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(3.2), Inches(6.9), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = LINE_GRAY
    line.line.fill.background()

    tb_bot = s1.shapes.add_textbox(Inches(0.8), Inches(3.45), Inches(7.1), Inches(3.5))
    tf_b = tb_bot.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0

    callouts_s1 = [
        ("Problem:", "Farmers and agronomists often lack timely, affordable, field-scale visibility into soil nutrient variability, making it difficult to detect NPK deficiencies early and optimize interventions."),
        ("Key innovation:", "This project combines Sentinel-2 satellite imagery, geospatial preprocessing, and machine learning to estimate soil NPK status and broader field health indicators from remote sensing signals."),
        ("Expected impact:", "The system aims to support faster, data-driven soil management decisions, reduce unnecessary sampling and input use, and improve crop productivity through more precise advisory recommendations.")
    ]
    for i, (label, text) in enumerate(callouts_s1):
        p = tf_b.paragraphs[0] if i == 0 else tf_b.add_paragraph()
        run_l = p.add_run()
        run_l.text = label + " "
        run_l.font.name = FONT_BODY
        run_l.font.bold = True
        run_l.font.size = Pt(11)
        run_l.font.color.rgb = PRIMARY_DARK
        run_t = p.add_run()
        run_t.text = text
        run_t.font.name = FONT_BODY
        run_t.font.size = Pt(10.5)
        run_t.font.color.rgb = TEXT_DARK
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 2: Why This Matters (5 Cards with Authentic Miniature Photos)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2)
    add_header(s2, "Why This Matters — The Critical Need for Soil Testing", "PROBLEM CONTEXT")

    cols_s2 = [
        ("page_02_img_01", "Soil Drives\nAgriculture",
         "Healthy soil fertility (N, P, K, SOC, pH) directly dictates crop yield, food security, and farm profitability.\n\nPrecision agriculture shifts practice from blanket fertilization to site-specific variable-rate management.", 0.8),
        ("page_02_img_02", "Smallholder\nConstraints",
         "Less than 15% of farmers regularly test soil due to long turnaround (2-4 weeks), lab inaccessibility, and high per-sample costs—creating a pressing need for low-cost, rapid alternatives.", 3.2),
        ("page_02_img_03", "Economic Impact of\nSoil Degradation",
         "Soil nutrient depletion, erosion, and pH imbalance reduce yields, increase fertilizer waste, and raise production costs.\n\nWithout testing, farmers overapply in some zones while starving others.", 5.6),
        ("page_02_img_04", "Climate Resilience\nThrough Soil Health",
         "Well-managed soils retain more moisture, support stronger root systems, and buffer crops against drought, heavy rain, and temperature stress.\n\nTesting helps protect organic matter season after season.", 8.0),
        ("page_02_img_05", "Precision\nAgriculture ROI",
         "Targeted nutrient application improves input efficiency, reduces unnecessary fertilizer spend, and increases yield consistency.\n\nSoil testing provides the data foundation for viable precision agriculture.", 10.4)
    ]
    for img_name, title, text, left_x in cols_s2:
        add_card(s2, left_x, 1.45, 2.15, 5.5)
        img_p = get_img(img_name)
        if img_p:
            s2.shapes.add_picture(img_p, Inches(left_x + 0.15), Inches(1.6), Inches(1.85), Inches(1.15))

        tb_t = s2.shapes.add_textbox(Inches(left_x + 0.15), Inches(2.85), Inches(1.85), Inches(0.75))
        tf_t = tb_t.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_TITLE
        p_t.font.size = Pt(12)
        p_t.font.bold = True
        p_t.font.color.rgb = PRIMARY_DARK

        tb_b = s2.shapes.add_textbox(Inches(left_x + 0.15), Inches(3.65), Inches(1.85), Inches(3.1))
        tf_b = tb_b.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0
        p_b = tf_b.paragraphs[0]
        p_b.text = text
        p_b.font.name = FONT_BODY
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 3: Proposed Solution (Split Layout + 4 Left-Accent Cards)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3)
    add_header(s3, "Proposed Solution — Remote Sensing + Chemometrics + AI", "SYSTEM OVERVIEW")

    tb = s3.shapes.add_textbox(Inches(0.8), Inches(1.45), Inches(6.6), Inches(3.7))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = "We combine ESA Copernicus Sentinel-2 multispectral satellite imagery with chemometric feature engineering and AI regression to estimate soil properties without physical sampling at every point. Sentinel-2 captures reflected light across visible, red-edge, near-infrared, and short-wave infrared bands at 10–20 m spatial resolution with a 5-day revisit cycle."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "Chemometrics means extracting quantitative, physically meaningful predictors from spectral data. Instead of using raw pixels alone, we derive indices and band ratios sensitive to soil background, moisture, organic matter, and clay/mineral composition. Key features include BSI (Bare Soil Index), NDRE (Normalized Difference Red Edge), and Clay Ratio (B11/B12)."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK
    p.space_after = Pt(10)

    p = tf.add_paragraph()
    p.text = "The AI layer uses supervised regression models such as XGBoost and LightGBM. These models learn the mapping from spectral features and indices to ground-truth soil chemistry measurements, predicting continuous nutrient values to produce high-resolution 2D fertility heatmaps and variable-rate fertilizer schedules."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK

    s3_img = get_img("page_03_img_01")
    if s3_img:
        s3.shapes.add_picture(s3_img, Inches(7.7), Inches(1.45), Inches(4.8), Inches(3.6))

    bottom_cards_s3 = [
        ("Sentinel-2 Data", "Multispectral imagery provides repeatable field coverage across visible, red-edge, NIR, and SWIR bands.", 0.8),
        ("Chemometric Features", "Engineered indices such as BSI, NDRE, and Clay Ratio convert raw reflectance into soil-relevant predictors.", 3.9),
        ("AI Regression", "XGBoost / LightGBM learn nonlinear relationships between spectral features and laboratory measurements.", 7.0),
        ("Decision Outputs", "Predictions are turned into fertility heatmaps and prescription layers for precision agriculture.", 10.1)
    ]
    for title, text, left_x in bottom_cards_s3:
        add_card(s3, left_x, 5.35, 2.45, 1.7, title="", left_bar_color=ACCENT_BROWN)
        tb = s3.shapes.add_textbox(Inches(left_x + 0.25), Inches(5.45), Inches(2.05), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_TITLE
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_DARK
        p.space_after = Pt(4)
        p2 = tf.add_paragraph()
        p2.text = text
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 4: Literature Survey (Part 1 - Data Engineering & Soil Spectroscopy)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4)
    add_header(s4, "Literature Foundations — Data Engineering & Soil Spectroscopy", "LITERATURE SURVEY (1/3)")

    papers_s4 = [
        ("page_04_img_01", "Sentinel-2 for Soil Mapping", "https://doi.org/10.1016/j.rse.2019.01.011",
         "Castaldi et al. (2019) and Gholizadeh et al. (2021) demonstrate Sentinel-2 multispectral fidelity and multi-temporal compositing effectively map topsoil properties and cancel ephemeral noise.", 0.8),
        ("page_04_img_02", "Spectral Libraries", "https://www.redalyc.org/pdf/687/68759600010.pdf",
         "Demattê et al. (2018) and Dotto et al. (2018) characterize absorption overtones for clay, organic matter, and moisture; fusing spectral data with terrain/climate improves P and K prediction.", 3.2),
        ("page_04_img_03", "Soil Moisture Effects", "https://doi.org/10.3390/s23041845",
         "Piccoli et al. (2023) show moisture strongly suppresses reflectance, especially in visible and NIR. Requires moisture-aware preprocessing and stratified modeling across soil moisture regimes.", 5.6),
        ("page_04_img_04", "Temporal Compositing", "https://doi.org/10.3390/rs13101952",
         "Recent studies compare median and percentile-based seasonal composites to build cleaner inputs, reducing atmospheric noise and residue while preserving true soil signals.", 8.0),
        ("page_04_img_05", "Validation Methodology", "https://doi.org/10.1016/j.geoderma.2018.01.037",
         "Recent work emphasizes rigorous validation: spatial blocking and independent holdouts to avoid spatial autocorrelation that falsely inflates accuracy in naive random splits.", 10.4)
    ]
    for img_name, title, url, text, left_x in papers_s4:
        add_card(s4, left_x, 1.45, 2.15, 5.5)
        img_p = get_img(img_name)
        if img_p:
            s4.shapes.add_picture(img_p, Inches(left_x + 0.15), Inches(1.6), Inches(1.85), Inches(1.15))

        tb = s4.shapes.add_textbox(Inches(left_x + 0.15), Inches(2.85), Inches(1.85), Inches(3.9))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_TITLE
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_DARK
        p.space_after = Pt(6)

        p2 = tf.add_paragraph()
        p2.text = text
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK
        p2.space_after = Pt(8)

        p_link = tf.add_paragraph()
        run = p_link.add_run()
        run.text = "[🔗 View Paper / DOI]"
        run.font.name = FONT_BODY
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = LINK_BLUE
        run.hyperlink.address = url

    # =========================================================================
    # SLIDE 5: Literature Survey (Part 2 - Machine Learning & Spatial Modeling)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5)
    add_header(s5, "Literature Foundations — Machine Learning & Spatial Modeling", "LITERATURE SURVEY (2/3)")

    grid_s5 = [
        ("Ensemble Models Lead", "https://arxiv.org/abs/2503.22276",
         "Kammerlander et al. (2025) and Vohland et al. (2018) benchmark tree-based ensembles (Random Forest, XGBoost), demonstrating they outperform neural nets on tabular spectral data when properly engineered.",
         0.8, 1.45, "🌲"),
        ("Feature & Validation Strategies", "https://doi.org/10.3389/frsen.2024.1342115",
         "Meta-analyses (Frontiers 2024; MDPI 2021) emphasize feature selection, moisture normalization, PCA/indices, and robust spatial cross-validation to avoid overfitting and inflated metrics.",
         6.8, 1.45, "📋"),
        ("Hyperparameter Tuning", "https://doi.org/10.3390/rs10081236",
         "Strong performance depends on careful tuning of complexity, learning rate, depth, and regularization. Bayesian optimization and nested CV balance accuracy with generalization.",
         0.8, 3.4, "🎛️"),
        ("Class Imbalance in Soil Data", "https://doi.org/10.1109/ACCESS.2021.3083561",
         "Soil datasets overrepresent common ranges while extreme nutrient deficiencies are under-sampled. Prior work supports stratified sampling and focal loss to improve minority-class recall.",
         6.8, 3.4, "⚖️"),
        ("Transfer Learning & Domain Adaptation", "https://doi.org/10.3390/s21186088",
         "When local field data are limited, transfer learning from larger spectral libraries (e.g. LUCAS) improves robustness, adapting across landscapes to reduce local ground truth collection costs.",
         0.8, 5.3, "🧠"),
        ("Uncertainty Quantification", "https://doi.org/10.1016/j.geoderma.2020.114251",
         "For mapping and decision support, point predictions are not enough. Ensemble variance and quantile regression provide uncertainty estimates that expose unreliable predictions.",
         6.8, 5.3, "🎯")
    ]
    for title, url, text, left_x, top_y, icon in grid_s5:
        add_card(s5, left_x, top_y, 5.7, 1.65, "")
        
        # Icon Pill
        icon_box = s5.shapes.add_textbox(Inches(left_x + 0.15), Inches(top_y + 0.14), Inches(0.4), Inches(0.4))
        tf_ic = icon_box.text_frame
        tf_ic.margin_left = tf_ic.margin_top = tf_ic.margin_right = tf_ic.margin_bottom = 0
        p_ic = tf_ic.paragraphs[0]
        p_ic.text = icon
        p_ic.font.size = Pt(14)

        tb = s5.shapes.add_textbox(Inches(left_x + 0.6), Inches(top_y + 0.14), Inches(4.9), Inches(1.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_TITLE
        p_t.font.size = Pt(12)
        p_t.font.bold = True
        p_t.font.color.rgb = PRIMARY_DARK
        p_t.space_after = Pt(3)

        p = tf.add_paragraph()
        p.text = text + " "
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_DARK
        
        run = p.add_run()
        run.text = "[🔗 View Paper]"
        run.font.name = FONT_BODY
        run.font.bold = True
        run.font.color.rgb = LINK_BLUE
        run.hyperlink.address = url

    # =========================================================================
    # SLIDE 6: Literature Survey (Part 3 - Target Variables & Mapping Evidence)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6)
    add_header(s6, "Target Variables & Spatial Mapping Evidence", "LITERATURE SURVEY (3/3)")

    papers_s6 = [
        ("page_06_img_01", "Topsoil Targets", "https://doi.org/10.1080/10106049.2024.2319623",
         "Studies (Charishma et al. 2024; Ng et al. 2019) demonstrate Sentinel-2 band combos and SWIR indices correlate with top 0–20 cm N, SOC, and available P/K when crop residue is masked.", 0.8),
        ("page_06_img_02", "Actionable Tiering", "https://www.ijset.in",
         "Models convert continuous ppm predictions into Low/Medium/High soil-health tiers and enable regionally calibrated fertilizer recommendations (Bhargavi & Anitha 2026; CIGR Journal 2025).", 3.2),
        ("page_06_img_03", "Seasonal Variation", "https://doi.org/10.3390/rs13071312",
         "Soil moisture, residue cover, and crop growth stage shift reflectance. Mapping is stronger when imagery is matched to consistent plowing windows or modeled with seasonal covariates (Wang et al. 2021).", 5.6),
        ("page_06_img_04", "Depth Profiles", "https://doi.org/10.1016/j.geoderma.2019.06.012",
         "Target variables must be defined by sampling depth; nutrient concentration declines with depth. Plowing homogenizes 0–20 cm, while canopy signals reflect deeper root-zone uptake.", 8.0),
        ("page_06_img_05", "Mixed Crop Types", "https://cigrjournal.org",
         "In heterogeneous fields, crop type confounds spectral signatures. Stratifying by crop class, masking crop canopies, or using crop-aware models prevents confusing crop signals with soil variation.", 10.4)
    ]
    for img_name, title, url, text, left_x in papers_s6:
        add_card(s6, left_x, 1.45, 2.15, 5.5)
        img_p = get_img(img_name)
        if img_p:
            s6.shapes.add_picture(img_p, Inches(left_x + 0.15), Inches(1.6), Inches(1.85), Inches(1.15))

        tb = s6.shapes.add_textbox(Inches(left_x + 0.15), Inches(2.85), Inches(1.85), Inches(3.9))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_TITLE
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_DARK
        p.space_after = Pt(6)

        p2 = tf.add_paragraph()
        p2.text = text
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK
        p2.space_after = Pt(8)

        p_link = tf.add_paragraph()
        run = p_link.add_run()
        run.text = "[🔗 View Paper / DOI]"
        run.font.name = FONT_BODY
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = LINK_BLUE
        run.hyperlink.address = url

    # =========================================================================
    # SLIDE 7: Limitations (Exact Petri Dish Photo + Top-Border Numbered Badges)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7)
    add_header(s7, "Known Limitations & Methodological Pitfalls", "EXISTING SYSTEM LIMITATIONS")

    s7_img = get_img("page_07_img_01")
    if s7_img:
        s7.shapes.add_picture(s7_img, Inches(0.8), Inches(1.45), Inches(3.9), Inches(5.5))

    callouts_s7 = [
        ("1", "Wet-Chemical Testing Constraints",
         "Lab tests are time-intensive (2–4 weeks), costly (₹500–₹2,500/sample), spatially sparse (composite samples erase intra-field variability), and destructive/manual."),
        ("2", "Naive Satellite Model Risks",
         "Vegetation cover confounds soil signals; naive assumptions ignore sensor physics (P/K depend on mineral covariance); random splits cause spatial leakage and inflated R²."),
        ("3", "Atmospheric Effects on Satellite Data",
         "Clouds, haze, aerosols, water vapor, and variable illumination can distort reflectance values. Residual atmospheric noise obscures subtle soil differences if uncorrected."),
        ("4", "Calibration Drift Over Time",
         "Sensor aging, platform transitions, and changing acquisition conditions introduce calibration drift that weakens model reliability across seasons and years."),
        ("5", "Weak Transferability Across Regions",
         "Models trained in one agro-ecological zone fail elsewhere because soil mineralogy, texture, and climate differ. Local fine-tuning and spatial stratification are essential.")
    ]
    top_pos = 1.45
    for num, title, text in callouts_s7:
        add_card(s7, 5.0, top_pos, 7.5, 0.98, "")
        
        top_bar = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.0), Inches(top_pos), Inches(7.5), Inches(0.04))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = ACCENT_BROWN
        top_bar.line.fill.background()

        badge = s7.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.55), Inches(top_pos - 0.16), Inches(0.36), Inches(0.36))
        badge.fill.solid()
        badge.fill.fore_color.rgb = PRIMARY_DARK
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = num
        p_b.font.name = FONT_BODY
        p_b.font.size = Pt(11)
        p_b.font.bold = True
        p_b.font.color.rgb = RGBColor(255, 255, 255)
        p_b.alignment = PP_ALIGN.CENTER

        tb = s7.shapes.add_textbox(Inches(5.2), Inches(top_pos + 0.18), Inches(7.1), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = FONT_TITLE
        p1.font.size = Pt(11.5)
        p1.font.bold = True
        p1.font.color.rgb = PRIMARY_DARK
        p1.space_after = Pt(2)
        p2 = tf.add_paragraph()
        p2.text = text
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_DARK
        
        top_pos += 1.12

    # =========================================================================
    # SLIDE 8: Problem Statement (Centered Text Stacked Arrows from PDF)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s8)
    add_header(s8, "Problem Statement & Research Challenges", "PROBLEM STATEMENT")

    tb_top = s8.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.7), Inches(1.75))
    tf_top = tb_top.text_frame
    tf_top.word_wrap = True
    tf_top.margin_left = tf_top.margin_top = tf_top.margin_right = tf_top.margin_bottom = 0

    p = tf_top.paragraphs[0]
    p.text = "Conventional laboratory soil testing is financially inaccessible, slow, and spatially sparse for smallholders, so most farmers make fertilizer decisions with incomplete information. The result is indiscriminate nutrient application, lower yields, avoidable input costs, and long-term soil degradation. Across smallholder farming systems, this challenge affects millions of farmers and has a direct economic impact through wasted fertilizer spend and missed precision nutrient management."
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK
    p.space_after = Pt(8)

    p = tf_top.add_paragraph()
    p.text = "This project asks three core research questions: (1) Can Sentinel-2 imagery be used to reliably estimate topsoil N, P, K, SOC, and pH at field-relevant 10m resolution? (2) Which spectral, spatial, and terrain-related signals are most predictive across highly variable cropping conditions? (3) How can predictions be translated into an automated, cloud-native advisory pipeline that is robust enough for operational use by farmers and agronomists?"
    p.font.name = FONT_BODY
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK

    # Taller Arrows with perfectly centered single-line text (matching Page 8 Gamma PDF)
    chev_data = [
        ("Resolve Depth Paradox", Inches(7.5), Inches(3.3), ACCENT_BROWN,
         "Tillage plow layer & canopy RedEdge proxies"),
        ("Isolate Bare Soil", Inches(8.9), Inches(4.15), ACCENT_TERRA,
         "SCL cloud mask & multi-temporal Barest Earth composite"),
        ("Model Secondary Covariance", Inches(10.4), Inches(5.0), ACCENT_GOLD,
         "P & K binding to iron oxides & clay absorption lattices")
    ]
    for title, width_in, top_y, color, subtitle in chev_data:
        chev = s8.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(0.8), top_y, width_in, Inches(0.74))
        chev.fill.solid()
        chev.fill.fore_color.rgb = color
        chev.line.fill.background()

        tb = s8.shapes.add_textbox(Inches(1.1), Inches(top_y.inches + 0.16), Inches(width_in.inches - 1.0), Inches(0.48))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        run_t = p.add_run()
        run_t.text = title + "  —  "
        run_t.font.name = FONT_TITLE
        run_t.font.size = Pt(11.5)
        run_t.font.bold = True
        run_t.font.color.rgb = RGBColor(255, 255, 255)

        run_s = p.add_run()
        run_s.text = subtitle
        run_s.font.name = FONT_BODY
        run_s.font.size = Pt(9.5)
        run_s.font.color.rgb = RGBColor(245, 245, 245)

    tb_bot = s8.shapes.add_textbox(Inches(0.8), Inches(5.8), Inches(11.7), Inches(1.3))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    tf_bot.margin_left = tf_bot.margin_top = tf_bot.margin_right = tf_bot.margin_bottom = 0
    p = tf_bot.paragraphs[0]
    p.text = "The technical hurdles are substantial: soil properties are not directly visible from space, vegetation cover obscures the signal, and nutrient responses vary by soil type, season, and management history. The model must also handle limited ground truth, eliminate spatial autocorrelation leakage via Spatial GroupKFold, generalize across fields, and produce outputs that are interpretable and actionable rather than just statistically accurate."
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 9: System Architecture & Flow Diagram (Visual Interactive Pipeline)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s9)
    add_header(s9, "System Architecture & End-to-End Pipeline Flow", "SYSTEM DESIGN (1/2)")

    tb_intro = s9.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.7), Inches(0.65))
    tf_i = tb_intro.text_frame
    tf_i.word_wrap = True
    tf_i.margin_left = tf_i.margin_top = tf_i.margin_right = tf_i.margin_bottom = 0
    p = tf_i.paragraphs[0]
    p.text = "The system operates as an end-to-end cloud-native pipeline converting Sentinel-2 imagery into farm-scale agronomic advisory. Streaming only required pixels via STAC API range requests, it enforces multi-temporal bare-soil compositing, extracts 17+ chemometric predictors, and runs spatial multi-target regression."
    p.font.name = FONT_BODY
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_DARK

    pipeline_stages = [
        ("STAGE 1: INGESTION", "Cloud STAC & COG Stream",
         "• Microsoft Planetary Computer STAC\n• Sentinel-2 L2A BOA reflectance\n• HTTP range requests on COGs\n• Sub-second bounding box crop\n• Zero local full-tile storage",
         0.8, ACCENT_BROWN),
        ("STAGE 2: FILTERING", "Bare Soil Compositing",
         "• SCL mask (clouds, shadow, cirrus)\n• Vegetation down-weight (NDVI < 0.25)\n• Bare Soil Index filter (BSI > 0.0)\n• Multi-temporal median composite\n• Ephemeral surface noise cancelled",
         3.8, ACCENT_TERRA),
        ("STAGE 3: MODELING", "Spatial Multi-Target ML",
         "• 10 Science Bands + 7 Indices + DEM\n• Supervised XGBoost & LightGBM\n• Spatial GroupKFold validation\n• Models N, P, K, pH, and SOC\n• Spatial leakage strictly eliminated",
         6.8, ACCENT_GOLD),
        ("STAGE 4: ADVISORY", "10m Heatmaps & Dosage",
         "• Georeferenced 10m nutrient rasters\n• Intra-field management zonation\n• Low / Medium / High Soil Card tiers\n• Precision fertilizer split (Urea, DAP, MOP)\n• Web GIS interactive interface",
         9.8, ACCENT_GREEN)
    ]
    for tag, title, bullets, left_x, color in pipeline_stages:
        add_card(s9, left_x, 2.15, 2.75, 4.8)

        hdr_bar = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_x), Inches(2.15), Inches(2.75), Inches(0.45))
        hdr_bar.fill.solid()
        hdr_bar.fill.fore_color.rgb = color
        hdr_bar.line.fill.background()
        tf_h = hdr_bar.text_frame
        p_h = tf_h.paragraphs[0]
        p_h.text = tag
        p_h.font.name = FONT_BODY
        p_h.font.size = Pt(10)
        p_h.font.bold = True
        p_h.font.color.rgb = RGBColor(255, 255, 255)
        p_h.alignment = PP_ALIGN.CENTER

        tb_sub = s9.shapes.add_textbox(Inches(left_x + 0.15), Inches(2.75), Inches(2.45), Inches(0.55))
        tf_s = tb_sub.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = 0
        p = tf_s.paragraphs[0]
        p.text = title
        p.font.name = FONT_TITLE
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_DARK

        tb_b = s9.shapes.add_textbox(Inches(left_x + 0.15), Inches(3.35), Inches(2.45), Inches(3.4))
        tf_b = tb_b.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0
        p = tf_b.paragraphs[0]
        p.text = bullets
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_DARK

        if left_x < 9.0:
            arrow = s9.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(left_x + 2.82), Inches(4.3), Inches(0.2), Inches(0.3))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = ACCENT_GOLD
            arrow.line.fill.background()

    # =========================================================================
    # SLIDE 10: Preprocessing & Chemometric Feature Engine
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10)
    add_header(s10, "Data Pipeline & Chemometric Feature Engineering", "SYSTEM DESIGN (2/2)")

    stages_s10 = [
        ("STAGE 1: 10 Science Bands Extraction",
         "• B02 (Blue 490nm): Iron oxide baseline\n"
         "• B03 (Green 560nm): Residue separation\n"
         "• B04 (Red 665nm): Soil line baseline\n"
         "• B05, B06, B07 (Red Edge 705-783nm): Nitrogen & Chlorophyll proxy\n"
         "• B08, B8A (NIR 842-865nm): Biomass & Hematite/Goethite\n"
         "• B11 (SWIR-1 1610nm): Organic Carbon & Soil Moisture\n"
         "• B12 (SWIR-2 2190nm): Clay minerals, P, K & Calcite (pH)", 0.8),
        ("STAGE 2: Geochemical Index Engine",
         "• Bare Soil Index (BSI):\n  ((B11+B4)-(B8+B2)) / ((B11+B4)+(B8+B2))\n\n"
         "• Clay Mineral Ratio (CMR):\n  B11 / B12 (Proxy for Clay, P, and K CEC)\n\n"
         "• Ferric Iron Index (FII):\n  B4 / B2 (Phosphate adsorption sites)\n\n"
         "• Carbonate Index (CI):\n  B12 / B11 (Calcite at 2340nm for pH)\n\n"
         "• Red Edge Nitrogen (NDRE):\n  (B8-B5) / (B8+B5) (Canopy RuBisCO N)\n\n"
         "• Soil Brightness Index (SBI):\n  sqrt((B4² + B3² + B8²) / 3)", 4.8),
        ("STAGE 3: ML Model & Validation Suite",
         "• Input Tensor: 10 Bands + 7 Indices + DEM\n\n"
         "• Target Chemical Array:\n  [Available N, Available P, Exch. K, pH, SOC]\n\n"
         "• Regression Algorithms:\n  XGBoost, LightGBM, Random Forest Regressors\n\n"
         "• Spatial Block Cross-Validation:\n  GroupKFold by regional administrative\n  clusters to strictly eliminate spatial leakage\n\n"
         "• Evaluation Metrics:\n  R² (Goodness of fit), RMSE, and RPIQ\n  (Ratio of Performance to InterQuartile distance)", 8.8)
    ]
    for title, text, left_x in stages_s10:
        add_card(s10, left_x, 1.45, 3.7, 5.5, title)
        tb = s10.shapes.add_textbox(Inches(left_x + 0.2), Inches(2.1), Inches(3.3), Inches(4.6))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 11: Objectives, Execution Plan & Expected Outcomes (Gamma Page 10)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s11)
    add_header(s11, "Objectives, Execution Plan & Expected Outcomes", "PROJECT ROADMAP")

    add_card(s11, 0.8, 1.35, 5.7, 1.6, "Objectives")
    tb = s11.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(1.05))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "• Automate STAC/COG ingestion for sub-second farm-level access.\n" \
             "• Isolate bare soil via temporal NDVI/BSI filters and SCL masks.\n" \
             "• Engineer spectral + geo indices; train XGBoost/LightGBM with spatial CV.\n" \
             "• Deliver 10m heatmaps and farmer-friendly Soil Health Card tiers."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_DARK

    add_card(s11, 6.8, 1.35, 5.7, 1.6, "Execution & Outcomes")
    tb = s11.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(1.05))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "• Phase 1 completed: literature survey, STAC access, benchmark datasets, spatial CV framework.\n" \
             "• Upcoming phases: feature extraction, ML benchmarking, raster inference engine, Web GIS advisory.\n" \
             "• Expected outcomes: validated regression suite for N/P/K/pH/SOC, continuous 10m intra-field maps, actionable fertilizer advisory engine."
    p.font.name = FONT_BODY
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_DARK

    phases_s11 = [
        ("Phase 1 — Foundations\nWeeks 1–4 [COMPLETED]",
         "• Literature review & target definition\n• STAC catalog access & COG retrieval\n• Benchmark labels & spatial CV setup", 0.8),
        ("Phase 2 — Feature Pipeline\nWeeks 5–8 [UPCOMING]",
         "• SCL cloud masking & temporal rules\n• Bare-soil compositing (NDVI/BSI)\n• Spectral, mineral, & geo indices", 3.8),
        ("Phase 3 — ML Benchmarking\nWeeks 9–12 [UPCOMING]",
         "• Train XGBoost & LightGBM for NPK\n• Spatial GroupKFold generalization\n• Feature importance & error slicing", 6.8),
        ("Phase 4 — Inference & GIS\nWeeks 13–16 [UPCOMING]",
         "• Raster inference engine (10m surfaces)\n• Zonation maps & fertilizer dosage\n• Web GIS integration & farmer review", 9.8)
    ]
    for title, text, left_x in phases_s11:
        add_card(s11, left_x, 3.1, 2.75, 2.1, title)
        tb = s11.shapes.add_textbox(Inches(left_x + 0.15), Inches(3.8), Inches(2.45), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_DARK

    footer_cols = [
        ("01 Validation approach", "Validate data quality first, then accuracy, then advisory usefulness via spatial CV & holdouts.", 0.8),
        ("02 KPIs", "Ingestion latency (<2s), cloud-free compositing rate, cross-validated R² by nutrient, inference throughput.", 3.8),
        ("03 Team responsibilities", "Remote sensing lead (imagery), ML lead (models), GIS engineer (pipelines), Agronomist (advisory).", 6.8),
        ("04 Resource requirements", "Cloud object storage, compute for training, geospatial libraries (Rasterio), reference soil samples.", 9.8)
    ]
    for num_title, text, left_x in footer_cols:
        tb = s11.shapes.add_textbox(Inches(left_x), Inches(5.45), Inches(2.75), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = num_title
        p.font.name = FONT_BODY
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_GOLD
        p.space_after = Pt(2)
        p2 = tf.add_paragraph()
        p2.text = text
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9)
        p2.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 12: Applications & Practical Relevance
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s12)
    add_header(s12, "Applications & Practical Relevance", "APPLICATIONS & IMPACT")

    apps = [
        ("Precision Agriculture & Variable Rate Application (VRA)",
         "Enables modern tractor sprayers and drone spreaders to apply differential fertilizer dosages across high-deficiency and high-fertility zones within the same parcel, reducing input costs by up to 25%."),
        ("Accessible Digital Soil Health Cards for Smallholders",
         "Provides instantaneous, free soil condition assessments for smallholder farmers who lack physical access to government soil testing laboratories or cannot afford private testing fees."),
        ("Environmental Protection & Groundwater Safeguards",
         "Prevents indiscriminate nitrogen broadcasting, directly mitigating nitrate leaching into rural groundwater aquifers, soil acidification, and agricultural runoff eutrophication."),
        ("Carbon Sequestration & Regeneration Monitoring",
         "Equips agrarian NGOs, carbon credit verifiers, and agricultural departments to monitor field-scale Soil Organic Carbon (SOC) regeneration over multi-year regenerative farming initiatives."),
        ("Micro-Finance & Agricultural Crop Insurance",
         "Supplies rural lending institutions and insurance underwriters with verified, objective land fertility benchmarks to assess farm productivity potential and risk prior to loan disbursement.")
    ]
    top_pos = 1.45
    for title, desc in apps:
        add_card(s12, 0.8, top_pos, 11.7, 0.98, "", left_bar_color=ACCENT_GREEN)
        tb = s12.shapes.add_textbox(Inches(1.1), Inches(top_pos + 0.1), Inches(11.2), Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = FONT_TITLE
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = PRIMARY_DARK
        p1.space_after = Pt(2)
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10)
        p2.font.color.rgb = TEXT_DARK
        top_pos += 1.1

    # =========================================================================
    # SLIDE 13: Hardware & Software Requirements
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s13)
    add_header(s13, "Hardware & Software Requirements", "REQUIREMENTS & SPECIFICATIONS")

    add_card(s13, 0.8, 1.45, 5.7, 5.5, "Hardware Specifications")
    tb = s13.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.2), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    hw_specs = [
        ("Processor:", "Multi-core Intel Core i5/i7 (11th Gen+) or AMD Ryzen 5/7 for parallel geospatial raster window clipping."),
        ("Memory (RAM):", "Minimum 16 GB DDR4/DDR5 RAM to handle multi-band satellite raster stacking in memory."),
        ("GPU Acceleration:", "NVIDIA GTX/RTX GPU (or Google Colab / Kaggle Cloud T4/V100 GPU) for accelerated model cross-validation."),
        ("Storage:", "50 GB High-Speed NVMe SSD for local dataset caching and preprocessed training tables."),
        ("Network:", "High-speed broadband connection (>20 Mbps) for streaming Cloud-Optimized GeoTIFFs via STAC API.")
    ]
    for i, (label, text) in enumerate(hw_specs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run_l = p.add_run()
        run_l.text = f"💻 {label} "
        run_l.font.name = FONT_BODY
        run_l.font.bold = True
        run_l.font.size = Pt(11)
        run_l.font.color.rgb = PRIMARY_DARK
        run_t = p.add_run()
        run_t.text = text
        run_t.font.name = FONT_BODY
        run_t.font.size = Pt(10.5)
        run_t.font.color.rgb = TEXT_DARK
        p.space_after = Pt(12)

    add_card(s13, 6.8, 1.45, 5.7, 5.5, "Software & Development Stack")
    tb = s13.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    sw_specs = [
        ("Programming Language:", "Python 3.10 / 3.11 with virtual environment encapsulation."),
        ("Cloud Earth APIs:", "Microsoft Planetary Computer STAC API (`pystac-client`, `planetary-computer`)."),
        ("Geospatial Stack:", "`rasterio`, `rioxarray`, `geopandas`, `shapely` for coordinate reprojection and COG windowing."),
        ("Machine Learning Suite:", "`scikit-learn`, `xgboost`, `lightgbm` for regression modeling and spatial cross-validation."),
        ("Visualization & Web GIS:", "`matplotlib`, `seaborn`, `folium` / `leaflet` for interactive intra-field heatmap rendering.")
    ]
    for i, (label, text) in enumerate(sw_specs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run_l = p.add_run()
        run_l.text = f"⚙️ {label} "
        run_l.font.name = FONT_BODY
        run_l.font.bold = True
        run_l.font.size = Pt(11)
        run_l.font.color.rgb = PRIMARY_DARK
        run_t = p.add_run()
        run_t.text = text
        run_t.font.name = FONT_BODY
        run_t.font.size = Pt(10.5)
        run_t.font.color.rgb = TEXT_DARK
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 14: Conclusion & Phase 2 Deliverables
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s14)
    add_header(s14, "Conclusion & Expected Outcomes", "CONCLUSION & DELIVERABLES")

    add_card(s14, 0.8, 1.45, 5.7, 5.5, "Key Takeaways from Phase 1")
    tb = s14.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.2), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    concl_takeaways = [
        ("Scientific Feasibility Proven:", "Verified the physical and spectral mechanisms linking Sentinel-2 VNIR/SWIR reflectance to soil organic carbon, clay minerals, and indirect NPK covariance."),
        ("Zero-Waste Cloud Architecture:", "Successfully implemented and verified Cloud-Optimized GeoTIFF streaming via STAC API, fetching farm-level data in 1.3 seconds without full-tile downloads."),
        ("Defensible Validation Strategy:", "Overcame spatial autocorrelation hazards by formulating Spatial Block Cross-Validation, ensuring models generalize to unseen farms."),
        ("Team Specialization:", "Distinct role allocation across Data Engineering, ML Modeling, Chemistry Targets, and GIS Mapping guarantees rapid Phase 2 execution.")
    ]
    for i, (label, text) in enumerate(concl_takeaways):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run_l = p.add_run()
        run_l.text = f"✔ {label} "
        run_l.font.name = FONT_BODY
        run_l.font.bold = True
        run_l.font.size = Pt(11)
        run_l.font.color.rgb = PRIMARY_DARK
        run_t = p.add_run()
        run_t.text = text
        run_t.font.name = FONT_BODY
        run_t.font.size = Pt(10.5)
        run_t.font.color.rgb = TEXT_DARK
        p.space_after = Pt(12)

    add_card(s14, 6.8, 1.45, 5.7, 5.5, "Expected Outcomes of Phase 2")
    tb = s14.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    concl_outcomes = [
        ("Trained AI Regression Suite:", "Validated machine learning regressors predicting Nitrogen, Available Phosphorus, Exchangeable Potassium, pH, and SOC."),
        ("Continuous 2D Nutrient Heatmaps:", "High-resolution (10m) intra-field fertility maps showing exact management zones within farm boundaries."),
        ("Actionable Advisory Engine:", "Direct translation of chemical values into customized fertilizer dosage plans (Urea, DAP, MOP)."),
        ("Empowerment of Smallholders:", "Democratizing soil health assessment by eliminating laboratory turnaround delays and testing expenses.")
    ]
    for i, (label, text) in enumerate(concl_outcomes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run_l = p.add_run()
        run_l.text = f"🚀 {label} "
        run_l.font.name = FONT_BODY
        run_l.font.bold = True
        run_l.font.size = Pt(11)
        run_l.font.color.rgb = PRIMARY_DARK
        run_t = p.add_run()
        run_t.text = text
        run_t.font.name = FONT_BODY
        run_t.font.size = Pt(10.5)
        run_t.font.color.rgb = TEXT_DARK
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 15: References (Curated 2-Column Grid with Active Clickable Buttons)
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s15)
    add_header(s15, "References (Journals & Conferences with Direct Access)", "REFERENCES & CITATIONS")

    refs_list = [
        ("[1] Castaldi, F. et al. (2019). Sentinel-2 for soil organic carbon & texture.", "Remote Sens. Environ.", "https://doi.org/10.1016/j.rse.2019.01.011"),
        ("[2] Gholizadeh, A. et al. (2021). Multi-Temporal Series to Estimate Topsoil.", "MDPI Remote Sensing", "https://doi.org/10.3390/rs13101952"),
        ("[3] Piccoli, I. et al. (2023). Soil characteristics from Sentinel-3 & DEM.", "MDPI Sensors", "https://doi.org/10.3390/s23041845"),
        ("[4] Demattê, J. A. M. et al. (2018). Soil spectral library & classification.", "Revista Ciência Agron.", "https://www.redalyc.org/pdf/687/68759600010.pdf"),
        ("[5] Kammerlander, C. et al. (2025). ML models for soil parameter prediction.", "arXiv:2503.22276", "https://arxiv.org/abs/2503.22276"),
        ("[6] Vohland, M. et al. (2018). Mapping soil properties with Sentinel-2.", "MDPI Remote Sensing", "https://doi.org/10.3390/rs10081236"),
        ("[7] Frontiers in Remote Sensing (2024). Prediction of soil texture review.", "Frontiers in RS", "https://doi.org/10.3389/frsen.2024.1342115"),
        ("[8] Dotto, A. C. et al. (2018). Predicting soil properties using ML & spectra.", "Geoderma", "https://doi.org/10.1016/j.geoderma.2018.01.037"),
        ("[9] Charishma, K. et al. (2024). Top soil properties by Sentinel-2 imaging.", "Taylor & Francis", "https://doi.org/10.1080/10106049.2024.2319623"),
        ("[10] Ng, W. et al. (2019). Utility of Sentinel-2 spectral data for SOC.", "Geoderma", "https://doi.org/10.1016/j.geoderma.2019.06.012"),
        ("[11] Bhargavi, P. & Anitha, S. (2026). Soil nutrient prediction using data mining.", "IJSET", "https://www.ijset.in"),
        ("[12] CIGR Journal (2025). Sensor framework for soil nutrients using DL.", "CIGR Journal", "https://cigrjournal.org"),
        ("[13] Taghizadeh-Mehrjardi, R. et al. (2020). Digital mapping of SOC using RS.", "Geoderma", "https://doi.org/10.1016/j.geoderma.2020.114251"),
        ("[14] IEEE Access (2021). Estimating SOM Content Using Sentinel-2.", "IEEE Access", "https://doi.org/10.1109/ACCESS.2021.3083561"),
        ("[15] Wang, J. et al. (2021). Soil salinity and nutrient mapping via Sentinel-2.", "MDPI Remote Sensing", "https://doi.org/10.3390/rs13071312")
    ]

    for idx, (cite, journal, url) in enumerate(refs_list):
        col = 0 if idx < 8 else 1
        row = idx if col == 0 else idx - 8
        left_x = 0.8 if col == 0 else 6.8
        top_y = 1.45 + (row * 0.68)

        add_card(s15, left_x, top_y, 5.7, 0.62)

        tb = s15.shapes.add_textbox(Inches(left_x + 0.15), Inches(top_y + 0.08), Inches(4.3), Inches(0.48))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = cite
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_DARK

        p_j = tf.add_paragraph()
        p_j.text = f"Published in: {journal}"
        p_j.font.name = FONT_BODY
        p_j.font.size = Pt(8.5)
        p_j.font.color.rgb = TEXT_MUTED

        btn = s15.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left_x + 4.55), Inches(top_y + 0.12), Inches(1.0), Inches(0.36))
        btn.fill.solid()
        btn.fill.fore_color.rgb = RGBColor(235, 243, 252)
        btn.line.color.rgb = LINK_BLUE
        btn.line.width = Pt(1.0)
        tf_btn = btn.text_frame
        p_btn = tf_btn.paragraphs[0]
        run_btn = p_btn.add_run()
        run_btn.text = "🔗 Access"
        run_btn.font.name = FONT_BODY
        run_btn.font.size = Pt(9)
        run_btn.font.bold = True
        run_btn.font.color.rgb = LINK_BLUE
        run_btn.hyperlink.address = url
        p_btn.alignment = PP_ALIGN.CENTER

    output_path = r"c:\Users\kisha\OneDrive\Desktop\agri\Phase_1_Gamma_Interactive_Presentation.pptx"
    prs.save(output_path)
    print(f"Interactive presentation matching Gamma PDF successfully saved to: {output_path}")

if __name__ == "__main__":
    build_presentation()
