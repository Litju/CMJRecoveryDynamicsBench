"use client";
import { useRef } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, INK, MUTED, SANS, linear } from "./chart-kit";
import { fmtInt, manuscript } from "@/lib/manuscript";
import { plotTheme } from "@/lib/plot-theme.mjs";
import { useUrlState } from "@/lib/use-url-state";

const d = manuscript.data.design;
const SPLITS = [
  { id: "training", label: "Training", data: d.training, color: plotTheme.ink },
  { id: "development", label: "Development", data: d.development, color: "#586773" },
  ...d.roots.map((r) => ({ id: `root-${r.id}`, label: `Evaluation root ${r.id}`, data: r, color: plotTheme.ridge })),
] as const;
type SplitId = (typeof SPLITS)[number]["id"];

export default function DesignFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [sel, setSel] = useUrlState<SplitId>("f2split", "training", SPLITS.map((s) => s.id));
  const split = SPLITS.find((s) => s.id === sel)!;
  const perCamp = split.data.episodes / split.data.camps;
  const W = 760;
  const sq = 15;
  const gap = 3;
  const bx = linear([0, 72000], [170, 690]);
  const groups = [
    { id: "training", x: 12, cols: 12 },
    { id: "development", x: 260, cols: 4 },
    { id: "root-A", x: 360, cols: 4 },
    { id: "root-B", x: 460, cols: 4 },
    { id: "root-C", x: 560, cols: 4 },
  ];
  const H = 470;

  return (
    <FigureFrame
      number={2}
      title="Public synthetic study design: camps, episodes, horizons and split boundaries"
      svgRef={svg}
      units="Counts of camps, episodes and horizon rows. One camp = 250 episodes = 750 horizon rows."
      interpretation={
        <p>
          The study trains on 96 camps ({fmtInt(d.training.episodes)} episodes, {fmtInt(d.training.rows)} horizon
          rows), selects hyperparameters on 16 development camps, and evaluates on three fixed roots of 16 camps
          each ({fmtInt(d.roots[0].rows)} rows per root; 4,000 per outcome–horizon cell). Every episode contributes
          H24, H48 and H72 queries that stay inside one split. Grouping keys, labels and target-time fields are
          excluded from the {d.contract.sourceFields}-field predictor schema.
        </p>
      }
      limitations={[
        "The three evaluation roots are draws from the same synthetic generator; they are not independent athlete populations or an out-of-distribution test.",
        "Participants and camps are synthetic generator units; no human records are involved.",
      ]}
      table={{
        caption: "Recorded split sizes and grouping-key counts from the fixed-mode study receipt.",
        columns: ["Split", "Camps", "Episodes", "Horizon rows", "Unique participants", "Unique queries", "Seed kind"],
        rows: SPLITS.map((s) => [s.label, s.data.camps, s.data.episodes, s.data.rows, s.data.participants, s.data.queries, s.data.seedKind]),
      }}
      json={d}
      readout={
        <>
          <strong>{split.label}:</strong> {split.data.camps} camps · {fmtInt(split.data.episodes)} episodes ({perCamp} per camp) ·{" "}
          {fmtInt(split.data.rows)} horizon rows · {fmtInt(split.data.participants)} unique participants ·{" "}
          {fmtInt(split.data.queries)} unique queries
        </>
      }
    >
      <div className="pub-controls">
        <div className="pub-segmented" role="group" aria-label="Split">
          <span className="pub-control-label" aria-hidden="true">
            Split
          </span>
          <div>
            {SPLITS.map((s) => (
              <button key={s.id} type="button" aria-pressed={s.id === sel} onClick={() => setSel(s.id)}>
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="pub-chart" tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="fig2-svg-title" className="pub-svg">
          <title id="fig2-svg-title">
            Camp grid: 96 training camps, 16 development camps and three evaluation roots of 16 camps; horizon-row counts per split; one episode yields H24, H48 and H72 queries.
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (a) Each square is one camp (250 episodes, 750 horizon rows)
          </text>
          {groups.map((g) => {
            const s = SPLITS.find((x) => x.id === g.id)!;
            const on = sel === g.id;
            return (
              <g key={g.id} onClick={() => setSel(s.id)} className="pub-clickable">
                <text x={g.x} y={46} fontFamily={SANS} fontSize={11} fill={INK} fontWeight={on ? 700 : 400}>
                  {s.label.replace("Evaluation root", "Root")} · {s.data.camps}
                </text>
                {Array.from({ length: s.data.camps }, (_, i) => (
                  <rect
                    key={i}
                    x={g.x + (i % g.cols) * (sq + gap)}
                    y={56 + Math.floor(i / g.cols) * (sq + gap)}
                    width={sq}
                    height={sq}
                    fill={s.color}
                    opacity={on ? 1 : 0.35}
                  />
                ))}
              </g>
            );
          })}
          <line x1={248} x2={248} y1={34} y2={200} stroke={MUTED} strokeDasharray="3 3" />
          <line x1={348} x2={348} y1={34} y2={200} stroke={INK} strokeWidth={1.5} />
          <text x={352} y={150} fontFamily={SANS} fontSize={10.5} fill={MUTED}>
            <tspan x={360} dy={0}>Fixed roots: same generator,</tspan>
            <tspan x={360} dy={14}>separate caller-supplied seeds.</tspan>
            <tspan x={360} dy={14}>No camp, episode, participant or query</tspan>
            <tspan x={360} dy={14}>identity crosses a split boundary.</tspan>
          </text>
          <text x={8} y={240} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (b) Horizon rows per split
          </text>
          {SPLITS.map((s, i) => {
            const y = 262 + i * 20;
            return (
              <g key={s.id} onClick={() => setSel(s.id)} className="pub-clickable">
                <text x={160} y={y + 4} textAnchor="end" fontFamily={SANS} fontSize={11} fill={INK} fontWeight={sel === s.id ? 700 : 400}>
                  {s.label}
                </text>
                <rect x={170} y={y - 6} width={bx(s.data.rows) - 170} height={12} fill={s.color} opacity={sel === s.id ? 1 : 0.45} />
                <text
                  x={s.data.rows > 50000 ? bx(s.data.rows) - 6 : bx(s.data.rows) + 6}
                  y={y + 4}
                  textAnchor={s.data.rows > 50000 ? "end" : "start"}
                  fontFamily={SANS}
                  fontSize={10.5}
                  fill={s.data.rows > 50000 ? "#fffdf7" : INK}
                >
                  {fmtInt(s.data.rows)} rows · {fmtInt(s.data.episodes)} episodes
                </text>
              </g>
            );
          })}
          <AxisX scale={bx} y={262 + 5 * 20 - 4} values={[0, 12000, 24000, 36000, 48000, 60000, 72000]} format={(v) => `${v / 1000}k`} />
          <text x={8} y={428} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (c) One episode → three queries
          </text>
          <g transform="translate(280 436)" fontFamily={SANS} fontSize={11} fill={INK}>
            <rect x={0} y={-14} width={86} height={22} fill="#fffdf7" stroke={INK} />
            <text x={43} y={1} textAnchor="middle">
              episode
            </text>
            <line x1={86} x2={130} y1={-3} y2={-3} stroke={INK} />
            <line x1={108} x2={108} y1={-3} y2={14} stroke={INK} />
            <line x1={108} x2={340} y1={14} y2={14} stroke={INK} />
            {["H24", "H48", "H72"].map((h, i) => (
              <g key={h}>
                <line x1={160 + i * 90} x2={160 + i * 90} y1={8} y2={14} stroke={INK} />
                <rect x={130 + i * 90} y={-14} width={60} height={22} fill={plotTheme.ridge} />
                <text x={160 + i * 90} y={1} textAnchor="middle" fill="#fffdf7" fontWeight={700}>
                  {h}
                </text>
              </g>
            ))}
          </g>
        </svg>
      </div>
      <dl className="pub-dl pub-dl-inline">
        <dt>Predictor schema</dt>
        <dd>
          {d.contract.sourceFields} source fields → {d.contract.encodedFields} encoded columns; horizon: {d.contract.horizonEncoding}
        </dd>
        <dt>Grouping keys as predictors</dt>
        <dd>{d.contract.groupingKeysAsPredictors ? "yes" : "no"}</dd>
        <dt>Target labels as predictors</dt>
        <dd>{d.contract.targetLabelsAsPredictors ? "yes" : "no"}</dd>
        <dt>Target-time / post-query fields</dt>
        <dd>{d.contract.targetTimeFields}</dd>
        <dt>Preprocessing</dt>
        <dd>{d.contract.preprocessing}</dd>
        <dt>Generated targets</dt>
        <dd>
          <code>{d.training.labels.join(", ")}</code>
        </dd>
      </dl>
    </FigureFrame>
  );
}
