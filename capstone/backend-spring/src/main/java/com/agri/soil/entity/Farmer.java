package com.agri.soil.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.ZonedDateTime;

@Entity
@Table(name = "farmers")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Farmer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, length = 100)
    private String username;

    @Column(length = 255)
    private String password;

    @Column(length = 255)
    private String email;

    @Column(length = 255)
    private String fullName;

    @Column(columnDefinition = "TEXT")
    private String pictureUrl;

    @Builder.Default
    private ZonedDateTime createdAt = ZonedDateTime.now();
}
