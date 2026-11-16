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

### CORE-01 verification

- Implemented and browser-tested in Dev, then promoted to `main` and deployed to CTC.
- CTC Home, About and Contact, navigation and login form were checked in a browser at 375, 767, 768, 769 and 1024px; direct About access was also checked.
- CTC PUBLIC-01 was accepted and closed; physical-device and accessibility checks remain outstanding.
- Verify loading and error behaviour, desktop behaviour and enabled-page configurations for other clubs.
