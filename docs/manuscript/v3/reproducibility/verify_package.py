"""Read-only evidence, cross-reference, and artifact checks for M10 V3."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "evidence" / "release_sources"
AUDIT = ROOT / "evidence" / "v2_audit"
REPORTS = ROOT / "reports"
MANUSCRIPT = ROOT / "manuscript.tex"
PRIVATE_MACHINE_PATH = re.compile(
    r"/(?:home|users|root|mnt|tmp|var/tmp)/[^\s'\"<>]+|[A-Z]:\\Users\\[^\s'\"<>]+",
    re.IGNORECASE,
)
PROTECTED_SUFFIXES = {".bin", ".ckpt", ".joblib", ".pkl", ".pt", ".pth", ".safetensors"}
BUILD_DIRECTORIES = {"build", "__pycache__", ".venv", "toolchain"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def csv_load(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, header: list[str], rows: list[list[str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def source_records():
    return json_load(RELEASE / "sources.json")


def source_ref(source_ids, local_paths=()):
    records = {r["source_id"]: r for r in source_records()}
    parts = []
    for source_id in source_ids:
        r = records[source_id]
        parts.append(f'{source_id}:{r["path"]}@{r["commit"]}#sha256={r["sha256"]}')
    for rel in local_paths:
        p = ROOT / rel
        parts.append(f"{rel}#sha256={sha256(p)}")
    return " | ".join(parts)


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def bib_entries():
    path = ROOT / "bibliography" / "references.bib"
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)(?=@[A-Za-z]+\{)", text.strip())
    result = {}
    for block in blocks:
        match = re.match(r"@([A-Za-z]+)\{([^,]+),", block)
        if not match:
            continue
        kind, key = match.group(1).lower(), match.group(2).strip()

        def field(name):
            m = re.search(r"(?m)^\s*" + re.escape(name) + r"\s*=\s*\{(.*)\}\s*,?\s*$", block)
            return m.group(1).strip() if m else ""

        author_match = re.search(r"(?m)^\s*author\s*=\s*\{(.*)\}\s*,?\s*$", block)
        result[key] = {
            "type": kind,
            "title": field("title"),
            "year": field("year"),
            "journal": field("journal"),
            "booktitle": field("booktitle"),
            "pages": field("pages"),
            "doi": field("doi"),
            "url": field("url"),
            "author": author_match.group(1) if author_match else "",
        }
    return result


def verify_bibliography():
    entries = bib_entries()
    metadata = json_load(ROOT / "bibliography" / "verified_metadata.json")
    assert len(entries) == 17, f"Expected 17 BibTeX entries, found {len(entries)}"
    assert {r["id"] for r in metadata} == set(entries)
    main = MANUSCRIPT.read_text(encoding="utf-8")
    cited = set()
    for match in re.finditer(r"\\cite\{([^}]+)\}", main):
        cited.update(k.strip() for k in match.group(1).split(","))
    assert cited == set(entries), f"Uncited or missing references: {sorted(set(entries) ^ cited)}"
    rows = []
    for item in metadata:
        key = item["id"]
        meta = item["metadata"]
        bib = entries[key]
        title = (meta.get("title") or [""])[0]
        venue = (meta.get("container-title") or [""])[0]
        dates = meta.get("issued", {}).get("date-parts") or meta.get("published", {}).get("date-parts") or [[""]]
        year = str(dates[0][0])
        doi = item.get("doi") or meta.get("DOI") or ""
        bib_venue = bib["journal"] or bib["booktitle"]
        title_ok = normalized(bib["title"]) == normalized(title)
        year_ok = not year or bib["year"] == year
        venue_ok = normalized(bib_venue) == normalized(venue)
        doi_ok = (bib["doi"].lower() == doi.lower()) if doi else not bib["doi"]
        names = [a["family"] for a in meta.get("author", [])]
        author_blob = re.sub(r"[^a-z0-9]+", "", bib["author"].lower())
        authors_ok = all(re.sub(r"[^a-z0-9]+", "", n.lower()) in author_blob for n in names)
        if item.get("doi_status", "").startswith("No DOI"):
            doi_ok = not bib["doi"] and bool(bib["url"])
        if key == "R14":
            type_ok = bib["type"] == "inproceedings" and bool(bib["booktitle"]) and not bib["journal"]
        elif key in {"R16", "R17", "R18", "R19", "R20"}:
            type_ok = bib["type"] == "misc"
        else:
            type_ok = bib["type"] == "article"
        assert all([title_ok, year_ok, venue_ok, doi_ok, authors_ok, type_ok]), f"Bibliography mismatch for {key}"
        rows.append(
            [
                key,
                "; ".join(names),
                year,
                title,
                venue,
                str(meta.get("volume", "")),
                str(meta.get("issue", "")),
                str(meta.get("page", "")),
                doi or "No DOI asserted; publisher URL retained",
                "publisher/registry metadata cross-checked; source version and identifier recorded",
            ]
        )
    write_csv(
        REPORTS / "bibliography_verification.csv",
        ["reference_id", "authors", "year", "title", "journal_or_proceedings", "volume", "issue", "pages", "doi_or_status", "verification"],
        rows,
    )
    return len(rows)


def verify_sources():
    records = source_records()
    assert len(records) == 35, f"Expected 35 release-linked source records, got {len(records)}"
    mismatches = []
    for record in records:
        filename = Path(record["staged_path"]).name
        path = RELEASE / filename
        if not path.is_file() or sha256(path) != record["sha256"]:
            mismatches.append(record["source_id"])
    assert not mismatches, f"Release snapshot hash mismatches: {mismatches}"
    return len(records)


def verify_receipt_arithmetic():
    results = json_load(RELEASE / "S01_M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json")
    six_rows = csv_load(AUDIT / "six_cell_results.csv")
    uncertainty_rows = csv_load(AUDIT / "recorded_uncertainty.csv")
    routes = csv_load(AUDIT / "model_identity_sanitized.csv")
    assert len(six_rows) == 24
    assert len(uncertainty_rows) == 6
    assert len(routes) == 18
    for row in six_rows:
        model = row["model"]
        cell = row["cell"]
        stored = results["across_root_variability"][model]["cell_nrmse_across_roots"][cell]
        source_values = stored["root_values"]
        csv_values = [float(row[f"root_{letter.lower()}"]) for letter in "ABC"]
        assert all(math.isclose(a, b, rel_tol=0, abs_tol=1e-14) for a, b in zip(source_values, csv_values, strict=True))
        assert math.isclose(float(row["mean"]), float(stored["root_mean_nrmse"]), rel_tol=0, abs_tol=1e-14)
        assert math.isclose(float(row["sample_sd"]), float(stored["root_sample_sd_nrmse"]), rel_tol=0, abs_tol=1e-14)
    bootstrap_by_root = {}
    for root in results["independent_test_roots"]:
        suffix_match = re.search(r"root-([abc])-", root["data"]["root_seed"])
        assert suffix_match is not None
        suffix = suffix_match.group(1).upper()
        bootstrap_by_root[suffix] = root["paired_camp_bootstrap"]["models"]
    for row in uncertainty_rows:
        source = bootstrap_by_root[row["root"]][row["model"]]
        assert int(row["valid_replicates"]) == source["valid_replicates"]
        for csv_key, source_key, idx in [
            ("nrmse_lower", "mean_six_cell_nrmse_95_percentile_interval", 0),
            ("nrmse_upper", "mean_six_cell_nrmse_95_percentile_interval", 1),
            ("paired_delta_vs_zero_lower", "paired_nrmse_delta_vs_zero_95_percentile_interval", 0),
            ("paired_delta_vs_zero_upper", "paired_nrmse_delta_vs_zero_95_percentile_interval", 1),
        ]:
            assert math.isclose(float(row[csv_key]), source[source_key][idx], rel_tol=0, abs_tol=1e-14)
    cpu = [r for r in routes if r["cpu_source"].startswith("Exact recorded")]
    saved_pass = [r for r in routes if r["saved_cuda"].lower() == "pass"]
    saved_fail = [r for r in routes if r["saved_cuda"].lower() == "fail"]
    assert len(cpu) == 18 and len(saved_pass) == 8 and len(saved_fail) == 10
    assert all(r["inference_rerun"] == "False" for r in routes)
    return {
        "six_cell_rows_checked": len(six_rows),
        "root_aggregate_rows_checked": len(six_rows),
        "stored_bootstrap_rows_checked": len(uncertainty_rows),
        "model_routes": len(routes),
        "cpu_source_exact_records": len(cpu),
        "saved_cuda_pass": len(saved_pass),
        "saved_cuda_fail": len(saved_fail),
        "new_model_execution": False,
        "new_bootstrap": False,
    }


def verify_v2_preserved():
    record_path = ROOT / "evidence" / "v2_preservation_record.json"
    if not record_path.exists():
        return {"available": False, "checked": False}
    record = json_load(record_path)
    workspace = os.environ.get("M10_V2_WORKSPACE")
    if not workspace:
        return {"available": False, "checked": False}
    v2 = Path(workspace)
    if not v2.is_dir():
        return {"available": False, "checked": False}
    inventory = []
    for path in sorted(v2.rglob("*")):
        if path.is_file():
            inventory.append(
                {
                    "path": path.relative_to(v2).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
    payload = json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
    aggregate = hashlib.sha256(payload).hexdigest()
    sums_hash = sha256(v2 / "SHA256SUMS")
    assert len(inventory) == record["file_count_at_v3_kickoff"]
    assert aggregate == record["aggregate_inventory_sha256"]
    assert sums_hash == record["source_SHA256SUMS_sha256"]
    return {"available": True, "checked": True, "files_unchanged": len(inventory)}


def verify_privacy_boundary():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == ROOT / "ARTIFACT_SHA256SUMS":
            continue
        relative = path.relative_to(ROOT)
        if BUILD_DIRECTORIES.intersection(relative.parts):
            continue
        assert path.suffix.lower() not in PROTECTED_SUFFIXES, relative
        if "private" in (part.casefold() for part in relative.parts):
            raise AssertionError(f"Restricted directory in public package: {relative}")
        content = path.read_bytes()
        if b"\0" in content:
            continue
        text = content.decode("utf-8", errors="replace")
        assert PRIVATE_MACHINE_PATH.search(text) is None, relative
        private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
        assert private_key_header not in text, relative
        assert not re.search(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b", text), relative
    return True


def verify_manuscript_crossrefs():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    labels = set(re.findall(r"\\label\{([^}]+)\}", text))
    labels.update(
        [
            "fig:genealogy",
            "fig:workflow",
            "fig:architecture",
            "fig:numerical",
            "fig:chronology",
            "fig:mechanics",
            "fig:performance",
            "fig:uncertainty",
            "fig:ablation",
            "fig:scope",
        ]
    )
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text))
    assert refs <= labels, f"Undefined labels: {sorted(refs - labels)}"
    figure_order = re.findall(r"\\ref\{(fig:[^}]+)\}", text)
    unique_order = list(dict.fromkeys(figure_order))
    expected = [
        "fig:genealogy",
        "fig:workflow",
        "fig:architecture",
        "fig:numerical",
        "fig:chronology",
        "fig:mechanics",
        "fig:performance",
        "fig:uncertainty",
        "fig:ablation",
        "fig:scope",
    ]
    assert unique_order == expected, f"Figure citation order mismatch: {unique_order}"
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.S).group(1)
    assert r"\cite" not in abstract
    abstract_plain = re.sub(r"\\[A-Za-z]+\b(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", abstract)
    word_count = len(re.findall(r"\b[\w'-]+\b", abstract_plain))
    assert word_count <= 300, f"Abstract is {word_count} words"
    assert r"\footnote" not in text
    return {"figure_order": unique_order, "abstract_word_count": word_count, "footnotes": 0}


def generate_ledgers():
    ids = source_records()
    by_id = {r["source_id"]: r for r in ids}

    def refs(source_ids, local_paths=()):
        return source_ref(source_ids, local_paths)

    figure_rows = [
        ("Figure", "1", "Formulation genealogy", ["S17", "S18"], [], "Recorded lineage graph; no quantitative recomputation", "Unknown ancestry remains open."),
        ("Figure", "2", "Public synthetic study sample structure", ["S01", "S02"], [], "Recorded camp, episode, and horizon-row counts by split", "Three evaluation roots share one generator and are not human cohorts."),
        ("Figure", "3", "Original architectures and parameter counts", ["S16", "S24", "S25", "S26"], ["evidence/v2_audit/architecture_qualification.csv"], "Architecture progression and counts copied from the sanitized record", "Parameter count is not an accuracy score; checkpoints excluded."),
        ("Figure", "4", "18-route numerical qualification", ["S06", "S12", "S13", "S14", "S15", "S16"], ["evidence/v2_audit/model_identity_sanitized.csv"], "Matrix of recorded route status and discrepancies", "Not a fresh inference or GPU replay; two outputs have different units."),
        ("Figure", "5", "Native and synthetic horizon chronology", ["S02", "S09", "S16"], [], "Time windows drawn from recorded contracts", "No athlete measurement events are plotted; synthetic horizons are separate."),
        ("Figure", "6", "Analytical force-time mechanics", ["S09", "S21"], [], "Piecewise analytical signal generated in the figure script", "Illustration only; not empirical athlete data."),
        ("Figure", "7", "Public six-cell synthetic benchmark", ["S01", "S23"], ["evidence/v2_audit/six_cell_results.csv"], "Root points and stored means copied from receipts", "Three roots share one generator; force and impulse are separate cells."),
        ("Figure", "8", "Recorded bootstrap intervals", ["S01"], ["evidence/v2_audit/recorded_uncertainty.csv"], "Stored point values and percentile endpoints copied from receipts", "Conditional within-root intervals only; no ridge-versus-structured interval."),
        ("Figure", "9", "Ablations and nested camp counts", ["S01"], [], "Stored root-level scores and means copied from receipt", "Diagnostic comparisons, not causal attribution or human sample efficiency."),
        ("Figure", "10", "Rich-history materialization row-count differences", ["S03", "S04"], [], "Clean-room minus historical row counts by split", "Recorded membership differences, not response effects or uncertainty intervals."),
        ("Table", "1", "Architecture and parameter counts", ["S16", "S24", "S25", "S26"], ["evidence/v2_audit/architecture_qualification.csv"], "Sanitized architecture record copied and condensed", "Original weights and config identities remain private."),
        ("Table", "2", "Six-cell NRMSE by reference model", ["S01", "S23"], ["evidence/v2_audit/six_cell_results.csv"], "Stored cell means and root sample SDs copied from receipt", "Three-root descriptive variation; no formal cross-model test."),
        ("Table", "3", "Overall six-cell summary", ["S01"], [], "Stored overall root means and sample SDs copied from receipt", "Root SD is not a confidence interval."),
    ]
    rows = []
    for kind, number, title, source_ids, local_paths, method, limit in figure_rows:
        source_text = refs(source_ids, local_paths)
        exports = (
            " | ".join(f"figures/Fig{number}{ext}" for ext in [".pdf", ".svg", ".png", ".tif"])
            if kind == "Figure"
            else "Embedded LaTeX table; full precision retained in evidence CSV."
        )
        rows.append(
            [
                kind,
                number,
                title,
                exports,
                source_text,
                "figure_source/generate_figures.py" if kind == "Figure" else "manuscript.tex / supplement table generator",
                sha256(ROOT / "figure_source" / "generate_figures.py") if kind == "Figure" else "",
                method,
                limit,
            ]
        )
    write_csv(
        REPORTS / "figure_provenance_ledger.csv",
        ["asset_type", "number", "title", "export_files", "source_file_ids_and_sha256", "generation_source", "generation_source_sha256", "method", "limitation"],
        rows,
    )

    claim_rows = [
        ("C01", "Methods", "Scientific software is anchored to v1.1.0 / immutable source commit 401f87aad1e4ef4108011fa0c1d769a24f1ad329.", "verified_public_source", ["S19", "S20", "S27"], [], "Software identity only; M8 historical experiment keeps its own source manifest."),
        ("C02", "Methods", "The archive contains eight scientific formulations with only recorded parent links shown.", "verified_public_source", ["S17", "S18"], [], "Three parent relationships remain unresolved."),
        ("C03", "Methods", "The Gate7 inventory contains nine neural families M0–M8 with two repeats each.", "privately_qualified_sanitized_summary", ["S16"], ["evidence/v2_audit/architecture_qualification.csv"], "No private checkpoint bytes or identities are included."),
        ("C04", "Methods", "Architecture parameter counts range from 1,346 to 10,796.", "privately_qualified_sanitized_summary", ["S16"], ["evidence/v2_audit/architecture_qualification.csv"], "Counts describe topology, not predictive accuracy."),
        ("C05", "Methods", "Native assessment is the arithmetic mean of three valid trials; baseline uses the two latest qualifying assessments in −240 to −24 hours.", "verified_public_source", ["S09", "S21"], [], "Event detection and measurement authority remain separate."),
        ("C06", "Methods", "Native target windows are H72 66–78 hours and D7 156–180 hours.", "verified_public_source", ["S09", "S16"], [], "No empirical event windows are evaluated in this manuscript."),
        ("C07", "Methods", "Native force and impulse units are N/kg and m/s, respectively.", "verified_public_source", ["S09", "S21", "S22"], [], "Physical units are never pooled in the native analysis."),
        ("C08", "Methods", "All 18 routes have recorded exact original-source CPU output equality.", "privately_qualified_sanitized_summary", ["S06", "S12", "S13", "S14", "S15", "S16"], ["evidence/v2_audit/model_identity_sanitized.csv"], "Receipt-backed; inference was not rerun for V3."),
        ("C09", "Results", "M0–M3 pass and M4–M8 fail the saved historical CUDA elementwise tolerance for both repeats.", "privately_qualified_sanitized_summary", ["S06", "S12", "S13", "S14", "S15", "S16"], ["evidence/v2_audit/model_identity_sanitized.csv"], "No historical GPU replay or cause attribution is claimed."),
        ("C10", "Results", "The saved-CUDA acceptance rule is |a−b| ≤ 10⁻⁵ + 10⁻⁴|b|.", "verified_public_source", ["S06", "S16"], [], "Threshold was not changed after observing failures."),
        ("C11", "Results", "M8-r0 and M8-r1 have stored maximum absolute discrepancies 0.00022125244140625 and 0.00030422210693359375, with 98 and 145 failing elements.", "privately_qualified_sanitized_summary", ["S16"], ["evidence/v2_audit/model_identity_sanitized.csv"], "Pooled maximum combines outputs with different units."),
        ("C12", "Methods", "Public synthetic study contains 96 training camps, 16 development camps, and three 16-camp evaluation roots.", "verified_public_receipt", ["S01", "S02", "S23"], [], "All roots are from the same generator and are not human cohorts."),
        ("C13", "Methods", "Public predictor schema has 82 source fields and 84 encoded numeric features.", "verified_public_receipt", ["S01", "S02", "S23"], [], "Grouping keys, labels, and oracle states are excluded."),
        ("C14", "Methods", "The public benchmark compares zero innovation, training mean, ridge, and structured models across H24/H48/H72 and two outcomes.", "verified_public_receipt", ["S01", "S02", "S23"], [], "Separate from original native H72/D7 model routes."),
        ("C15", "Results", "Mean six-cell NRMSE is 0.736270 ridge, 0.773316 structured, 1.036038 training mean, and 2.430659 zero innovation.", "verified_public_receipt", ["S01", "S23"], ["evidence/v2_audit/six_cell_results.csv"], "Descriptive mean across three roots; no formal ridge-vs-structured inference."),
        ("C16", "Results", "Root-level variation is the sample SD across three public evaluation roots.", "verified_public_receipt", ["S01", "S23"], ["evidence/v2_audit/six_cell_results.csv"], "Not a confidence interval or a human-population uncertainty estimate."),
        ("C17", "Methods", "Recorded bootstrap uses 5,000 paired camp resamples of 16 camps per root with PCG64 seed 49,505,000.", "verified_public_receipt", ["S01", "S23"], ["evidence/v2_audit/recorded_uncertainty.csv"], "Each camp retains its 250 episodes and three horizon queries."),
        ("C18", "Results", "No ridge-versus-structured bootstrap interval is recorded.", "verified_public_receipt", ["S01", "S23"], ["evidence/v2_audit/recorded_uncertainty.csv"], "Marginal intervals are not combined into an unrecorded comparison."),
        ("C19", "Results", "Ridge ablation mean scores are 0.819681 without prior history, 0.867735 without current exposure, and 0.736346 without participant context.", "verified_public_receipt", ["S01", "S23"], [], "Ablations do not identify causal feature importance."),
        ("C20", "Results", "Nested 24/48/96-camp full-ridge scores are 0.736889, 0.736602, and 0.736270.", "verified_public_receipt", ["S01", "S23"], [], "Full-data-selected alpha was held fixed; generator-conditional only."),
        ("C21", "Results", "Rich-history training rows differ by 48 and validation rows by 4 between clean-room and historical records.", "verified_public_receipt", ["S03", "S04"], [], "Documented horizon-membership differences, not a response effect."),
        ("C22", "Discussion", "The article reports no new training, fitting, checkpoint inference, athlete-data acquisition, or empirical scoring.", "verified_artifact_scope", ["S05", "S06"], ["evidence/v2_audit/research_integrity.md"], "Figures regenerate from receipts and sanitized summaries only."),
        ("C23", "Limitations", "Athlete predictive validity, clinical utility, transportability, and production readiness are not established.", "explicit_nonclaim", ["S04", "S05"], ["evidence/v2_audit/research_integrity.md"], "No human cohort or independent validation is available in this evidence package."),
        ("C24", "Availability", "Original fitted checkpoints and restricted scientific records are not redistributed.", "rights_boundary", ["S20", "S27"], ["evidence/v2_audit/model_identity_sanitized.csv"], "Public source license does not grant checkpoint or record redistribution rights."),
        ("C25", "Methods", "The force-time curve in Fig. 6 is generated from an explicit piecewise equation and is not athlete data.", "analytical_illustration", ["S21"], ["figure_source/generate_figures.py"], "A methodological illustration only."),
    ]
    rows = []
    for cid, section, claim, status, source_ids, local_paths, limit in claim_rows:
        rows.append([cid, section, claim, status, refs(source_ids, local_paths), limit])
    write_csv(
        REPORTS / "claims_verification_register.csv",
        ["claim_id", "article_section", "claim", "evidence_status", "authoritative_source_and_sha256", "limitation"],
        rows,
    )
    write_csv(
        REPORTS / "source_to_claim_matrix.csv",
        ["claim_id", "article_section", "claim", "source_ids", "source_paths_and_sha256", "limitation"],
        [[r[0], r[1], r[2], r[4], r[4], r[5]] for r in rows],
    )


def verify_manuscript():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    entries = bib_entries()
    cited = set()
    for match in re.finditer(r"\\cite\{([^}]+)\}", text):
        cited.update(k.strip() for k in match.group(1).split(","))
    assert cited == set(entries), f"Citations and bibliography differ: {sorted(cited ^ set(entries))}"
    declared = set(re.findall(r"\\label\{([^}]+)\}", text))
    declared.update(
        [
            "fig:genealogy",
            "fig:workflow",
            "fig:architecture",
            "fig:numerical",
            "fig:chronology",
            "fig:mechanics",
            "fig:performance",
            "fig:uncertainty",
            "fig:ablation",
            "fig:scope",
        ]
    )
    referenced = {
        label
        for label in re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text)
        if not label.startswith("#")
    }
    assert referenced <= declared, f"Undefined cross references: {sorted(referenced - declared)}"
    figure_order = list(dict.fromkeys(re.findall(r"\\ref\{(fig:[^}]+)\}", text)))
    assert figure_order == [
        "fig:genealogy",
        "fig:workflow",
        "fig:architecture",
        "fig:numerical",
        "fig:chronology",
        "fig:mechanics",
        "fig:performance",
        "fig:uncertainty",
        "fig:ablation",
        "fig:scope",
    ], f"Figure citation order is {figure_order}"
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.S).group(1)
    assert r"\cite" not in abstract
    plain = re.sub(r"\\[A-Za-z]+\b(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", abstract)
    word_count = len(re.findall(r"\b[\w'-]+\b", plain))
    assert word_count <= 300
    assert r"\footnote" not in text
    return {"abstract_words": word_count, "citations": len(cited), "figures_in_order": figure_order}


def verify_private_boundary():
    return verify_privacy_boundary()


def verify_differential_claims_audit():
    claim_path = REPORTS / "claims_differential_audit.csv"
    summary_path = REPORTS / "claims_differential_audit_summary.json"
    claims = csv_load(claim_path)
    summary = json_load(summary_path)
    required = {
        "claim_id",
        "unit_type",
        "manuscript_location",
        "exact_statement",
        "supporting_source_id_path",
        "source_commit_or_version",
        "source_sha256",
        "manuscript_source_sha256",
        "evidence_level",
        "public_reproducibility_status",
        "qualification_or_limitation",
        "verification_decision",
        "differential_status",
    }
    assert claims and required <= set(claims[0]), f"Incomplete claims audit columns: {sorted(required - set(claims[0]))}"
    assert len({r["claim_id"] for r in claims}) == len(claims), "Duplicate stable claim IDs"
    assert len(claims) > 25, "Differential audit must exceed the high-level summary register"
    assert all(all(r[k].strip() for k in required) for r in claims), "Blank claim-audit field"
    assert all(re.fullmatch(r"[0-9a-f]{64}", r["manuscript_source_sha256"]) for r in claims)
    assert all(r["manuscript_source_sha256"] == sha256(MANUSCRIPT) for r in claims)
    assert all(re.search(r"(?:=|#sha256=)[0-9a-f]{64}", r["source_sha256"]) for r in claims)
    current = [r for r in claims if r["unit_type"] != "removed_historical_claim"]
    legacy = csv_load(RELEASE / "claims.csv")
    assert len(legacy) == summary["v2_historical_audit_rows_preserved"] == 553
    assert sha256(RELEASE / "claims.csv") == summary["v2_historical_audit_sha256"]
    expected_status = summary["differential_status_counts"]
    actual_status = {}
    for row in claims:
        actual_status[row["differential_status"]] = actual_status.get(row["differential_status"], 0) + 1
    assert actual_status == expected_status
    assert len(current) == summary["current_v3_claim_units"]
    substantive = [r for r in current if r["unit_type"] != "author_or_ai_disclosure"]
    disclosures = [r for r in current if r["unit_type"] == "author_or_ai_disclosure"]
    assert len(substantive) == summary["substantive_current_claim_units"]
    assert len(disclosures) == summary["administrative_disclosures"]
    return {
        "current_claim_units": len(current),
        "substantive_claim_units": len(substantive),
        "administrative_disclosures": len(disclosures),
        "differential_status_counts": actual_status,
        "historical_v2_rows_preserved": len(legacy),
        "historical_v2_sha256_verified": True,
        "independent_human_review": False,
    }


def post_build_check():
    pdfs = [
        ROOT / "academic_review_manuscript.pdf",
        ROOT / "full_illustrated_research_manuscript.pdf",
        ROOT / "technical_supplement.pdf",
    ]
    for path in pdfs:
        assert path.is_file() and path.stat().st_size > 10000, f"Missing or unexpectedly small PDF: {path.name}"
    logs = [
        ROOT / "build" / "academic_review" / "manuscript-review.log",
        ROOT / "build" / "full_illustrated" / "manuscript.log",
        ROOT / "build" / "technical_supplement" / "technical_supplement.log",
    ]
    overfull = {path.name: [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if "Overfull \\hbox" in line] for path in logs}
    assert not any(overfull.values()), f"Overfull boxes remain: {overfull}"
    fig_stems = [
        "Fig1",
        "Fig2",
        "Fig3",
        "Fig4",
        "Fig5",
        "Fig6",
        "Fig7",
        "Fig8",
        "Fig9",
        "Fig10",
    ]
    for stem in fig_stems:
        for ext in [".pdf", ".svg", ".png", ".tif"]:
            path = ROOT / "figures" / f"{stem}{ext}"
            assert path.is_file() and path.stat().st_size > 1000, f"Missing/invalid export {path}"
        tif = ROOT / "figures" / f"{stem}.tif"
        with Image.open(tif) as image:
            assert image.mode == "RGB", f"{tif.name} must be flattened RGB"
            assert image.info.get("dpi") == (600.0, 600.0), f"{tif.name} must be 600 dpi"
            assert image.info.get("compression") == "tiff_lzw", f"{tif.name} must use LZW compression"
            width_at_300dpi = image.width / 2
            height_at_300dpi = image.height / 2
            assert 789 <= width_at_300dpi <= 2250, f"{tif.name} has an unsupported width"
            assert height_at_300dpi <= 2625, f"{tif.name} is taller than one page"
            assert tif.stat().st_size < 10 * 1024 * 1024, f"{tif.name} exceeds the PLOS 10 MB limit"
    full_pdf = fitz.open(ROOT / "full_illustrated_research_manuscript.pdf")
    figure_pages = {}
    for page_number, page in enumerate(full_pdf, start=1):
        text = page.get_text("text")
        for figure_number in range(1, 11):
            if re.search(rf"Fig\.?\s*{figure_number}\.", text):
                assert page.get_drawings() or page.get_images(full=True), f"Fig. {figure_number} has a caption but no embedded graphic on page {page_number}"
                figure_pages[figure_number] = page_number
    full_pdf.close()
    assert set(figure_pages) == set(range(1, 11)), f"Missing embedded figures in primary manuscript: {sorted(set(range(1, 11)) - set(figure_pages))}"
    receipts = sorted((ROOT / "reproducibility" / "figure_receipts").glob("Fig*.json"))
    assert len(receipts) == 9, f"Expected 9 quantitative figure receipts, found {len(receipts)}"
    for receipt_path in receipts:
        receipt = json_load(receipt_path)
        assert receipt["numerical_test"]["passed"]
        assert receipt["figure_pdf_sha256"] == sha256(ROOT / "figures" / f"{receipt['figure']}.pdf")
    for render in ["academic_review", "full_illustrated", "technical_supplement"]:
        pages = list((ROOT / "renders" / render).glob("page-*.png"))
        assert pages, f"No rendered pages found for {render}"
    return {"pdfs": [p.name for p in pdfs], "figures": 10, "quantitative_figure_receipts": len(receipts), "primary_figure_pages": figure_pages, "page_render_sets": 3}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-build", action="store_true")
    parser.add_argument("--post-build", action="store_true")
    args = parser.parse_args()
    if not args.pre_build and not args.post_build:
        args.pre_build = True
    REPORTS.mkdir(exist_ok=True)
    generate_ledgers()
    source_count = verify_sources()
    receipt = verify_receipt_arithmetic()
    bibliography_count = verify_bibliography()
    manuscript = verify_manuscript()
    privacy = verify_private_boundary()
    claims_audit = verify_differential_claims_audit()
    v2 = verify_v2_preserved()
    build = post_build_check() if args.post_build else {}
    result = {
        "release_source_records_hash_verified": source_count,
        "receipt_arithmetic_checks": receipt,
        "bibliography_entries_verified": bibliography_count,
        "manuscript_checks": manuscript,
        "private_boundary": privacy,
        "claims_differential_audit": claims_audit,
        "v2_preservation": v2,
        "build_outputs": build,
    }
    (REPORTS / "package_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
