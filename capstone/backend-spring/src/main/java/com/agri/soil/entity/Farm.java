package com.agri.soil.entity;

import jakarta.persistence.*;
import lombok.*;
import org.locationtech.jts.geom.Polygon;
import java.time.ZonedDateTime;

@Entity
@Table(name = "farms")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Farm {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "farmer_id", nullable = false)
    private Farmer farmer;

    @Column(nullable = false, length = 150)
    private String farmName;

    // PostGIS native geometric polygon mapping (EPSG:4326)
    @Column(columnDefinition = "geometry(Polygon, 4326)", nullable = false)
    private Polygon boundary;

    // Geodesic area in acres computed via PostGIS
    private Double areaAcres;

    // Centroid for map centering
    private Double centroidLat;
    private Double centroidLon;

    // Enclosing Bounding box for Satellite STAC
    private Double minLon;
    private Double minLat;
    private Double maxLon;
    private Double maxLat;

    @OneToMany(mappedBy = "farm", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private java.util.List<FertilityAssessment> assessments = new java.util.ArrayList<>();

    @Builder.Default
    private ZonedDateTime createdAt = ZonedDateTime.now();
}
