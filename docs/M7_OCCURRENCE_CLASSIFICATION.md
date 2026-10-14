# M7 historical occurrence classification

## Scope and decision rule

This report adjudicates the 28 distinct SHA-1 object references and 19 machine-path findings recorded by the M7 baseline scan. The `OBJ-##` and `PATH-##` labels below are report aliases; raw object identifiers, machine paths, and scan fingerprints are not repeated here.

The 28 values are hash-shaped SHA-1 strings in historical commit/tree reference fields. Classification is based on M0 crosswalk evidence and object lookup, not the pattern alone. Fifteen have an exact M0 commit/tree crosswalk; five more occur in source rows classified `PRIVATE_ARCHIVE_ONLY` but lack an exact object-reference match; eight have no exact M0 classification. A private-archive label does not prove that an individual identifier is secret or grant permission to publish it. None of the 28 values resolves to an object in the currently available public Git object database. The M0 exact-byte fingerprint check is a separate result and does not classify these references.

The object aliases follow the order of the unique SHA-1 rows in the sealed M7 reference review. “Entry locations” are paths in the starting tree. “History paths” is the baseline count of distinct reachable historical paths containing that reference.

## Distinct object-reference inventory

| ID | M0 crosswalk / publication class | Entry locations | History paths | Decision |
|---|---|---|---:|---|
| OBJ-01 | `M0_REACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/registry.py` | 2 | Remove from public tree |
| OBJ-02 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_rich_history.py` | 3 | Remove from public tree; no rights inferred |
| OBJ-03 | `M0_UNREACHABLE_COMMIT` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/single_exposure.py`; `tests/test_single_exposure.py` | 3 | Remove from public tree |
| OBJ-04 | `M0_UNREACHABLE_COMMIT` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/later_single_exposure.py`; `study_reconstruction/registry.py`; `tests/test_later_single_exposure.py` | 4 | Remove from public tree |
| OBJ-05 | `NO_EXACT_M0_GIT_REF_MATCH` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/single_exposure.py`; `tests/test_single_exposure.py` | 3 | Remove from public tree |
| OBJ-06 | `M0_REACHABLE_COMMIT` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py` | 1 | Remove from public tree |
| OBJ-07 | `M0_UNREACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/single_exposure.py`; `tests/test_single_exposure.py` | 3 | Remove from public tree |
| OBJ-08 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `provenance/historical_aliases.py` | 1 | Remove from public tree; no rights inferred |
| OBJ-09 | `NO_EXACT_M0_GIT_REF_MATCH` / `PRIVATE_ARCHIVE_ONLY` | `study_reconstruction/registry.py`; `tests/test_study_reconstruction.py` | 2 | Remove from public tree |
| OBJ-10 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_rich_history.py` | 3 | Remove from public tree; no rights inferred |
| OBJ-11 | `M0_UNREACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/single_exposure.py`; `tests/test_single_exposure.py` | 3 | Remove from public tree |
| OBJ-12 | `M0_UNREACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `study_reconstruction/registry.py` | 1 | Remove from public tree |
| OBJ-13 | `M0_UNREACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_rich_history.py` | 3 | Remove from public tree |
| OBJ-14 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_rich_history.py` | 3 | Remove from public tree; no rights inferred |
| OBJ-15 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `model_reproduction/registry.py` | 1 | Remove from public tree; no rights inferred |
| OBJ-16 | `M0_REACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/later_single_exposure.py`; `tests/test_later_single_exposure.py` | 3 | Remove from public tree |
| OBJ-17 | `M0_REACHABLE_COMMIT` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/later_single_exposure.py`; `tests/test_later_single_exposure.py` | 3 | Remove from public tree |
| OBJ-18 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `model_reproduction/registry.py` | 1 | Remove from public tree; no rights inferred |
| OBJ-19 | `NO_EXACT_M0_GIT_REF_MATCH` / `PRIVATE_ARCHIVE_ONLY` | `study_reconstruction/registry.py` | 1 | Remove from public tree |
| OBJ-20 | `M0_REACHABLE_COMMIT` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_rich_history.py` | 4 | Remove from public tree |
| OBJ-21 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_d04_membership.py`; `tests/test_rich_history.py` | 4 | Remove from public tree; no rights inferred |
| OBJ-22 | `M0_UNREACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py` | 1 | Remove from public tree |
| OBJ-23 | `NO_EXACT_M0_GIT_REF_MATCH` / `NO_EXACT_M0_CLASSIFICATION` | `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_rich_history.py` | 3 | Remove from public tree; no rights inferred |
| OBJ-24 | `M0_UNREACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/later_single_exposure.py`; `study_reconstruction/registry.py`; `tests/test_later_single_exposure.py` | 4 | Remove from public tree |
| OBJ-25 | `NO_EXACT_M0_GIT_REF_MATCH` / `PRIVATE_ARCHIVE_ONLY` | `study_reconstruction/registry.py`; `tests/test_study_reconstruction.py` | 2 | Remove from public tree |
| OBJ-26 | `NO_EXACT_M0_GIT_REF_MATCH` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/single_exposure.py`; `tests/test_single_exposure.py` | 3 | Remove from public tree |
| OBJ-27 | `M0_UNREACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/single_exposure.py`; `tests/test_single_exposure.py` | 3 | Remove from public tree |
| OBJ-28 | `M0_REACHABLE_TASK_TREE` / `PRIVATE_ARCHIVE_ONLY` | `provenance/historical_aliases.py`; `reproduction/registry.py`; `reproduction/rich_history.py`; `tests/test_rich_history.py` | 4 | Remove from public tree |

