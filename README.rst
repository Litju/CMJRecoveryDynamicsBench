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
----------------------------------

Tests verify public contracts and supported synthetic behavior. They do not
establish exact replay of historical campaigns or empirical validation.
Reproduction and study registries record exact, partial, unresolved, and
rights-withheld authority separately. Historical evidence, private evaluators,
checkpoints, and restricted empirical data remain external; do not copy them into
this repository or use them to claim public reproducibility.

M7 was administratively closed with a documented, owner-accepted exception for
old GitHub-managed pull-request refs. This exception is not historical or
third-party rights clearance. RES-529 records independent release-candidate
qualification; an official GitHub release and matching tag establish publication.
Package metadata alone does not establish whether a release was published.
Current-tree redaction does not sanitize earlier Git history. See
``docs/M7_PUBLIC_TREE_REDACTION.md``, ``docs/M7_OCCURRENCE_CLASSIFICATION.md``, and
``docs/M7_QUALIFICATION.md`` for the boundaries and outstanding decisions.
The owner confirms original-project code ownership and approves Apache-2.0
for that code, with Julio Rodriguez as sole software author. These decisions
apply to project code only; they do not clear external datasets, restricted
derivatives, retained history, or other third-party materials.

Public reference studies
------------------------

Two executable research studies supplement the registered baseline path:
``python -m cmj_recovery_dynamics.studies.reference_model_study`` for retired
rich-history zero/ridge, and
``python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study`` with separate
``pilot``, ``select``, and ``evaluate`` stages for the active fixed-mode candidate.
See ``docs/M8_REFERENCE_MODEL_STUDY.md`` and
``docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md`` for protocols and commands.
The fixed-mode comparison uses three public RNG roots from the same synthetic
world; it establishes neither OOD robustness nor human athlete performance.
Its production scorer remains unimplemented.

The separate native research engineering rehearsal is executable with
``python -m cmj_recovery_dynamics.metrics.native_rehearsal --synthetic-rehearsal``.
It tests native mechanics, dataset admission, four-cell errors, paired participant
uncertainty and locked decisions using invented labels and predictions only.
It does not authorize empirical execution or reproduce historical scores.
See ``docs/GATE7_INTERNAL_RESEARCH_V1.md`` for the schema, steward-side assessment,
measurement specification, basis dependencies and qualification boundaries.

The source distribution includes these protocols, receipts, and citation file.
Wheel users should obtain the matching source distribution for documentation;
all runtime modules are in the wheel. Candidate changes and release limits are
in ``docs/M8_RELEASE_NOTES.md``; independent qualification is recorded in
``docs/M8_V1_RELEASE_AUDIT.md``. Package and citation metadata are synchronized at
``1.0.0``. The candidate qualification recorded in
``docs/M8_V1_PUBLICATION_RECEIPT.json`` is a dated prepublication assessment.
Check the corresponding GitHub release for published files and checksums.

License and citation
--------------------

Copyright 2026 Julio Rodriguez. Original project source code and documentation
are licensed under Apache-2.0; see ``LICENSE``. This license does not cover
external datasets, restricted empirical derivatives, preserved private archives,
or other third-party materials.

Use ``CITATION.cff`` to cite version ``1.0.0``. This metadata does not assert
a DOI, publication date, or empirical validation; the corresponding official
release record, if any, identifies its publication date and artifacts.
Original experiment receipts retain their audited version and provenance.
Exact M8 digest replay uses the original frozen study snapshot. Version metadata
changes the package-source hash, so pre-1.0 selection locks cannot be reused.

Research showcase
-----------------

The interactive research showcase is live at
https://recovery-observatory.vercel.app and its Next.js source, fixtures, and
browser tests are in the separate package at `website/README.md
<website/README.md>`__. The scientific Python package and its tests remain
independent; the site is a synthetic research exhibit, not empirical athlete
validation.
