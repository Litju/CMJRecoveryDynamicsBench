"use client";
import { useRef, useState } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, INK, MUTED, Marker, SANS, Segmented, linear, useTooltip, GRID } from "./chart-kit";
import {
  MODELS,
  OUTCOMES,
  ROOTS,
  ROOT_SHAPE,
  cellValue,
  fmt,
  manuscript,
  signed,
  sixCellScore,
  type ModelKey,
  type OutcomeKey,
  type RootKey,
} from "@/lib/manuscript";
import { useUrlState } from "@/lib/use-url-state";

const LOW = [40, 84, 184]; // cobalt
const MID = [236, 235, 228]; // neutral paper gray
const HIGH = [182, 66, 43]; // vermilion
const mix = (a: number[], b: number[], t: number) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
/** Diverging encoding centred at NRMSE = 1 (the value of a cell-mean predictor). */
export function heat(v: number) {
  const rgb = v <= 1 ? mix(MID, LOW, Math.min(1, (1 - v) / 0.45)) : mix(MID, HIGH, Math.min(1, (v - 1) / 2.1));
  const lum = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255;
  return { fill: `rgb(${rgb.join(",")})`, text: lum < 0.5 ? "#fffdf7" : INK };
}

const cells = manuscript.data.sixCell.cells;
const ROW_LABELS = [
  ...cells.map((c) => `${c.horizon} ${OUTCOMES[c.outcome as OutcomeKey].short}`),
  "Six-cell mean",
];

