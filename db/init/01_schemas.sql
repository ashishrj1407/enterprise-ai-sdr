-- =============================================================================
-- STEP 1 · Bootstrap (ops / first install only)
-- =============================================================================
-- Creates empty databases and GRANTs for the app user.
-- Does NOT create tables — Alembic owns all table DDL (steps 2–4).
--
-- Docker: mounted as /docker-entrypoint-initdb.d (runs once on empty volume).
-- New customer later: add CREATE DATABASE + GRANT here (or equivalent ops job),
-- then re-init volume OR run the same statements as root, then migrate_all.
-- =============================================================================

-- Platform catalog database (tenant directory — not lead data)
CREATE DATABASE IF NOT EXISTS `generic` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tenant / customer databases (empty shells)
CREATE DATABASE IF NOT EXISTS schema_customer_1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS schema_customer_2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS schema_customer_3 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- App user must already exist (Compose MYSQL_USER=poc). Grant per-database access.
GRANT ALL PRIVILEGES ON `generic`.* TO 'poc'@'%';
GRANT ALL PRIVILEGES ON schema_customer_1.* TO 'poc'@'%';
GRANT ALL PRIVILEGES ON schema_customer_2.* TO 'poc'@'%';
GRANT ALL PRIVILEGES ON schema_customer_3.* TO 'poc'@'%';
FLUSH PRIVILEGES;
