# M7 remediation qualification evidence

## State

`M7_BLOCKED`. RES-288 remains `In Progress`; RES-291/M8 remains `Todo`. The changes are on the local-only branch `res-288-m7-remediation`. No merge, push, release, tag, or history rewrite was performed.

The accepted public starting point was `f59aae4`. The working tree was clean before edits. The remediation commits are separated by purpose:

- `b7c18b8` — redact rights-restricted empirical result metadata.
- `46547ea` — remove historical object references from the current public tree.
- `026b517` — tighten provenance and release-boundary controls.
- `4a18e2e` — apply formatting to the redaction changes.

## Before and after qualification

| Check | M7 baseline at `f59aae4` | Remediation candidate before the report commit |
|---|---:|---:|
| Unit tests | 288 passed | 289 passed |
| Ruff lint | Pass | Pass |
| Ruff format check | Pass | 97 files already formatted |
| Pyright | Pass | 0 errors, 0 warnings, 0 informations |
| `git diff --check` | Pass | Pass |
| Reachable commits in scan | 37 | 41 |
| Reachable blobs in scan | 203 | 235 |
| Protected M0 SHA-256 fingerprints | 25,069 | 25,069 |
| Bound source records behind those fingerprints | 28,858 | 28,858 |
| Exact protected-byte matches | 0 | 0 |

The baseline M7 audit and the frozen M0 classification checksum manifests verified before use. The post-remediation exact-byte check read the preserved M0 fingerprint set and compared it with every reachable blob across the refs available before the M7 reports were committed. It found no exact matches. No fingerprint values or preserved archive bytes were copied into the repository.

## Wheel inspection and isolation

The M7 baseline wheel contained 81 entries and was installed outside the checkout. The rebuilt `0.1.0` wheel also contains 81 entries: 77 package files and four wheel metadata files. It contains no tests, M7 documents, or protected payload files. Its declared runtime dependency remains NumPy; no license was added.

The wheel installed with its dependency into a fresh Python 3.12 environment under `/tmp`, then imported from outside the checkout. The import resolved from that environment’s `site-packages`; it exposed all eight benchmark identities and the generic rights-restricted empirical record. The installed package reports `PROHIBITED` redistribution for that record, and the historical alias type has no commit/tree reference fields.

## Public scientific claims

The sealed M6 certification contained 35 claims, including seven with a White-derived rights dependency. The public synthesis now contains 34 claims: the source-specific ranking claim was removed, and the six remaining program-level claims no longer bind restricted result values, splits, or model comparisons. Their M2–M5 scientific bindings remain. A registry comparison confirmed that the current claim set equals the certified baseline set with only that source-specific claim removed; the synthesis tests validate every remaining claim.

The unresolved empirical-grounding limitation remains public and states that no rights-cleared source/split/scorer crosswalk is established. It does not assert a benchmark result.

## Security and path boundary

The current-tree boundary checks reject machine-local absolute paths, credentials, private keys, and 40-character SHA-1 object references. The public GitHub account name is allowed; a regression test confirms that a real machine path and a synthetic token are still rejected.

The top-level allowlist remains `src`, `tests`, and the exact `docs` report paths. Markdown remains denied elsewhere, and protected data, archive, checkpoint, and evidence classes remain denied. The public account identity is no longer treated as private machine provenance.

## Rights, packaging, and remaining owner decisions

M0 has an explicit handling decision for each of its 36 rights questions: 24 `DO_NOT_REDISTRIBUTE`, 11 `PRIVATE_ARCHIVE_ONLY`, and one `NOT_APPLICABLE_TO_PUBLIC_RELEASE`. The empirical source and derivatives remain prohibited from redistribution. The public tree has no owner-selected license, and no citation identity is asserted.

Owner decisions still required:

1. Select a project license and establish the author identity needed for license and citation metadata.
2. Obtain written rights clearance before any empirical source, derivative, split, comparison, or result summary is proposed for redistribution.
3. Decide whether to authorize a coordinated rewrite of public history. The current tree no longer contains the adjudicated object references, but earlier public commits still do; 19 historical machine-path occurrences also remain.
4. Provide exact M0 evidence or keep omitted the eight object references without an exact M0 classification. They have been removed from the current tree regardless.

The 25,069-fingerprint byte check does not clear those object identifiers or historical paths, and it does not establish redistribution rights. M8 reproduction was not run. M7 remains blocked pending owner decisions and any authorized historical remediation.
