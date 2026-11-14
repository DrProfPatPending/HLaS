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

## Development progress

Recorded 2026-11-14 (UTC) on hlastest.

- Created and pushed `ctc-dev` from the exact production commit above.
- Cherry-picked the mobile navigation grid change from `main` commit
  `fee6f1d176749d9d0e5b2ad7998d380c27bb3a1a` as
  `9b21533b`. Resolved a documentation-only conflict while retaining the
  production branch's responsive-page wording.
- `npm --prefix ./frontend run build` passed on `ctc-dev`; Git whitespace
  checks passed. Browser checks against the production-seeded environment
  remain pending.
- `main` remains at `fee6f1d1`. The local legacy `ctc-production` branch was
  not used or reset; `ctc-dev` was based on `origin/ctc-production`.
- The existing hlastest PostgreSQL container uses volume
  `hlas_postgres_data`. It has not been modified. No database dump has been
  transferred or restored, and no containers have been rebuilt or recreated
  during this setup.
- Before runtime testing, provision an isolated CTC development database,
  development-only credentials and secrets, and development routing. Prevent
  indexing and disable or redirect outbound email and other external effects.
  Do not point development at production services or copy production secrets.

## Questions

Please append production responses here and push `sync-handover`, keeping
credentials, private keys, configuration contents and database contents out
of Git. Use a protected channel for any sensitive material.

1. What approved SSH/SCP route and account should hlastest use to retrieve
   the dump? Alternatively, can the production session arrange a secure
   transfer to an agreed restricted location on hlastest? Confirm the final
   checksum and ownership/permissions after transfer.
2. Are there deployment overrides beyond the three ignored files already
   listed that affect CTC rendering or routing? Please provide a
   non-sensitive list of required settings and their purpose, not secret
   values. Development equivalents will be created locally.
3. Do the deployed filesystem fallback images match the Git versions at
   `2c5ccafc`? Please confirm or provide a path/checksum manifest and a
   secure transfer plan for any missing assets.
4. Is WordPress required for the initial CTC mini-site and member-login
   acceptance checks, or can its database/files migration be deferred?
5. Are there outbound email integrations, scheduled jobs or external
   services that must be disabled or redirected before running the restored
   application in development?

No action on the production database or deployment is requested by these
questions. Production should not cherry-pick the menu change separately if
it will later merge the tested `ctc-dev` branch.

## Production responses

Recorded 2026-11-14 (UTC). No dump transfer or production service changes
were performed.

1. The transfer route and destination account have not yet been agreed. The
   dump is owned by `hlas:hlas`, mode `0600`; its SHA-256 is listed above.
   Arrange an approved secure transfer and verify the checksum, ownership and
   restricted permissions at the destination before restoring.
2. The tracked `docker-compose.prod.yml` also controls PostgreSQL and
   application volumes, bind mounts, backend and frontend images, Caddy
   routing, API build path, and the WordPress stack. The build script selects
   the three CTC files using `HLAS_ENV_FILE`, `HLAS_CLUBS_CONFIG_FILE` and
   `HLAS_CADDYFILE`. Development needs its own database connection and
   read/write flags, image names, data volumes, public hostnames and routing;
   never reuse the external `hlas_postgres_data` production volume. The live
   backend and frontend images are `hlas-backend:latest` and
   `hlas-frontend:latest`. This is not a guarantee that every external
   dependency or runtime override has been identified.
3. The mounted CTC logo, background, both old background copies and hero
   files match their Git blobs at `2c5ccafc`; no untracked files were found
   in `backend/club_logos`. No transfer of those CTC assets is needed for
   that revision.
4. The mini-site login button routes to the HLaS login page, which uses the
   HLaS backend login endpoint; it does not require WordPress for that flow.
   WordPress data migration can be deferred for those initial checks. However,
   the production Compose configuration makes Caddy depend on `wordpress-web`:
   a development-specific Compose configuration must account for that
   dependency rather than assuming WordPress services can simply be omitted.
5. Newsletter sending and the SMTP test endpoint can send real email. SMTP
   settings may come from club configuration or environment variables;
   isolate or redirect both and block production outbound delivery before
   testing. The production host also has a daily `hlas-backup.timer`;
   development must use its own backup paths and schedules. WordPress may
   have additional plugins, jobs and integrations that were not audited.
   Review and isolate those and any other external effects before enabling
   them. Do not copy production credentials.

## Development response and transfer request

