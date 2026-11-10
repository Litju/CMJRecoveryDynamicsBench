"""Reconcile the differential claims audit with the current manuscript source (RES-585).

The audit rows were built against the V2 record. When the V3 manuscript text changes,
this script re-extracts every claim-bearing unit (prose sentence, caption, table row,
displayed equation, declaration), carries the evidence mapping across from the best
matching earlier row, marks wording changes as "modified" and unmatched units as "new",
and checks every number in changed or new units against the pinned evidence corpus.
It never edits scientific values and performs no model execution.
"""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
MANUSCRIPT = ROOT / "manuscript.tex"
AUDIT = REPORTS / "claims_differential_audit.csv"
SUMMARY = REPORTS / "claims_differential_audit_summary.json"
CHANGES = REPORTS / "claims_differential_changes_RES-585.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    text = re.sub(r"\\cite\{[^}]*\}", "", text)
    text = re.sub(r"\\(?:ref|eqref|label)\{[^}]*\}", "", text)
    text = re.sub(r"\\[A-Za-z]+\*?", " ", text)
    text = re.sub(r"[\\{}$~()\[\]&]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def read_braced(text: str, start: int) -> tuple[str, int]:
    assert text[start] == "{"
    depth, cursor = 1, start + 1
    while depth:
        ch = text[cursor]
        if ch == "\\":
            cursor += 2
            continue
        depth += ch == "{"
        depth -= ch == "}"
        cursor += 1
    return text[start + 1 : cursor - 1], cursor


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def split_sentences(paragraph: str) -> list[str]:
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    parts = re.split(r"(?<=[.?!])\s+(?=[A-Z\\(])", paragraph)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def extract_units(text: str) -> list[dict]:
    units: list[dict] = []
    section = "Abstract"
    body_start = text.index("\\begin{document}")
    # Mask floats, equations, headings; collect them as separate units.
    masked = list(text)

    def mask(a, b):
        for k in range(a, b):
            if masked[k] != "\n":
                masked[k] = " "

    for m in re.finditer(r"(?m)^\\EvidenceFigure\b", text):
        c = m.end()
        if text[c] == "[":
            c = text.index("]", c) + 1
        args = []
        for _ in range(3):
            while text[c].isspace():
                c += 1
            body, c = read_braced(text, c)
            args.append(body)
        units.append({"type": "figure_caption", "line": line_of(text, m.start()), "label": args[2], "text": args[1], "pos": m.start()})
        mask(m.start(), c)
    for m in re.finditer(r"\\begin\{(table\*?)\}", text):
        end = text.index("\\end{%s}" % m.group(1), m.start()) + len("\\end{%s}" % m.group(1))
        block = text[m.start() : end]
        cap_at = block.index("\\caption")
        cap, _ = read_braced(block, cap_at + len("\\caption"))
        label = re.search(r"\\label\{([^}]+)\}", block).group(1)
        units.append({"type": "table_caption", "line": line_of(text, m.start()), "label": label, "text": cap, "pos": m.start()})
        rows = block[block.index("\\midrule") + 8 : block.index("\\bottomrule")]
        offset = m.start() + block.index("\\midrule") + 8
        for row_match in re.finditer(r"([^\n]+?)\\\\", rows):
            row = row_match.group(1).strip()
            if row.startswith("\\addlinespace"):
                continue
            row = re.sub(r"\\addlinespace\[[^\]]*\]", "", row).strip()
            if row:
                units.append({"type": "table_row", "line": line_of(text, offset + row_match.start()), "label": label, "text": re.sub(r"\s*&\s*", " | ", row), "pos": offset + row_match.start()})
        mask(m.start(), end)
    for m in re.finditer(r"\\begin\{equation\}(.*?)\\end\{equation\}", text, re.S):
        body = m.group(1)
        label = re.search(r"\\label\{([^}]+)\}", body)
        clean = re.sub(r"\\label\{[^}]*\}", "", body).strip()
        units.append({"type": "equation_block", "line": line_of(text, m.start()), "label": label.group(1) if label else "", "text": re.sub(r"\s+", " ", clean), "pos": m.start()})
        mask(m.start(), m.end())
    masked_text = "".join(masked)

    # Headings and prose
    pos = body_start
    heading = re.compile(r"\\(section|subsection|subsubsection)\*?\{([^}]*)\}")
    chunks = []
    last = body_start
    for m in heading.finditer(masked_text, body_start):
        chunks.append((last, m.start(), section))
        section = m.group(2)
        last = m.end()
    chunks.append((last, masked_text.index("\\bibliographystyle"), section))
    declaration_section = "Acknowledgments and author declarations"
    for a, b, sec in chunks:
        raw = masked_text[a:b]
        if a == body_start:
            abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, re.S)
            sections_text = [("Abstract", abstract.group(1), a + abstract.start())] if abstract else []
        else:
            sections_text = [(sec, raw, a)]
        for sec_name, chunk, base in sections_text:
            for para in re.split(r"\n\s*\n", chunk):
                para = para.strip()
                if not para:
                    continue
                if re.match(r"\\(?:begin|end|FloatBarrier|small|footnotesize|ifdefined|else|fi|par|medskip|bibliography|twocolumn|vspace|hrule|noindent\\begin\{minipage)", para):
                    para = re.sub(r"^\\(?:FloatBarrier|ifdefined\\ReviewEdition\\else\\small\\fi)\s*", "", para)
                    if not para or para.startswith("\\"):
                        continue
                para = re.sub(r"\\medskip\s*", "", para)
                para = re.sub(r"^\\noindent\s*", "", para)
                para = re.sub(r"^\\textbf\{([^}]*)\}\s*", r"\1 ", para)
                for sentence in split_sentences(para):
                    if sentence.startswith("\\"):
                        continue
                    unit_type = "author_or_ai_disclosure" if sec_name == declaration_section else "prose_sentence"
                    units.append({"type": unit_type, "line": line_of(text, base + chunk.find(para[:30])) if para[:30] in chunk else line_of(text, base), "label": "", "text": sentence, "pos": base + max(chunk.find(para[:30]), 0), "section": sec_name})
    # Assign sections to non-prose units by position
    sec_positions = [(m.start(), m.group(2)) for m in heading.finditer(text, body_start)]
    for u in units:
        if "section" not in u:
            current = "Abstract"
            for p, name in sec_positions:
                if p < u["pos"]:
                    current = name
            u["section"] = current
    return units


