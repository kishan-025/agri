package com.agri.soil.dto;

import lombok.Data;
import java.util.List;

@Data
public class CreateFarmRequest {
    private Long farmerId;
    private String farmName;
    // Exactly 4 [longitude, latitude] coordinate pairs
    private List<List<Double>> corners;
}
