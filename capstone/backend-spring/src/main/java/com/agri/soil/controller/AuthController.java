package com.agri.soil.controller;

import com.agri.soil.dto.FarmerResponse;
import com.agri.soil.dto.GoogleAuthRequest;
import com.agri.soil.entity.Farmer;
import com.agri.soil.service.GoogleAuthService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*") // Allows Streamlit on port 8501
public class AuthController {

    private final GoogleAuthService googleAuthService;

    public AuthController(GoogleAuthService googleAuthService) {
        this.googleAuthService = googleAuthService;
    }

    @PostMapping("/google")
    public ResponseEntity<?> authenticateGoogle(@RequestBody GoogleAuthRequest request) {
        try {
            if (request.getIdToken() == null || request.getIdToken().trim().isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of("error", "idToken is required."));
            }

            Farmer farmer = googleAuthService.verifyAndAuthenticate(request.getIdToken());
            FarmerResponse response = FarmerResponse.builder()
                    .id(farmer.getId())
                    .googleId(farmer.getGoogleId())
                    .email(farmer.getEmail())
                    .fullName(farmer.getFullName())
                    .pictureUrl(farmer.getPictureUrl())
                    .build();

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication failed: " + e.getMessage()));
        }
    }
}