export default function HeatmapFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [root, setRoot] = useUrlState("f7root", "mean", ["mean", "A", "B", "C"] as const);
  const [sel, setSel] = useState<{ row: number; col: number }>({ row: 6, col: 2 });
  const tip = useTooltip();
  const r = root as RootKey | "mean";
  const value = (row: number, model: ModelKey) =>
    row < 6 ? cellValue(cells[row], model, r) : sixCellScore(model, r);
  const W = 720;
  const cw = 104;
  const ch = 38;
  const x0 = 170;
  const y0 = 46;
  const bx = linear([0, 0.05], [x0, x0 + cw * 4]);
  const by0 = y0 + ch * 7 + 70;
  const H = by0 + 6 * 26 + 50;

  const selModel = MODELS[sel.col].key as ModelKey;
  const selValue = value(sel.row, selModel);
  const rowValues = MODELS.map((m) => value(sel.row, m.key as ModelKey));
  const rank = [...rowValues].sort((a, b) => a - b).indexOf(selValue) + 1;
  const vsRidge = selValue - value(sel.row, "ridge_full");

  const tableRows = ROW_LABELS.map((label, i) => [
    label,
    ...MODELS.map((m) => Number(fmt(value(i, m.key as ModelKey), 6))),
  ]);
  const diffs = cells.flatMap((c) =>
    ROOTS.map((rk, k) => ({
      cell: `${c.horizon} ${OUTCOMES[c.outcome as OutcomeKey].short}`,
      root: rk,
      diff: c.models.structured_full.roots[k].nrmse - c.models.ridge_full.roots[k].nrmse,
    })),
  );

  return (
    <FigureFrame
      number={7}
      title="Model-by-cell NRMSE heatmap and structured-minus-ridge differences"
      svgRef={svg}
      units="NRMSE, dimensionless. Lower is better. Colour is centred at 1, the error of a cell-mean predictor."
      interpretation={
        <p>
          Ridge regression has the lowest NRMSE in every cell and in the six-cell mean, whichever root is
          selected. Panel (b) shows that the structured comparator is higher than ridge in all 18
          root-cell comparisons, by 0.025 to 0.047. These are descriptive differences of recorded values.
        </p>
      }
      limitations={[
        "No significance test or ridge-versus-structured interval was recorded; differences are descriptive only.",
        "All roots come from the same synthetic generator; the ordering is not evidence about athletes or the historical neural models.",
      ]}
      table={{
        caption: `Recorded NRMSE (${root === "mean" ? "stored across-root mean" : `root ${root}`}); final row is the equal-weight six-cell score.`,
        columns: ["Cell", ...MODELS.map((m) => m.label)],
        rows: tableRows,
      }}
      json={{ root, heatmap: tableRows, structuredMinusRidge: diffs }}
      readout={
        <>
          <strong>
            {ROW_LABELS[sel.row]} · {MODELS[sel.col].label}:
          </strong>{" "}
          NRMSE {fmt(selValue, 6)} · rank {rank} of 4 in this row
          {selModel !== "ridge_full" && <> · {signed(vsRidge)} vs ridge</>}
          <span className="pub-muted"> ({root === "mean" ? "across-root mean" : `root ${root}`})</span>
        </>
      }
    >
      <div className="pub-controls">
        <Segmented
          label="Values"
          value={root}
          onChange={setRoot}
          options={[
            { value: "mean", label: "Across-root mean" },
            ...ROOTS.map((rk) => ({ value: rk, label: `Root ${rk}` })),
          ]}
        />
      </div>
      <div className="pub-chart" ref={tip.host} tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby="fig7-svg-title" className="pub-svg">
          <title id="fig7-svg-title">
            Heatmap of recorded NRMSE for four models across six cells and the six-cell mean, with structured-minus-ridge differences per root.
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (a) Recorded NRMSE · {root === "mean" ? "across-root mean" : `root ${root}`}
          </text>
          {MODELS.map((m, j) => (
            <text key={m.key} x={x0 + j * cw + cw / 2} y={y0 - 8} textAnchor="middle" fontFamily={SANS} fontSize={11.5} fill={INK}>
              {m.label}
            </text>
          ))}
          {ROW_LABELS.map((label, i) => {
            const vals = MODELS.map((m) => value(i, m.key as ModelKey));
            const best = Math.min(...vals);
            const yy = y0 + i * ch + (i === 6 ? 8 : 0);
            return (
              <g key={label}>
                <text x={x0 - 10} y={yy + ch / 2 + 4} textAnchor="end" fontFamily={SANS} fontSize={11.5} fill={INK} fontWeight={i === 6 ? 700 : 400}>
                  {label}
                </text>
                {MODELS.map((m, j) => {
                  const v = vals[j];
                  const h = heat(v);
                  const isSel = sel.row === i && sel.col === j;
                  return (
                    <g
                      key={m.key}
                      role="button"
                      tabIndex={0}
                      aria-label={`${fmt(v, 3)}: ${label}, ${m.label}, NRMSE ${fmt(v)}${v === best ? ", lowest in row" : ""}`}
                      aria-pressed={isSel}
                      onClick={() => setSel({ row: i, col: j })}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setSel({ row: i, col: j });
                        }
                      }}
                      onFocus={(e) => tip.showAt(e.currentTarget, `${m.label} · ${label}: ${fmt(v, 6)}`)}
                      onBlur={tip.hide}
                      onMouseEnter={(e) => tip.show(e, `${m.label} · ${label}: ${fmt(v, 6)}`)}
                      onMouseLeave={tip.hide}
                      className="pub-cell"
                    >
                      <rect x={x0 + j * cw + 1} y={yy + 1} width={cw - 2} height={ch - 2} fill={h.fill} />
                      {v === best && <rect x={x0 + j * cw + 3} y={yy + 3} width={cw - 6} height={ch - 6} fill="none" stroke={INK} strokeWidth={2} />}
                      {isSel && <rect x={x0 + j * cw + 1} y={yy + 1} width={cw - 2} height={ch - 2} fill="none" stroke={INK} strokeWidth={1} strokeDasharray="3 2" data-export-ignore />}
                      <text x={x0 + j * cw + cw / 2} y={yy + ch / 2 + 4} textAnchor="middle" fontFamily={SANS} fontSize={12.5} fill={h.text} fontWeight={v === best ? 700 : 400}>
                        {fmt(v, 3)}
                      </text>
                    </g>
                  );
                })}
              </g>
            );
          })}
          {/* colour key */}
          <g transform={`translate(${x0 + cw * 4 + 22} ${y0})`} fontFamily={SANS} fontSize={10.5} fill={MUTED}>
            {[0.6, 0.8, 1, 1.5, 2, 3].map((v, k) => (
              <g key={v} transform={`translate(0 ${k * 30})`}>
                <rect width={22} height={22} fill={heat(v).fill} stroke={GRID} />
                <text x={28} y={15}>
                  {v.toFixed(1)}
                </text>
              </g>
            ))}
            <text y={196} fill={INK}>
              ▢ lowest in row
            </text>
          </g>
          <text x={8} y={by0 - 34} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (b) Structured minus ridge NRMSE, per root (positive: ridge lower)
          </text>
          <AxisX scale={bx} y={by0 + 6 * 26} values={[0, 0.01, 0.02, 0.03, 0.04, 0.05]} format={(v) => v.toFixed(2)} grid={[by0 - 12, by0 + 6 * 26]} />
          {cells.map((c, i) => {
            const label = ROW_LABELS[i];
            const yy = by0 + i * 26;
            return (
              <g key={c.cell}>
                <text x={x0 - 10} y={yy + 4} textAnchor="end" fontFamily={SANS} fontSize={11} fill={INK}>
                  {label}
                </text>
                {ROOTS.map((rk, k) => {
                  const d = c.models.structured_full.roots[k].nrmse - c.models.ridge_full.roots[k].nrmse;
                  const dim = root !== "mean" && root !== rk;
                  return (
                    <g key={rk} onMouseEnter={(e) => tip.show(e, `${label}, root ${rk}: ${signed(d, 6)}`)} onMouseLeave={tip.hide}>
                      <circle cx={bx(d)} cy={yy + (k - 1) * 6} r={9} fill="transparent" />
                      <Marker shape={ROOT_SHAPE[rk]} x={bx(d)} y={yy + (k - 1) * 6} r={4.2} fill={INK} opacity={dim ? 0.2 : 0.9} />
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
        {tip.node}
      </div>
      <p className="pub-hint">Cells are keyboard-focusable: Tab to a cell, press Enter to read its rank and difference from ridge.</p>
    </FigureFrame>
  );
}
