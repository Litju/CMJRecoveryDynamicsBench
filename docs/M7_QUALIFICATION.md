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

## Independent review replay

The review reconfirmed branch `res-288-m7-remediation`, HEAD `1bafc13`, and a clean working tree before this evidence update. The diff against `f59aae4` covers 30 files with 565 insertions and 645 deletions. The three M7 reports were checked for raw machine paths, object identifiers, restricted result values, and private archive details; none were found. The occurrence report uses report aliases and relative repository paths.

Set `TMPDIR` to a writable temporary directory; the commands parameterize temporary paths so the report does not record a host-specific absolute path. The following repository checks passed on the candidate:

```text
UV_CACHE_DIR="${TMPDIR}/cmj-uv-cache" uv run --no-sync pytest
289 passed in 17.94s

UV_CACHE_DIR="${TMPDIR}/cmj-uv-cache" uv run --no-sync ruff check .
All checks passed!

UV_CACHE_DIR="${TMPDIR}/cmj-uv-cache" uv run --no-sync ruff format --check .
98 files already formatted

UV_CACHE_DIR="${TMPDIR}/cmj-uv-cache" uv run --no-sync pyright
0 errors, 0 warnings, 0 informations

git diff --check f59aae4..HEAD
passed
```

An independent `uv build --wheel` replay could not resolve `setuptools>=68` because network DNS was unavailable. The fallback command `python3 -m pip wheel --no-build-isolation --no-deps . --wheel-dir "${TMPDIR}/cmj-m7-review-wheel"` succeeded with the locally installed setuptools 68.1.2. The resulting wheel had 81 entries: 77 package files and four metadata files, with no tests, docs, or protected payloads. It was installed into a fresh Python 3.12 virtual environment and imported from outside the checkout. The isolated import resolved from that environment's `site-packages`, loaded pinned NumPy 2.5.3, exposed eight benchmark identities, and confirmed that `HistoricalAlias` has no commit/tree fields. The dependency was seeded from the existing environment because offline dependency resolution was unavailable.

The sealed RES-362 and RES-288 checksum manifests verified 10/10 and 17/17 files. The protected-byte comparison on reviewed HEAD `1bafc13`, before this evidence update, covered the preserved 25,069 fingerprints and 28,858 bound records against 238 reachable blobs across 42 reachable commits; it found zero exact matches. The current-tree scan on that HEAD reported zero machine-local paths, secrets/private keys, private URLs, and 40-character SHA-1 references. Raw fingerprints, raw occurrence values, and the private comparator invocation remain outside public Git.

At reviewed candidate HEAD `1bafc13`, rewriting the earliest affected commit would change 36 commits on `main`, 22 commits on origin's legacy registry-gate branch, and 41 on `res-288-m7-remediation`; the union is 41 distinct affected commits. There were no local tags. PR refs, forks, and external clones had not been inspected at that review point. The refreshed inventory below supersedes these counts. A targeted rewrite retains more provenance but changes descendant SHAs; a clean baseline built from the sanitized tree gives a fresh graph but discards public history. Neither action can revoke copies already held by clones or caches. No history operation was performed.

The review recommendation is to treat the candidate as suitable for a separate current-tree code merge only if the owner accepts that the earlier affected history remains reachable. Such a merge would reduce disclosure at HEAD but would not clear the repository for M7 or M8. RES-288 remains `In Progress`; RES-291/M8 remains `Todo` and unstarted. No push, merge, release, tag, or history rewrite was performed.

## Post-appendix qualification and integration

The 31-line independent-review appendix was diff-checked and committed as `0d6de93`. Qualification was rerun on that committed HEAD: 289 tests passed; Ruff passed; all 98 files passed the format check; Pyright reported zero errors, warnings, and informations; and `git diff --check f59aae4..HEAD` passed. A wheel rebuilt successfully with 81 entries (77 package Python files and four metadata files), with no tests, docs, or protected payloads.

The sealed RES-288, RES-362, and RES-363 manifests verified 17/17, 10/10, and 44/44 entries. The read-only M0/M7 replay compared 25,069 protected fingerprints covering 28,858 source records against the blobs reachable from the available refs; exact byte matches: zero. This result does not clear historical identifiers or paths and does not establish redistribution rights.

