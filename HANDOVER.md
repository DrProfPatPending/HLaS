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

## Development receiving endpoint (completed; do not upload again)

- Prepared `/tmp/ctc-dev-seed.sYUpS5` on hlastest, owned by `rob`.
  Only `rob` can read it; a named-user ACL permits `hlas` to write the
  upload without granting group/other access or access to `rob`'s home.
- From Windows, upload the already-verified dump using:
  ```powershell
  scp C:\Temp\ctc-dev-seed-20261114T121523Z.dump hlas@hlastest:/tmp/ctc-dev-seed.sYUpS5
  ```
- After upload, development will revoke the `hlas` write ACL, verify size
  and SHA-256, and copy it to a mode-0600 file outside the repository.
  At preparation time the receiving file was empty. Transfer and verification
  have since completed, and this temporary file has been removed; see the
  completion report below.

## Recovery and maintenance to-do list

Recorded 2026-11-14 following read-only production checks at approximately
14:05 UTC. These are pending actions, not confirmation of completed recovery
or maintenance.

### Full recovery rehearsal in ctc-dev

- [x] Finish the seed upload and verify its checksum and restricted permissions.
  The verified dump captures PostgreSQL at 12:15 UTC; later production changes
  require a fresh snapshot if they must be included.
- [x] Rehearse recovery from an empty, isolated development database and fresh
  application data volumes. Preserve the existing development stack and rollback
  data; do not erase or reuse production or legacy volumes.
- [x] Restore the dump and recreate development equivalents of required
  deployment configuration. Clear restored SMTP settings/credentials before
  application startup and retain blocked backend egress and no-index controls.
- [ ] Check recovery against the snapshot: beat maps, pools, parking, waypoints,
  member/user status, account roles, mini-site pages/settings, field order and
  database-backed images. Test mobile/desktop navigation and member login.
  Record deliberate development-only differences without publishing personal
  data or credentials.
- [x] Resolve field-order recovery expectations. Both on-disk CTC beat exports
  matched PostgreSQL during the check, but `backend/field_order.json` differed
  from the global database setting. No CTC-specific field-order row was present.
  A Git-only rebuild cannot reproduce all current application state; restore
  database settings rather than treating JSON defaults as a complete backup.
- [ ] Ensure protected backup coverage includes `.env.ctc`,
  `clubs.config.ctc.json` and `deploy/caddy/Caddyfile.ctc`. The scheduled backup
  uses `.env.prod` and its default filesystem sources do not explicitly include
  those three live CTC files. Keep their contents outside Git.
- [ ] Independently verify the scheduled full backup and rehearse restoration of
  any required filesystem data. Today's scheduled job reported success, but its
  protected archive has not been independently verified. WordPress's separate
  database/files remain outside the transferred PostgreSQL seed; include a
  separate WordPress recovery test before claiming complete-site recovery.
- [x] Record the reproducible recovery procedure, snapshot/commit used, required
  protected inputs, validation results and remaining gaps in this handover.

### Production OS maintenance (user-managed)

- [x] User patched and rebooted the host. The running kernel is now
  `7.0.0-43-generic`; no reboot is pending.
- [ ] Apply the three remaining Ubuntu updates observed after the reboot:
  `python3-software-properties`, `software-properties-common` and `snapd`.
- [x] Post-reboot verification completed after the production image refresh:
  containers are healthy; CTC home, API, login route, background and hero image
  endpoints return HTTP 200; the gated WordPress host returns its expected
  HTTP 401; the daily backup timer is active.

### Build environment and container updates (after OS maintenance)

- [ ] Review Docker's package source configuration: Docker Engine `29.5.3`,
  Compose `5.1.4` and Buildx `0.34.1` were installed as Ubuntu 24.04 packages
  on Ubuntu 26.04. The Docker repository file is disabled and points at `noble`;
  no enabled Docker APT repository is configured. Docker's official repository
  supports `resolute`; user is reviewing source configuration. Installed-only
  APT candidates do not prove these tools are current. The official Engine
  release notes listed `29.9.3` while this host remained at `29.5.3`.
