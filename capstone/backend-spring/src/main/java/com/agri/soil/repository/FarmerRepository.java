package com.agri.soil.repository;

import com.agri.soil.entity.Farmer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface FarmerRepository extends JpaRepository<Farmer, Long> {
    Optional<Farmer> findByUsername(String username);
    boolean existsByUsername(String username);
    Optional<Farmer> findByEmail(String email);
}
