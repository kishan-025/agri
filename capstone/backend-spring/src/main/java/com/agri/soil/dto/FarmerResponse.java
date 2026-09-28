package com.agri.soil.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FarmerResponse {
    private Long id;
    private String googleId;
    private String email;
    private String fullName;
    private String pictureUrl;
}
