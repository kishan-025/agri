-- ==============================================================================
-- CAPSTONE DATABASE INITIALIZATION SCRIPT FOR AIVEN CLOUD POSTGRESQL (POSTGIS)
-- Project: Precision Soil Nutrient Diagnosis via Sentinel-2 & XGBoost
-- Run this in the Aiven Cloud Console -> 'Query' tab or via psql / pgAdmin / DBeaver
-- ==============================================================================

-- 1. Enable PostGIS Extension (Cloud-hosted geospatial engine)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify PostGIS Version
SELECT PostGIS_Full_Version();

-- 2. Create Farmer Account Table (Strictly Farmer Role - Google OAuth)
CREATE TABLE IF NOT EXISTS farmers (
    id BIGSERIAL PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    picture_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Farms Table with PostGIS Polygon Boundary
-- Stores exact 4-corner quadrilateral boundary in WGS84 coordinate system (SRID 4326)
CREATE TABLE IF NOT EXISTS farms (
    id BIGSERIAL PRIMARY KEY,
    farmer_id BIGINT NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
    farm_name VARCHAR(255) NOT NULL,
    boundary GEOMETRY(Polygon, 4326) NOT NULL,
    area_acres DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial Index (R-Tree / GiST) for lightning-fast spatial queries
CREATE INDEX IF NOT EXISTS idx_farms_boundary_gist ON farms USING GIST(boundary);

-- 4. Create Fertility Assessments Table (Assessment History & Heatmaps)
CREATE TABLE IF NOT EXISTS fertility_assessments (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    satellite_date VARCHAR(50),
    cloud_cover_pct DOUBLE PRECISION,
    mean_ph DOUBLE PRECISION,
    min_ph DOUBLE PRECISION,
    max_ph DOUBLE PRECISION,
    mean_n DOUBLE PRECISION,
    min_n DOUBLE PRECISION,
    max_n DOUBLE PRECISION,
    mean_p DOUBLE PRECISION,
    min_p DOUBLE PRECISION,
    max_p DOUBLE PRECISION,
    mean_k DOUBLE PRECISION,
    min_k DOUBLE PRECISION,
    max_k DOUBLE PRECISION,
    heatmap_json TEXT,
    assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fertility_assessments_farm_id ON fertility_assessments(farm_id);
