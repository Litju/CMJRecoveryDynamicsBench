import { ArrowDown, ArrowUpRight } from "lucide-react";
import { aggregate, models, sourceLink } from "@/lib/science";
import { MetricLesson, StudyMethods } from "./experiment-methods";

export function QuickRoute() {
  return <aside className="shell quick-route" aria-labelledby="quick-title">
    <div><span className="eyebrow">UNDERSTAND IN 90 SECONDS</span><h2 id="quick-title">One question.<br/><span>A testable research program.</span></h2><p>Follow the story, or open “Methods & evidence” in each exhibit for the scientific detail.</p></div>
    <ol>
      <li><a href="#world"><span>01 / THE QUESTION</span><strong>Can past assessments and a known exposure predict later force and impulse changes?</strong></a></li>
      <li><a href="#lineage"><span>02 / THE METHOD</span><strong>Build eight explicit synthetic formulations. Separate the world, measurement and model.</strong></a></li>
      <li><a href="#experiment"><span>03 / THE FINDING</span><strong>Learning helped here. Ridge recorded {aggregate("ridge_full","mean").toFixed(3)} mean NRMSE, below the structured model’s {aggregate("structured_full","mean").toFixed(3)}.</strong></a></li>
      <li><a href="#evidence"><span>04 / THE BOUNDARY</span><strong>Reproducible synthetic evidence. Human validity, world shifts and exact historical replay remain open.</strong></a></li>
    </ol>
  </aside>;
}

