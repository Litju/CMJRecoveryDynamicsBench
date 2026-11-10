import { ArrowRight, FileText } from "lucide-react";
import { MODELS, PAPER, fmt, manuscript, sixCellScore, type ModelKey } from "@/lib/manuscript";
import { plotTheme } from "@/lib/plot-theme.mjs";

const d = manuscript.data;
const routesPass = d.routes.filter((r) => r.savedCuda === "pass").length;
const edges = d.genealogy.filter((g) => g.parent).length;

const FINDINGS = [
  {
    id: "RQ1",
    href: "/methods/#fig-1",
    figure: "Fig. 1, 2, 10",
    finding: `${d.genealogy.length} formulations and ${d.architectures.families.length} neural families are identified; ${edges} direct parent links are recorded and ${d.genealogy.length - edges} remain unresolved. The public rich-history reconstruction differs from the historical split by −48 training and +4 validation rows.`,
  },
  {
    id: "RQ2",
    href: "/models/#fig-4",
    figure: "Fig. 3, 4",
    finding: `Recovered CPU inference matches the original CPU outputs on all ${d.routes.length} routes. Against archived GPU arrays, ${routesPass} routes (M0–M3) pass and ${d.routes.length - routesPass} (both repeats of M4–M8) fail the unchanged tolerance.`,
  },
  {
    id: "RQ3",
    href: "/results/#fig-6",
    figure: "Fig. 6–9",
    finding: `On the public synthetic benchmark, ridge regression has the lowest mean six-cell NRMSE (${fmt(sixCellScore("ridge_full", "mean"), 6)}), then the structured comparator (${fmt(sixCellScore("structured_full", "mean"), 6)}), training mean (${fmt(sixCellScore("training_constant", "mean"), 6)}) and zero innovation (${fmt(sixCellScore("zero_innovation", "mean"), 6)}). This does not estimate athlete performance.`,
  },
];

function GlanceChart() {
  const W = 520;
  const H = 300;
  const x0 = 150;
  const x1 = 500;
  const sx = (v: number) => x0 + (v / 3) * (x1 - x0);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="glance-title glance-desc" className="glance-chart">
      <title id="glance-title">Evidence at a glance</title>
      <desc id="glance-desc">
        Recorded mean six-cell NRMSE of four reference models on the public synthetic benchmark, and the archived-GPU
        qualification status of the 18 original model routes.
      </desc>
      <rect width={W} height={H} fill="#fffdf7" />
      <text x={16} y={26} fontSize={12.5} fontWeight={700} fill={plotTheme.ink} fontFamily="Geist, Arial, sans-serif">
        Public synthetic benchmark · mean six-cell NRMSE (lower is better)
      </text>
      {[0, 0.5, 1, 1.5, 2, 2.5, 3].map((v) => (
        <g key={v}>
          <line x1={sx(v)} x2={sx(v)} y1={40} y2={170} stroke={plotTheme.grid} />
          <text x={sx(v)} y={186} textAnchor="middle" fontSize={10.5} fill={plotTheme.muted} fontFamily="Geist, Arial, sans-serif">
            {v.toFixed(1)}
          </text>
        </g>
      ))}
      {MODELS.map((m, i) => {
        const v = sixCellScore(m.key as ModelKey, "mean");
        const y = 58 + i * 30;
        return (
          <g key={m.key} fontFamily="Geist, Arial, sans-serif">
            <text x={x0 - 10} y={y + 4} textAnchor="end" fontSize={11.5} fill={plotTheme.ink}>
              {m.label}
            </text>
            <line x1={x0} x2={sx(v)} y1={y} y2={y} stroke={m.color} strokeWidth={2} />
            <circle cx={sx(v)} cy={y} r={6} fill={m.color} stroke="#fffdf7" strokeWidth={2} />
            <text x={sx(v) + 10} y={y + 4} fontSize={11} fill={plotTheme.ink}>
              {fmt(v, 6)}
            </text>
          </g>
        );
      })}
      <text x={16} y={222} fontSize={12.5} fontWeight={700} fill={plotTheme.ink} fontFamily="Geist, Arial, sans-serif">
        18 original routes · archived-GPU comparison
      </text>
      {d.routes.map((r, i) => (
        <g key={r.route}>
          <rect x={16 + i * 27 + (i % 2 ? -2 : 0)} y={232} width={23} height={20} fill={r.savedCuda === "pass" ? "#1f7a6d" : plotTheme.structured}>
            <title>{`${r.model} repeat ${r.repeat}: archived GPU ${r.savedCuda === "pass" ? "within" : "outside"} tolerance`}</title>
          </rect>
          {i % 2 === 0 && (
            <text x={16 + i * 27 + 24} y={266} textAnchor="middle" fontSize={10} fill={plotTheme.ink} fontFamily="Geist, Arial, sans-serif">
              {r.model}
            </text>
          )}
        </g>
      ))}
      <text x={16} y={288} fontSize={10.5} fill={plotTheme.muted} fontFamily="Geist, Arial, sans-serif">
        Pairs = repeats r0, r1 · green: within tolerance (8) · red: outside (10) · CPU source exact on all 18
      </text>
    </svg>
  );
}

