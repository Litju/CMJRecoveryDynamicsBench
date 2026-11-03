# Public API and safe inference loading

Install from the reviewed checkout in a clean Python environment:

```sh
python3 -m pip install .
# Optional recovered-model runtime:
python3 -m pip install '.[inference]'
python3 -m cmj_recovery_dynamics.studies.fixed_mode_reference_study --help
```

See the [root README](../README.rst) for the supported module entrypoints and
synthetic reproduction commands. Do not substitute a newer package for the
historical frozen M8 study when asserting digest replay.

The recovered loaders live in `model_reproduction.checkpoint_inference` (M0–M6),
`checkpoint_m7`, and `checkpoint_m8_inference`. Use their published signatures;
checkpoint and configuration SHA-256 pins must come from an independently
authenticated authority. Never calculate an unknown file's hash and treat that
same hash as independent authentication. The implementation validates configuration,
state keys, shapes and finite values and loads on CPU with `weights_only=True`.
Do not bypass these checks or switch to unrestricted pickle loading.

Inputs must preserve the same row identities and ordering across raw, history,
horizon and basis tensors. Frozen fitted statistics belong to the authenticated
configuration; do not fit replacements on a new cohort. Outputs are additive
innovations ordered force (N/kg), impulse (m/s), not standardized scores.
Baseline addition is separate. See the [measurement contract](GATE7_NATIVE_MEASUREMENT_V1.md).

A safe loading recipe cannot include publicly unavailable checkpoint paths or
invented trusted hashes. Operators must independently obtain permitted artifacts
and grants. Public synthetic smoke execution verifies wiring, not predictive
accuracy. Empirical evaluation additionally requires native preflight, target
and measurement authority, rights review, and separately authorized offline
execution; see the [offline contract](GATE7_OFFLINE_STUDY_V1.md).

## M0–M8 model family reference

Each family has independent r0/r1 configurations and checkpoints. All 18 routes
have documented CPU source parity. Historical saved-CUDA comparisons passed the
recorded rule for M0–M3 and remain outside tolerance for M4–M8.

| Family | Recovered architecture |
| --- | --- |
| M0 | 39 → 32 → 2; exact GELU |
| M1 | 39 → 64 → 2; exact GELU |
| M2 | 39 → 64 → 64 → 2; exact GELU |
| M3 | Raw backbone + pointwise history encoder; mean/latest pooling → 128 → 2 |
| M4 | Raw backbone + 4 → 32 GRU; mean/latest pooling → 128 → 2 |
| M5 | M4 + 2 × 8 horizon embedding → 136 → 2 |
| M6 | M5 + first two basis values → 16 → 152 → 2 |
| M7 | M5 + all five basis values → 16 → 152 → 2 |
| M8 | M7 + bias-free 5 → 2 linear basis head |

M3 history encoding is pointwise; M4 onward uses a one-layer GRU and mean/latest
pooling. M6 validates five basis inputs but consumes only the first two in its
basis projection. M7 and M8 consume all five. Dropout is disabled for inference.
Raw features use frozen train-only scaling; participant identity is not a raw
feature. See the exact source links in the atlas for implementation details.

The M8 loader contract is:

```python
from pathlib import Path
from cmj_recovery_dynamics.model_reproduction.checkpoint_m8_inference import load_gate7_m8


def load_authorized_pair(
    config: Path,
    checkpoint: Path,
    trusted_config_sha256: str,
    trusted_checkpoint_sha256: str,
    repeat: int,
):
    return load_gate7_m8(
        config,
        checkpoint,
        config_sha256=trusted_config_sha256,
        checkpoint_sha256=trusted_checkpoint_sha256,
        repeat=repeat,  # 0 or 1, independently bound to this exact pair
    )
```

This example defines the safe call shape; it cannot run without independently
provisioned authorized artifacts and authenticated pins. Public synthetic
reproduction commands in the README require no original checkpoint.
