"use client";
import { useRef } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, AxisY, INK, MUTED, Marker, SANS, Segmented, linear, useTooltip } from "./chart-kit";
import { ROOTS, ROOT_SHAPE, fmt, manuscript, signed, type RootKey } from "@/lib/manuscript";
import { plotTheme } from "@/lib/plot-theme.mjs";
import { useUrlState } from "@/lib/use-url-state";

const a = manuscript.data.ablations;
const COLOR = { ridge: plotTheme.ridge, structured: plotTheme.structured } as const;
const fullOf = (family: string) => a.variants.find((v) => v.key === `${family}_full`)!;
const ridgeFull = fullOf("ridge");
// Ridge ablations ordered by recorded increase over full ridge (largest first).
const ranked = a.variants
  .filter((v) => v.family === "ridge" && v.key !== "ridge_full")
  .sort((x, y) => y.mean - x.mean);
const ridgeN = a.nested.series.find((s) => s.family === "ridge")!.points;
const structN = a.nested.series.find((s) => s.family === "structured")!.points;

export default function AblationFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [root, setRoot] = useUrlState("f9root", "all", ["all", "A", "B", "C"] as const);
  const tip = useTooltip();
  const W = 760;
  const H = 360;
  const ax = linear([0.725, 0.935], [190, 370]);
  const rowH = 40;
  const top = 58;
  const bxs = linear([24, 96], [480, 690]);
  const bys = linear([0.728, 0.782], [H - 54, top - 6]);
  const dim = (rk: RootKey) => root !== "all" && root !== rk;

  const tableRows = [
    ...a.variants.map((v) => {
      const full = fullOf(v.family);
      return [v.label, "all camps (96)", ...v.roots.map((x) => Number(fmt(x, 6))), Number(fmt(v.mean, 6)), v.key === full.key ? null : Number(fmt(v.mean - full.mean, 6))];
    }),
    ...a.nested.series.flatMap((s) =>
      s.points.map((p) => [
        s.family === "ridge" ? "Ridge (nested)" : "Structured (nested)",
        `${p.camps} camps`,
        ...p.roots.map((x) => Number(fmt(x, 6))),
        Number(fmt(p.mean, 6)),
        null,
      ]),
    ),
  ];

  return (
    <FigureFrame
      number={9}
      title="Recorded ablations and nested training-camp counts"
      svgRef={svg}
      units="Mean six-cell NRMSE, dimensionless. Training subsets are counted in synthetic camps."
      interpretation={
        <p>
          Among the recorded ridge ablations, removing {ranked[0].label.replace("Ridge − ", "")} raises the mean
          six-cell NRMSE most ({fmt(ranked[0].mean)}, {signed(ranked[0].mean - ridgeFull.mean)}), followed by{" "}
          {ranked[1].label.replace("Ridge − ", "")} ({fmt(ranked[1].mean)}, {signed(ranked[1].mean - ridgeFull.mean)});
          removing {ranked[2].label.replace("Ridge − ", "")} changes it by only {signed(ranked[2].mean - ridgeFull.mean)}.
          Nested training subsets change the scores very little: ridge {fmt(ridgeN[0].mean)} at {ridgeN[0].camps} camps
          versus {fmt(ridgeN[2].mean)} at {ridgeN[2].camps}; structured {fmt(structN[0].mean)} versus{" "}
          {fmt(structN[2].mean)}. Ridge stays below the structured comparator at every size. Evaluation roots and the
          full-data regularization are held fixed.
        </p>
      }
      limitations={[
        "Descriptive diagnostics under the registered protocol: no interval, no causal feature-importance claim.",
        "Camp counts are synthetic generator units; this is not athlete-level sample efficiency.",
        "Nested subsets follow one seeded permutation of the 96 public training camps; other orderings were not recorded.",
      ]}
      table={{
        caption: "Recorded mean six-cell NRMSE by evaluation root; Δ is the change from the full model of the same family.",
        columns: ["Variant", "Training set", "Root A", "Root B", "Root C", "Mean", "Δ vs full"],
        rows: tableRows,
      }}
      json={a}
    >
      <div className="pub-controls">
        <Segmented
          label="Highlight root"
          value={root}
          onChange={setRoot}
          options={[{ value: "all", label: "All roots" }, ...ROOTS.map((rk) => ({ value: rk, label: `Root ${rk}` }))]}
        />
      </div>
      <div className="pub-chart" ref={tip.host} tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="fig9-svg-title" className="pub-svg">
          <title id="fig9-svg-title">
            Ablation dot plot and nested training-camp line chart of recorded mean six-cell NRMSE for ridge and structured models.
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={22} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (a) Recorded ablations
          </text>
          <text x={420} y={22} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (b) Nested training-camp results
          </text>
          <AxisX scale={ax} y={top + a.variants.length * rowH} values={[0.75, 0.8, 0.85, 0.9]} format={(v) => v.toFixed(2)} grid={[top - 12, top + a.variants.length * rowH]} label="Mean six-cell NRMSE" />
          {a.variants.map((v, i) => {
            const yy = top + i * rowH + rowH / 2;
            const full = fullOf(v.family);
            const color = COLOR[v.family as keyof typeof COLOR];
            return (
              <g key={v.key}>
                <text x={182} y={yy + 4} textAnchor="end" fontFamily={SANS} fontSize={11} fill={INK} fontWeight={v.key === full.key ? 700 : 400}>
                  {v.label}
                </text>
                <line x1={ax(Math.min(...v.roots))} x2={ax(Math.max(...v.roots))} y1={yy} y2={yy} stroke={color} strokeWidth={2} opacity={0.45} />
                {v.roots.map((x, k) => {
                  const rk = ROOTS[k];
                  return (
                    <g key={rk} onMouseEnter={(e) => tip.show(e, `${v.label}, root ${rk}: ${fmt(x, 6)}`)} onMouseLeave={tip.hide}>
                      <circle cx={ax(x)} cy={yy} r={9} fill="transparent" />
                      <Marker shape={ROOT_SHAPE[rk]} x={ax(x)} y={yy} r={4.6} fill={color} opacity={dim(rk) ? 0.2 : 1} />
                    </g>
                  );
                })}
                <line x1={ax(v.mean)} x2={ax(v.mean)} y1={yy - 9} y2={yy + 9} stroke={INK} strokeWidth={2} />
                <text x={ax(Math.max(...v.roots)) + 9} y={yy + 4} fontFamily={SANS} fontSize={10.5} fill={MUTED}>
                  {fmt(v.mean)}
                  {v.key !== full.key ? ` (${signed(v.mean - full.mean)})` : ""}
                </text>
              </g>
            );
          })}
          <AxisX scale={bxs} y={H - 54} values={a.nested.camps} format={(v) => String(v)} label="Training camps (α fixed at its full-data value)" />
          <AxisY scale={bys} x={480} values={[0.73, 0.74, 0.75, 0.76, 0.77, 0.78]} format={(v) => v.toFixed(2)} grid={[480, 690]} />
          {a.nested.series.map((s) => {
            const color = COLOR[s.family as keyof typeof COLOR];
            const dash = s.family === "structured" ? "6 4" : undefined;
            return (
              <g key={s.family}>
                {ROOTS.map((rk, k) => (
                  <g key={rk} opacity={dim(rk) ? 0.18 : 0.75}>
                    <polyline points={s.points.map((p) => `${bxs(p.camps)},${bys(p.roots[k])}`).join(" ")} fill="none" stroke={color} strokeWidth={1.2} strokeDasharray={dash} />
                    {s.points.map((p) => (
                      <g key={p.camps} onMouseEnter={(e) => tip.show(e, `${s.family === "ridge" ? "Ridge" : "Structured"}, ${p.camps} camps, root ${rk}: ${fmt(p.roots[k], 6)}`)} onMouseLeave={tip.hide}>
                        <circle cx={bxs(p.camps)} cy={bys(p.roots[k])} r={8} fill="transparent" />
                        <Marker shape={ROOT_SHAPE[rk]} x={bxs(p.camps)} y={bys(p.roots[k])} r={4} fill={color} />
                      </g>
                    ))}
                  </g>
                ))}
                <polyline points={s.points.map((p) => `${bxs(p.camps)},${bys(p.mean)}`).join(" ")} fill="none" stroke={INK} strokeWidth={2.2} strokeDasharray={dash} />
                <text x={bxs(96) + 8} y={bys(s.points[2].mean) + 4} fontFamily={SANS} fontSize={10.5} fill={INK}>
                  {fmt(s.points[2].mean)}
                </text>
                <text x={bxs(24) - 8} y={bys(s.points[0].mean) + 4} fontFamily={SANS} fontSize={10.5} fill={INK} textAnchor="end">
                  {fmt(s.points[0].mean)}
                </text>
                <text
                  x={585}
                  y={s.family === "ridge" ? bys(Math.min(...s.points[1].roots)) + 18 : bys(Math.max(...s.points[1].roots)) - 10}
                  fontFamily={SANS}
                  fontSize={11}
                  fill={color}
                  textAnchor="middle"
                >
                  {s.family === "ridge" ? "ridge regression (solid)" : "structured comparator (dashed)"}
                </text>
              </g>
            );
          })}
        </svg>
        {tip.node}
      </div>
      <div className="pub-legend">
        <span>● A ■ B ▲ C roots</span>
        <span>▮ / thick line: across-root mean</span>
        <span>Δ: change from the full model of the same family</span>
      </div>
    </FigureFrame>
  );
}
