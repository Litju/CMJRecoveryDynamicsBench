"""Loopback-only browser qualification with synthetic observations and weights.

Only the first origin receives a source-constructed synthetic basis grant; other
origins retain their refusal path. This script registers no original checkpoint.
"""

import os
from dataclasses import replace

from cmj_recovery_dynamics.model_reproduction.gate7_projection import (
    _public_row_from_camp_input,  # pyright: ignore[reportPrivateUsage]
)
from cmj_recovery_dynamics.observations.native_mechanics import gate7_basis_v1
from cmj_recovery_dynamics.research_lab import (
    BasisGrant,
    ResearchLab,
    _inputs,  # pyright: ignore[reportPrivateUsage]
    fixture_observations,
    row_digest,
    serve,
)


def main() -> None:
    observations = list(fixture_observations())
    for index in (0, 1):
        item = observations[index]
        public = _public_row_from_camp_input(item.builder.build(item.origin_id, item.horizon))
        basis = gate7_basis_v1(public)
        raw, history, horizon = _inputs(item)
        binding = row_digest(
            item.builder.expected_observations_sha256,
            item.origin_id,
            raw,
            history,
            horizon,
            basis,
        )
        observations[index] = replace(
            item, basis=BasisGrant(basis, binding, "source-constructed-synthetic-fixture-v1")
        )
    serve(ResearchLab(tuple(observations)), os.environ["GATE7_LAB_TOKEN"])


if __name__ == "__main__":
    main()
