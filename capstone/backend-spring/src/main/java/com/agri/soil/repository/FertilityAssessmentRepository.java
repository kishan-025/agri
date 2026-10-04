package com.agri.soil.repository;

import com.agri.soil.entity.FertilityAssessment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Repository
public interface FertilityAssessmentRepository extends JpaRepository<FertilityAssessment, Long> {
    List<FertilityAssessment> findByFarmIdOrderByCreatedAtDesc(Long farmId);

    @Transactional
    @Modifying
    @Query("DELETE FROM FertilityAssessment fa WHERE fa.farm.id = :farmId")
    void deleteByFarmId(@Param("farmId") Long farmId);
}