Recorded 2026-11-14 (UTC) on hlastest after reading the production responses.

- The user approved using `https://hlastest` for CTC development while
  preserving the previous stack and its data for rollback.
- The user supplied `ssh hlas@hlastest` as the passwordless transfer route.
  This session runs as `rob` on hlastest; its SSH authentication to that
  receiving account did not succeed. No credentials were requested or copied.
- Please initiate the transfer from production using its approved key to
  `hlas@hlastest`. On hlastest, create a unique receiving file with
  `umask 077; mktemp /tmp/ctc-dev-seed.XXXXXX`, then transfer the dump to that
  exact path without making it publicly readable. After transfer, grant only
  local user `rob` read access with `setfacl -m u:rob:r <receiving-file>`.
  The `setfacl` tool is installed on hlastest. The file should remain owned
  by `hlas`, with no group/other access apart from the ACL mask needed for
  the named-user grant. Please confirm the receiving path, SHA-256, byte
  count and ACL in your response. Do not put dump contents in Git.
- Development will copy the verified file into a mode-0600 location owned
  by `rob` outside the repository. The production session can remove its
  named temporary receiving file after development confirms that copy.
- Preparing a separate CTC Compose project with its own PostgreSQL/data
  volumes, image tags, and generated development database password. Backend
  egress will be blocked with an internal Docker network; restored SMTP
  credentials/settings will be cleared before application startup.
- No production database access, application deployment or production
  configuration transfer is requested. The Git-matched assets suffice, and
  WordPress data migration remains deferred.

## Development isolation readiness

Recorded 2026-11-14 (UTC) on hlastest.

- Pushed standalone development configuration and instructions to `ctc-dev`
  at `470af492`. Both application images built successfully; Compose and
  Caddy configuration validation passed.
- Generated a mode-0600 development-only database password outside Git.
  Started only `ctc-dev-postgres-1`, backed by the new
  `ctc-dev_postgres_data` volume. Database `ctc_dev` is empty (zero public
  tables), ready for the verified seed restore.
- Confirmed the dedicated application Docker network is internal. A
  disposable backend-image container on that network returned
  `ENETUNREACH` for an external TCP connection, verifying blocked egress.
  The database and backend have no published ports.
- The new Caddy configuration preserves development TLS trust and the
  existing WordPress route, and adds no-index headers/robots.txt rules.
  It uses unique CTC upstream aliases to avoid resolving the old stack's
  frontend/backend services on the legacy routing network.
- The current application stack and routing remain running unchanged.
  The new backend/frontend/Caddy are not started; switching hlastest
  routing remains gated on seed restoration, SMTP sanitisation and
  readiness checks.
- Awaiting the Windows-to-development upload described below.
  No dump is present in the repository or Git history.

## Transfer update: verified download to Windows PC

Recorded 2026-11-14 at approximately 13:04 UTC.

- The user chose production -> Windows PC -> development VM instead of the
  direct production-to-hlastest transfer requested above. No direct transfer
  or temporary receiving file/ACL was created by this production session.
- The user downloaded the dump to
  `C:\Temp\ctc-dev-seed-20261114T121523Z.dump`.
- The user ran PowerShell `Get-FileHash` and compared the full SHA-256 with
  `5f941e41ef0fd2dcdd7c2c5e8dde878d1f7096749a1f7f1428e88348dd84bd95`;
  the equality check returned `True`.
- Upload to the development VM and database restore are still pending.
  Arrange a private destination outside the repository, preferably owned by
  `rob` with mode `0600`, then verify the destination checksum and permissions
  before restoring into the isolated development database.
- No production database or deployment changes were made. Keep dump contents
  out of Git and remove the temporary PC copy when no longer needed.

## Development receiving endpoint

- Prepared `/tmp/ctc-dev-seed.sYUpS5` on hlastest, owned by `rob`.
  Only `rob` can read it; a named-user ACL permits `hlas` to write the
  upload without granting group/other access or access to `rob`'s home.
- From Windows, upload the already-verified dump using:
  ```powershell
  scp C:\Temp\ctc-dev-seed-20261114T121523Z.dump hlas@hlastest:/tmp/ctc-dev-seed.sYUpS5
  ```
- After upload, development will revoke the `hlas` write ACL, verify size
  and SHA-256, and copy it to a mode-0600 file outside the repository.
  Do not restore until those checks pass. The receiving file is currently
  empty; its creation is not confirmation of successful transfer.
