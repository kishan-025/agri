package com.agri.soil.service;

import com.agri.soil.entity.Farmer;
import com.agri.soil.repository.FarmerRepository;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdToken;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdTokenVerifier;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.gson.GsonFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.Optional;

@Service
public class GoogleAuthService {

    private final FarmerRepository farmerRepository;
    private final String clientId;

    public GoogleAuthService(FarmerRepository farmerRepository, 
                             @Value("${google.client.id}") String clientId) {
        this.farmerRepository = farmerRepository;
        this.clientId = clientId;
    }

    public Farmer verifyAndAuthenticate(String idTokenString) throws Exception {
        // If developer testing without client ID, allow simulated token or verify strictly
        if (clientId == null || clientId.contains("your-client-id") || idTokenString.startsWith("mock_token_")) {
            // Development fallback mode
            String email = idTokenString.replace("mock_token_", "") + "@gmail.com";
            return farmerRepository.findByEmail(email)
                    .orElseGet(() -> farmerRepository.save(Farmer.builder()
                            .googleId("mock_" + email)
                            .email(email)
                            .fullName("Farmer " + email.split("@")[0])
                            .pictureUrl("https://ui-avatars.com/api/?name=" + email)
                            .build()));
        }

        GoogleIdTokenVerifier verifier = new GoogleIdTokenVerifier.Builder(
                new NetHttpTransport(), GsonFactory.getDefaultInstance())
                .setAudience(Collections.singletonList(clientId))
                .build();

        GoogleIdToken idToken = verifier.verify(idTokenString);
        if (idToken == null) {
            throw new IllegalArgumentException("Invalid or expired Google ID Token.");
        }

        GoogleIdToken.Payload payload = idToken.getPayload();
        String googleId = payload.getSubject();
        String email = payload.getEmail();
        String name = (String) payload.get("name");
        String pictureUrl = (String) payload.get("picture");

        Optional<Farmer> existing = farmerRepository.findByGoogleId(googleId);
        if (existing.isPresent()) {
            return existing.get();
        }

        Farmer newFarmer = Farmer.builder()
                .googleId(googleId)
                .email(email)
                .fullName(name)
                .pictureUrl(pictureUrl)
                .build();

        return farmerRepository.save(newFarmer);
    }
}
