-- Membership Paused Verification Pack (parameterized by club)
-- Usage:
--   1) Edit the club short name in the params CTE.
--   2) Run the whole script, or run each query block individually.

WITH params AS (
  SELECT 'GAAFFS'::text AS club_short_name
)
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
JOIN params p ON c.short_name = p.club_short_name
GROUP BY c.short_name;


WITH params AS (
  SELECT 'GAAFFS'::text AS club_short_name
)
SELECT
  COALESCE(NULLIF(TRIM(m.paused), ''), '<BLANK>') AS paused_value,
  COUNT(*) AS row_count
FROM members m
JOIN clubs c ON c.id = m.club_id
JOIN params p ON c.short_name = p.club_short_name
GROUP BY 1
ORDER BY row_count DESC, paused_value;


WITH params AS (
  SELECT 'GAAFFS'::text AS club_short_name
)
SELECT
  m.number AS "Number",
  m.members_name AS "Members_Name",
  m.paused AS "Paused"
FROM members m
JOIN clubs c ON c.id = m.club_id
JOIN params p ON c.short_name = p.club_short_name
WHERE UPPER(TRIM(COALESCE(m.paused, ''))) = 'Y'
ORDER BY
  CASE WHEN TRIM(m.number) ~ '^[0-9]+$' THEN TRIM(m.number)::int END NULLS LAST,
  m.number;


WITH params AS (
  SELECT 'GAAFFS'::text AS club_short_name
)
SELECT
  m.number AS "Number",
  m.members_name AS "Members_Name",
  m.paused AS "Paused"
FROM members m
JOIN clubs c ON c.id = m.club_id
JOIN params p ON c.short_name = p.club_short_name
WHERE TRIM(COALESCE(m.paused, '')) = ''
ORDER BY
  CASE WHEN TRIM(m.number) ~ '^[0-9]+$' THEN TRIM(m.number)::int END NULLS LAST,
  m.number
LIMIT 50;


WITH params AS (
  SELECT 'GAAFFS'::text AS club_short_name
)
SELECT
  m.number AS "Number",
  m.members_name AS "Members_Name",
  m.paused AS "Paused"
FROM members m
JOIN clubs c ON c.id = m.club_id
JOIN params p ON c.short_name = p.club_short_name
WHERE TRIM(COALESCE(m.paused, '')) <> ''
  AND UPPER(TRIM(m.paused)) NOT IN ('Y', 'N')
ORDER BY m.paused, m.number;
