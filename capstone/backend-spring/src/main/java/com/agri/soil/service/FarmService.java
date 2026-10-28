package com.agri.soil.service;

import com.agri.soil.dto.CreateFarmRequest;
import com.agri.soil.dto.FarmResponse;
import com.agri.soil.entity.Farm;
import com.agri.soil.entity.Farmer;
import com.agri.soil.repository.FarmRepository;
import com.agri.soil.repository.FarmerRepository;
import com.agri.soil.repository.FertilityAssessmentRepository;
import org.locationtech.jts.geom.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
public class FarmService {

    private final FarmRepository farmRepository;
    private final FarmerRepository farmerRepository;
    private final FertilityAssessmentRepository assessmentRepository;
    private final GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(), 4326);

    public FarmService(FarmRepository farmRepository, 
                       FarmerRepository farmerRepository,
                       FertilityAssessmentRepository assessmentRepository) {
        this.farmRepository = farmRepository;
        this.farmerRepository = farmerRepository;
        this.assessmentRepository = assessmentRepository;
    }

    @Transactional
    public FarmResponse createFarm(CreateFarmRequest request) {
        if (request.getCorners() == null || request.getCorners().size() != 4) {
            throw new IllegalArgumentException("A farm requires exactly 4 corner coordinates [[lon, lat], ...].");
        }

        Farmer farmer = farmerRepository.findById(request.getFarmerId())
                .orElseThrow(() -> new IllegalArgumentException("Farmer with ID " + request.getFarmerId() + " not found."));

        // Build JTS Polygon from 4 coordinates (closed with 5 points)
        List<List<Double>> corners = request.getCorners();
        Coordinate[] coordinates = new Coordinate[5];
        for (int i = 0; i < 4; i++) {
            double lon = corners.get(i).get(0);
            double lat = corners.get(i).get(1);
            coordinates[i] = new Coordinate(lon, lat);
        }
        coordinates[4] = coordinates[0]; // Close the ring

        LinearRing shell = geometryFactory.createLinearRing(coordinates);
        Polygon boundary = geometryFactory.createPolygon(shell);
        boundary.setSRID(4326);

        Envelope envelope = boundary.getEnvelopeInternal();
        Point centroid = boundary.getCentroid();

        Farm farm = Farm.builder()
                .farmer(farmer)
                .farmName(request.getFarmName())
                .boundary(boundary)
                .centroidLat(centroid.getY())
                .centroidLon(centroid.getX())
                .minLon(envelope.getMinX())
                .minLat(envelope.getMinY())
                .maxLon(envelope.getMaxX())
                .maxLat(envelope.getMaxY())
                .build();

        farm = farmRepository.save(farm);

        // Compute geodesic area in acres via PostGIS ST_Area
        try {
            Double acres = farmRepository.calculateAreaInAcres(farm.getId());
            if (acres != null) {
                farm.setAreaAcres(Math.round(acres * 100.0) / 100.0);
                farm = farmRepository.save(farm);
            }
        } catch (Exception e) {
            // Fallback estimation if running without PostGIS active
            farm.setAreaAcres(1.0);
        }

        return mapToResponse(farm);
    }

    public List<FarmResponse> getFarmsByFarmer(Long farmerId) {
        return farmRepository.findByFarmerId(farmerId).stream()
                .map(this::mapToResponse)
                .toList();
    }

    public Farm getFarmEntity(Long farmId) {
        return farmRepository.findById(farmId)
                .orElseThrow(() -> new IllegalArgumentException("Farm with ID " + farmId + " not found."));
    }

    @Transactional
    public void deleteFarm(Long farmId) {
        assessmentRepository.deleteByFarmId(farmId);
        farmRepository.deleteById(farmId);
    }

    public java.util.Map<String, Object> getSoilTrends(Long farmId) {
        List<com.agri.soil.entity.FertilityAssessment> list = assessmentRepository.findByFarmIdOrderByCreatedAtDesc(farmId);
        java.util.Map<String, Object> result = new java.util.HashMap<>();
        result.put("farm_id", farmId);

        if (list.isEmpty()) {
            result.put("has_history", false);
            result.put("total_scans", 0);
            result.put("history", java.util.Collections.emptyList());
            result.put("summary", "No historical assessments found. Run a nutrient check to start tracking trends.");
            return result;
        }

        result.put("has_history", true);
        result.put("total_scans", list.size());

        List<java.util.Map<String, Object>> history = new ArrayList<>();
        for (com.agri.soil.entity.FertilityAssessment fa : list) {
            java.util.Map<String, Object> item = new java.util.HashMap<>();
            item.put("assessment_id", fa.getId());
            item.put("satellite_date", fa.getSatelliteDate());
            item.put("created_at", fa.getCreatedAt() != null ? fa.getCreatedAt().toString() : null);
            item.put("pH", fa.getMeanPh());
            item.put("Nitrogen", fa.getMeanN());
            item.put("Phosphorus", fa.getMeanP());
            item.put("Potassium", fa.getMeanK());
            item.put("soil_health_index", fa.getSoilHealthIndex());
            item.put("condition_tier", fa.getConditionTier());
            item.put("rainfall_mm", fa.getRainfallMm());
            item.put("soil_moisture", fa.getSoilMoisture());
            item.put("recommended_crop", fa.getRecommendedCrop());
            item.put("crop_match_pct", fa.getCropMatchPct());
            history.add(item);
        }
        result.put("history", history);

        // Compute deltas if at least 2 scans exist
        if (list.size() >= 2) {
            com.agri.soil.entity.FertilityAssessment curr = list.get(0);
            com.agri.soil.entity.FertilityAssessment prev = list.get(1);

            double dPh = round2((curr.getMeanPh() != null ? curr.getMeanPh() : 0.0) - (prev.getMeanPh() != null ? prev.getMeanPh() : 0.0));
            double dN = round2((curr.getMeanN() != null ? curr.getMeanN() : 0.0) - (prev.getMeanN() != null ? prev.getMeanN() : 0.0));
            double dP = round2((curr.getMeanP() != null ? curr.getMeanP() : 0.0) - (prev.getMeanP() != null ? prev.getMeanP() : 0.0));
            double dK = round2((curr.getMeanK() != null ? curr.getMeanK() : 0.0) - (prev.getMeanK() != null ? prev.getMeanK() : 0.0));

            java.util.Map<String, Object> deltas = new java.util.HashMap<>();
            deltas.put("delta_pH", dPh);
            deltas.put("trend_pH", Math.abs(dPh) < 0.2 ? "STABLE" : (dPh > 0 ? "ALKALINIZING" : "ACIDIFYING"));

            deltas.put("delta_N", dN);
            deltas.put("trend_N", Math.abs(dN) < 0.3 ? "STABLE" : (dN > 0 ? "ACCUMULATING" : "DEPLETING"));

            deltas.put("delta_P", dP);
            deltas.put("trend_P", Math.abs(dP) < 3.0 ? "STABLE" : (dP > 0 ? "ACCUMULATING" : "DEPLETING"));

            deltas.put("delta_K", dK);
            deltas.put("trend_K", Math.abs(dK) < 10.0 ? "STABLE" : (dK > 0 ? "ACCUMULATING" : "DEPLETING"));

            if (curr.getSoilHealthIndex() != null && prev.getSoilHealthIndex() != null) {
                double dShi = round2(curr.getSoilHealthIndex() - prev.getSoilHealthIndex());
                deltas.put("delta_SHI", dShi);
                deltas.put("trend_SHI", Math.abs(dShi) < 2.0 ? "STABLE" : (dShi > 0 ? "IMPROVING" : "DECLINING"));
            }

            result.put("trends", deltas);
        } else {
            result.put("trends", java.util.Collections.emptyMap());
        }

        return result;
    }

    private double round2(double val) {
        return Math.round(val * 100.0) / 100.0;
    }

    private FarmResponse mapToResponse(Farm farm) {
        List<List<Double>> corners = new ArrayList<>();
        if (farm.getBoundary() != null) {
            Coordinate[] coords = farm.getBoundary().getCoordinates();
            for (int i = 0; i < Math.min(4, coords.length); i++) {
                corners.add(List.of(coords[i].x, coords[i].y));
            }
        }

        String geoJson = null;
        try {
            geoJson = farmRepository.getBoundaryAsGeoJson(farm.getId());
        } catch (Exception ignored) {}

        return FarmResponse.builder()
                .id(farm.getId())
                .farmerId(farm.getFarmer().getId())
                .farmName(farm.getFarmName())
                .areaAcres(farm.getAreaAcres())
                .centroidLat(farm.getCentroidLat())
                .centroidLon(farm.getCentroidLon())
                .minLon(farm.getMinLon())
                .minLat(farm.getMinLat())
                .maxLon(farm.getMaxLon())
                .maxLat(farm.getMaxLat())
                .corners(corners)
                .geoJson(geoJson)
                .build();
    }
}
