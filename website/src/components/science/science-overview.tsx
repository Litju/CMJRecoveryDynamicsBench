import { ArrowRight, FileText } from "lucide-react";
import flagship from "@/data/flagship.json";
import { fmt, MODELS, sixCellScore, manuscript, type ModelKey } from "@/lib/manuscript";
import { plotTheme } from "@/lib/plot-theme.mjs";
import { CHAPTERS } from "./chapter-head";

const paper = flagship.files.find((f) => f.id === "illustrated")!;
const abl = (key: string) => manuscript.data.ablations.variants.find((v) => v.key === key)!.mean;

function ScoreChart() {
  const W = 520;
  const sx = (v: number) => 150 + (v / 3) * 350;
  return (
    <svg viewBox={`0 0 ${W} 190`} role="img" aria-labelledby="sc-title sc-desc" className="glance-chart">
      <title id="sc-title">Four reference models, mean six-cell NRMSE</title>
      <desc id="sc-desc">
        Zero innovation {fmt(sixCellScore("zero_innovation", "mean"), 6)}, training mean{" "}
        {fmt(sixCellScore("training_constant", "mean"), 6)}, ridge {fmt(sixCellScore("ridge_full", "mean"), 6)},
        structured comparator {fmt(sixCellScore("structured_full", "mean"), 6)}. Lower is better. Synthetic data.
      </desc>
      <rect width={W} height={190} fill="#fffdf7" />
      <text x={16} y={24} fontSize={12.5} fontWeight={700} fill={plotTheme.ink} fontFamily="Geist, Arial, sans-serif">
        Mean six-cell NRMSE, synthetic benchmark (lower is better)
      </text>
      {[0, 1, 2, 3].map((v) => (
        <g key={v}>
          <line x1={sx(v)} x2={sx(v)} y1={38} y2={150} stroke={plotTheme.grid} />
          <text x={sx(v)} y={166} textAnchor="middle" fontSize={10.5} fill={plotTheme.muted} fontFamily="Geist, Arial, sans-serif">
            {v}
          </text>
        </g>
      ))}
      {MODELS.map((m, i) => {
        const v = sixCellScore(m.key as ModelKey, "mean");
        const y = 56 + i * 27;
        return (
          <g key={m.key} fontFamily="Geist, Arial, sans-serif">
            <text x={140} y={y + 4} textAnchor="end" fontSize={11.5} fill={plotTheme.ink}>
              {m.label}
            </text>
            <line x1={150} x2={sx(v)} y1={y} y2={y} stroke={m.color} strokeWidth={2} />
            <circle cx={sx(v)} cy={y} r={6} fill={m.color} stroke="#fffdf7" strokeWidth={2} />
            <text x={sx(v) + 10} y={y + 4} fontSize={11} fill={plotTheme.ink}>
              {fmt(v, 6)}
            </text>
          </g>
        );
      })}
      <text x={16} y={184} fontSize={10.5} fill={plotTheme.muted} fontFamily="Geist, Arial, sans-serif">
        One synthetic generator · three evaluation roots · not athlete accuracy
      </text>
    </svg>
  );
}

const FINDINGS = [
  {
    id: "RQ1",
    title: "Measurement",
    q: "How are CMJ mean concentric force and net impulse defined, measured in the synthetic system, and expressed as baseline-relative change?",
    a: "Gross time-mean force per unit mass (N/kg) and net impulse (m/s) over the concentric phase; each assessment is a three-trial mean, and the target is criterion minus baseline. Peak force is a different quantity.",
    href: "#ch1",
    link: "Chapter 1",
  },
  {
    id: "RQ2",
    title: "Recovery modeling",
    q: "How are exposure, time, history and participant variation represented?",
    a: "A two-mode exponential response (fixed 24 h and 84 h, a synthetic assumption) with exposure-, participant- and camp-dependent amplitudes; nine original neural families encode history, horizon and a schedule basis.",
    href: "#ch2",
    link: "Chapters 2–3",
  },
  {
    id: "RQ3",
    title: "Prediction",
    q: "What do the four-model synthetic experiments show about prediction error?",
    a: `Mean six-cell NRMSE: ridge ${fmt(sixCellScore("ridge_full", "mean"), 6)}, structured ${fmt(sixCellScore("structured_full", "mean"), 6)}, training mean ${fmt(sixCellScore("training_constant", "mean"), 6)}, zero ${fmt(sixCellScore("zero_innovation", "mean"), 6)}. Descriptive, synthetic, one generator.`,
    href: "#ch5",
    link: "Chapter 5",
  },
  {
    id: "RQ4",
    title: "Limitations",
    q: "What do uncertainty, ablations and diagnostics support?",
    a: `Removing current exposure (${fmt(abl("ridge_no_current_exposure"), 6)}) or prior history (${fmt(abl("ridge_no_prior_history"), 6)}) raised ridge error; removing participant context did not (${fmt(abl("ridge_no_participant_context"), 6)}). Intervals compare with zero only.`,
    href: "#ch6",
    link: "Chapter 6",
  },
];

