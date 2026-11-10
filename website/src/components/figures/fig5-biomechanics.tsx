"use client";
import { useMemo, useRef, useState } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, AxisY, INK, MUTED, SANS, Segmented, linear } from "./chart-kit";
import { fmt, manuscript } from "@/lib/manuscript";
import { analyticalForce, cumulativeNetImpulse, forceQuantities, sampleForce } from "@/lib/manuscript-mechanics.mjs";
import { plotTheme } from "@/lib/plot-theme.mjs";
import { useUrlState } from "@/lib/use-url-state";

const p = manuscript.data.mechanics;
const MODES = {
  mean: { label: "Gross mean force", color: INK },
  peak: { label: "Peak force", color: plotTheme.structured },
  impulse: { label: "Net impulse", color: plotTheme.ridge },
} as const;

export default function BiomechanicsFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [mode, setMode] = useUrlState("f5mode", "mean", ["mean", "peak", "impulse"] as const);
  const [t, setT] = useState(p.peakTime);
  const q = useMemo(() => forceQuantities(p, p.samples), []);
  const curve = useMemo(() => sampleForce(p, 221), []);
  const weight = p.mass * p.gravity;
  const W = 760;
  const H = 520;
  const x = linear([-0.02, 0.58], [70, 460]);
  const y = linear([0, 1800], [300, 40]);
  const tx = linear([-255, 195], [100, W - 20]);
  const path = curve.map((s, i) => `${i ? "L" : "M"}${x(s.t)},${y(s.force)}`).join(" ");
  const area = `M${x(0)},${y(0)} ${curve.map((s) => `L${x(s.t)},${y(s.force)}`).join(" ")} L${x(p.duration)},${y(0)} Z`;
  // Net impulse: signed area between F(t) and body weight (only positive part exists before the fall crosses mg).
  const netArea = `M${x(0)},${y(weight)} ${curve.map((s) => `L${x(s.t)},${y(Math.max(s.force, weight))}`).join(" ")} L${x(p.duration)},${y(weight)} Z`;
  const below = `M${x(0)},${y(weight)} ${curve.map((s) => `L${x(s.t)},${y(Math.min(s.force, weight))}`).join(" ")} L${x(p.duration)},${y(weight)} Z`;
  const ft = analyticalForce(t, p);
  const jt = cumulativeNetImpulse(p, t);
  const meanN = q.meanForceN;

  const values = [
    { k: "mean", name: "Gross mean concentric force", eq: "F_mean = (1/mT) ∫₀ᵀ F(t) dt", v: q.meanForceNPerKg, unit: "N/kg" },
    { k: "peak", name: "Peak force", eq: "max F(t) / m", v: q.peakForceNPerKg, unit: "N/kg" },
    { k: "impulse", name: "Gravity-adjusted net impulse", eq: "J = (1/m) ∫₀ᵀ (F(t) − mg) dt", v: q.netImpulseMPerS, unit: "m/s" },
  ];

  return (
    <FigureFrame
      number={5}
      title="Native measurement definitions and assessment chronology"
      svgRef={svg}
      units="Force N; mass kg; time s; mean and peak force N/kg; net impulse m/s; chronology in hours relative to the index exposure."
      interpretation={
        <p>
          One analytical curve yields three different quantities. Dividing the area under F(t) by mT gives gross
          mean concentric force ({fmt(q.meanForceNPerKg, 2)} N/kg); the signed area relative to body weight,
          divided by m, gives gravity-adjusted net impulse ({fmt(q.netImpulseMPerS, 2)} m/s); peak force (
          {fmt(q.peakForceNPerKg, 2)} N/kg) is a different quantity again. They satisfy F_mean = g + J/T (per unit mass). The public
          synthetic benchmark scores the <em>innovation</em> of the gross mean (criterion minus baseline assessment),
          not peak force.
        </p>
      }
      limitations={[
        "Analytical, equation-generated signal: not athlete data and not a simulated trial from the benchmark generator.",
        "Native H72/D7 windows describe the original measurement contract; the public synthetic H24/H48/H72 queries are a separate task.",
        "No uncertainty is implied; this is a deterministic illustration of definitions.",
      ]}
      table={{
        caption: `Quantities of the analytical curve (m = ${p.mass} kg, g = ${p.gravity} m/s², A = ${p.amplitude} N, tp = ${p.peakTime} s, T = ${p.duration} s; ${p.samples.toLocaleString()} trapezoid points) and assessment windows.`,
        columns: ["Quantity", "Definition", "Value", "Unit"],
        rows: [
          ...values.map((v) => [v.name, v.eq, Number(fmt(v.v, 4)), v.unit]),
          ["Gross area under F(t)", "∫₀ᵀ F(t) dt", Number(fmt(q.grossAreaNs, 3)), "N·s"],
          ...p.windows.map((w) => [w.label, `native contract, ${w.start} to ${w.end} h`, w.end - w.start, "h width"]),
          ...p.syntheticQueries.map((h) => [`Synthetic H${h} query`, "public synthetic task (nominal)", h, "h"]),
        ],
      }}
      json={{ parameters: p, quantities: q }}
      readout={
        <>
          <strong>t = {fmt(t, 3)} s:</strong> F(t) = {fmt(ft, 1)} N ({fmt(ft / p.mass, 2)} N/kg) · net impulse so far{" "}
          {fmt(jt, 3)} m/s
          <span className="pub-muted"> · analytical signal, not athlete data</span>
        </>
      }
    >
      <div className="pub-controls">
        <Segmented
          label="Highlight"
          value={mode}
          onChange={setMode}
          options={(Object.keys(MODES) as (keyof typeof MODES)[]).map((k) => ({ value: k, label: MODES[k].label }))}
        />
        <div className="pub-segmented pub-range">
          <label className="pub-control-label" htmlFor="f5-time">
            Time {fmt(t, 3)} s
          </label>
          <input id="f5-time" type="range" min={0} max={p.duration} step={0.005} value={t} onChange={(e) => setT(Number(e.target.value))} aria-valuetext={`${fmt(t, 3)} seconds, force ${fmt(ft, 0)} newtons`} />
        </div>
      </div>
      <div className="pub-chart" tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="fig5-svg-title" className="pub-svg">
          <title id="fig5-svg-title">
            Analytical force–time curve with onset, peak and takeoff, showing gross mean force, peak force and net impulse, and an assessment chronology of native windows and synthetic queries.
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (a) Analytical vertical force–time curve · not athlete data
          </text>
          <AxisY scale={y} x={70} values={[0, 300, 600, 900, 1200, 1500, 1800]} grid={[70, 460]} label="Vertical force F (N)" />
          <AxisX scale={x} y={300} values={[0, 0.1, 0.2, 0.3, 0.4, 0.5]} format={(v) => v.toFixed(1)} label="Time from concentric onset (s)" />
          {mode === "mean" && <path d={area} fill={INK} opacity={0.1} />}
          {mode === "impulse" && (
            <>
              <path d={netArea} fill={plotTheme.ridge} opacity={0.22} />
              <path d={below} fill={plotTheme.structured} opacity={0.18} />
            </>
          )}
          <line x1={70} x2={460} y1={y(weight)} y2={y(weight)} stroke={MUTED} strokeDasharray="5 3" />
          <text x={455} y={y(weight) + 14} textAnchor="end" fontFamily={SANS} fontSize={10} fill={MUTED}>
            body weight mg = {fmt(weight, 1)} N
          </text>
          {mode === "mean" && (
            <>
              <line x1={x(0)} x2={x(p.duration)} y1={y(meanN)} y2={y(meanN)} stroke={INK} strokeWidth={2.2} />
              <text x={455} y={y(meanN) - 6} textAnchor="end" fontFamily={SANS} fontSize={10.5} fill={INK}>
                gross mean {fmt(meanN, 0)} N
              </text>
            </>
          )}
          {mode === "peak" && (
            <>
              <line x1={x(p.peakTime)} x2={x(p.peakTime)} y1={y(0)} y2={y(q.peakForceN)} stroke={plotTheme.structured} strokeDasharray="3 3" />
              <circle cx={x(p.peakTime)} cy={y(q.peakForceN)} r={6} fill={plotTheme.structured} />
            </>
          )}
          <path d={path} fill="none" stroke={INK} strokeWidth={2.2} />
          {[
            { t: 0, label: "onset" },
            { t: p.peakTime, label: "peak" },
            { t: p.duration, label: "takeoff" },
          ].map((e) => (
            <g key={e.label}>
              <line x1={x(e.t)} x2={x(e.t)} y1={300} y2={308} stroke={INK} strokeWidth={2} />
              <text x={x(e.t)} y={y(1800) + 4} textAnchor="middle" fontFamily={SANS} fontSize={10.5} fill={MUTED}>
                {e.label}
              </text>
            </g>
          ))}
          <g data-export-ignore>
            <line x1={x(t)} x2={x(t)} y1={y(1800)} y2={300} stroke={plotTheme.ochre} strokeWidth={1.5} />
            <circle cx={x(t)} cy={y(ft)} r={5} fill={plotTheme.ochre} stroke="#fffdf7" strokeWidth={1.5} />
          </g>
          <text x={490} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (b) Three different quantities
          </text>
          {values.map((v, i) => {
            const on = v.k === mode;
            const yy = 52 + i * 74;
            return (
              <g key={v.k} onClick={() => setMode(v.k as typeof mode)} className="pub-clickable">
                <rect x={490} y={yy - 18} width={258} height={64} fill={on ? "#f1efe6" : "#fffdf7"} stroke={on ? MODES[v.k as keyof typeof MODES].color : "#ccd1ce"} strokeWidth={on ? 2 : 1} />
                <text x={500} y={yy} fontFamily={SANS} fontSize={11.5} fontWeight={700} fill={INK}>
                  {v.name}
                </text>
                <text x={500} y={yy + 18} fontFamily={SANS} fontSize={11} fill={MUTED}>
                  {v.eq}
                </text>
                <text x={740} y={yy + 36} fontFamily={SANS} fontSize={17} fontWeight={700} textAnchor="end" fill={MODES[v.k as keyof typeof MODES].color}>
                  {fmt(v.v, 2)} {v.unit}
                </text>
              </g>
            );
          })}
          <text x={8} y={372} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (c) Assessment chronology relative to the index exposure
          </text>
          <text x={8} y={408} fontFamily={SANS} fontSize={11} fontWeight={700} fill={INK}>
            Native contract
          </text>
          <text x={8} y={458} fontFamily={SANS} fontSize={11} fontWeight={700} fill={INK}>
            Public synthetic
          </text>
          {p.windows.map((w) => {
            const col = w.id === "baseline" ? plotTheme.ridge : w.id === "H72" ? "#1f7a6d" : plotTheme.ochre;
            return (
              <g key={w.id}>
                <rect x={tx(w.start)} y={394} width={tx(w.end) - tx(w.start)} height={20} fill={col} opacity={0.25} stroke={col} />
                <text x={(tx(w.start) + tx(w.end)) / 2} y={428} textAnchor="middle" fontFamily={SANS} fontSize={10} fill={INK}>
                  {w.label} {Math.abs(w.start)}–{Math.abs(w.end)} h{w.id === "baseline" ? " before" : ""}
                </text>
              </g>
            );
          })}
          <line x1={tx(0)} x2={tx(0)} y1={384} y2={470} stroke={plotTheme.structured} strokeWidth={1.5} strokeDasharray="4 3" />
          <text x={tx(0) + 4} y={390} fontFamily={SANS} fontSize={10} fill={plotTheme.structured}>
            index exposure
          </text>
          {p.syntheticQueries.map((h) => (
            <g key={h}>
              <circle cx={tx(h)} cy={454} r={6} fill={plotTheme.ridge} />
              <text x={tx(h)} y={472} textAnchor="middle" fontFamily={SANS} fontSize={10} fill={INK}>
                H{h}
              </text>
            </g>
          ))}
          <AxisX scale={tx} y={482} values={[-240, -168, -96, -24, 0, 72, 168]} format={(v) => `${v}`} />
          <text x={W / 2} y={514} textAnchor="middle" fontFamily={SANS} fontSize={11} fill={INK}>
            Hours relative to index exposure · {p.assessment}
          </text>
        </svg>
      </div>
    </FigureFrame>
  );
}
