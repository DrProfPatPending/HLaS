# HLaS Core Issue Log

## Purpose

Track issues and feature requests affecting the shared HLaS codebase across deployments. Club-specific content, configuration, and CTC release decisions remain in the CTC Chairman feedback log.

When triaging a club request that needs a shared change, create a core item with its own ID and a reference to the originating club item. Keep the club item to track its specific requirements and release outcome, and reference the core item there. Agree scope and priority before implementation.

This log is intended to be maintained with the shared code on `main`; promote updates between branches as appropriate.

## Issues

| ID | Area | Issue / requested outcome | Origin | Open questions | Status |
|---|---|---|---|---|---|
| CORE-01 | Public mini-site / mobile | Make enabled mini-site pages usable on mobile viewports. The shared container now renders the club-configured mini-site at all viewport widths, using responsive navigation and page styling. Preserve desktop behaviour and per-club configuration. | CTC PUBLIC-01 in the CTC Chairman feedback log. | Complete real-device accessibility checks and verify loading/error behaviour and configured navigation for other clubs. | Implemented on main; CTC release verification pending |

### CORE-01 verification

- Frontend production build passes; responsive layout checked in-browser at 375, 767, 768, 769, and 1024px. Direct About access and login sizing were also checked.
- Dev CTC page configuration is set to Home, About, and Contact enabled; the public API confirms the flags. Recheck configured navigation on mobile when browser control is available.
- Complete real-device checks and verify desktop behaviour and other enabled-page configurations as follow-up validation.
- After promotion to CTC, verify its Home, About and Contact pages on mobile; track CTC release readiness under PUBLIC-01.