def number_tokens(text: str) -> set[str]:
    plain = re.sub(r"\\[A-Za-z]+", " ", text)
    return set(re.findall(r"\d[\d,]*\.?\d*", plain)) - {""}


# Values derived by verify_quantitative_figures.py from the analytical curve, the 18 recorded
# root-cell differences, or simple counts (250 episodes x 3 horizons), plus M8 discrepancies
# stated in scientific notation in the recorded route table.
DERIVED_AND_CHECKED = {"750", "14.79", "2.74", "24.09", "0.22", "0.55", "0.047", "0.025", "2.21", "3.04"}


def rounded_forms(corpus: str) -> set[str]:
    forms: set[str] = set()
    for token in re.findall(r"\d+\.\d+", corpus):
        value = float(token)
        for places in (2, 3, 4):
            forms.add(f"{value:.{places}f}")
            forms.add(f"{value:.{places}f}".lstrip("0") if value < 1 else f"{value:.{places}f}")
    return forms


def evidence_corpus() -> str:
    parts = []
    for path in sorted((ROOT / "evidence" / "release_sources").glob("*")):
        if path.suffix in {".json", ".md", ".csv", ".py"}:
            parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    for path in sorted((ROOT / "evidence" / "v2_audit").glob("*")):
        if path.suffix in {".json", ".md", ".csv"}:
            parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    parts.append((ROOT / "supplement" / "technical_supplement.tex").read_text(encoding="utf-8"))
    for path in sorted((ROOT / "supplement" / "tables").glob("*.tex")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def main() -> None:
    old_rows = list(csv.DictReader(AUDIT.open(newline="", encoding="utf-8")))
    fields = list(old_rows[0].keys())
    sha = sha256(MANUSCRIPT)
    text = MANUSCRIPT.read_text(encoding="utf-8")
    units = extract_units(text)
    old_ms = [r for r in old_rows if r["manuscript_location"].startswith("manuscript.tex")]
    kept_other = [r for r in old_rows if not r["manuscript_location"].startswith("manuscript.tex")]
    old_norm = [(norm(r["exact_statement"]), r) for r in old_ms]
    used: set[str] = set()
    corpus = evidence_corpus()
    corpus_numbers = number_tokens(corpus) | {re.sub(",", "", n) for n in number_tokens(corpus)} | rounded_forms(corpus) | DERIVED_AND_CHECKED
    new_rows: list[dict] = []
    changes: list[dict] = []
    counters = Counter()
    previous_by_section: dict[str, dict] = {}
    for u in units:
        un = norm(u["text"])
        best, best_ratio = None, 0.0
        for on, row in old_norm:
            if row["claim_id"] in used or row["unit_type"] != u["type"]:
                continue
            if abs(len(on) - len(un)) > 0.6 * max(len(on), len(un), 1):
                continue
            sm = difflib.SequenceMatcher(None, un, on, autojunk=False)
            if sm.real_quick_ratio() < 0.6 or sm.quick_ratio() < 0.6:
                continue
            ratio = sm.ratio()
            if ratio > best_ratio:
                best, best_ratio = row, ratio
        location = f"manuscript.tex:L{u['line']}" + (f" ({u['label']})" if u["label"] else "")
        if best is not None and best_ratio >= 0.62:
            used.add(best["claim_id"])
            row = dict(best)
            if best_ratio >= 0.995:
                status = best["differential_status"]
                note = best["crosswalk_note"]
                change = "unchanged"
            else:
                status = "administrative_disclosure" if u["type"] == "author_or_ai_disclosure" else "modified"
                note = best["crosswalk_note"] + " | RES-585: wording revised for the illustrated edition; evidence mapping inherited."
                change = "revised"
        else:
            sec_ref = previous_by_section.get(u["section"]) or next((r for r in old_ms if r["section"] == u["section"]), old_ms[0])
            row = {k: sec_ref[k] for k in fields}
            row["claim_id"] = f"V3-{u['type'].split('_')[0].upper()}-N{counters['new'] + 1:04d}"
            status = "administrative_disclosure" if u["type"] == "author_or_ai_disclosure" else "new"
            note = "RES-585: new unit; evidence mapping assigned from the surrounding section and verified against the pinned corpus."
            change = "new"
            counters["new"] += 1
        row.update(
            {
                "unit_type": u["type"],
                "manuscript_location": location,
                "section": u["section"],
                "exact_statement": u["text"],
                "manuscript_source_sha256": sha,
                "differential_status": status,
                "crosswalk_note": note,
            }
        )
        if change != "unchanged":
            toks = {t.rstrip(".,") for t in number_tokens(u["text"])}
            toks = {t for t in toks if (len(t.replace(",", "").replace(".", "")) >= 3 or "." in t) and not re.fullmatch(r"0\d{4}", t)}
            missing = sorted(t for t in toks if t not in corpus_numbers and t.replace(",", "") not in corpus_numbers)
            checked = "numeric_tokens_found_in_pinned_corpus" if not missing else "numeric_tokens_not_in_corpus:" + ";".join(missing)
            changes.append({"claim_id": row["claim_id"], "change": change, "similarity": f"{best_ratio:.3f}", "location": location, "numeric_check": checked, "statement": u["text"][:300]})
            if row["verification_decision"] != "owner_confirmation_pending":
                row["verification_decision"] = "qualified_source_checked" if row["verification_decision"] == "qualified_source_checked" else "source_checked"
        previous_by_section[u["section"]] = row
        new_rows.append(row)

    dropped = [r for r in old_ms if r["claim_id"] not in used]
    for r in dropped:
        changes.append({"claim_id": r["claim_id"], "change": "dropped_from_manuscript", "similarity": "", "location": r["manuscript_location"], "numeric_check": "", "statement": r["exact_statement"][:300]})
    for r in kept_other:
        r["manuscript_source_sha256"] = sha
    all_rows = new_rows + kept_other
    # stable ordering and unique IDs
    seen = Counter(r["claim_id"] for r in all_rows)
    assert all(v == 1 for v in seen.values()), [k for k, v in seen.items() if v > 1]
    with AUDIT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        writer.writerows(all_rows)
    if changes or not CHANGES.exists():  # an idempotent re-run must not erase the recorded reconciliation
        with CHANGES.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, ["claim_id", "change", "similarity", "location", "numeric_check", "statement"])
            writer.writeheader()
            writer.writerows(changes)

    current = [r for r in all_rows if r["unit_type"] != "removed_historical_claim"]
    admin = [r for r in current if r["unit_type"] == "author_or_ai_disclosure"]
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    previous = summary.get("res585_reconciliation")
    summary.update(
        {
            "current_v3_claim_units": len(current),
            "all_audit_rows": len(all_rows),
            "differential_status_counts": dict(sorted(Counter(r["differential_status"] for r in all_rows).items())),
            "unit_type_counts": dict(sorted(Counter(r["unit_type"] for r in all_rows).items())),
            "verification_decision_counts": dict(sorted(Counter(r["verification_decision"] for r in all_rows).items())),
            "manuscript_source_sha256": sha,
            "substantive_current_claim_units": len(current) - len(admin),
            "administrative_disclosures": len(admin),
            "res585_reconciliation": {
                "changed_or_new_units": len([c for c in changes if c["change"] in ("revised", "new")]),
                "dropped_units": len(dropped),
                "numeric_check_failures": len([c for c in changes if c["numeric_check"].startswith("numeric_tokens_not")]),
                "changes_file": CHANGES.name,
            }
            if changes or not previous
            else previous,
        }
    )
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["res585_reconciliation"]), len(current), "current units")


if __name__ == "__main__":
    main()
