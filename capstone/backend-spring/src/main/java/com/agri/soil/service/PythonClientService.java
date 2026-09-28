package com.agri.soil.service;

import com.agri.soil.entity.Farm;
import com.agri.soil.entity.FertilityAssessment;
import com.agri.soil.repository.FertilityAssessmentRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.locationtech.jts.geom.Coordinate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.*;

@Service
public class PythonClientService {

    private final WebClient webClient;
    private final FertilityAssessmentRepository assessmentRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final String pythonServiceUrl;

    public PythonClientService(WebClient webClient, 
                               FertilityAssessmentRepository assessmentRepository,
                               @Value("${python.ai.service.url:http://localhost:7000}") String pythonServiceUrl) {
        this.webClient = webClient;
        this.assessmentRepository = assessmentRepository;
        this.pythonServiceUrl = pythonServiceUrl;
    }

    @Transactional
    public Map<String, Object> executeFertilityCheck(Farm farm) {
        // Extract 4 corners in [lon, lat] order
        List<List<Double>> corners = new ArrayList<>();
        Coordinate[] coords = farm.getBoundary().getCoordinates();
        for (int i = 0; i < Math.min(4, coords.length); i++) {
            corners.add(List.of(coords[i].x, coords[i].y));
        }

        Map<String, Object> requestBody = Map.of(
                "farm_id", farm.getId(),
                "farm_name", farm.getFarmName(),
                "corners", corners
        );

        // Call Python AI Satellite Microservice on Port 7000
        Map<String, Object> pythonResponse = webClient.post()
                .uri(pythonServiceUrl + "/api/fertility-check")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Map.class)
                .block();

        if (pythonResponse == null || !"SUCCESS".equals(pythonResponse.get("status"))) {
            throw new RuntimeException("Python AI microservice failed to process the farm.");
        }

        String satelliteDate = (String) pythonResponse.get("satellite_date");
        Number cloudCover = (Number) pythonResponse.get("cloud_cover_pct");
        Map<String, Map<String, Object>> metrics = (Map<String, Map<String, Object>>) pythonResponse.get("metrics");

        // Parse metrics for saving
        double meanPh = ((Number) metrics.get("pH").get("mean")).doubleValue();
        double minPh = ((Number) metrics.get("pH").get("min")).doubleValue();
        double maxPh = ((Number) metrics.get("pH").get("max")).doubleValue();

        double meanN = ((Number) metrics.get("Nitrogen").get("mean")).doubleValue();
        double minN = ((Number) metrics.get("Nitrogen").get("min")).doubleValue();
        double maxN = ((Number) metrics.get("Nitrogen").get("max")).doubleValue();

        double meanP = ((Number) metrics.get("Phosphorus").get("mean")).doubleValue();
        double minP = ((Number) metrics.get("Phosphorus").get("min")).doubleValue();
        double maxP = ((Number) metrics.get("Phosphorus").get("max")).doubleValue();

        double meanK = ((Number) metrics.get("Potassium").get("mean")).doubleValue();
        double minK = ((Number) metrics.get("Potassium").get("min")).doubleValue();
        double maxK = ((Number) metrics.get("Potassium").get("max")).doubleValue();

        String heatmapsJsonString = "";
        try {
            heatmapsJsonString = objectMapper.writeValueAsString(pythonResponse.get("heatmaps"));
        } catch (Exception ignored) {}

        // Persist to Aiven Cloud PostgreSQL
        FertilityAssessment assessment = FertilityAssessment.builder()
                .farm(farm)
                .satelliteDate(satelliteDate)
                .cloudCoverPct(cloudCover != null ? cloudCover.doubleValue() : 0.0)
                .meanPh(meanPh).minPh(minPh).maxPh(maxPh)
                .meanN(meanN).minN(minN).maxN(maxN)
                .meanP(meanP).minP(minP).maxP(maxP)
                .meanK(meanK).minK(minK).maxK(maxK)
                .heatmapJson(heatmapsJsonString)
                .build();

        assessment = assessmentRepository.save(assessment);

        pythonResponse.put("assessment_id", assessment.getId());
        return pythonResponse;
    }
}