The local integration check against `main` was clean and fast-forwardable. Its prospective tree is identical to the remediation candidate tree. The current-tree scan found no machine-local path, credential, private key, private URL, or full SHA-1 reference. It found three occurrences of the known public repository account label (two case forms) and one intentional malformed-URL test fixture; all were manually adjudicated. The two case forms account for the new pattern hits relative to current `main` and add no private provenance. Existing historical paths and reference strings remain reachable after a fast-forward, so this integration does not clear M7.

The public origin inventory contains branches `main` and `tmp/res393-registry-gate`, no tags, no visible PR refs, zero pull requests in the GitHub API, and zero forks. External clones and caches cannot be inventoried from this repository. Rewriting the earliest affected commit would change 36 commits on `main`, 22 on the legacy branch, and 43 on `res-288-m7-remediation`; these refs overlap, for 43 distinct affected commits at the final report HEAD.

## History-remediation dry-run plans

Neither plan was executed. The M0 archive and sealed classification files remain read-only and outside public Git. `git-filter-repo` is not installed in this checkout.

**Targeted rewrite.** Generate a private replacement map from the sealed M7 review: 28 exact reference strings and 11 distinct path strings, each matched literally and replaced with a non-path redaction marker. Keep both the map and the dry-run exports outside Git with private permissions. In a disposable mirror containing all current local and origin-tracking refs, run:

```sh
umask 077
MIRROR="$(mktemp -d)/cmj-m7-mirror.git"
MAP="${M7_PRIVATE_DIR}/literal-replacements.txt"
git clone --mirror --no-local "$PWD" "$MIRROR"
git -C "$MIRROR" filter-repo --dry-run --replace-text "$MAP"
```

Each map line uses the default literal matching form, with a fixed redaction marker after `==>`. Review the filtered export against the original, confirm the only distinct match values are the 39 mapped literals, and check all refs for residual findings. If the owner authorizes a rewrite after this dry run, validate it in another disposable mirror against the sealed M0 bytes and rerun the full qualification. Do not pass `--refs`: the plan must cover every inventoried branch, and partial rewriting can leave mixed old/new history. No push is part of this plan.

**Clean baseline.** In a separate private temporary directory, export only the sanitized candidate tree, then initialize a new repository with one root commit after the owner selects the author identity. Do not add a remote:

```sh
umask 077
BASELINE="$(mktemp -d)/cmj-m7-clean"
mkdir "$BASELINE"
git archive --format=tar HEAD | tar -xf - -C "$BASELINE"
git -C "$BASELINE" init -b main
git -C "$BASELINE" add -A
git -C "$BASELINE" -c user.name="$APPROVED_AUTHOR_NAME" \
  -c user.email="$APPROVED_AUTHOR_EMAIL" commit -m "Create sanitized public baseline"
test "$(git -C "$BASELINE" rev-parse HEAD^{tree})" = "$(git rev-parse HEAD^{tree})"
git -C "$BASELINE" rev-list --parents --all
```

The tree comparison must pass and the final `rev-list` line must contain one commit ID with no parent. Scan its full reachable history and wheel, and repeat the sealed M0 byte comparison. Do not add a license unless the owner separately selects one. This produces a fresh graph but loses public commit provenance; it does not revoke old clones, caches, or copied refs.

| Approach | Keeps | Changes | Remaining limit |
|---|---|---|---|
| Current-tree fast-forward | Existing history and commit links | Makes the sanitized candidate tree current on `main` | All historical references and paths stay reachable; M7 remains blocked |
| Targeted rewrite | Unaffected project history and most provenance | Rewrites 43 affected commits across the known refs; requires coordinated non-fast-forward updates | External clones and caches can retain old history |
| Clean baseline | Sanitized current files and M0 authority kept privately | Replaces project history with a new root and invalidates old commit links | Loses public provenance; external copies remain |

## Owner decisions still required

1. Select a project license and the author/citation identity for any release metadata.
2. Obtain written rights clearance before proposing any empirical source, derivative, split, comparison, or result summary for redistribution; otherwise keep those materials omitted under the M0 prohibition.
3. Provide exact M0 evidence for the eight unclassified references or leave them unclassified and omitted. No rights are inferred.
4. Choose between current-tree integration, targeted rewrite, or clean baseline, and authorize any eventual public ref update separately. Decide whether to rewrite or retire the legacy branch as part of that action.
5. Coordinate with any external clone owners before history changes; public forks and pull requests were absent from the inventory, but external clones and caches are not enumerable.

M7 remains `BLOCKED`; RES-288 remains `In Progress`; RES-291/M8 remains `Todo` and unstarted. No history rewrite, force-push, public merge, license addition, rights clearance, or v1.0 release was performed.
