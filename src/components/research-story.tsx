import { ArrowDown, ArrowUpRight } from "lucide-react";
import { aggregate, models, sourceLink } from "@/lib/science";
import { MetricLesson, StudyMethods } from "./experiment-methods";
import MeasurementExhibit, { ExposureContext } from "./measurement-exhibit";
import HeroInstrument from "./hero-instrument";
import context from "@/data/context.json";

export function QuickRoute() {
  return (
    <aside className="shell quick-route" aria-labelledby="quick-title">
      <div>
        <span className="eyebrow">UNDERSTAND IN 90 SECONDS</span>
        <h2 id="quick-title">
          One question.
          <br />
          <span>A testable research program.</span>
        </h2>
        <p>
          Follow the story, or open “Methods & evidence” in each exhibit for the
          scientific detail.
        </p>
      </div>
      <ol>
        <li>
          <a href="#world">
            <span>01 / THE QUESTION</span>
            <strong>
              Can past assessments and a known exposure predict later force and
              impulse changes?
            </strong>
          </a>
        </li>
        <li>
          <a href="#lineage">
            <span>02 / THE METHOD</span>
            <strong>
              Build eight explicit synthetic formulations. Separate the world,
              measurement and model.
            </strong>
          </a>
        </li>
        <li>
          <a href="#experiment">
            <span>03 / THE FINDING</span>
            <strong>
              Learning helped here. Ridge recorded{" "}
              {aggregate("ridge_full", "mean").toFixed(3)} mean NRMSE, below the
              structured model’s{" "}
              {aggregate("structured_full", "mean").toFixed(3)}.
            </strong>
          </a>
        </li>
        <li>
          <a href="#evidence">
            <span>04 / THE BOUNDARY</span>
            <strong>
              Reproducible synthetic evidence. Human validity, world shifts and
              exact historical replay remain open.
            </strong>
          </a>
        </li>
      </ol>
    </aside>
  );
}

export function Question() {
  return (
    <section
      id="question"
      className="shell section story-act question-act"
      aria-labelledby="question-title"
    >
      <div className="eyebrow">
        <span className="section-number">01 / THE SETTING</span> SPORTS SCIENCE
        → A FORECASTING PROBLEM
      </div>
      <div className="question-layout">
        <h2 id="question-title" className="editorial-heading">
          Training is the exposure.
          <br />
          <span>The jump is the assessment.</span>
        </h2>
        <div className="question-copy">
          <p className="story-lead">
            Imagine measuring a jump before a training exposure, then asking how
            that measurement will change over the next three days.
          </p>
          <p>
            That is the setting behind the active research question. The model
            sees a baseline, a known exposure and earlier episodes. It must
            predict later force and net-impulse innovations—a change from the
            pre-index baseline.
          </p>
        </div>
      </div>
      <div className="setting-context">
        <article>
          <span className="context-index">A / THE REAL-WORLD MOTIVATION</span>
          <h3>Why examine a jump?</h3>
          <p>
            Sports scientists investigate countermovement jumps as repeatable
            assessments of neuromuscular performance. A force plate records how
            the push is produced over time. Reliability and the choice of
            measurement matter before a change can be interpreted.
          </p>
          <p>
            This motivates a forecasting question: can what is known after a
            training exposure tell us something useful about a later assessment?
          </p>
          <div className="context-citations">
            {context.references.map((r) => (
              <a key={r.id} href={r.href}>
                {r.authors.split(",")[0]} et al. · {r.year}{" "}
                <ArrowUpRight size={12} />
              </a>
            ))}
          </div>
        </article>
        <article>
          <span className="context-index">B / THE ACTUAL EXPERIMENT HERE</span>
          <h3>A controlled synthetic world.</h3>
          <p>
            This website presents a public computational benchmark.
            Participants, exposure patterns, latent responses and measurements
            are generated under explicit mathematical rules. The active study
            does not contain athlete observations.
          </p>
          <p>
            A dedicated baseline is assessed about two hours before one current
            exposure. Four earlier episodes are available. There is no
            additional material current-episode exposure through H72 in the
            observation contract.
          </p>
          <a className="quiet-link" href={sourceLink(context.source)}>
            Read the exact information boundary ↗
          </a>
        </article>
      </div>
      <ExposureContext />
      <MeasurementExhibit />
      <div
        className="forecast-strip"
        aria-label="Illustrative forecast design, no observed athlete data"
      >
        <div className="forecast-origin">
          <span className="eyebrow">FREEZE THE INPUTS HERE</span>
          <strong>
            Baseline + exposure
            <br />+ observed history
          </strong>
          <span>
            The requested horizon is known. The future outcome is not.
          </span>
        </div>
        <div className="forecast-future">
          <span className="eyebrow">PREDICT THE LATER CHANGE</span>
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
        These are benchmark query times, not a claim that all athletes recover
        on a three-day schedule. The preseason family instead asks about H72 and
        D7.{" "}
        <a
          href={sourceLink(
            "src/cmj_recovery_dynamics/benchmarks/preliminary_post_exposure_recovery.py",
          )}
        >
          Inspect the task contract ↗
        </a>
      </p>
      <details className="context-literature">
        <summary>Background literature & the boundary of this project</summary>
        {context.references.map((r) => (
          <article key={r.id}>
            <a href={r.href}>
              <strong>{r.title}</strong> ↗
            </a>
            <p>
              {r.authors} · {r.year} · DOI {r.doi}
            </p>
            <p>{r.evidence}</p>
          </article>
        ))}
        <p>
          {context.boundary} The benchmark's own pinned observation contract
          defines its phase semantics; the background studies are not presented
          as its protocol or as its evaluation data.
        </p>
      </details>
      <a className="quiet-link chapter-next" href="#world">
        Now follow one episode, from input to held-out target{" "}
        <ArrowDown size={16} />
      </a>
    </section>
  );
}

