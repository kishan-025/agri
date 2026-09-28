package com.agri.soil.repository;

import com.agri.soil.entity.FertilityAssessment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface FertilityAssessmentRepository extends JpaRepository<FertilityAssessment, Long> {
    List<FertilityAssessment> findByFarmIdOrderByCreatedAtDesc(Long farmId);
}
