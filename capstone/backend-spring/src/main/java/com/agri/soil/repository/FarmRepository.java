package com.agri.soil.repository;

import com.agri.soil.entity.Farm;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface FarmRepository extends JpaRepository<Farm, Long> {

    List<Farm> findByFarmerId(Long farmerId);

    // Native PostGIS query: Calculates geodesic area in Acres based on Earth's ellipsoid
    @Query(value = "SELECT ST_Area(f.boundary::geography) / 4046.86 FROM farms f WHERE f.id = :farmId", nativeQuery = true)
    Double calculateAreaInAcres(@Param("farmId") Long farmId);

    // Native PostGIS query: Converts boundary polygon into standard GeoJSON string
    @Query(value = "SELECT ST_AsGeoJSON(f.boundary) FROM farms f WHERE f.id = :farmId", nativeQuery = true)
    String getBoundaryAsGeoJson(@Param("farmId") Long farmId);
}
