"use client";
import { useRef } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, INK, MUTED, SANS, linear } from "./chart-kit";
import { fmtInt, manuscript } from "@/lib/manuscript";
import { plotTheme } from "@/lib/plot-theme.mjs";
import { useUrlState } from "@/lib/use-url-state";

const { classes, rows } = manuscript.data.evidence;
const rich = manuscript.data.richHistory;
const CLASS_COLOR: Record<string, string> = {
  "public-source": plotTheme.ridge,
  "public-regenerable": "#1f7a6d",
  "private-summary": plotTheme.ochre,
  "not-established": plotTheme.structured,
};
const FILTERS = ["all", ...classes.map((c) => c.id)] as const;
type Filter = (typeof FILTERS)[number];

export default function EvidenceFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [filter, setFilter] = useUrlState<Filter>("f10class", "all", FILTERS);
  const W = 800;
  const H = 430;
  const x = linear([-60, 40], [100, 300]);
  const cx0 = 594;
  const cw = 50;

  return (
    <FigureFrame
      number={10}
      title="Historical reproducibility gaps and the evidence boundary"
      svgRef={svg}
      units="Panel (a): horizon rows (public reconstruction minus historical record). Panel (b): evidence categories, not a numerical confidence score."
      interpretation={
        <p>
          The public reconstruction of the retired rich-history materialization does not reproduce the historical
          split membership: training has {fmtInt(rich[0].publicRows)} rows against {fmtInt(rich[0].historicalRows)} recorded (
          {rich[0].difference}), validation {fmtInt(rich[1].publicRows)} against {fmtInt(rich[1].historicalRows)} (+{rich[1].difference}). Panel (b)
          classifies what each result rests on. Only the synthetic benchmark and these row counts are regenerable from
          public files; the original route qualification is a private record with a public summary; athlete validity is
          not established.
        </p>
      }
      limitations={[
        "Row-count differences are membership differences in preserved splits, not response effects or uncertainty intervals.",
        "Evidence categories follow the manuscript's classification; they are not a score and are not combined into one.",
        "Historical CUDA mismatches (M4–M8) remain unexplained; the site does not attempt to explain them.",
      ]}
      table={{
        caption: "Evidence class of each result as described in the manuscript; and rich-history row counts.",
        columns: ["Result", "Evidence class"],
        rows: [
          ...rows.map((r) => [r.claim, classes.find((c) => c.id === r.class)!.label]),
          ...rich.map((r) => [`Rich-history ${r.split} rows: public ${r.publicRows} vs historical ${r.historicalRows}`, `difference ${r.difference > 0 ? "+" : ""}${r.difference}`]),
        ],
      }}
      json={{ richHistory: rich, evidence: manuscript.data.evidence }}
    >
      <div className="pub-controls">
        <div className="pub-segmented" role="group" aria-label="Evidence class">
          <span className="pub-control-label" aria-hidden="true">
            Evidence
          </span>
          <div>
            {FILTERS.map((f) => (
              <button key={f} type="button" aria-pressed={filter === f} onClick={() => setFilter(f)}>
                {f !== "all" && <span className="pub-swatch" style={{ background: CLASS_COLOR[f] }} aria-hidden="true" />}
                {f === "all" ? "All" : classes.find((c) => c.id === f)!.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="pub-chart" tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="fig10-svg-title" className="pub-svg">
          <title id="fig10-svg-title">
            Rich-history row-count differences of minus 48 training and plus 4 validation rows, and a matrix assigning ten results to four evidence classes.
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (a) Rich-history materialization
          </text>
          <line x1={x(0)} x2={x(0)} y1={50} y2={190} stroke={INK} />
          {rich.map((r, i) => {
            const yy = 82 + i * 70;
            const col = r.difference < 0 ? plotTheme.ridge : plotTheme.structured;
            return (
              <g key={r.split}>
                <text x={92} y={yy + 4} textAnchor="end" fontFamily={SANS} fontSize={11.5} fill={INK}>
                  {r.split === "training" ? "Training" : "Validation"}
                </text>
                <line x1={x(0)} x2={x(r.difference)} y1={yy} y2={yy} stroke={col} strokeWidth={6} />
                <circle cx={x(r.difference)} cy={yy} r={6} fill={col} stroke="#fffdf7" strokeWidth={1.5} />
                <text x={r.difference < 0 ? x(r.difference / 2) : x(r.difference) + 10} y={r.difference < 0 ? yy - 12 : yy + 4} textAnchor={r.difference < 0 ? "middle" : "start"} fontFamily={SANS} fontSize={12} fontWeight={700} fill={col}>
                  {r.difference > 0 ? "+" : ""}
                  {r.difference} rows
                </text>
                <text x={x(0)} y={yy + 24} textAnchor="middle" fontFamily={SANS} fontSize={10.5} fill={MUTED}>
                  public {fmtInt(r.publicRows)} vs historical {fmtInt(r.historicalRows)}
                </text>
              </g>
            );
          })}
          <AxisX scale={x} y={200} values={[-60, -40, -20, 0, 20, 40]} label="Public − historical (horizon rows)" />
          <text x={8} y={268} fontFamily={SANS} fontSize={10.5} fill={MUTED}>
            <tspan x={8} dy={0}>Membership differences in the preserved splits;</tspan>
            <tspan x={8} dy={14}>not response effects or uncertainty intervals.</tspan>
          </text>
          <text x={340} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (b) Evidence boundary: what each result rests on
          </text>
          {classes.map((c, j) => (
            <text key={c.id} x={cx0 + j * cw + cw / 2} y={44} textAnchor="middle" fontFamily={SANS} fontSize={9.5} fontWeight={700} fill={CLASS_COLOR[c.id]}>
              <tspan x={cx0 + j * cw + cw / 2} dy={0}>
                {c.label.split(" ")[0]}
              </tspan>
              <tspan x={cx0 + j * cw + cw / 2} dy={12}>
                {c.label.split(" ").slice(1).join(" ")}
              </tspan>
            </text>
          ))}
          {rows.map((r, i) => {
            const yy = 78 + i * 33;
            const faded = filter !== "all" && filter !== r.class;
            return (
              <g key={r.claim} opacity={faded ? 0.25 : 1}>
                {i % 2 === 0 && <rect x={340} y={yy - 16} width={W - 344} height={33} fill="#f4f2ea" />}
                <text x={348} y={yy + 4} fontFamily={SANS} fontSize={10.5} fill={INK}>
                  {r.claim}
                </text>
                {classes.map((c, j) =>
                  c.id === r.class ? (
                    <circle key={c.id} cx={cx0 + j * cw + cw / 2} cy={yy} r={7} fill={CLASS_COLOR[c.id]} />
                  ) : (
                    <circle key={c.id} cx={cx0 + j * cw + cw / 2} cy={yy} r={1.6} fill="#b8bdb9" />
                  ),
                )}
              </g>
            );
          })}
        </svg>
      </div>
      <ul className="pub-class-list">
        {classes.map((c) => (
          <li key={c.id}>
            <span className="pub-swatch" style={{ background: CLASS_COLOR[c.id] }} aria-hidden="true" /> <strong>{c.label}:</strong> {c.description}
          </li>
        ))}
      </ul>
    </FigureFrame>
  );
}
