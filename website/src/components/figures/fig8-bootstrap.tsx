"use client";
import { useRef } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, INK, MUTED, Marker, SANS, Segmented, linear, useTooltip } from "./chart-kit";
import { ROOT_SHAPE, fmt, fmtInt, manuscript, modelMeta, type RootKey } from "@/lib/manuscript";
import { useUrlState } from "@/lib/use-url-state";

const b = manuscript.data.bootstrap;

export default function BootstrapFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [view, setView] = useUrlState("f8view", "nrmse", ["nrmse", "delta"] as const);
  const tip = useTooltip();
  const W = 720;
  const rowH = 40;
  const x0 = 210;
  const x1 = W - 40;
  const top = 50;
  const H = top + b.rows.length * rowH + 56;
  const domain: [number, number] = view === "nrmse" ? [0.72, 0.79] : [-1.8, 0];
  const x = linear(domain, [x0, x1]);
  const tickValues = view === "nrmse" ? [0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79] : [-1.8, -1.5, -1.2, -0.9, -0.6, -0.3, 0];

  return (
    <FigureFrame
      number={8}
      title="Recorded camp-bootstrap uncertainty within each evaluation root"
      svgRef={svg}
      units="NRMSE and paired NRMSE differences, dimensionless. Intervals are stored 95% percentile intervals."
      interpretation={
        <p>
          Within each root, the stored intervals for ridge regression lie below those for the structured
          comparator, and every paired model-minus-zero interval lies well below zero: each model has
          lower error than zero innovation inside that root. Intervals come from {fmtInt(b.replicates)} paired
          resamples of {b.campsPerRoot} whole camps per root (all {b.episodesPerCamp} episodes and three
          horizons kept together; PCG64 seed {fmtInt(b.seed)}).
        </p>
      }
      limitations={[
        "No ridge-versus-structured interval was recorded; non-overlap here is not a recorded test of that difference.",
        "Intervals are conditional on one root; they are not intervals across roots and do not reflect refitting on new training samples.",
        "The clustering unit is the synthetic camp, not an athlete.",
      ]}
      table={{
        caption: `Stored 95% percentile intervals (${b.interval}); ${fmtInt(b.replicates)} replicates; clustering unit: ${b.unit}.`,
        columns: ["Root", "Model", "Mean six-cell NRMSE", "Lower", "Upper", "Paired Δ vs zero", "Δ lower", "Δ upper", "Valid replicates"],
        rows: b.rows.map((r) => [
          r.root,
          modelMeta(r.model).label,
          Number(fmt(r.estimate, 6)),
          Number(fmt(r.interval[0], 6)),
          Number(fmt(r.interval[1], 6)),
          Number(fmt(r.deltaVsZero, 6)),
          Number(fmt(r.deltaInterval[0], 6)),
          Number(fmt(r.deltaInterval[1], 6)),
          r.replicates,
        ]),
      }}
      json={b}
    >
      <div className="pub-controls">
        <Segmented
          label="Panel"
          value={view}
          onChange={setView}
          options={[
            { value: "nrmse", label: "(a) Mean six-cell NRMSE" },
            { value: "delta", label: "(b) Paired difference vs zero innovation" },
          ]}
        />
      </div>
      <div className="pub-chart" ref={tip.host} tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="fig8-svg-title" className="pub-svg">
          <title id="fig8-svg-title">
            {view === "nrmse"
              ? "Stored 95% camp-bootstrap intervals for mean six-cell NRMSE, ridge and structured, roots A to C."
              : "Stored 95% paired intervals for model-minus-zero-innovation NRMSE, ridge and structured, roots A to C."}
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={22} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            {view === "nrmse" ? "(a) Mean six-cell NRMSE with stored 95% interval" : "(b) Model − zero-innovation NRMSE (paired), stored 95% interval"}
          </text>
          <AxisX
            scale={x}
            y={top + b.rows.length * rowH}
            values={tickValues}
            format={(v) => v.toFixed(view === "nrmse" ? 2 : 1)}
            grid={[top - 10, top + b.rows.length * rowH]}
            label={view === "nrmse" ? "Mean six-cell NRMSE (lower is better)" : "Paired NRMSE difference (below 0 favours the named model)"}
          />
          {view === "delta" && <line x1={x(0)} x2={x(0)} y1={top - 10} y2={top + b.rows.length * rowH} stroke={INK} strokeWidth={1.5} />}
          {b.rows.map((r, i) => {
            const m = modelMeta(r.model);
            const yy = top + i * rowH + rowH / 2;
            const est = view === "nrmse" ? r.estimate : r.deltaVsZero;
            const [lo, hi] = view === "nrmse" ? r.interval : r.deltaInterval;
            return (
              <g
                key={`${r.root}-${r.model}`}
                onMouseEnter={(e) =>
                  tip.show(e, (
                    <>
                      <strong>{m.label}</strong> · root {r.root}
                      <br />
                      estimate {fmt(est, 6)}
                      <br />
                      95% [{fmt(lo, 6)}, {fmt(hi, 6)}]
                      <br />
                      {fmtInt(r.replicates)} valid replicates
                    </>
                  ))
                }
                onMouseLeave={tip.hide}
              >
                <rect x={x0} y={yy - rowH / 2} width={x1 - x0} height={rowH} fill="transparent" />
                <text x={x0 - 12} y={yy + 4} textAnchor="end" fontFamily={SANS} fontSize={11.5} fill={INK}>
                  Root {r.root} · {m.label}
                </text>
                <line x1={x(lo)} x2={x(hi)} y1={yy} y2={yy} stroke={m.color} strokeWidth={3} strokeLinecap="round" />
                <line x1={x(lo)} x2={x(lo)} y1={yy - 6} y2={yy + 6} stroke={m.color} strokeWidth={2} />
                <line x1={x(hi)} x2={x(hi)} y1={yy - 6} y2={yy + 6} stroke={m.color} strokeWidth={2} />
                <Marker shape={ROOT_SHAPE[r.root as RootKey]} x={x(est)} y={yy} r={5.5} fill={m.color} />
                <text x={x(hi) + 10} y={yy + 4} fontFamily={SANS} fontSize={10.5} fill={MUTED}>
                  {fmt(est)} [{fmt(lo)}, {fmt(hi)}]
                </text>
              </g>
            );
          })}
        </svg>
        {tip.node}
      </div>
      <p className="pub-note">
        <strong>Not recorded:</strong> a ridge-versus-structured interval, an across-root interval, and
        cell-level intervals. The site does not compute or approximate them.
      </p>
    </FigureFrame>
  );
}
