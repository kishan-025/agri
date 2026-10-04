package com.agri.soil.config;

import com.agri.soil.service.AuthService;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class DatabaseMigration {

    private static final Logger log = LoggerFactory.getLogger(DatabaseMigration.class);
    private final JdbcTemplate jdbcTemplate;

    public DatabaseMigration(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void migrate() {
        try {
            log.info("Executing database migration for custom Username/Password auth...");

            // 1. Add username & password columns if not present
            try {
                jdbcTemplate.execute("ALTER TABLE farmers ADD COLUMN IF NOT EXISTS username VARCHAR(100);");
            } catch (Exception e) {
                log.warn("Notice adding column username: {}", e.getMessage());
            }

            try {
                jdbcTemplate.execute("ALTER TABLE farmers ADD COLUMN IF NOT EXISTS password VARCHAR(255);");
            } catch (Exception e) {
                log.warn("Notice adding column password: {}", e.getMessage());
            }

            // 2. Drop NOT NULL constraints on google_id and email if present
            try {
                jdbcTemplate.execute("ALTER TABLE farmers ALTER COLUMN google_id DROP NOT NULL;");
            } catch (Exception e) {
                log.debug("Notice dropping NOT NULL on google_id: {}", e.getMessage());
            }

            try {
                jdbcTemplate.execute("ALTER TABLE farmers ALTER COLUMN email DROP NOT NULL;");
            } catch (Exception e) {
                log.debug("Notice dropping NOT NULL on email: {}", e.getMessage());
            }

            // 3. Create unique index on username
            try {
                jdbcTemplate.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_farmers_username ON farmers(username);");
            } catch (Exception e) {
                log.debug("Notice creating unique index idx_farmers_username: {}", e.getMessage());
            }

            // 4. Ensure farmer with id=1 has username 'farmer_kishan' and default password
            String defaultHash = AuthService.hashPassword("farmer123");
            try {
                jdbcTemplate.update(
                        "UPDATE farmers SET username = 'farmer_kishan', password = ? WHERE id = 1",
                        defaultHash
                );
                log.info("Ensured farmer ID 1 has username 'farmer_kishan'.");
            } catch (Exception e) {
                log.warn("Could not set farmer_kishan for id=1: {}", e.getMessage());
            }

            // 5. Update any remaining records without a username uniquely by id
            int updated = jdbcTemplate.update(
                    "UPDATE farmers SET username = 'farmer_' || id, password = ? WHERE username IS NULL OR username = ''",
                    defaultHash
            );
            if (updated > 0) {
                log.info("Assigned unique usernames and default password to {} existing farmer records.", updated);
            }

            // 6. Ensure at least one default farmer exists if the table is completely empty
            Integer count = jdbcTemplate.queryForObject("SELECT count(*) FROM farmers", Integer.class);
            if (count == null || count == 0) {
                jdbcTemplate.update(
                        "INSERT INTO farmers (username, password, full_name, email, picture_url, created_at) " +
                                "VALUES ('farmer_kishan', ?, 'Farmer Kishan', 'farmer_kishan@agrisoil.org', 'https://ui-avatars.com/api/?name=Farmer+Kishan&background=10b981&color=fff', NOW())",
                        defaultHash
                );
                log.info("Created initial default farmer 'farmer_kishan' with password 'farmer123'.");
            }

            log.info("Database migration completed successfully.");
        } catch (Exception e) {
            log.error("Error during database migration: {}", e.getMessage(), e);
        }
    }
}
