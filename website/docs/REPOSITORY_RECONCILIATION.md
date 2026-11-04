# Historical website repository reconciliation

**Assessment date:** 2026-10-20

This report preserves the website integration snapshot from that date. Its repository, branch and publication observations are historical, not current release or deployment status. See [deployment operations](DEPLOYMENT.md) and the [release checklist](RELEASE_CHECKLIST.md) for current status.

## Canonical repository and source history

The website was integrated into the public GitHub repository `Litju/CMJRecoveryDynamicsBench`, whose `main` branch was at `3dc4c82f0c948add6e4a9ebdebfd227933c823d3` at the time. The website history was preserved through an unsquashed subtree merge under `website/`; the original standalone source checkout remained intact. No nested Git repository or submodule was added.

The imported website history contained 27 single-parent commits, 504 blobs and approximately 59,100 KiB of source objects. Its largest historical blob was a 2,730,656-byte generated screenshot. A text scan of the imported history found no common private-key, credential or access-token patterns. A dangling 5,147-byte release-checklist blob was scanned and not transferred.

The integrated website contained 210 tracked files, including source manifests, public synthetic JSON fixtures, the lockfile, documentation, screenshots and font licensing. Ignored local material such as build output, dependencies, recordings, environment files and caches remained excluded.

## Scientific and licensing boundary

Website source manifests pinned the scientific authority to `3dc4c82f0c948add6e4a9ebdebfd227933c823d3`. The build verified the source and fixture hashes, including SHA-256 `cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9` for the public fixed-mode results receipt.

All 80 Python modules under `src/cmj_recovery_dynamics` were byte-identical to the scientific source at integration time. Python package metadata and packaging files were preserved. The website source has its own Apache-2.0 license; the scientific source, Geist font and npm dependencies retain separate licensing. The website presents public synthetic evidence and contains no human-participant records.

## Historical qualification snapshot

At the time of this snapshot, the website qualification reported:

- Clean `npm ci`, 118 packages, zero reported npm vulnerabilities.
- 15/15 scientific/unit tests and a passing strict TypeScript check.
- A successful static build and 31/31 Chromium UI tests.
- Tests for the 96 sourced benchmark views, desktop/mobile states, keyboard interaction, accessibility, reduced motion and WebGL fallback.
- Python pytest 321 passed, Ruff lint and format passed, and strict Pyright reported zero errors and warnings.
- Wheel and source-distribution builds succeeded; neither included website assets.

The website source and receipt were merged through the public repository history. At this snapshot, the separate scientific Python release and production deployment were not yet established. Those statuses changed later; use the current release and deployment records linked above.
