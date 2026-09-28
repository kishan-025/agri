package com.agri.soil.controller;

import com.agri.soil.dto.CreateFarmRequest;
import com.agri.soil.dto.FarmResponse;
import com.agri.soil.entity.Farm;
import com.agri.soil.service.FarmService;
import com.agri.soil.service.PythonClientService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/farms")
@CrossOrigin(origins = "*") // Allows Streamlit on port 8501
public class FarmController {

    private final FarmService farmService;
    private final PythonClientService pythonClientService;

    public FarmController(FarmService farmService, PythonClientService pythonClientService) {
        this.farmService = farmService;
        this.pythonClientService = pythonClientService;
    }

    @GetMapping
    public ResponseEntity<List<FarmResponse>> getFarms(@RequestParam Long farmerId) {
        return ResponseEntity.ok(farmService.getFarmsByFarmer(farmerId));
    }

    @PostMapping
    public ResponseEntity<?> createFarm(@RequestBody CreateFarmRequest request) {
        try {
            FarmResponse response = farmService.createFarm(request);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Failed to save farm: " + e.getMessage()));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteFarm(@PathVariable Long id) {
        try {
            farmService.deleteFarm(id);
            return ResponseEntity.ok(Map.of("message", "Farm deleted successfully."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Failed to delete farm: " + e.getMessage()));
        }
    }

    @PostMapping("/{id}/fertility-check")
    public ResponseEntity<?> runFertilityCheck(@PathVariable Long id) {
        try {
            Farm farm = farmService.getFarmEntity(id);
            Map<String, Object> result = pythonClientService.executeFertilityCheck(farm);
            return ResponseEntity.ok(result);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Fertility check error: " + e.getMessage()));
        }
    }
}
