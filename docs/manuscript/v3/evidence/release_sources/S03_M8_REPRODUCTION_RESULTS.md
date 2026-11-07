# M8 public reproduction results

## Execution

The full run used an isolated Python 3.12.13 CPython environment with the
`0.1.0` wheel installed outside the checkout, NumPy 2.5.3, Linux x86_64, and no
accelerator. It completed in 2,447.53 seconds. The command was:

```text
python -m cmj_recovery_dynamics.reproducibility.qualification
```

To rebuild the wheel and write a receipt after installing it in a fresh
environment, run from the repository root:

```text
uv build --offline --wheel --out-dir wheelhouse .
python3.12 -m venv clean-environment
clean-environment/bin/python -m pip install --no-cache-dir numpy==2.5.3 wheelhouse/cmj_recovery_dynamics-0.1.0-py3-none-any.whl
clean-environment/bin/python -m cmj_recovery_dynamics.reproducibility.qualification > rerun-public-reproduction-receipts.json
```

The machine-readable receipt records the source, configuration, and output
digests; per-split generation-and-hash time and total runtime; clean-room seed
identities; runtime versions; M2 historical row counts; numerical checks; and
registered M1 expected-result values. Its row-output SHA-256 is over ordered UTF-8 compact
JSON rows, one row per line, with object keys sorted. Missing target values are
counted separately; non-finite feature values are encoded as strings for the
row digest, and non-finite target values are reported as a failed numerical
check.

## Public synthetic generation

The hashes below are shortened for the table; the receipt contains full
SHA-256 values. Counts are observed rows / M2 historical rows. A count match
does not establish historical dataset identity; M2 remains partial for every
materialized dataset hash.

| Benchmark | Training rows | Validation rows | Training SHA-256 prefix | Validation SHA-256 prefix | Missing target values (train / validation) |
|---|---:|---:|---|---|---:|
| `initial_preseason_camp_recovery` | 4,096 / 4,096 | 512 / 512 | `012f5c5352e2ea90` | `0f990cd6bfcab06f` | 0 / 0 |
| `canonical_preseason_camp_recovery` | 4,096 / 4,096 | 512 / 512 | `d4106a42092a1322` | `24ffa71ff19fe6a4` | 0 / 0 |
| `rich_history_camp_recovery` | 15,134 / 15,182 | 3,799 / 3,795 | `a5766360d1def715` | `866de852240833cd` | 1,726 / 404 |
| `preliminary_post_exposure_recovery` | 72,000 / 72,000 | 12,000 / 12,000 | `1893b54d5881db27` | `3bcaf565b4c63d17` | 0 / 0 |
| `phase_consistent_post_exposure_recovery` | 72,000 / 72,000 | 12,000 / 12,000 | `e017cff611370f63` | `adc38ae10df8a371` | 0 / 0 |
| `correlated_exposure_recovery` | 72,000 / 72,000 | 12,000 / 12,000 | `d63af7d828613a99` | `9018a50dcffd330d` | 0 / 0 |
| `threshold_response_recovery` | 72,000 / 72,000 | 12,000 / 12,000 | `8a609a27fb1ef8fd` | `c8c67abe14c31108` | 0 / 0 |
| `fixed_mode_discrepancy_recovery` | 72,000 / 72,000 | 12,000 / 12,000 | `b3b6a3d523b8c468` | `d267bffdd3e039fb` | 0 / 0 |

All 16 generated split streams had stable row schemas, exactly two target
slots per row, finite values for every present target, and matching repeated
three-row probes. No target value was non-finite. Fourteen observed row counts
match M2; the two rich-history counts differ because the M8 clean-room roots
generate new horizon membership. The rich-history missing target slots are
preserved and excluded from the diagnostic's cell values.

An initial full pass from the development environment and the fresh wheel run
produced identical SHA-256 hashes for all 16 row streams. Their source and
configuration manifest digests also matched. This verifies the clean install
against the checkout execution; it does not upgrade M2's historical dataset
hash authority.

## Executed model and metric

The registered rich-history zero-innovation baseline ran on the 3,799-row
clean-room public-validation split with the native raw-progress diagnostic.
Its result was **0.0 dimensionless progress**, matching the M1 zero-baseline
value within an absolute tolerance of `1e-12`. The receipt labels this as a
fresh clean-room output compared with historical evidence; M2 dataset-hash
authority is not exact, so this is not an exact historical replay.

No other registered model adapter forms a complete public end-to-end scoring
path on the current projected rows. In particular, the initial OLS feature
projection is absent, the M0 checkpoint is not loaded, and other benchmark
models are result evidence only or unresolved. No production benchmark score
was claimed from those records.

The later fixed-mode reference-study runner is a separate research-only path;
see `M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md`. The adapter limitation above
describes this original qualification, not the availability of that new study.

## Validation and packaging

The implementation was checked with:

```text
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pyright
```

The suite passed 305 tests; Ruff lint and formatting passed; strict Pyright
reported zero errors, warnings, or informations. The original M8 build had 82
wheel entries (78 Python modules and four metadata files). The current licensed
build has 83 entries: 78 Python modules and five distribution files, including
``licenses/LICENSE``. Both include the qualification runner and exclude tests
and documentation. The current wheel installed with NumPy 2.5.3 in an isolated
environment and imported from outside the checkout. This packaging difference
does not change the numerical reproduction; the original reproduction receipt
is preserved unchanged.

The run is synthetic. It does not establish empirical recovery performance or
replay any private result family. Full commands, per-run durations, complete
hashes, M1 expected-result records, and M2–M6 qualification evidence are in
[the machine-readable receipt](M8_PUBLIC_REPRODUCTION_RECEIPTS.json).
