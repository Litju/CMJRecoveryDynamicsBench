"use client";
import { useRef, useState } from "react";
import FigureFrame from "./figure-frame";
import { AxisY, INK, MUTED, Marker, SANS, Segmented, Toggles, linear, ticks, useTooltip, GRID } from "./chart-kit";
import {
  MODELS,
  OUTCOMES,
  ROOTS,
  ROOT_SHAPE,
  cellOf,
  fmt,
  manuscript,
  type ModelKey,
  type OutcomeKey,
  type RootKey,
} from "@/lib/manuscript";
import { useUrlState } from "@/lib/use-url-state";

const HORIZONS = ["H24", "H48", "H72"] as const;
const OUTCOME_KEYS: OutcomeKey[] = ["force", "impulse"];
const SCALES = { full: [0, 3.2], detail: [0.55, 1.1] } as const;
const W = 330;
const H = 236;
const M = { l: 58, r: 14, t: 34, b: 30 };

export default function SixCellFigure() {
  const container = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useUrlState("f6scale", "full", ["full", "detail"] as const);
  const [root, setRoot] = useUrlState("f6root", "all", ["all", "A", "B", "C"] as const);
  const [focus, setFocus] = useUrlState(
    "f6cell",
    "H24-force",
    HORIZONS.flatMap((h) => OUTCOME_KEYS.map((o) => `${h}-${o}` as const)),
  );
  const [shown, setShown] = useState<ModelKey[]>(MODELS.map((m) => m.key));
  const tip = useTooltip();
  const [fh, fo] = focus.split("-") as [string, OutcomeKey];
  const focusCell = cellOf(fh, fo);
  const y = linear([...SCALES[scale]] as [number, number], [H - M.b, M.t]);
  const yTicks = scale === "full" ? [0, 0.5, 1, 1.5, 2, 2.5, 3] : ticks(0.6, 1.1, 5);
  const xs = linear([0, MODELS.length - 1], [M.l + 26, W - M.r - 26]);

  const rows = manuscript.data.sixCell.cells.flatMap((c) =>
    MODELS.map((m) => {
      const v = c.models[m.key as ModelKey];
      return [
        `${c.horizon} ${OUTCOMES[c.outcome as OutcomeKey].short}`,
        m.label,
        c.unit,
        ...v.roots.map((r) => Number(fmt(r.nrmse, 6))),
        Number(fmt(v.mean, 6)),
        Number(fmt(v.sampleSd, 6)),
      ];
    }),
  );

  return (
    <FigureFrame
      number={6}
      title="Four reference models across six outcome–horizon cells"
      svgRef={container}
      units="NRMSE is dimensionless (cell RMSE ÷ that cell's truth population SD). Force cells score mean concentric-force innovation (N/kg); impulse cells score net-impulse innovation (m/s). Units are never pooled."
      interpretation={
        <p>
          In every cell, ridge regression and the structured comparator sit below the training-mean
          baseline (NRMSE ≈ 1), which is in turn far below zero innovation. The gap between ridge and
          structured is small and consistent across roots; both lose accuracy as the horizon lengthens
          from H24 to H72. Root points show descriptive variation across three fixed draws of one
          generator.
        </p>
      }
      limitations={[
        "Public synthetic study only: three roots of one declared generator, not athlete cohorts or out-of-distribution tests.",
        "No interval or test is shown; root spread is not a confidence interval.",
        "This is the H24/H48/H72 synthetic six-cell experiment, not the native H72/D7 four-cell evaluation.",
      ]}
      table={{
        caption: "Recorded cellwise NRMSE by root, stored across-root mean and root-to-root sample SD (ddof = 1).",
        columns: ["Cell", "Model", "Target unit", "Root A", "Root B", "Root C", "Mean", "Sample SD"],
        rows,
      }}
      json={manuscript.data.sixCell}
      readout={
        <>
          <strong>
            {fh} · {OUTCOMES[fo].label} ({OUTCOMES[fo].unit}):
          </strong>{" "}
          {MODELS.map((m) => {
            const v = focusCell.models[m.key as ModelKey];
            return (
              <span key={m.key} className="pub-readout-item">
                <span className="pub-swatch" style={{ background: m.color }} aria-hidden="true" />
                {m.label} {fmt(root === "all" ? v.mean : v.roots[ROOTS.indexOf(root as RootKey)].nrmse)}
              </span>
            );
          })}
          <span className="pub-muted">{root === "all" ? "across-root mean" : `root ${root}`}</span>
        </>
      }
    >
      <div className="pub-controls">
        <Segmented
          label="Axis"
          value={scale}
          onChange={setScale}
          options={[
            { value: "full", label: "Full range 0–3.2", title: "Shared axis including zero innovation" },
            { value: "detail", label: "Detail 0.55–1.1", title: "Shared zoom; zero innovation is off-scale" },
          ]}
        />
        <Segmented
          label="Root"
          value={root}
          onChange={setRoot}
          options={[
            { value: "all", label: "All roots" },
            ...ROOTS.map((r) => ({ value: r, label: `Root ${r}` })),
          ]}
        />
        <Toggles
          label="Models"
          values={shown}
          onChange={setShown}
          options={MODELS.map((m) => ({ value: m.key, label: m.short, color: m.color }))}
        />
      </div>
      <div className="pub-chart" ref={tip.host} tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <div className="pub-grid-2" ref={container} data-cols={2}>
          {HORIZONS.flatMap((h) =>
            OUTCOME_KEYS.map((o) => {
              const c = cellOf(h, o);
              const active = focus === `${h}-${o}`;
              return (
                <svg
                  key={`${h}-${o}`}
                  data-panel
                  viewBox={`0 0 ${W} ${H}`}
                  role="img"
                  aria-label={`${h}, ${OUTCOMES[o].label}: ${MODELS.map((m) => `${m.label} mean NRMSE ${fmt(c.models[m.key as ModelKey].mean)}`).join("; ")}.`}
                  className={active ? "pub-panel is-active" : "pub-panel"}
                  onClick={() => setFocus(`${h}-${o}`)}
                >
                  <rect x={0} y={0} width={W} height={H} fill="#fffdf7" />
                  <text x={M.l} y={16} fontFamily={SANS} fontSize={12} fontWeight={700} fill={INK}>
                    {h} · {OUTCOMES[o].short}
                  </text>
                  <text x={W - M.r} y={16} fontFamily={SANS} fontSize={11} fill={MUTED} textAnchor="end">
                    target {c.unit}
                  </text>
                  <AxisY scale={y} x={M.l} values={yTicks} format={(v) => v.toFixed(scale === "full" ? 1 : 2)} grid={[M.l, W - M.r]} label="NRMSE" />
                  <line x1={M.l} x2={W - M.r} y1={y(1)} y2={y(1)} stroke={MUTED} strokeDasharray="4 3" strokeWidth={1} />
                  <text x={W - M.r} y={y(1) - 4} fontFamily={SANS} fontSize={10} fill={MUTED} textAnchor="end">
                    cell-mean predictor = 1
                  </text>
                  {MODELS.map((m, i) => {
                    if (!shown.includes(m.key as ModelKey)) return null;
                    const v = c.models[m.key as ModelKey];
                    const x = xs(i);
                    const off = v.mean > SCALES[scale][1];
                    if (off)
                      return (
                        <g key={m.key}>
                          <polygon points={`${x},${M.t - 2} ${x - 6},${M.t + 8} ${x + 6},${M.t + 8}`} fill={m.color} />
                          <text x={x} y={M.t + 22} fontFamily={SANS} fontSize={10} fill={INK} textAnchor="middle">
                            {fmt(v.mean, 2)}↑
                          </text>
                          <text x={x} y={H - 8} fontFamily={SANS} fontSize={10} fill={MUTED} textAnchor="middle">
                            {m.short}
                          </text>
                        </g>
                      );
                    return (
                      <g key={m.key}>
                        <line x1={x - 22} x2={x + 22} y1={y(v.mean)} y2={y(v.mean)} stroke={INK} strokeWidth={2} />
                        {active && (
                          <text x={x + 24} y={y(v.mean) - 6} fontFamily={SANS} fontSize={10} fill={INK}>
                            {fmt(v.mean, 3)}
                          </text>
                        )}
                        {v.roots.map((r, k) => {
                          const rk = ROOTS[k];
                          const dim = root !== "all" && root !== rk;
                          return (
                            <g
                              key={rk}
                              onMouseEnter={(e) =>
                                tip.show(e, (
                                  <>
                                    <strong>{m.label}</strong> · root {rk}
                                    <br />
                                    {h} {OUTCOMES[o].short}
                                    <br />
                                    NRMSE {fmt(r.nrmse, 6)}
                                    <br />
                                    RMSE {fmt(r.rmse, 5)} {c.unit} · truth SD {fmt(r.truthSd, 5)} {c.unit}
                                    <br />
                                    {r.rows.toLocaleString()} rows
                                  </>
                                ))
                              }
                              onMouseLeave={tip.hide}
                            >
                              <circle cx={x + (k - 1) * 10} cy={y(r.nrmse)} r={11} fill="transparent" />
                              <Marker shape={ROOT_SHAPE[rk]} x={x + (k - 1) * 10} y={y(r.nrmse)} r={4.2} fill={m.color} opacity={dim ? 0.22 : 1} />
                            </g>
                          );
                        })}
                        <text x={x} y={H - 8} fontFamily={SANS} fontSize={10} fill={MUTED} textAnchor="middle">
                          {m.short}
                        </text>
                      </g>
                    );
                  })}
                  <rect x={0.5} y={0.5} width={W - 1} height={H - 1} fill="none" stroke={active ? INK : GRID} strokeWidth={active ? 1.5 : 1} data-export-ignore />
                </svg>
              );
            }),
          )}
        </div>
        {tip.node}
      </div>
      <div className="pub-legend">
        {MODELS.map((m) => (
          <span key={m.key}>
            <span className="pub-swatch" style={{ background: m.color }} aria-hidden="true" /> {m.label}
          </span>
        ))}
        <span>▬ stored across-root mean</span>
        <span>● A ■ B ▲ C roots</span>
      </div>
      <p className="pub-hint">Select a panel to read its exact values below. Hover a mark for its root-level RMSE and truth SD.</p>
      <label className="pub-visually-hidden" htmlFor="f6-cell-select">
        Inspect cell
      </label>
      <select id="f6-cell-select" className="pub-select" value={focus} onChange={(e) => setFocus(e.target.value as typeof focus)}>
        {HORIZONS.flatMap((h) =>
          OUTCOME_KEYS.map((o) => (
            <option key={`${h}-${o}`} value={`${h}-${o}`}>
              Inspect {h} · {OUTCOMES[o].label}
            </option>
          )),
        )}
      </select>
    </FigureFrame>
  );
}