export function Question() {
  return (
    <section
      id="question"
      className="shell section story-act question-act"
      aria-labelledby="question-title"
    >
      <div className="eyebrow">
        <span className="section-number">ACT I</span> THE QUESTION
      </div>
      <div className="question-layout">
        <h2 id="question-title" className="editorial-heading">
          A measurement
          <br />
          is a moment.
          <br />
          <span>
            Recovery is
            <br />a process.
          </span>
        </h2>
        <div className="question-copy">
          <p className="story-lead">
            After a training exposure, force and impulse can change.
          </p>
          <p>
            Can the information available at the forecast origin predict their
            later innovations?
          </p>
          <p>
            A countermovement jump (CMJ) provides force and net-impulse
            assessments: how force is expressed, and its net effect over time.
            Here, an innovation means a change from the pre-index baseline.
          </p>
          <p>
            This research asks a forecasting question in synthetic worlds. It
            does not diagnose recovery or prescribe training.
          </p>
        </div>
      </div>
      <div
        className="forecast-strip"
        aria-label="Illustrative forecast design, no observed athlete data"
      >
        <div className="forecast-origin">
          <span className="eyebrow">AVAILABLE AT ORIGIN</span>
          <strong>
            Assessments +<br />
            exposure history
          </strong>
          <span>Current exposure and public context</span>
        </div>
        <div className="forecast-future">
          <span className="eyebrow">ASK ABOUT LATER INNOVATIONS</span>
          <ol>
            {[24, 48, 72].map((h) => (
              <li key={h}>
                <span className="forecast-point" />
                <strong>
                  {h}
                  <small>h</small>
                </strong>
                <span>Force + net impulse</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
      <p className="story-caption">
        Illustrative post-exposure design, not an athlete trace. The preseason
        family instead asks about H72 and D7.{" "}
        <a
          href={sourceLink(
            "src/cmj_recovery_dynamics/benchmarks/preliminary_post_exposure_recovery.py",
          )}
        >
          Read the task contract ↗
        </a>
      </p>
      <a className="quiet-link chapter-next" href="#world">
        Step inside a synthetic episode <ArrowDown size={16} />
      </a>
    </section>
  );
}

export function Experiment() {
  const improvement =
    (1 -
      aggregate("ridge_full", "mean") /
        aggregate("training_constant", "mean")) *
    100;
  return (
    <section
      id="experiment"
      className="shell section story-act"
      aria-labelledby="experiment-title"
    >
      <div className="eyebrow">
        <span className="section-number">ACT III</span> THE EXPERIMENT
      </div>
      <h2 id="experiment-title" className="editorial-heading">
        The model has to
        <br />
        <span>earn its prediction.</span>
      </h2>
      <p className="story-deck">
        One active formulation. Four reference models.
        <br />
        First ask what each model is allowed to know.
      </p>
      <div className="model-primer">
        {models.map((m, i) => (
          <details key={m.id}>
            <summary>
              <span className="mono">0{i + 1}</span>
              <strong>{m.name}</strong>
              <span aria-hidden="true">+</span>
            </summary>
            <p>{m.description}</p>
            <p>{m.id === "zero_innovation" ? "Knows no fitted relationship. A useful reference for how far observations move from baseline." : m.id === "training_constant" ? "Knows training-cell label means, but cannot adapt to the particular current exposure or prior response history." : m.id === "ridge_full" ? "Learns a flexible regularized linear relationship from public inputs. A strong regression baseline is not an explanation of biological recovery or learned physical kinetics." : "Imposes a 24 h / 84 h basis on public exposures. It does not receive the generator’s amplitudes, hidden states or discrepancy. The structured assumption is tested, not validated as biology."}</p>
          </details>
        ))}
      </div>
      <div className="experiment-layout">
        <div>
          <h3>Does learning help here?</h3>
          <p className="experiment-answer">
            <strong>{improvement.toFixed(1)}%</strong> lower recorded mean error
            for ridge than the training constant.
          </p>
          <p>
            Three independent public roots from the same generator. Each score
            averages six cells: two outcomes at three horizons.
          </p>
          <p>
            Within each cell, RMSE is divided by the truth population standard
            deviation (ddof = 0). Then the six normalized errors are equally
            weighted. Lower NRMSE is better.
          </p>
        </div>
        <figure className="story-results">
          <figcaption>
            RECORDED SIX-CELL MEAN NRMSE <span>LOWER IS BETTER ↓</span>
          </figcaption>
          <div className="result-bars">
            {[models[0], models[1], models[3], models[2]].map((m) => (
              <div className="result-bar" key={m.id} data-model={m.id}>
                <div>
                  <span>{m.name}</span>
                  <strong>{aggregate(m.id, "mean").toFixed(6)}</strong>
                </div>
                <div className="bar-track">
                  <span
                    style={{
                      width: `${(aggregate(m.id, "mean") / 2.6) * 100}%`,
                      background: m.color,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
          <p>
            Arithmetic mean of the three root-specific scores.{" "}
            <a
              href={sourceLink(
                "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json",
              )}
            >
              Audited result receipt <ArrowUpRight size={12} />
            </a>
          </p>
        </figure>
      </div>
      <p className="story-caveat">
        This establishes a recorded comparison in this synthetic generator. It
        does not establish population significance, out-of-distribution
        generalization or human athlete efficacy. Published paired
        camp-bootstrap contrasts are against zero; no ridge-versus-structured
        interval is claimed.
      </p>
      <MetricLesson />
      <StudyMethods />
      <a className="quiet-link chapter-next" href="#explorer">
        Now inspect the cells, roots and comparisons <ArrowDown size={16} />
      </a>
    </section>
  );
}

export function Remaining() {
  return (
    <section
      id="remaining"
      className="shell section story-act remaining-act"
      aria-labelledby="remaining-title"
    >
      <div className="eyebrow">
        <span className="section-number">ACT IV</span> WHAT REMAINS
      </div>
      <h2 id="remaining-title" className="editorial-heading">
        A reproducible result
        <br />
        <span>is not the end of the question.</span>
      </h2>
      <p className="story-deck">
        The active candidate anchors its response to two fixed mathematical
        modes, at 24 and 84 hours, plus bounded smooth discrepancy.
      </p>
      <p className="remaining-copy">
        The lab below isolates those two anchors so you can inspect their shape.
        They are mathematical choices, not biological compartments. Arbitrary
        amplitudes show the equation; they do not reproduce a fitted model or
        its discrepancy term.
      </p>
      <a href="#lab" className="quiet-link chapter-next">
        Explore the mathematics, then its limits <ArrowDown size={16} />
      </a>
    </section>
  );
}
