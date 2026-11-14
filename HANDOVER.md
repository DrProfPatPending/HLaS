# CTC development environment handover

Recorded 2026-11-14 (UTC) on the CTC production server.

## Code

- `origin/ctc-production`: `2c5ccafca3f2ccce4d0782164cc9d3e12c2efe8b`.
- The local `ctc-production` branch matched that remote commit and its
  working tree was clean before this handover branch was created.
- Create `ctc-dev` from that production commit, not from `sync-handover`.

## PostgreSQL backup

- Production server: `/home/hlas/backups/ctc-dev-seed-20261114T121523Z.dump`
- Custom-format `pg_dump`; 8,611,452 bytes; file permissions `0600`.
- SHA-256: `5f941e41ef0fd2dcdd7c2c5e8dde878d1f7096749a1f7f1428e88348dd84bd95`
- Verification: `pg_restore --list` and a full `pg_restore` to `/dev/null`
  succeeded. A test restore into a database has not been performed.
- This backup contains production data. Transfer it securely outside Git,
  restrict access, and restore only into a verified isolated development
  database. Do not restore into the existing production database.

## Additional production dependencies

- The live deployment uses ignored files `.env.ctc`, `clubs.config.ctc.json`,
  and `deploy/caddy/Caddyfile.ctc`. Provision development equivalents securely
  and adapt their hostnames, credentials, mounts, and database connection for
  isolation. Do not commit the production files or their contents.
- The PostgreSQL dump covers the application database, including database-backed
  images and mini-site configuration. It does not include WordPress's separate
  database, WordPress files, or other Docker volume data. Assess and transfer
  those separately if needed, using an appropriately protected backup.
- Filesystem club logos and background fallback images are mounted from
  `backend/club_logos`; verify the deployed files against the Git copy when
  reproducing the site.
- Running images observed during handover include `postgres:17-alpine` and
  `wordpress:6.9-php8.3-fpm-alpine`. The running WordPress version may differ
  from the image specified by the Git commit; inspect before reproducing it.
- The scheduled snapshot directory is `/data/backups/snapshots`; its protected
  contents were not inspected or verified for this handover.
