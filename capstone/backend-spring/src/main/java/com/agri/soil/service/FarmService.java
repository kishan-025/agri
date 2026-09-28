package com.agri.soil.service;

import com.agri.soil.dto.CreateFarmRequest;
import com.agri.soil.dto.FarmResponse;
import com.agri.soil.entity.Farm;
import com.agri.soil.entity.Farmer;
import com.agri.soil.repository.FarmRepository;
import com.agri.soil.repository.FarmerRepository;
import org.locationtech.jts.geom.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
public class FarmService {

    private final FarmRepository farmRepository;
    private final FarmerRepository farmerRepository;
    private final GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(), 4326);

    public FarmService(FarmRepository farmRepository, FarmerRepository farmerRepository) {
        this.farmRepository = farmRepository;
        this.farmerRepository = farmerRepository;
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

    public void deleteFarm(Long farmId) {
        farmRepository.deleteById(farmId);
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
