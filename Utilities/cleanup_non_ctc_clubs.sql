-- Remove non-CTC club data from PostgreSQL for CTC-only production.
-- Targets: GAAFFS, LADFFA, TEST
-- Safety: aborts if CTC club row is missing.
-- Usage:
--   docker exec -i hlas-postgres-1 psql -v ON_ERROR_STOP=1 -U hlas -d hlas -f Utilities/cleanup_non_ctc_clubs.sql

BEGIN;

DO $$
DECLARE
  v_ctc_count integer;
  v_target_count integer;
BEGIN
  SELECT count(*) INTO v_ctc_count
  FROM clubs
  WHERE upper(short_name) = 'CTC';

  IF v_ctc_count <> 1 THEN
    RAISE EXCEPTION 'Safety check failed: expected exactly one CTC row in clubs, found %', v_ctc_count;
  END IF;

  SELECT count(*) INTO v_target_count
  FROM clubs
  WHERE upper(short_name) IN ('GAAFFS', 'LADFFA', 'TEST');

  IF v_target_count = 0 THEN
    RAISE NOTICE 'No target clubs found (GAAFFS/LADFFA/TEST). Nothing to clean.';
  END IF;
END
$$;

CREATE TEMP TABLE tmp_target_clubs ON COMMIT DROP AS
SELECT id, upper(short_name) AS short_name
FROM clubs
WHERE upper(short_name) IN ('GAAFFS', 'LADFFA', 'TEST');

-- Remove non-FK session rows keyed by club short name.
DELETE FROM member_sessions s
WHERE upper(s.club_short_name) IN (SELECT short_name FROM tmp_target_clubs);

DELETE FROM member_refresh_sessions rs
WHERE upper(rs.club_short_name) IN (SELECT short_name FROM tmp_target_clubs);

-- Remove assets keyed by club short name.
DELETE FROM club_logos cl
WHERE upper(cl.club_short_name) IN (SELECT short_name FROM tmp_target_clubs);

DELETE FROM club_backgrounds cb
WHERE upper(cb.club_short_name) IN (SELECT short_name FROM tmp_target_clubs);

-- Remove audit rows that would otherwise keep null-club references.
DELETE FROM security_audit_log sal
WHERE sal.club_id IN (SELECT id FROM tmp_target_clubs);

-- Delete target clubs; FK CASCADE removes dependent club-scoped data.
DELETE FROM clubs c
WHERE c.id IN (SELECT id FROM tmp_target_clubs);

-- Post-check summary.
SELECT 'remaining_target_clubs' AS check_name, count(*) AS value
FROM clubs
WHERE upper(short_name) IN ('GAAFFS', 'LADFFA', 'TEST');

SELECT 'remaining_target_sessions' AS check_name, count(*) AS value
FROM member_sessions
WHERE upper(club_short_name) IN ('GAAFFS', 'LADFFA', 'TEST');

SELECT 'remaining_target_refresh_sessions' AS check_name, count(*) AS value
FROM member_refresh_sessions
WHERE upper(club_short_name) IN ('GAAFFS', 'LADFFA', 'TEST');

SELECT 'remaining_target_logos' AS check_name, count(*) AS value
FROM club_logos
WHERE upper(club_short_name) IN ('GAAFFS', 'LADFFA', 'TEST');

SELECT 'remaining_target_backgrounds' AS check_name, count(*) AS value
FROM club_backgrounds
WHERE upper(club_short_name) IN ('GAAFFS', 'LADFFA', 'TEST');

COMMIT;
