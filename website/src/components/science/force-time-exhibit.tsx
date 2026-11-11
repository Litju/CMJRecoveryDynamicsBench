"use client";
import { useMemo, useRef, useState } from "react";
import ExhibitFrame from "./exhibit-frame";
import { AxisX, AxisY, INK, SANS, linear } from "@/components/figures/chart-kit";
import { G, impulseRange, trial } from "@/lib/cmj-science.mjs";
import { plotTheme } from "@/lib/plot-theme.mjs";

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const num = (s: string, fallback: number) => (Number.isFinite(Number(s)) && s !== "" ? Number(s) : fallback);

export default function ForceTimeExhibit() {
  const svg = useRef<SVGSVGElement>(null);
  const [fRaw, setF] = useState("20");
  const [jRaw, setJ] = useState("2.7");
  const meanForce = clamp(num(fRaw, 20), 12, 30);
  const range = impulseRange(meanForce)!;
  const impulse = clamp(num(jRaw, 2.7), range[0], range[1]);
  const t = useMemo(() => trial(meanForce, impulse), [meanForce, impulse]);
  const W = 640;
  const H = 330;
  const x = linear([0, 0.8], [66, W - 24]);
  const y = linear([0, 36], [H - 48, 22]);
  const path = t.times.map((tt, i) => `${i ? "L" : "M"}${x(tt)},${y(t.force[i])}`).join(" ");
  const net = `M${x(0)},${y(G)} ${t.times.map((tt, i) => `L${x(tt)},${y(Math.max(t.force[i], G))}`).join(" ")} L${x(t.duration)},${y(G)} Z`;
  const rows = [0, 8, 16, 24, 32, 40, 48, 56, 64].map((i) => [t.times[i].toFixed(4), t.force[i].toFixed(3)]);
  const summary = [
    ["Gross mean concentric force", t.meanForce.toFixed(2), "N/kg"],
    ["Peak force (not scored)", t.peak.toFixed(2), "N/kg"],
    ["Net concentric impulse", t.netImpulse.toFixed(2), "m/s"],
    ["Concentric duration", t.duration.toFixed(3), "s"],
  ] as const;
  return (
    <ExhibitFrame
      id="exhibit-force-time"
      chapter="Chapter 1"
      figure={2}
      title="Mean force, peak force and net impulse from one force–time curve"
      question="How are the scored CMJ quantities defined, and how do they differ from peak force?"
      svgRef={svg}
      units="Force per unit mass N/kg; time s; net impulse m/s; g = 9.80665 N/kg."
      readout={
        <p data-testid="force-time-readout">
          Mean {t.meanForce.toFixed(2)} N/kg · peak {t.peak.toFixed(2)} N/kg · net impulse {t.netImpulse.toFixed(2)} m/s
          · duration {t.duration.toFixed(3)} s
        </p>
      }
      interpretation={
        <p>
          The scored force quantity is the <strong>gross time-mean</strong> of F<sub>z</sub>/m over the concentric phase.
          Subtracting gravity and integrating gives the <strong>net impulse</strong>, J = (F̄ − g)·T. Peak force is a
          different quantity: for the simulator&apos;s half-sine pulse it equals g + (π/2)(F̄ − g), here{" "}
          {t.continuousPeak.toFixed(2)} N/kg. Each assessment is the mean of three such trials, and the target is the
          criterion assessment minus the baseline assessment.
        </p>
      }
      limitations={[
        "The half-sine pulse is a simulator choice, not an observed athlete waveform.",
        "Values are analytical illustrations; they are not athlete data and are not scored.",
        "The duration is constrained to 0.075–0.80 s; the impulse control follows that support.",
      ]}
      table={{
        caption: `Simulated trial at mean force ${t.meanForce.toFixed(2)} N/kg and net impulse ${t.netImpulse.toFixed(2)} m/s (every eighth node of 65)`,
        columns: ["Time (s)", "Force per mass (N/kg)"],
        rows,
      }}
    >
      <div className="sci-controls">
        <label>
          Gross mean concentric force: <output>{meanForce.toFixed(1)} N/kg</output>
          <input
            type="range"
            min={14}
            max={28}
            step={0.5}
            value={meanForce}
            onChange={(e) => setF(e.target.value)}
            aria-label="Gross mean concentric force, N/kg"
          />
        </label>
        <label>
          Net impulse: <output>{impulse.toFixed(2)} m/s</output>
          <input
            type="range"
            min={Number(range[0].toFixed(2))}
            max={Number(Math.min(range[1], 5).toFixed(2))}
            step={0.05}
            value={impulse}
            onChange={(e) => setJ(e.target.value)}
            aria-label="Net concentric impulse, m/s"
          />
        </label>
      </div>
      <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="ft-title ft-desc" className="sci-chart">
        <title id="ft-title">Simulated concentric force–time curve</title>
        <desc id="ft-desc">
          Half-sine force per unit mass over {t.duration.toFixed(3)} seconds with gross mean {t.meanForce.toFixed(2)} newtons
          per kilogram, peak {t.peak.toFixed(2)} and net impulse {t.netImpulse.toFixed(2)} meters per second.
        </desc>
        <rect width={W} height={H} fill="#fffdf7" />
        <AxisX scale={x} y={H - 48} values={[0, 0.2, 0.4, 0.6, 0.8]} label="Time since concentric onset (s)" grid={[22, H - 48]} />
        <AxisY scale={y} x={66} values={[0, 10, 20, 30]} label="Force per mass (N/kg)" grid={[66, W - 24]} />
        <path d={net} fill={plotTheme.structured} opacity={0.18} />
        <path d={path} fill="none" stroke={plotTheme.cobalt} strokeWidth={2.4} />
        <line x1={x(0)} x2={x(t.duration)} y1={y(G)} y2={y(G)} stroke={plotTheme.muted} strokeDasharray="5 4" />
        <line x1={x(0)} x2={x(t.duration)} y1={y(t.meanForce)} y2={y(t.meanForce)} stroke={INK} strokeWidth={2} />
        <circle cx={x(t.times[32])} cy={y(t.peak)} r={4.5} fill={INK} />
        <g fontFamily={SANS} fontSize={11.5} fill={INK}>
          <text x={x(t.duration) + 6} y={y(t.meanForce) + 4}>mean</text>
          <text x={x(t.times[32]) + 10} y={y(t.peak) + 4}>peak (not scored)</text>
          <text x={x(t.duration) + 6} y={y(G) + 4} fill={plotTheme.muted}>g</text>
          <text x={x(t.duration / 2)} y={y((G + t.meanForce) / 2) + 4} textAnchor="middle" fill={plotTheme.structured}>net impulse</text>
        </g>
      </svg>
      <dl className="sci-summary">
        {summary.map(([k, v, u]) => (
          <div key={k}>
            <dt>{k}</dt>
            <dd>
              {v} <span>{u}</span>
            </dd>
          </div>
        ))}
      </dl>
    </ExhibitFrame>
  );
}
