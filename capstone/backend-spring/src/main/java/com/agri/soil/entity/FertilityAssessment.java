package com.agri.soil.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.ZonedDateTime;

@Entity
@Table(name = "fertility_assessments")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class FertilityAssessment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "farm_id", nullable = false)
    private Farm farm;

    @Column(nullable = false, length = 30)
    private String satelliteDate;

    private Double cloudCoverPct;

    // Soil pH
    private Double meanPh;
    private Double minPh;
    private Double maxPh;

    // Nitrogen (N)
    private Double meanN;
    private Double minN;
    private Double maxN;

    // Phosphorus (P)
    private Double meanP;
    private Double minP;
    private Double maxP;

    // Potassium (K)
    private Double meanK;
    private Double minK;
    private Double maxK;

    // JSON payload of heatmaps and grid stats
    @Column(columnDefinition = "TEXT")
    private String heatmapJson;

    // Phase 2: Soil Health Profile & Multi-Source Climate (Requirement 2)
    private Double soilHealthIndex;
    private String conditionTier;
    private Double rainfallMm;
    private Double temperatureCelsius;
    private Double soilMoisture;

    // Phase 2: Region-Specific Crop Recommendation & LLM Advisory (Requirement 3)
    private String recommendedCrop;
    private Double cropMatchPct;

    @Column(columnDefinition = "TEXT")
    private String cropAdvisoryJson;

    @Column(columnDefinition = "TEXT")
    private String climateJson;

    @Builder.Default
    private ZonedDateTime createdAt = ZonedDateTime.now();
}
