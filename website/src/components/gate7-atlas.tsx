"use client";
import { useEffect, useState } from "react";
import { atlas } from "@/lib/gate7";
import { plotTheme as theme } from "@/lib/plot-theme.mjs";
import { mechanics } from "@/lib/native-mechanics.mjs";
import { familyNames, familySlug } from "@/lib/model-families";
const sourceTitles = [
  "Inference verification",
  "CPU reproduction policy",
  "Additive model recovery",
  "Measurement methods",
  "Feedforward and recurrent implementations",
  "Five-basis implementation",
  "Additive-basis implementation",
];
const repeatLabel = (repeat: string) => `Repeat ${Number(repeat.slice(1)) + 1}`;
const repository = "https://github.com/Litju/CMJRecoveryDynamicsBench";
const source = (path: string) => `${repository}/blob/${atlas.commit}/${path}`;
const chapters = [
  [
    "question",
    "The question",
    "A jump measures a moment. Recovery forecasting asks what happens after exposure.",
  ],
  [
    "lineage",
    "Eight formulations",
    "Historical formulations changed contracts as well as dynamics. Their scores are not interchangeable.",
  ],
  [
    "explorer",
    "Public synthetic benchmark",
    "Four public reference models, three independent roots, six normalized error cells. No athlete observations.",
  ],
  [
    "model-atlas",
    "Original model recovery",
    "Nine model families, two repeats each. Source-faithful execution is engineering evidence, not predictive accuracy.",
  ],
  [
    "native-mechanics",
    "Native mechanics",
    "Integrate gross force between supplied concentric onset and takeoff; retain force and impulse as separate targets.",
  ],
  [
    "research-evidence",
    "Evidence and limits",
    "Loading a model and checking its execution do not authenticate an empirical cohort or authorize scoring.",
  ],
  [
    "research-docs",
    "Reproduce and inspect",
    "Follow the public methods, API and source records to reproduce the work.",
  ],
];
function Export({ id }: { id: string }) {
  return (
    <button
      className="atlas-export"
      onClick={() => {
        const svg = document.querySelector(`#${id} svg`);
        if (!svg) return;
        const blob = new Blob([new XMLSerializer().serializeToString(svg)], {
          type: "image/svg+xml",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${id.replace("gate7", "model")}.svg`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }}
    >
      Export SVG
    </button>
  );
}
export function ResearchTour() {
  const [step, setStep] = useState(0);
  return (
    <aside className="shell atlas-tour" aria-label="90 second research tour">
      <div>
        <span className="eyebrow">THE RESEARCH IN 90 SECONDS</span>
        <h2>{chapters[step][1]}</h2>
        <p>{chapters[step][2]}</p>
      </div>
      <div className="tour-controls">
        <span>{step + 1} / 7 · ~12 seconds per chapter</span>
        <progress value={step + 1} max={7} aria-label="Tour progress" />
        <div>
          <button disabled={step === 0} onClick={() => setStep(step - 1)}>
            Previous
          </button>
          <a href={`#${chapters[step][0]}`}>Explore chapter ↗</a>
          <button disabled={step === 6} onClick={() => setStep(step + 1)}>
            Next
          </button>
        </div>
      </div>
    </aside>
  );
}
export default function Gate7Atlas() {
  const [model, setModel] = useState("M8");
  const [repeat, setRepeat] = useState("r0");
  const [duration, setDuration] = useState(0.4);
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    const m =
      atlas.models.find(
        (entry) => familySlug(entry.id) === q.get("architecture"),
      )?.id ?? q.get("gate7");
    const r =
      q.get("run") === "1"
        ? "r0"
        : q.get("run") === "2"
          ? "r1"
          : q.get("repeat");
    if (atlas.models.some((x) => x.id === m)) setModel(m!);
    if (r === "r0" || r === "r1") setRepeat(r);
  }, []);
  const selected = atlas.models.find((m) => m.id === model)!;
  const architecture = selected.architecture.replace(
    /M[0-8]/g,
    (id) => familyNames[id],
  );
  const signal = mechanics(duration);
  const update = (m: string, r: string) => {
    setModel(m);
    setRepeat(r);
    const url = new URL(location.href);
    url.searchParams.delete("gate7");
    url.searchParams.delete("repeat");
    url.searchParams.set("architecture", familySlug(m));
    url.searchParams.set("run", String(Number(r.slice(1)) + 1));
    url.hash = "model-atlas";
    history.replaceState(null, "", url);
  };
  return (
    <div className="atlas-wrap">
      <span id="gate7" aria-hidden="true" />
      <section
        id="model-atlas"
        className="shell atlas-section"
        aria-labelledby="model-atlas-title"
      >
        <div className="atlas-heading">
          <div>
            <span className="eyebrow">04 / MODEL RECONSTRUCTION</span>
            <h2 id="model-atlas-title">
              Recover the model.
              <br />
              <em>Follow its architecture.</em>
            </h2>
          </div>
          <p>
            Nine architectures, each recovered from two original runs. This
            atlas describes recovered execution contracts; it is not a
            model-performance leaderboard.
          </p>
        </div>
        <div className="atlas-stats">
          <div>
            <strong>09 × 02</strong>
            <span>architectures × original runs</span>
          </div>
          <div>
            <strong>72 h / 7 d</strong>
            <span>forecast horizons</span>
          </div>
          <div>
            <strong>Source parity</strong>
            <span>reconstruction, not accuracy</span>
          </div>
        </div>
        <div className="atlas-grid">
          <figure id="gate7-routes" className="atlas-panel">
            <figcaption>
              <span className="eyebrow">ORIGINAL MODELS / REPEATED RUNS</span>
              <h3>Explore an architecture</h3>
            </figcaption>
            <div className="route-matrix">
              {atlas.models.map((m) => (
                <div key={m.id}>
                  <strong>{familyNames[m.id]}</strong>
                  {m.repeats.map((r) => (
                    <button
                      key={r}
                      aria-pressed={model === m.id && repeat === r}
                      onClick={() => update(m.id, r)}
                    >
                      {repeatLabel(r)} <span>Source matched</span>
                    </button>
                  ))}
                  <span className={m.id >= "M4" ? "atlas-warning" : ""}>
                    {m.cuda}
                  </span>
                </div>
              ))}
            </div>
            <p>
              CPU: exact original-source parity in the documented qualification.
              CUDA: compatibility with saved predictions under the historical
              rule, not a new score.
            </p>
            <a href={source(atlas.sources[0].path)}>Qualification record ↗</a>
          </figure>
          <article className="atlas-panel atlas-detail" aria-live="polite">
            <span className="eyebrow">
              {repeatLabel(repeat)} · RECOVERED ARCHITECTURE
            </span>
            <h3>{familyNames[model]}</h3>
            <figure id="gate7-architecture">
              <svg
                viewBox="0 0 560 180"
                role="img"
                aria-label={`${familyNames[model]}: ${architecture}`}
              >
                <title>{architecture}</title>
                {[
                  "39 → raw backbone",
                  ...(Number(model.slice(1)) >= 3
                    ? [
                        model === "M3"
                          ? "4×4 → pointwise 4→32"
                          : "4×4 → GRU 4→32",
                      ]
                    : []),
                  ...(Number(model.slice(1)) >= 5
                    ? ["H72/D7 → embedding 2×8"]
                    : []),
                  ...(Number(model.slice(1)) >= 6
                    ? [
                        model === "M6"
                          ? "Basis first 2 → 16"
                          : "Basis all 5 → 16",
                      ]
                    : []),
                ].map((label, i) => (
                  <g key={label}>
                    <rect
                      x="4"
                      y={i * 42 + 4}
                      width="245"
                      height="34"
                      rx="0"
                      fill={theme.surface}
                      stroke={theme.cobalt}
                    />
                    <text x="14" y={i * 42 + 26} fill={theme.ink} fontSize="13">
                      {label}
                    </text>
                    <path
                      d={`M249 ${i * 42 + 21} H280 V87 H306`}
                      fill="none"
                      stroke={theme.cobalt}
                    />
                  </g>
                ))}
                <rect
                  x="306"
                  y="60"
                  width="245"
                  height="56"
                  fill={theme.surface}
                  stroke={theme.cobalt}
                />
                <text
                  x="428"
                  y="84"
                  textAnchor="middle"
                  fill={theme.ink}
                  fontSize="13"
                >
                  {model === "M8"
                    ? "Residual + linear basis heads"
                    : "Concatenation → output head"}
                </text>
                <text
                  x="428"
                  y="104"
                  textAnchor="middle"
                  fill={theme.cobalt}
                  fontSize="12"
                >
                  2 additive innovations
                </text>
              </svg>
              <figcaption>{architecture}</figcaption>
              <Export id="gate7-architecture" />
            </figure>
            <details className="atlas-reference">
              <summary>Technical reference and model identifier</summary>
              <p>
                Original model {model}, {repeatLabel(repeat).toLowerCase()} (
                {repeat}).
              </p>
            </details>
            <dl>
              <dt>Model inputs</dt>
              <dd>{selected.inputs}</dd>
              <dt>Preprocessing</dt>
              <dd>
                Frozen train-only means and sample standard deviations (ddof=1);
                zero scales become one. Standardize then cast to float32. No
                refit.
              </dd>
              <dt>Predicted quantities</dt>
              <dd>
                Mean concentric-force innovation (N/kg), then net-impulse innovation (m/s). Identity
                output transform; baseline addition is separate.
              </dd>
              <dt>Reproduction evidence</dt>
              <dd>
                {selected.cpu}. {selected.cuda} against saved CUDA predictions.
              </dd>
            </dl>
            <a
              href={source(
                model === "M8"
                  ? atlas.sources[6].path
                  : model === "M7"
                    ? atlas.sources[5].path
                    : atlas.sources[4].path,
              )}
            >
              Inspect implementation ↗
            </a>
            <p className="atlas-warning">
              No checkpoint bytes, fitted scalers, private predictions or cohort
              records are distributed.
            </p>
          </article>
        </div>
      </section>
      <section
        id="native-mechanics"
        className="shell atlas-section"
        aria-labelledby="native-title"
      >
        <div className="atlas-heading">
          <div>
            <span className="eyebrow">05 / MEASUREMENT METHODS</span>
            <h2 id="native-title">
              From contact
              <br />
              <em>to a forecast target.</em>
            </h2>
          </div>
          <p>
            Analytical schematic, not a measured jump or recovered prediction.
            Events are supplied by the caller: the source does not detect
            concentric onset or takeoff.
          </p>
        </div>
        <div className="atlas-grid">
          <figure id="native-force" className="atlas-panel">
            <figcaption>
              <span className="eyebrow">FORCE-TIME INTEGRATION</span>
              <h3>Same mean force. Different impulse.</h3>
            </figcaption>
            <label htmlFor="concentric-duration">
              Concentric duration: {duration.toFixed(2)} s
            </label>
            <input
              id="concentric-duration"
              type="range"
              min="0.2"
              max="0.6"
              step="0.01"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
            />
            <svg
              viewBox="0 0 560 260"
              role="img"
              aria-label={`Linear gross force, 75 kg system mass; mean ${signal.force.toFixed(5)} N/kg, net impulse ${signal.impulse.toFixed(3)} m/s`}
            >
              <title>
                Analytical force-time signal: F(t) = 75 × (9.80665 + 8 − 4t/T) N
              </title>
              <path d="M60 25 V210 H530" fill="none" stroke={theme.muted} />
              {[0, 500, 1000, 1500].map((f) => (
                <g key={f}>
                  <path d={`M60 ${210 - f * 0.1} H530`} stroke={theme.grid} />
                  <text
                    x="50"
                    y={215 - f * 0.1}
                    textAnchor="end"
                    fill={theme.muted}
                    fontSize="12"
                  >
                    {f}
                  </text>
                </g>
              ))}
              <path
                d={`M60 ${210 - 75 * 9.80665 * 0.1} H${60 + duration * 750}`}
                stroke={theme.terracotta}
                strokeDasharray="5 4"
              />
              <path
                d={`M60 ${210 - 75 * 9.80665 * 0.1} V${210 - signal.samples[0].force * 0.1} L${60 + duration * 750} ${210 - signal.samples[40].force * 0.1} V${210 - 75 * 9.80665 * 0.1} Z`}
                fill={theme.cobalt}
                fillOpacity=".18"
              />
              <path
                d={`M60 ${210 - signal.samples[0].force * 0.1} L${60 + duration * 750} ${210 - signal.samples[40].force * 0.1}`}
                stroke={theme.cobalt}
                strokeWidth="3"
              />
              <text x="60" y="233" fill={theme.ink} fontSize="12">
                0 / supplied onset
              </text>
              <text
                x={60 + duration * 750}
                y="253"
                textAnchor="end"
                fill={theme.ink}
                fontSize="12"
              >
                {duration.toFixed(2)} s / takeoff
              </text>
              <text x="65" y="20" fill={theme.ink} fontSize="12">
                Gross force (N)
              </text>
              <text x="360" y="125" fill={theme.terracotta} fontSize="12">
                Weight = 735.49875 N
              </text>
            </svg>
            <p>
              Mass 75 kg; g = 9.80665 m/s². Shaded area is net impulse. Fixed
              time axis: 0–0.6 s. F(t) = 75 × (g + 8 − 4t/T) N.
            </p>
            <dl>
              <dt>Gross time-mean force</dt>
              <dd>{signal.force.toFixed(5)} N/kg</dd>
              <dt>Net concentric impulse</dt>
              <dd>{signal.impulse.toFixed(5)} m/s</dd>
            </dl>
            <Export id="native-force" />
            <details>
              <summary>Exact signal values / 41 trapezoid nodes</summary>
              <table>
                <thead>
                  <tr>
                    <th>Time (s)</th>
                    <th>Gross force (N)</th>
                  </tr>
                </thead>
                <tbody>
                  {signal.samples.map(
                    (s: { time: number; force: number }, i: number) => (
                      <tr key={i}>
                        <td>{s.time.toPrecision(10)}</td>
                        <td>{s.force.toPrecision(10)}</td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </details>
            <a href={source(atlas.sources[3].path)}>
              Measurement equations and implementation limits ↗
            </a>
          </figure>
          <div className="atlas-panel">
            <span className="eyebrow">ASSESSMENT WINDOWS</span>
            <h3>What is known at origin?</h3>
            <figure id="native-time">
              <svg
                viewBox="0 0 560 200"
                role="img"
                aria-label="Baseline uses two latest qualifying assessments between minus 240 and minus 24 hours. H72 window 66 to 78 hours. D7 window 156 to 180 hours."
              >
                <title>
                  Native assessment windows, hours relative to origin
                </title>
                <path d="M25 110 H535" stroke={theme.muted} />
                {atlas.windows.map((w) => (
                  <g key={w.id}>
                    <rect
                      x={25 + (w.start + 240) * 1.2}
                      y="65"
                      width={(w.end - w.start) * 1.2}
                      height="45"
                      fill={
                        w.id === "baseline" ? theme.terracotta : theme.cobalt
                      }
                    />
                    <text
                      x={25 + (w.start + 240) * 1.2}
                      y="50"
                      fill={theme.ink}
                      fontSize="14"
                    >
                      {w.id}
                    </text>
                  </g>
                ))}
                <path
                  d="M313 20 V145"
                  stroke={theme.ink}
                  strokeDasharray="4 4"
                />
                <text
                  x="313"
                  y="170"
                  textAnchor="middle"
                  fill={theme.ink}
                  fontSize="12"
                >
                  origin / 0 h
                </text>
                <text x="25" y="140" fill={theme.ink} fontSize="12">
                  −240 h
                </text>
                <text
                  x="535"
                  y="140"
                  textAnchor="end"
                  fill={theme.ink}
                  fontSize="12"
                >
                  +180 h
                </text>
              </svg>
              <Export id="native-time" />
            </figure>
            <table>
              <caption>Native windows, hours relative to origin</caption>
              <thead>
                <tr>
                  <th>Assessment</th>
                  <th>Inclusive window</th>
                </tr>
              </thead>
              <tbody>
                {atlas.windows.map((w) => (
                  <tr key={w.id}>
                    <th>{w.id}</th>
                    <td>
                      {w.start} to {w.end} h
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p>
              Three distinct valid trials → arithmetic mean assessment. Two
              latest distinct qualifying assessments in −240 to −24 h →
              arithmetic mean baseline.
            </p>
            <p>
              History, query and planned exposures must be authenticated as
              known at origin. Future measurements and realized future exposure
              are unavailable to inference.
            </p>
            <p className="atlas-warning">
              Native H72/D7 four-cell errors in N/kg and m/s cannot be pooled or
              ranked against the public synthetic benchmark’s H24/H48/H72
              six-cell NRMSE.
            </p>
          </div>
        </div>
      </section>
      <span id="gate7-evidence" aria-hidden="true" />
      <section id="research-evidence" className="shell atlas-section">
        <span className="eyebrow">
          06 / EVIDENCE DOES NOT TRANSFER AUTOMATICALLY
        </span>
        <h2>Every arrow has a condition.</h2>
        <figure id="gate7-flow" className="atlas-panel">
          <figcaption>FROM SOURCE CODE TO SCIENTIFIC EVALUATION</figcaption>
          <ol className="atlas-flow">
            {[
              "Documented source definitions",
              "Verified configuration and model weights",
              "Safe model loading on CPU",
              "Synthetic execution check",
              "Measurement, permissions and target checks",
              "Separately authorized research study",
            ].map((label, i) => (
              <li key={label}>
                <span>0{i + 1}</span>
                {label}
              </li>
            ))}
          </ol>
          <p>
            Each step requires its own evidence. Public software supplies
            interfaces; an installation supplies neither restricted artifacts
            nor evaluation authority.
          </p>
          <a
            href={source(
              "docs/GATE7_TARGET_AUTHORITY_AND_DATA_READINESS_V1.md",
            )}
          >
            Inspect target-authority boundaries ↗
          </a>
        </figure>
        <div className="atlas-limits">
          <h3>Unresolved limits are part of the result.</h3>
          <p>
            The recurrent and basis-augmented families remain outside the
            recorded tolerances for saved CUDA predictions. Rich-history
            row-count differences remain qualified. There is no empirical
            athlete validation, clinical utility claim or production-readiness
            finding. Windows/NVDA manual acceptance is pending; automated
            accessibility checks do not replace it.
          </p>
        </div>
      </section>
      <section id="research-docs" className="shell atlas-section">
        <span className="eyebrow">07 / OPEN METHODS</span>
        <h2>Read it. Reproduce it. Inspect it.</h2>
        <div className="atlas-docs">
          {[
            ["Documentation index", "docs/INDEX.md"],
            ["Install and API", "README.rst"],
            ["Native measurement", "docs/GATE7_NATIVE_MEASUREMENT_V1.md"],
            [
              "Evaluation protocol",
              "docs/GATE7_SCIENTIFIC_EVALUATION_PROTOCOL_V1.md",
            ],
            ["Model recovery", "docs/RES-546_INFERENCE_VERIFICATION.md"],
            ["Citation", "CITATION.cff"],
            ["Rights and license", "LICENSE"],
            ["Figure regeneration", "website/docs/GATE7_ATLAS.md"],
          ].map(([label, path]) => (
            <a
              key={path}
              href={`${repository}/blob/main/${path}`}
            >
              {label} ↗
            </a>
          ))}
        </div>
        <details className="atlas-panel">
          <summary>Source files and verification hashes</summary>
          {atlas.sources.map((s, index) => (
            <p key={s.path}>
              <a href={source(s.path)}>{sourceTitles[index]}</a>
              <br />
              <code className="atlas-hash">SHA-256 {s.sha256}</code>
            </p>
          ))}
        </details>
        <p>
          Synthetic benchmark results and recovered-model contracts have
          separate source snapshots. This presentation does not publish a
          software release.
        </p>
      </section>
    </div>
  );
}