export function ResearchCover() {
  return (
    <figure className="research-cover" aria-labelledby="cover-title">
      <figcaption>
        <span>FIELD NOTES / CMJ RECOVERY</span>
        <span>PUBLIC RESEARCH · 01</span>
      </figcaption>
      <div className="cover-heading">
        <span>THE EXPERIMENT IN ONE VIEW</span>
        <h2 id="cover-title">
          Measure.
          <br />
          Expose.
          <br />
          <em>Forecast change.</em>
        </h2>
      </div>
      <div className="cover-flow">
        <div className="cover-baseline">
          <span>BEFORE</span>
          <strong>
            Baseline
            <br />
            assessment
          </strong>
          <small>Force · impulse · depth</small>
        </div>
        <div className="cover-origin">
          <span>AT ORIGIN</span>
          <strong>
            One known
            <br />
            exposure
          </strong>
          <small>Inputs freeze here</small>
        </div>
      </div>
      <div className="cover-futures">
        <span>WHAT WILL CHANGE?</span>
        <div>
          {[24, 48, 72].map((h) => (
            <div key={h}>
              <strong>
                {h}
                <small>h</small>
              </strong>
              <span>Reassess</span>
            </div>
          ))}
        </div>
      </div>
      <div className="cover-legend">
        <span>
          <i />
          Force / N·kg⁻¹
        </span>
        <span>
          <i />
          Net impulse / m·s⁻¹
        </span>
      </div>
      <p>
        One exposure, two outcomes, three horizons.
        <br />
        An explicit forecasting task in a synthetic world.
      </p>
    </figure>
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
        Does a structured model
        <br />
        <span>beat a flexible baseline?</span>
      </h2>
      <p className="story-deck">
        The same public information boundary. The same held-out targets. Four
        different assumptions. A comparison that can challenge the modelling
        idea, rather than reward it by design.
      </p>
      <div className="experiment-setup">
        <article>
          <span>01 / TRAIN</span>
          <h3>Learn from public examples.</h3>
          <p>
            Fit transformations and coefficients using training rows. Neither
            validation means nor future test labels are features.
          </p>
        </article>
        <article>
          <span>02 / SELECT</span>
          <h3>Freeze the modelling choices.</h3>
          <p>
            Use development data to select regularisation. Lock the protocol
            before generating and scoring independent test roots.
          </p>
        </article>
        <article>
          <span>03 / CHALLENGE</span>
          <h3>Ask which assumption earns its place.</h3>
          <p>
            Compare zero change, a fitted constant, full ridge regression and a
            fixed-mode structured comparator on the same six cells.
          </p>
        </article>
      </div>
      <div className="model-primer">
        {models.map((m, i) => (
          <details key={m.id}>
            <summary>
              <span className="mono">0{i + 1}</span>
              <strong>{m.name}</strong>
              <span aria-hidden="true">+</span>
            </summary>
            <p>{m.description}</p>
            <p>
              {m.id === "zero_innovation"
                ? "Knows no fitted relationship. A useful reference for how far observations move from baseline."
                : m.id === "training_constant"
                  ? "Knows training-cell label means, but cannot adapt to the particular current exposure or prior response history."
                  : m.id === "ridge_full"
                    ? "Learns a flexible regularized linear relationship from public inputs. A strong regression baseline is not an explanation of biological recovery or learned physical kinetics."
                    : "Imposes a 24 h / 84 h basis on public exposures. It does not receive the generator’s amplitudes, hidden states or discrepancy. The structured assumption is tested, not validated as biology."}
            </p>
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
      <div className="instrument-interlude">
        <div>
          <span className="eyebrow">THE MATHEMATICAL HYPOTHESIS</span>
          <h3>
            Give the model a shape.
            <br />
            <em>Then test whether it helps.</em>
          </h3>
          <p>
            The structured comparator borrows fixed 24 h and 84 h exponential
            bases. Isolate each mode and scrub the illustration to see the
            assumption. The experiment above shows why a plausible structure
            still needs a strong comparator.
          </p>
          <p>
            The height of this illustrative field follows the equation; its
            spatial geometry is decorative. It is not a measured force trace,
            body motion or a fitted forecast.
          </p>
        </div>
        <HeroInstrument />
      </div>
      <a href="#lab" className="quiet-link chapter-next">
        Explore the mathematics, then its limits <ArrowDown size={16} />
      </a>
    </section>
  );
}