The inventory has 15 exact private commit/tree crosswalks, five file-context `PRIVATE_ARCHIVE_ONLY` classifications without exact object identity, and eight references without an exact M0 classification. All 28 were removed from current source/tests, including source and test assertions that repeated them. A current-tree assertion now rejects 40-character SHA-1 references. Earlier public blobs remain reachable; no history rewrite was performed.

## Eight paired commit/tree findings

These pair rows group object references already represented in the 28-reference inventory. M0 classifies each pair as `PRIVATE_ARCHIVE_ONLY`; the decision is `REMOVE_FROM_PUBLIC_TREE` for every pair. The pair fields were removed from `HistoricalAlias`; scientific aliases remain.

| Pair | Benchmark record | M0 commit crosswalk | M0 tree crosswalk | Decision |
|---|---|---|---|---|
| PAIR-01 | `initial_preseason_camp_recovery` | `M0_REACHABLE_COMMIT` | `M0_REACHABLE_TASK_TREE` | Remove from public tree |
| PAIR-02 | `canonical_preseason_camp_recovery` | `NO_EXACT_M0_COMMIT_MATCH` | `M0_UNREACHABLE_TASK_TREE` | Remove from public tree |
| PAIR-03 | `rich_history_camp_recovery` | `M0_REACHABLE_COMMIT` | `M0_REACHABLE_TASK_TREE` | Remove from public tree |
| PAIR-04 | `preliminary_post_exposure_recovery` | `NO_EXACT_M0_COMMIT_MATCH` | `M0_UNREACHABLE_TASK_TREE` | Remove from public tree |
| PAIR-05 | `phase_consistent_post_exposure_recovery` | `M0_UNREACHABLE_COMMIT` | `M0_UNREACHABLE_TASK_TREE` | Remove from public tree |
| PAIR-06 | `correlated_exposure_recovery` | `NO_EXACT_M0_COMMIT_MATCH` | `M0_UNREACHABLE_TASK_TREE` | Remove from public tree |
| PAIR-07 | `threshold_response_recovery` | `M0_UNREACHABLE_COMMIT` | `M0_UNREACHABLE_TASK_TREE` | Remove from public tree |
| PAIR-08 | `fixed_mode_discrepancy_recovery` | `M0_REACHABLE_COMMIT` | `M0_REACHABLE_TASK_TREE` | Remove from public tree |

## Nineteen historical machine-path findings

Each row below is one M7 `PRIVATE_ABSOLUTE_PATH` occurrence in a reachable historical blob. The finding is a real machine-local path string, not a synthetic path fixture. Its value is intentionally withheld.

| ID | Historical repository file | Classification | Decision |
|---|---|---|---|
| PATH-01 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-02 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-03 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-04 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-05 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-06 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-07 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-08 | `src/cmj_recovery_dynamics/reproducibility/contracts.py` | Private absolute path in historical blob | History remediation required |
| PATH-09 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-10 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-11 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-12 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-13 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-14 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-15 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-16 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-17 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-18 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |
| PATH-19 | `tests/test_reproducibility_core.py` | Private absolute path in historical blob | History remediation required |

