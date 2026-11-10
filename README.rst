CMJ Recovery Dynamics Bench
===========================

Scientific contracts, synthetic generators, evaluation definitions, and recovered
research lineage for eight countermovement-jump recovery benchmarks.
The canonical repository is https://github.com/Litju/CMJRecoveryDynamicsBench.

Start here
----------

Research paper (current)
    `Full illustrated research manuscript
    <docs/manuscript/v3/full_illustrated_research_manuscript.pdf>`_ — *Retrospective
    reconstruction and numerical qualification of historical countermovement-jump
    recovery research: An evidence-bounded case study*. It is an **unsubmitted
    research draft**: it has not been peer reviewed, submitted to a journal or
    assigned a DOI. The `academic review edition
    <docs/manuscript/v3/academic_review_manuscript.pdf>`_, `technical supplement
    <docs/manuscript/v3/technical_supplement.pdf>`_, `reproducible figures
    <docs/manuscript/v3/figures/>`_ and their `regeneration guide
    <docs/manuscript/v3/README.md>`_ are in the same package.

Interactive companion
    The `Recovery Observatory <https://recovery-observatory.vercel.app>`_ is the
    source-backed interactive research exhibit (``website/``).

Everything else
    ``docs/INDEX.md`` is the single navigation index for the software, public
    synthetic benchmark, recovered model documentation, native biomechanics
    methods, release, citation and limitations. Earlier manuscript packages under
    ``docs/manuscript/`` are preserved as historical evidence only.

The paper's force outcome is the **mean concentric-force innovation (N/kg)**: the
baseline-relative change in gross time-mean concentric force per unit body mass.
Its frozen registered evaluation key keeps the legacy identifier
``relative_peak_mean_force_innovation``; it is not peak force and not net impulse.
No result in this repository establishes real-athlete recovery-forecasting accuracy.

Installation
------------

Use Python 3.12 or newer. From a source checkout, install the core package with
its pinned NumPy runtime dependency::

    python3.12 -m pip install .

The core install includes the synthetic generators, public lineage and evaluation
contracts, native mechanics and projection, and synthetic-only statistical
rehearsal. CPU checkpoint inference, the local inference service, and offline
native-study execution use the optional PyTorch dependency::

    python3.12 -m pip install '.[inference]'

The package contains no recovered model checkpoints or restricted data. Inference
requires independently authenticated and legitimately available model artifacts;
offline study execution additionally requires separately authenticated scientific
and institutional authorization. See ``CHANGELOG.md`` for this release's scope
and public limitations.

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

The earlier public-tree review closed with a documented, owner-accepted exception
for old GitHub-managed pull-request refs. This exception is not historical or
third-party rights clearance. Earlier candidate qualification is a historical
record; the final v1.1.0 source, tag, artifacts and provenance are identified by the
`official GitHub release <https://github.com/Litju/CMJRecoveryDynamicsBench/releases/tag/v1.1.0>`_.
The existing ``v1.0.0`` tag and assets remain unchanged. See ``CHANGELOG.md`` for
the released scope and limitations.
Current-tree redaction does not sanitize earlier Git history. See the historical
public-tree and occurrence-classification records in ``docs/INDEX.md`` for those
boundaries.
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

Gate7 inference and offline study execution
--------------------------------------------

The package provides recovered M0–M8 CPU inference interfaces, including two
repeat routes per model, plus the public observation builder, feature projection,
native force/impulse mechanics and native statistical evaluation. The inference
loaders are in ``cmj_recovery_dynamics.model_reproduction.checkpoint_inference``
(M0–M6), ``checkpoint_m7`` and ``checkpoint_m8_inference``. They require the
``inference`` extra and verify caller-supplied config/checkpoint SHA-256 pins before
weights-only CPU loading. No checkpoint bytes, private hash pins or authorization
records ship in this package.

