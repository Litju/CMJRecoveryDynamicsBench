import {
  ArrowUpRight,
  BookOpen,
  Fingerprint,
  GitBranch,
  ShieldCheck,
} from "lucide-react";
import { data, sourceLink } from "@/lib/science";
const names: Record<string, string> = {
  initial_preseason_camp_recovery: "Initial preseason",
  canonical_preseason_camp_recovery: "Canonical preseason",
  rich_history_camp_recovery: "Rich-history camp",
  preliminary_post_exposure_recovery: "Preliminary post-exposure",
  phase_consistent_post_exposure_recovery: "Phase-consistent",
  correlated_exposure_recovery: "Correlated exposure",
  threshold_response_recovery: "Threshold response",
  fixed_mode_discrepancy_recovery: "Fixed-mode discrepancy",
};
export default function Evidence() {
  return (
    <section
      id="evidence"
      className="shell section evidence-section"
      aria-labelledby="evidence-title"
    >
      <div className="section-top">
        <div className="eyebrow">
          <span className="section-number">03</span> EVIDENCE & METHODS
        </div>
        <span className="panel-label">
          OPEN BY DESIGN. BOUNDED BY EVIDENCE.
        </span>
      </div>
      <div className="section-heading">
        <div>
          <h2 id="evidence-title">
            The full picture.
            <br />
            <span>Including the limits.</span>
          </h2>
          <p>
            Scientific transparency means showing what a result can—and
            cannot—say.
          </p>
        </div>
        <a
          href={sourceLink("docs/M8_REPRODUCIBILITY_MATRIX.md")}
          className="quiet-link"
        >
          Reproduction matrix <ArrowUpRight size={15} />
        </a>
      </div>
      <div className="evidence-grid">
        <div className="lineage-panel">
          <div className="detail-title">
            <h3>Eight formulations, one research lineage</h3>
            <GitBranch size={17} />
          </div>
          <ol className="lineage-list">
            {data.formulations.map((f, i) => (
              <li
                key={f.id}
                className={
                  f.status === "Active candidate" ? "active-formulation" : ""
                }
              >
                <span className="lineage-index">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <span className="formulation-name">{names[f.id]}</span>
                  <code>{f.id}</code>
                </div>
                <span
                  className={`formulation-status ${f.status.toLowerCase().replaceAll(" ", "-")}`}
                >
                  {f.status}
                </span>
              </li>
            ))}
          </ol>
          <p className="table-note">
            All eight have public synthetic generators and a partially
            reproducible generation-plus-result chain. None has an exact
            historical result replay. Formulation status and reproducibility
            status are different axes.
          </p>
        </div>
        <div className="evidence-notes">
          <article>
            <ShieldCheck size={20} />
            <div>
              <h3>Trained on public inputs only</h3>
              <p>
                82 public predictors; 84 encoded columns. Training-only scaling.
                No labels, grouping keys, future outcomes, hidden effects, or
                oracle states enter as predictors. Model selection is locked
                before independent testing.
              </p>
            </div>
          </article>
          <article>
            <BookOpen size={20} />
            <div>
              <h3>Synthetic research, with boundaries</h3>
              <p>
                Three independently seeded populations from the same generator
                do not establish generalization to humans. This is a new public
                synthetic study, not exact historical replay or an accepted
                production scorer.
              </p>
            </div>
          </article>
          <article>
            <Fingerprint size={20} />
            <div>
              <h3>Every number leaves a trace</h3>
              <p>
                The site reads committed receipts. No simulation, inference, or
                model training runs in your browser. A frozen source revision
                and checksums travel with the downloadable fixture.
              </p>
            </div>
          </article>
          <div className="retired-note">
            <span className="small-tag">SEPARATE RETIRED FORMULATION</span>
            <h4>Rich-history diagnostic</h4>
            <p>
              The earlier rich-history study uses a 24-cell raw-progress
              diagnostic, with a different target and evaluation identity. Its
              results are kept in their own study and are never ranked alongside
              active six-cell NRMSE.
            </p>
            <p className="retired-result">
              Declared primary ridge (α = 1): reported raw progress{" "}
              <strong>
                {data.retiredStudy.reportedPrimaryRawProgress.toFixed(4)}
              </strong>
              . Paired improvement over zero: 95% interval [
              {data.retiredStudy.reportedPaired95Interval
                .map((v) => v.toFixed(4))
                .join(", ")}
              ], 500 camp-bootstrap replicates, conditional on one fixed
              training split. Different metric; not comparable to the active
              scores.
            </p>
            <a
              className="quiet-link"
              href={sourceLink("docs/M8_REFERENCE_MODEL_STUDY.md")}
            >
              Read the retired study <ArrowUpRight size={14} />
            </a>
          </div>
        </div>
      </div>
      <details className="provenance">
        <summary>
          <Fingerprint size={16} /> Inspect this snapshot{" "}
          <span className="mono">{data.provenance.commit.slice(0, 12)}</span>
        </summary>
        <div className="provenance-content">
          <dl>
            <div>
              <dt>Scientific source commit</dt>
              <dd>
                <a
                  href={`${data.provenance.repository}/tree/${data.provenance.commit}`}
                >
                  {data.provenance.commit}
                </a>
              </dd>
            </div>
            <div>
              <dt>Original result file SHA-256</dt>
              <dd>{data.provenance.resultsSha256}</dd>
            </div>
            <div>
              <dt>Scientific-results SHA-256</dt>
              <dd>{data.provenance.scientificResultsSha256}</dd>
            </div>
            <div>
              <dt>Study code revision</dt>
              <dd>{data.provenance.studyCode} (upstream abbreviation)</dd>
            </div>
            <div>
              <dt>Selection-lock SHA-256</dt>
              <dd>{data.provenance.selectionLockSha256}</dd>
            </div>
          </dl>
          <div className="provenance-links">
            <a
              href={sourceLink(
                "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json",
              )}
            >
              Original result receipt <ArrowUpRight size={13} />
            </a>
            <a href={sourceLink("docs/M8_V1_RELEASE_AUDIT_RECEIPT.json")}>
              Release audit receipt <ArrowUpRight size={13} />
            </a>
            <a href={sourceLink("CITATION.cff")}>
              Unchanged software citation <ArrowUpRight size={13} />
            </a>
          </div>
          <p>
            This showcase is independent of the package release process. A
            release audit is evidence, not publication authorization; this site
            does not assert a v1.0 release.
          </p>
        </div>
      </details>
    </section>
  );
}
