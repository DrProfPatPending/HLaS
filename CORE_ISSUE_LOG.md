# HLaS Core Issue Log

## Purpose

Track issues and feature requests affecting the shared HLaS codebase across deployments. Club-specific content, configuration, and CTC release decisions remain in the CTC Chairman feedback log.

When triaging a club request that needs a shared change, create a core item with its own ID and a reference to the originating club item. Keep the club item to track its specific requirements and release outcome, and reference the core item there. Agree scope and priority before implementation.

This log is intended to be maintained with the shared code on `main`; promote updates between branches as appropriate.

## Issues

| ID | Area | Issue / requested outcome | Origin | Open questions | Status |
|---|---|---|---|---|---|
| CORE-01 | Public mini-site / mobile | Make enabled mini-site pages usable on mobile viewports while preserving desktop behaviour and club-specific configuration. | CTC PUBLIC-01 in the CTC Chairman feedback log. | Complete real-device accessibility checks and verify loading/error behaviour and configured navigation for other clubs. | Implemented; follow-up verification outstanding |
| CORE-02 | Public mini-site / content | Bring the shared mini-site work developed on `ctc-dev` back to `main`: per-page hero images with Home/banner fallback, per-page editable heading, subheading and sanitised body text (replacing the separate `main` implementation), the Home "Welcome to" heading fix, Contact page icons, and per-club SEO tags with `/sitemap.xml`. CTC-specific default text, navigation and logout behaviour stay on the CTC branches. | CTC PUBLIC-02 and the CTC mini-site content work in the CTC Chairman feedback log. | Verify the nginx `/club/...` SEO route and sitemap on the shared production stack, and check default pages for GAAFFS, LADFFA and TEST. | Ported to `main`; verification pending |
| CORE-03 | Beat maps / scrolling | Stop the Beat Details and Fishing Beats maps capturing page scroll: no mouse-wheel zoom, and no one-finger panning on touch devices. Zoom buttons, pinch zoom and desktop drag remain. | CTC BEAT-03 (#28). | Confirm this is the scrolling the Chairman meant; physical-device check outstanding. | Implemented on branch; not deployed |
| CORE-04 | Membership Admin / labels | Label the E_Mail column "Email" by default (field-order template). Clubs that set their own label keep it. | CTC ADMIN-04 (#31), label part only. | Whether to hide Username as a duplicate depends on how login identifiers work; not changed. | Implemented on branch; not deployed |
| CORE-05 | Membership Admin / ordering | Default the member list to surname order (ascending) instead of ID. | CTC ADMIN-03 (#30), ordering part only. | Handling of resigned/holding-list members and first-name tie-breaks still to be agreed. | Implemented on branch; not deployed |
| CORE-06 | Beats / startup sync | Startup beats sync deleted and re-inserted every club's beats from `clubs.config.json`, discarding beat edits made in the app on each restart or rebuild. Now only seeds clubs with no beats; `sync_beats_json_to_postgres.py --replace` keeps the deliberate overwrite. | Found while documenting data storage (CLAUDE.md). Affects `production` and `ctc-production` (sync on by default); ctc-dev has the sync off. | Before the first production deploy that includes this, check whether any beats were edited in the production app since the last deploy, and export them if so. | Implemented on branch; tested on ctc-dev; recommended for `ctc-production` |
| CORE-07 | Club backgrounds / startup sync | Startup logo/background sync upserts `club_logos/<CLUB>_background.png` into `club_backgrounds` on every start. Background uploads are stored only in PostgreSQL, so a restart replaces an uploaded background with the older file. | Found while testing CORE-05. Affects deployments with `HLAS_SYNC_FILES_ON_STARTUP` on. | Choose a fix: seed-only (as CORE-05), or also write uploads to disk as logo uploads already do. | Open |

### CORE-01 verification

- Implemented and browser-tested in Dev, then promoted to `main` and deployed to CTC.
- CTC Home, About and Contact, navigation and login form were checked in a browser at 375, 767, 768, 769 and 1024px; direct About access was also checked.
- CTC PUBLIC-01 was accepted and closed; physical-device and accessibility checks remain outstanding.
- Verify loading and error behaviour, desktop behaviour and enabled-page configurations for other clubs.
