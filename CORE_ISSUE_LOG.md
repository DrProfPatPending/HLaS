# HLaS Core Issue Log

## Purpose

Track issues and feature requests affecting the shared HLaS codebase across deployments. Club-specific content, configuration, and CTC release decisions remain in the CTC Chairman feedback log.

When triaging a club request that needs a shared change, create a core item with its own ID and a reference to the originating club item. Keep the club item to track its specific requirements and release outcome, and reference the core item there. Agree scope and priority before implementation.

This log is intended to be maintained with the shared code on `main`; promote updates between branches as appropriate.

## Issues

| ID | Area | Issue / requested outcome | Origin | Open questions | Status |
|---|---|---|---|---|---|
| CORE-01 | Public mini-site / mobile | Make enabled mini-site pages usable on mobile viewports. The shared container currently replaces them with a placeholder below 768px; existing responsive styling needs to be assessed and completed. Preserve desktop behaviour and club-specific configuration. | CTC PUBLIC-01 in the CTC Chairman feedback log. | Confirm mobile navigation and accessibility, direct page access, loading and error behaviour, and behaviour for other clubs and enabled pages. | Planned for Dev |

### CORE-01 verification

- Implement and test in the Dev environment before promoting shared changes to `main`.
- Test enabled pages, navigation and login on a real mobile device and across representative viewport widths, including either side of 768px.
- Check desktop behaviour and different club configurations for regressions.
- After promotion to CTC, verify its Home, About and Contact pages on mobile; track CTC release readiness under PUBLIC-01.
