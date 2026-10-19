import { ArrowUpRight, BookOpen, Fingerprint, ShieldCheck } from "lucide-react";
import { data, sourceLink } from "@/lib/science";
import methods from "@/data/methods.json";
export default function Evidence() {
  return (
    <section
      id="evidence"
      className="shell section evidence-section"
      aria-labelledby="evidence-title"
    >
      <div className="section-top">
        <div className="eyebrow">
          <span className="section-number">IV / EVIDENCE</span> EVIDENCE &
          METHODS
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
      <div className="scrutiny-intro">
        <span className="eyebrow">RESULTS THAT CONSTRAIN THE STORY</span>
        <h3>Keep the inconvenient findings.</h3>
      </div>
      <div className="scrutiny-cards">
        <article>
          <span className="mono">01 / STRUCTURE DID NOT WIN</span>
          <h4>A useful assumption can still lose.</h4>
          <p>
            The structured model’s recorded mean NRMSE was{" "}
            {methods.variants.structured_full.root_mean_nrmse.toFixed(6)},
            against ridge’s{" "}
            {methods.variants.ridge_full.root_mean_nrmse.toFixed(6)}. Fixed
            modes did not establish an advantage here. There is no reported
            direct paired interval for that comparison.
          </p>
        </article>
        <article>
          <span className="mono">02 / LITTLE CONTEXT EFFECT</span>
          <h4>More inputs did not always help much.</h4>
          <p>
            Removing participant context increased ridge mean NRMSE by{" "}
            {(
              methods.variants.ridge_no_participant_context.root_mean_nrmse -
              methods.variants.ridge_full.root_mean_nrmse
            ).toFixed(6)}
            . Small sample-efficiency differences do not show that small
            real-world datasets are sufficient.
          </p>
        </article>
        <article>
          <span className="mono">03 / SELECTION HIT THE EDGE</span>
          <h4>The grid did not locate an optimum.</h4>
          <p>
            All six selected alphas were 0.01, the lower edge of the frozen
            grid. Weaker regularization needs a separately preregistered study;
            post-test tuning would change the experiment.
          </p>
        </article>
      </div>
      <p className="story-caption">
        <a href={sourceLink("docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md")}>
          Inspect the recorded findings and their interpretation ↗
        </a>
      </p>
      <div className="evidence-grid">
        <div className="evidence-ladder">
          <span className="eyebrow">THE EVIDENCE LADDER</span>
          <h3>
            Reproducible.
            <br />
            <span>Within these boundaries.</span>
          </h3>
          <div className="evidence-rung">
            <span className="small-tag">WHAT IS REPRODUCIBLE</span>
            <h4>Fresh public synthetic data</h4>
            <p>
              Eight clean-room generator paths and sixteen train/validation
              streams. Public code and metrics; new retired and active reference
              studies.
            </p>
          </div>
          <div className="evidence-rung">
            <span className="small-tag">
              WHAT MATCHED IN CLEAN-ROOM STUDIES
            </span>
            <h4>New fits and scores, checked across packaging</h4>
            <p>
              The recorded source and isolated-wheel evaluations matched exactly
              on scientific fields. That qualifies the new public study’s
              execution; it does not replay historical campaigns.
            </p>
          </div>
          <div className="evidence-rung">
            <span className="small-tag">WHAT IS NOT ESTABLISHED</span>
            <h4>Exact historical campaign replay</h4>
            <p>
              All eight generation-plus-result chains are only partially
              reproducible. Historical numbers remain evidence-only for six
              formulations; two have no registered public numeric historical
              result.
            </p>
          </div>
          <div className="evidence-rung">
            <span className="small-tag">WHAT IS NOT IMPLEMENTED</span>
            <h4>Active production calibrated scoring</h4>
            <p>
              The research six-cell NRMSE is implemented. The active production
              scoring path is not; this exhibition cannot issue a production
              recovery score.
            </p>
          </div>
          <div className="evidence-rung">
            <span className="small-tag">WHAT IS NOT ESTABLISHED</span>
            <h4>External applicability or real-world efficacy</h4>
            <p>
              No exact historical score replay. Active production calibrated
              scoring remains unresolved. Same-generator roots do not establish
              out-of-distribution generalization or human athlete efficacy.
            </p>
          </div>
          <a className="quiet-link" href="#lineage">
            Return to the scientific lineage ↗
          </a>
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
                The site reads committed receipts. No benchmark generation,
                inference, or model training runs in your browser. A frozen
                source revision and checksums travel with the downloadable
                fixture.
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
      <div className="roadmap">
        <div>
          <span className="eyebrow">OPEN QUESTIONS / PROPOSED WORK</span>
          <h3>
            What would change
            <br />
            <span>our confidence?</span>
          </h3>
          <p>
            Questions to test next. No future result or completion date is
            implied.
          </p>
        </div>
        <div>
          <details>
            <summary>Does the ranking survive a different world?</summary>
            <p>
              Preregister independent shifts in exposure distributions, response
              dynamics and observation laws. A reversal would limit the current
              ranking to its generating assumptions.
            </p>
          </details>
          <details>
            <summary>Can it forecast measurements from real athletes?</summary>
            <p>
              Establish rights, measurement quality, baselines and prospective
              temporal splits in an empirical cohort. Validate rather than
              transfer a synthetic score into practice.
            </p>
          </details>
          <details>
            <summary>How much uncertainty comes from training?</summary>
            <p>
              The reported camp bootstrap conditions on a fixed fitted model.
              Refit preprocessing, selection and coefficients across training
              resamples to assess a wider source of uncertainty.
            </p>
          </details>
          <details>
            <summary>What happens below the alpha grid boundary?</summary>
            <p>
              Freeze a new selection protocol before evaluating new roots. Test
              weaker regularization without reusing the current test outcomes to
              pick a winner.
            </p>
          </details>
        </div>
      </div>
      <div className="reproduce-cta">
        <div>
          <span className="eyebrow">TAKE THE QUESTION FURTHER</span>
          <h3>Read it. Run it. Inspect it.</h3>
          <p>
            After installation, run this in the scientific repository at the
            pinned revision to inspect the matrix. The source instructions also
            cover fresh synthetic runs.
          </p>
        </div>
        <div>
          <pre>
            <code>
              python -m cmj_recovery_dynamics.reproducibility.qualification
              --matrix-only
            </code>
          </pre>
          <div className="provenance-links">
            <a href={sourceLink("README.rst")}>Code & run instructions ↗</a>
            <a
              href={sourceLink("docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md")}
            >
              Method ↗
            </a>
            <a href={sourceLink("CITATION.cff")}>Citation ↗</a>
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
            does not assert a v1.0 release. The pinned software citation retains
            version 0.1.0 and authorship by Julio Rodriguez. Publication is not
            claimed; PR #8 was not merged by this work.
          </p>
        </div>
      </details>
    </section>
  );
}