The path scan separately adjudicated three malformed `example.org` URL parser fixtures as synthetic negative tests. They contain no private host, credential, or payload and are retained. Existing public Git author/committer account metadata is also classified separately from a private machine path; the public GitHub account `Litju` is allowed by the revised checks.

## History-remediation decision matrix

| Finding class | Current-tree action | Historical action | Status |
|---|---|---|---|
| Eight commit/tree pairs | Remove both object-reference fields from the alias record | Rewrite only if the owner authorizes it | Current tree complete; history unchanged |
| Twenty-eight SHA-1 object references | Remove from source, registries, and tests | Rewrite only if the owner authorizes it | Current tree complete; history unchanged |
| Nineteen private absolute-path occurrences | Keep current tree free of such paths | Rewrite affected historical blobs only with owner approval | Current tree scan clean; history unchanged |
| Three malformed URL fixtures | Retain as synthetic parser-negative fixtures | No history action | Adjudicated false positives |
| Public GitHub account metadata | Permit the exact public account identity | No history action | Not private machine provenance |
| M0 protected payload bytes | No exact byte matches were reported at baseline; recheck recorded in qualification evidence | No payload removal indicated by this check | Exact-byte result reported separately |

## Conditional history-rewrite impact

No rewrite, force-push, merge, or release action was taken. The starting public history contained 37 reachable commits. At the remediation-branch scan, the complete ref set contained 40 reachable commits and 232 unique blobs. The earliest affected commit is the second commit in oldest-first topology, titled `feat: implement scientific benchmark contracts`.

If the owner later authorizes removal from every current ref, changing that early tree would change every descendant commit identifier: 36 commits on `main`, 22 on the older `tmp/res393-registry-gate` ref, and 39 on this remediation branch at the time of the scan. The refs overlap; the unique affected descendant set is 39 commits. GitHub commit links and clones based on those descendants would need reconciliation, and updating `main` would require a coordinated non-fast-forward push. These counts are as of the impact scan, before the later style-only and evidence-report commits. The refreshed counts and remote inventory below supersede this estimate. No rewrite is authorized by this report.

## Follow-up sensitivity adjudication

The post-appendix replay checked each historical reference against the current Git object database. None resolves to an object reachable from the currently available local or origin-tracking refs. The 15 exact M0 matches identify commit/tree objects in the private archive; the five file-level `PRIVATE_ARCHIVE_ONLY` classifications do not establish an exact identity for the reference itself; and the remaining eight stay unclassified. These strings are historical provenance identifiers, not evidence that protected file bytes are present. Their continued presence in reachable history is still uncleared under M0, so they remain rewrite candidates. The zero-match byte check does not clear them.

The 19 `PRIVATE_ABSOLUTE_PATH` findings are 11 distinct hard-coded local path values across 18 historical findings in `tests/test_reproducibility_core.py` and one in `src/cmj_recovery_dynamics/reproducibility/contracts.py`. Context review classifies them as workstation/workspace locators, including home and temporary-directory paths. Some carry the public repository account label; the path layout is the sensitive part. No credential, private key, or private URL was associated with these path findings. They do not disclose dataset bytes, but they reveal local environment structure and remain historical disclosure findings until an authorized rewrite removes them.

The current candidate tree has no absolute-path, credential, private-key, private-URL, or 40-character object-reference finding. Current account-label matches are the already-public repository identity, and the malformed URL hit is an intentional parser-negative fixture. These are adjudicated separately from the historical path and reference findings.

## Recovery severity assessment

The restricted empirical summaries in earlier source versions are the substantive
rights blocker: M0 prohibits their redistribution, even though no preserved payload
bytes match exactly. The earlier literal rewrite left these ancestor versions
reachable in nine source files; its clean reference/path scan was incomplete for
rights qualification.

The workstation paths reveal local directory layout but have no associated
credential, private key, private service address, or restricted data content in the
reviewed context. Treat them as low-severity provenance hygiene, not proof of an
operational compromise or a sufficient reason to discard scientific ancestry.
Opaque object identifiers likewise are not private object payloads; 15 have exact
private crosswalks, five have only file-context classification, and eight remain
unknown. They stay omitted at HEAD without inventing a rights determination.
Synthetic malformed-URL fixtures and the public account identity need no remedy.
Any historical change remains an owner decision; prioritize binding empirical
rights restrictions over benign pattern findings.