export default function ScienceOverview() {
  return (
    <section id="overview" className="shell overview" aria-labelledby="overview-title">
      <div className="overview-grid">
        <div className="overview-copy">
          <p className="pub-eyebrow">Computational and synthetic study · owner-review draft · not peer reviewed</p>
          <h1 id="overview-title">One jump, three days: modeling how countermovement-jump outcomes change after training</h1>
          <p className="overview-title-paper">{flagship.title}</p>
          <p className="overview-summary">
            A countermovement jump yields a force–time curve. Its gross mean concentric force and net impulse can be
            tracked against a baseline. This research defines those quantities, builds a controlled synthetic world in
            which training exposure changes them over the next three days, describes nine neural architectures for
            forecasting that change, and reports what four simple reference models actually predicted. No athlete was
            measured; the results describe a simulated forecasting task.
          </p>
          <div className="overview-actions">
            <a className="button primary" href="/paper/">
              <FileText size={16} aria-hidden="true" /> Read the flagship paper
            </a>
            <a className="button" href="#ch1">
              Start with the jump <ArrowRight size={15} aria-hidden="true" />
            </a>
            <a className="button" href="/results/">
              Jump to the results <ArrowRight size={15} aria-hidden="true" />
            </a>
          </div>
          <p className="pub-muted">
            PDF: <a href={paper.href}>full illustrated paper</a> ({paper.pages} pages)
          </p>
        </div>
        <figure className="overview-figure">
          <ScoreChart />
          <figcaption>
            Recorded values of the public four-model synthetic experiment. The nine original neural architectures were
            not scored in it.
          </figcaption>
        </figure>
      </div>

      <nav aria-label="Seven chapters" className="sci-chapters">
        <h2 className="overview-h2">Seven chapters</h2>
        <ol>
          {CHAPTERS.map((c) => (
            <li key={c.id}>
              <a href={`#${c.id}`}>
                <span>{c.n}</span> {c.q}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <h2 className="overview-h2">Four research questions</h2>
      <ol className="overview-rqs">
        {FINDINGS.map((f) => (
          <li key={f.id}>
            <p className="pub-rq-id">
              {f.id} · {f.title}
            </p>
            <p className="overview-q">{f.q}</p>
            <p className="overview-finding">{f.a}</p>
            <a href={f.href} className="pub-inline-link">
              {f.link} <ArrowRight size={13} aria-hidden="true" />
            </a>
          </li>
        ))}
      </ol>

      <aside className="overview-limits" aria-labelledby="limits-title">
        <h2 id="limits-title">What this research does not establish</h2>
        <ul>
          <li>Real-athlete recovery forecasting, clinical use or transportability: every result is simulated.</li>
          <li>That the fixed 24 h and 84 h modes are biological recovery constants: they are assumptions of the simulator.</li>
          <li>Any ranking of the nine original neural networks: they were not scored in the public experiment.</li>
          <li>That ridge outperforms the structured comparator beyond the recorded descriptive values: no paired interval was recorded.</li>
        </ul>
        <p>
          How the original architectures were reconstructed and numerically qualified is in{" "}
          <a href="#ch7">Chapter 7</a> and a companion paper.
        </p>
      </aside>
    </section>
  );
}
