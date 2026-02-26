-- scripts/db-seed-sanity.sql
-- Reusable sanity checks for equipment seed quality.
--
-- Usage example:
--   docker exec -i <postgres-container> psql -U agd -d agd_dev -v ON_ERROR_STOP=1 -f /dev/stdin < scripts/db-seed-sanity.sql

\echo '=== equipment_catalog category counts ==='
SELECT category, COUNT(*) AS item_count
FROM equipment_catalog
GROUP BY category
ORDER BY category;

\echo ''
\echo '=== duplicate type_code guard (should return 0 rows) ==='
SELECT type_code, COUNT(*) AS dup_count
FROM equipment_catalog
GROUP BY type_code
HAVING COUNT(*) > 1
ORDER BY dup_count DESC, type_code;

\echo ''
\echo '=== missing origin_country references (should return 0 rows) ==='
SELECT e.type_code, e.name, e.origin_country
FROM equipment_catalog e
LEFT JOIN countries c ON c.code = e.origin_country
WHERE e.origin_country IS NOT NULL
  AND c.code IS NULL
ORDER BY e.type_code;
