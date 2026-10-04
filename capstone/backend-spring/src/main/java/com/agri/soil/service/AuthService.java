package com.agri.soil.service;

import com.agri.soil.dto.FarmerResponse;
import com.agri.soil.dto.LoginRequest;
import com.agri.soil.dto.RegisterRequest;
import com.agri.soil.entity.Farmer;
import com.agri.soil.repository.FarmerRepository;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

@Service
public class AuthService {

    private final FarmerRepository farmerRepository;

    public AuthService(FarmerRepository farmerRepository) {
        this.farmerRepository = farmerRepository;
    }

    /**
     * Compute SHA-256 Hex Hash for password storage and verification
     */
    public static String hashPassword(String password) {
        if (password == null || password.trim().isEmpty()) {
            throw new IllegalArgumentException("Password cannot be blank.");
        }
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(password.trim().getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }

    /**
     * Authenticate farmer using username & password
     */
    public FarmerResponse login(LoginRequest request) {
        if (request.getUsername() == null || request.getUsername().trim().isEmpty()) {
            throw new IllegalArgumentException("Username is required.");
        }
        if (request.getPassword() == null || request.getPassword().trim().isEmpty()) {
            throw new IllegalArgumentException("Password is required.");
        }

        String username = request.getUsername().trim();
        String hashedPassword = hashPassword(request.getPassword().trim());

        Farmer farmer = farmerRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("Invalid username or password."));

        if (!hashedPassword.equals(farmer.getPassword())) {
            throw new IllegalArgumentException("Invalid username or password.");
        }

        return toResponse(farmer);
    }

    /**
     * Register a new farmer account with username & password
     */
    public FarmerResponse register(RegisterRequest request) {
        if (request.getUsername() == null || request.getUsername().trim().isEmpty()) {
            throw new IllegalArgumentException("Username is required.");
        }
        if (request.getPassword() == null || request.getPassword().trim().isEmpty()) {
            throw new IllegalArgumentException("Password is required.");
        }

        String username = request.getUsername().trim();
        if (username.length() < 3) {
            throw new IllegalArgumentException("Username must be at least 3 characters.");
        }

        if (farmerRepository.existsByUsername(username)) {
            throw new IllegalArgumentException("Username '" + username + "' is already registered. Please choose another username or sign in.");
        }

        String fullName = (request.getFullName() != null && !request.getFullName().trim().isEmpty())
                ? request.getFullName().trim()
                : username;
        String email = (request.getEmail() != null && !request.getEmail().trim().isEmpty())
                ? request.getEmail().trim()
                : username + "@agrisoil.org";

        Farmer farmer = Farmer.builder()
                .username(username)
                .password(hashPassword(request.getPassword().trim()))
                .fullName(fullName)
                .email(email)
                .pictureUrl("https://ui-avatars.com/api/?name=" + fullName.replace(" ", "+") + "&background=10b981&color=fff")
                .build();

        Farmer saved = farmerRepository.save(farmer);
        return toResponse(saved);
    }

    public FarmerResponse toResponse(Farmer farmer) {
        return FarmerResponse.builder()
                .id(farmer.getId())
                .username(farmer.getUsername())
                .fullName(farmer.getFullName())
                .email(farmer.getEmail())
                .pictureUrl(farmer.getPictureUrl())
                .build();
    }
}