``cmj_recovery_dynamics.native_study.execute_native_study`` is an offline API, not
a command or network endpoint. It requires all 18 model grants and a separately
authenticated authorization supplied by the responsible operator. Installation,
synthetic fixtures and preflight checks do not grant empirical data access,
checkpoint use, ethics approval or permission to disclose results. The optional
local Research Lab starts with synthetic demonstrations; original-checkpoint use
requires an operator-provisioned private startup script and independently verified
grants. See ``docs/RESEARCH_LAB.md`` and ``docs/GATE7_OFFLINE_STUDY_V1.md``.

The public module entrypoints are::

    python -m cmj_recovery_dynamics.observations.public_builder
    python -m cmj_recovery_dynamics.observations.native_preflight input.json
    python -m cmj_recovery_dynamics.metrics.native_rehearsal --synthetic-rehearsal
    python -m cmj_recovery_dynamics.reproducibility.qualification --matrix-only
    python -m cmj_recovery_dynamics.reproducibility.qualification
    python -m cmj_recovery_dynamics.studies.reference_model_study
    python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study --help

The local Research Lab uses ``python -m cmj_recovery_dynamics.research_lab`` and
requires the ``inference`` extra; its token, private startup procedure and
original-checkpoint controls are documented in ``docs/RESEARCH_LAB.md``. The
fixed-mode CLI requires a full source Git SHA and
the ``pilot`` → ``select`` → ``evaluate`` protocol; selection locks must be created
before evaluation. Its three public roots sample one synthetic world and do not
establish OOD robustness, human-athlete predictive validity or clinical utility.
The production fixed-mode scorer remains unimplemented.

The public tests exercise synthetic checkpoint fixtures and refusal controls. They
do not contain original weights or establish empirical validation. Source-side CPU
inference qualification is distinct from historical CUDA replay: M4–M8 did not
meet the preserved CUDA tolerances. See the `model-family and safe-loading guide
<docs/RESEARCH_API.md>`_. The Windows/NVDA manual
acceptance remains ``SCREEN_READER_ACCEPTANCE_PENDING`` in
``docs/GATE7_NVDA_ACCEPTANCE_V1.md``.

The source distribution includes the reviewed protocols, receipts, ``CHANGELOG.md``
and citation file. Wheel users should obtain the matching source distribution for
documentation; runtime modules are in the wheel. ``docs/M8_RELEASE_NOTES.md`` and
``docs/M8_V1_RELEASE_AUDIT.md`` describe the historical v1.0.0 release and remain
unchanged. The package and citation metadata are synchronized at ``1.1.0``. The
official release page lists the published files and checksums.

License and citation
--------------------

Copyright 2026 Julio Rodriguez. Original project source code and documentation
are licensed under Apache-2.0; see ``LICENSE``. This license does not cover
external datasets, restricted empirical derivatives, preserved private archives,
or other third-party materials.

``CITATION.cff`` identifies version ``1.1.0``; cite the `v1.1.0 GitHub
release <https://github.com/Litju/CMJRecoveryDynamicsBench/releases/tag/v1.1.0>`_.
No DOI is assigned, and this citation does not assert empirical validation.
Original experiment receipts retain their audited version and provenance.
Exact M8 digest replay uses the original frozen study snapshot. Version metadata
changes the package-source hash, so pre-1.0 selection locks cannot be reused.

Research showcase
-----------------

The interactive research showcase is live at
https://recovery-observatory.vercel.app and its Next.js source, fixtures, and
browser tests are in ``website/`` in this monorepo; its deployment is managed
separately from the Python package. A package version change does not itself
require a site deployment. The site is a synthetic research exhibit, not empirical
athlete validation.

Research documentation and presentation
---------------------------------------

The navigable public documentation index is ``docs/INDEX.md``. The Recovery
Observatory includes the public synthetic benchmark explorer, a separate original
model/repeat atlas, native mechanics, assessment windows and an explicit evidence
boundary. Its public contracts are
pinned independently of the historical M8 synthetic receipts. See
``website/docs/SCIENCE_AND_DATA.md`` for figure sources and
``website/docs/GATE7_ATLAS.md`` for the model atlas.
