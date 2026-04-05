-- Membership Paused Verification Pack (psql variable version)
-- Usage examples:
--   psql "postgresql://hlas:hlas@hlastest:5433/hlas" -v club='GAAFFS' -f Utilities/member_paused_verification_pack_psql.sql
--   psql "$DATABASE_URL" -v club='CTC' -f Utilities/member_paused_verification_pack_psql.sql
--
-- Notes:
--   - Requires psql variable 'club' to be set.
--   - In psql, variable substitution uses :'club'.

-- 1) Summary counts for Paused
SELECT
  c.short_name,
  COUNT(*) AS total_members,
  COUNT(*) FILTER (WHERE UPPER(TRIM(COALESCE(m.paused, ''))) = 'Y') AS paused_y,
  COUNT(*) FILTER (WHERE UPPER(TRIM(COALESCE(m.paused, ''))) = 'N') AS paused_n,
  COUNT(*) FILTER (WHERE TRIM(COALESCE(m.paused, '')) = '') AS paused_blank,
  COUNT(*) FILTER (
    WHERE TRIM(COALESCE(m.paused, '')) <> ''
      AND UPPER(TRIM(m.paused)) NOT IN ('Y', 'N')
  ) AS paused_other
FROM members m
JOIN clubs c ON c.id = m.club_id
WHERE c.short_name = :'club'
GROUP BY c.short_name;


-- 2) Distribution of actual Paused values
SELECT
  COALESCE(NULLIF(TRIM(m.paused), ''), '<BLANK>') AS paused_value,
  COUNT(*) AS row_count
FROM members m
JOIN clubs c ON c.id = m.club_id
WHERE c.short_name = :'club'
GROUP BY 1
ORDER BY row_count DESC, paused_value;


-- 3) Members with Paused = Y
SELECT
  m.number AS "Number",
  m.members_name AS "Members_Name",
  m.paused AS "Paused"
FROM members m
JOIN clubs c ON c.id = m.club_id
WHERE c.short_name = :'club'
  AND UPPER(TRIM(COALESCE(m.paused, ''))) = 'Y'
ORDER BY
  CASE WHEN TRIM(m.number) ~ '^[0-9]+$' THEN TRIM(m.number)::int END NULLS LAST,
  m.number;


-- 4) Members with blank Paused (top 50)
SELECT
  m.number AS "Number",
  m.members_name AS "Members_Name",
  m.paused AS "Paused"
FROM members m
JOIN clubs c ON c.id = m.club_id
WHERE c.short_name = :'club'
  AND TRIM(COALESCE(m.paused, '')) = ''
ORDER BY
  CASE WHEN TRIM(m.number) ~ '^[0-9]+$' THEN TRIM(m.number)::int END NULLS LAST,
  m.number
LIMIT 50;


-- 5) Unexpected non Y/N non-blank values
SELECT
  m.number AS "Number",
  m.members_name AS "Members_Name",
  m.paused AS "Paused"
FROM members m
JOIN clubs c ON c.id = m.club_id
WHERE c.short_name = :'club'
  AND TRIM(COALESCE(m.paused, '')) <> ''
  AND UPPER(TRIM(m.paused)) NOT IN ('Y', 'N')
ORDER BY m.paused, m.number;