- [ ] Test the refreshed production image set in ctc-dev before any subsequent
  production changes. The user explicitly chose to refresh production before
  that test; treat the production update below as an exception, not evidence
  that the dev validation step is complete.
- [x] Refreshed production images on 2026-11-14 after user authorization:
  PostgreSQL `17.12`, Caddy `2.11.9`, Nginx `1.31.8`, MySQL `8.4.13`, PHP
  `8.3.36`, WordPress core `7.1.4`. Pulled CTC Compose image digests and
  recreated services; backend/frontend application images were not rebuilt.
- [x] Resolved the WordPress image/volume mismatch. The refreshed image alone
  had left the persistent document-root at WordPress `7.0`; official WP-CLI
  updated the persistent core to `7.1.4`. Core checksums verified and the
  database reported its schema at the current version (`61833`).
- [x] Pre-refresh full backup and CTC configuration archive were copied to
  `/home/hlas/backups/pre-container-refresh-20261114T153310Z/`, mode `0600`
  files in a mode `0700` directory. PostgreSQL archive decoding, WordPress
  dump gzip integrity, filesystem tar and configuration tar checks passed.
  Full-snapshot SHA-256:
  `d7075154393f931f0846598f687f4dd4ccc4032ff5d3eff8f4358b094f4ee388`;
  CTC-config archive SHA-256:
  `fd45afd388e7af804fce7cdb791e5023d2f61636d2acf6b7acd1ad50ab1924c6`.
- [x] Post-deployment public checks passed. Caddy uses
  `deploy/caddy/Caddyfile.ctc`. For direct Compose commands, set
  `HLAS_CADDYFILE=./deploy/caddy/Caddyfile.ctc`; otherwise Compose defaults to
  `Caddyfile.prod`.

### Production infrastructure refresh report

Recorded 2026-11-14 after the user chose to proceed with production updates.

- Image pull first hit Docker Hub's anonymous rate limit; after the user
  completed Docker Hub login, pulls succeeded. No credentials were shared.
- All seven production services are running. PostgreSQL and MySQL are healthy;
  backend, frontend and WordPress web proxy health checks pass.
- The refreshed Caddy image was initially started with the default production
  Caddyfile during a direct Compose call, causing brief TLS failures. Corrected
  immediately by recreating only Caddy with the explicit CTC Caddyfile mount.
  Public TLS checks now pass.
- CTC home, `/api/clubs`, mini-site login route, background and hero endpoints
  return HTTP 200. The WordPress public host returns HTTP 401 as expected due
  to its access gate.
- Docker Engine, Compose and Buildx packages were not changed: APT still has no
  enabled Docker repository and this session has no privileged APT access.

## Development restore and routing completed

This report supersedes the earlier pending upload and routing status.

### Snapshot and isolation

- The Windows upload completed. Verified the full SHA-256 stated above and
  the 8,611,452-byte size, then retained the seed outside Git at
  `/home/rob/ctc-dev-seed-20261114T121523Z.dump`, owned by `rob:rob`, mode
  `0600`. Revoked the upload ACL and removed the temporary receiving file.
  No further upload to that temporary path is needed.
- Restored into `ctc_dev` on `ctc-dev-postgres-1`, using only the new
  `ctc-dev_postgres_data` volume. The original `hlas_postgres_data` volume
  and database container remain untouched.
- Cleared the development copy's SMTP connection/credential fields and
  truncated `member_sessions` and `member_refresh_sessions`. These are
  deliberate development-only differences, not production changes.
- The running backend has no external route: the TCP egress test returned
  `ENETUNREACH`. Backend, frontend and database publish no host ports.
  Backup API routes are disabled and no production timer was copied.

### Startup protection and recovery verification

- Found that the existing first-request startup hooks replace database beats
  and images from filesystem defaults. Added `HLAS_SYNC_FILES_ON_STARTUP`
  with the existing behaviour retained by default; the isolated CTC stack
  sets it to `false`. Re-restored the snapshot with the application stopped
  after discovering the hooks, then verified data was preserved on startup.
  No change to production startup behaviour has been deployed.