export default function ResearchOverview() {
  const p = manuscript.paper;
  return (
    <section id="overview" className="shell overview" aria-labelledby="overview-title">
      <div className="overview-grid">
        <div className="overview-copy">
          <p className="pub-eyebrow">
            Computational research · V3 manuscript, unsubmitted draft · software v{p.releaseVersion}
          </p>
          <h1 id="overview-title">Reconstructing a historical countermovement-jump recovery research program</h1>
          <p className="overview-title-paper">{p.title}</p>
          <p className="overview-summary">
            This retrospective case study recovers what a partially preserved machine-learning research archive can
            still support: eight scientific formulations, nine neural model families with their numerical
            qualification, the native force–time measurement contract, and a public synthetic benchmark. It keeps
            source-equivalent computation, compatibility with archived outputs, public reproducibility and
            predictive validity as separate questions.
          </p>
          <div className="overview-actions">
            <a className="button primary" href={PAPER.href}>
              <FileText size={16} aria-hidden="true" /> Read the research paper
            </a>
            <a className="button" href="/results/">
              Explore scientific results <ArrowRight size={15} aria-hidden="true" />
            </a>
            <a className="button" href="/models/">
              Inspect recovered models <ArrowRight size={15} aria-hidden="true" />
            </a>
            <a className="button" href="/evidence/">
              Reproduce the evidence <ArrowRight size={15} aria-hidden="true" />
            </a>
          </div>
        </div>
        <figure className="overview-figure">
          <GlanceChart />
          <figcaption>
            Recorded values from the pinned V3 manuscript package. Synthetic benchmark scores and route
            qualification answer different questions and are never combined.
          </figcaption>
        </figure>
      </div>

      <ul className="overview-scope" aria-label="Research scope">
        <li>
          <strong>{d.genealogy.length}</strong> recorded formulations
        </li>
        <li>
          <strong>{d.architectures.families.length} × 2</strong> neural families × repeats = {d.routes.length} routes
        </li>
        <li>
          <strong>3 × 16</strong> evaluation roots × camps, one generator
        </li>
        <li>
          <strong>6</strong> outcome–horizon cells (H24–H72)
        </li>
      </ul>

      <h2 className="overview-h2">Research questions and verified findings</h2>
      <ol className="overview-rqs">
        {p.researchQuestions.map((q) => {
          const f = FINDINGS.find((x) => x.id === q.id)!;
          return (
            <li key={q.id}>
              <p className="pub-rq-id">
                {q.id} · {q.title}
              </p>
              <p className="overview-q">{q.question}</p>
              <p className="overview-finding">{f.finding}</p>
              <a href={f.href} className="pub-inline-link">
                {f.figure} — explore <ArrowRight size={13} aria-hidden="true" />
              </a>
            </li>
          );
        })}
      </ol>

      <aside className="overview-limits" aria-labelledby="limits-title">
        <h2 id="limits-title">What this research does not establish</h2>
        <ul>
          <li>Real-athlete recovery-forecasting accuracy, transportability or clinical utility.</li>
          <li>A public rerun of the original checkpoints: their weights and inference arrays are private.</li>
          <li>The cause of the M4–M8 archived-GPU differences, or the exact historical split membership.</li>
          <li>Statistical superiority of ridge over the structured comparator: no such interval or test was recorded.</li>
        </ul>
        <p>
          The synthetic benchmark (H24/H48/H72, six cells) and the native measurement contract (H72/D7, four cells)
          are separate experiments.
        </p>
      </aside>

      <div className="overview-story-intro">
        <h2>The interactive story</h2>
        <p>
          Below, the original Observatory walks through the measurement, the synthetic world, the research lineage,
          the benchmark explorer, the Recovery Lab and the model atlas.
        </p>
      </div>
    </section>
  );
}
