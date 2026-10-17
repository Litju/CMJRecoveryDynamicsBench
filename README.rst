CMJ Recovery Dynamics Bench
===========================

Scientific contracts, synthetic generators, evaluation definitions, and recovered
research lineage for eight countermovement-jump recovery benchmarks.
The canonical repository is https://github.com/Litju/CMJRecoveryDynamicsBench.

Development
-----------

Use Python 3.12 or newer. From the repository root::

    python3.12 -m venv .venv
    .venv/bin/python -m pip install -e '.[dev]'
    .venv/bin/python -m pytest
    .venv/bin/ruff check .
    .venv/bin/ruff format --check .
    .venv/bin/pyright
    git diff --check

Installation resolves the declared dependencies from their upstream package index.
Pyright runs in strict mode. For a distributable wheel::

    .venv/bin/python -m pip wheel --no-deps . --wheel-dir dist

Inspect the scientific identities without historical archives::

    .venv/bin/python -c 'from cmj_recovery_dynamics import BENCHMARK_REGISTRY; print("\n".join(BENCHMARK_REGISTRY))'

Inspect the M1–M6 reproduction matrix and run the public synthetic qualification::

    .venv/bin/python -m cmj_recovery_dynamics.reproducibility.qualification --matrix-only
    .venv/bin/python -m cmj_recovery_dynamics.reproducibility.qualification

The run hashes complete public training and validation row streams and executes
the registered rich-history zero baseline diagnostic. It does not replay
historical score families or establish empirical validation. See
``docs/M8_REPRODUCIBILITY_MATRIX.md`` and ``docs/M8_REPRODUCTION_RESULTS.md``.

Reproducibility and release status
---------------------------------

Tests verify public contracts and supported synthetic behavior. They do not
establish exact replay of historical campaigns or empirical validation.
Reproduction and study registries record exact, partial, unresolved, and
rights-withheld authority separately. Historical evidence, private evaluators,
checkpoints, and restricted empirical data remain external; do not copy them into
this repository or use them to claim public reproducibility.

M7 was administratively closed with a documented, owner-accepted exception for
old GitHub-managed pull-request refs. This exception is not historical or
third-party rights clearance. M8 is in progress; v1.0 has not been released.
Current-tree redaction does not sanitize earlier Git history. See
``docs/M7_PUBLIC_TREE_REDACTION.md``, ``docs/M7_OCCURRENCE_CLASSIFICATION.md``, and
``docs/M7_QUALIFICATION.md`` for the boundaries and outstanding decisions.
The owner confirms original-project code ownership and approves Apache-2.0
for that code, with Julio Rodriguez as sole software author. These decisions
apply to project code only; they do not clear external datasets, restricted
derivatives, retained history, or other third-party materials.

License and citation
--------------------

Copyright 2026 Julio Rodriguez. Original project source code and documentation
are licensed under Apache-2.0; see ``LICENSE``. This license does not cover
external datasets, restricted empirical derivatives, preserved private archives,
or other third-party materials.

Use ``CITATION.cff`` to cite this software. Version ``0.1.0`` remains
pre-release; no DOI, v1.0 publication, or empirical validation is claimed.