- Restored a temporary reference database from the same seed and compared
  complete-row fingerprints without publishing records. All 18 checked tables
  matched: clubs, members, app users, member/user links, roles, role
  assignments, beats, mini-sites, app settings, club field order, logos,
  backgrounds, heroes, map rotations, member photos, documents, newsletter
  templates and catch returns. The temporary reference database was removed.
- Confirmed the live CTC field-order API resolves to the restored global
  PostgreSQL configuration, including its overrides, rather than JSON
  defaults. The snapshot's lack of a club-specific row is preserved.
- The targeted startup-hook regression test passed. Both application Docker
  images built successfully; Compose and Caddy validation passed.

### Development routing and acceptance checks

- `ctc-dev` is pushed at `1142f0cc` and remains checked out with a clean
  working tree. Setup, safe restore prerequisites and routing rollback are
  documented in `CTC_SETUP.md`.
- `https://hlastest/club/CTC/` now uses the seeded CTC stack. The previous
  `hlas-caddy-1` is stopped but preserved for rollback; the other original
  services and their data remain running unchanged.
- HTTPS certificate verification passed using the existing development CA.
  Both hlastest hosts return no-index headers and valid multiline robots
  exclusion rules. The existing WordPress health route still responds.
  This does not constitute a WordPress recovery test.
- Home, About, Contact and the member login page return HTTP 200. Database
  logo, hero and background endpoints return images. Enabled pages are
  Home, About and Contact as captured by the snapshot.
- Firefox checks passed at 320, 375, 390, 768 and 1024px widths. Mobile
  navigation has three columns and 44px-or-larger tap targets; six simulated
  links form two rows. About/Contact clicks work, and Log In opens the
  member password form. Invalid credentials correctly return HTTP 401.
- A successful login with an authorised account and visual acceptance of
  the actual beat maps remain manual checks. No production password was
  requested, changed or published. The broader recovery acceptance item
  remains unchecked for those checks.

### Remaining boundaries

- The baseline is the 12:15 UTC snapshot, not any later production changes.
- WordPress data recovery, protected live-configuration backup coverage,
  scheduled archive verification, OS maintenance and refreshed container
  testing remain pending as listed above. Do not claim complete-site
  disaster recovery or update production on the basis of these CTC checks.
- The user can remove the temporary Windows dump once no longer needed.
  Retain or dispose of the protected development seed under the agreed
  backup/data-retention policy.

## Per-page hero images ready for CTC acceptance

- Implemented, tested and pushed `ctc-dev` commit `e1c35ad2`; rebuilt only
  the isolated development backend/frontend and verified them healthy.
  Production and `main` were not updated by this feature work.
- Club Settings > Club Mini Site now provides an optional image URL and
  fallback selection for each inner page. Home retains its existing hero
  URL field. Page settings use the existing PostgreSQL `pages` JSON; no
  database migration or production data edit is needed.
- The user chose existing inner pages to inherit the Home hero by default.
  A page-specific image takes precedence; when missing or broken, it uses
  the selected Home-then-banner or banner-only fallback. A broken Home
  image also falls back to the light green banner. To show only the banner,
  leave the page URL empty and choose the banner fallback.
- All six pages share the same compact header. Image headers use white
  text with a dark overlay; banners use dark green text on a light green
  gradient. Measured normal-text contrast is at least 7.69:1 on the plain
  banner and 5.74:1 against a worst-case white image under the overlay.
- Three backend regression tests passed (save/reload, legacy defaults,
  invalid-setting rejection). Frontend and both Docker builds passed.
  Browser checks covered valid/missing/broken image chains, all six page
  types, banner-only selection, and Club Settings load/edit/save payloads
  without modifying stored site configuration.
- Live HTTPS checks confirmed Home, About and Contact load the Home hero
  with readable white headings at 320, 375, 390, 768 and 1024px widths.
  The restored beats fingerprint remains unchanged and SMTP credentials
  remain cleared in development.
- Updated `MINI_SITE_PAGES.md` and `README.md`. Production promotion and
  final visual acceptance remain user-controlled. The infrastructure
  refresh recorded above is separate work, not part of this deployment.
