package com.agri.soil.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FarmResponse {
    private Long id;
    private Long farmerId;
    private String farmName;
    private Double areaAcres;
    private Double centroidLat;
    private Double centroidLon;
    private Double minLon;
    private Double minLat;
    private Double maxLon;
    private Double maxLat;
    private List<List<Double>> corners;
    private String geoJson;
}
