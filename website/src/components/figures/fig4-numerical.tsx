"use client";
import { useRef } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, INK, MUTED, SANS, Segmented, log10, useTooltip, GRID } from "./chart-kit";
import { manuscript } from "@/lib/manuscript";
import { plotTheme } from "@/lib/plot-theme.mjs";
import { useUrlState } from "@/lib/use-url-state";

const routes = manuscript.data.routes;
type RouteId = (typeof routes)[number]["route"];
const PASS = "#1f7a6d";
const FAIL = plotTheme.structured;
const POW: Record<number, string> = { 6: "10⁻⁶", 5: "10⁻⁵", 4: "10⁻⁴", 3: "10⁻³" };
const sci = (v: number) => v.toExponential(2).replace("e-", " × 10⁻").replace(/⁻(\d+)/, (_, d: string) => "⁻" + d.split("").map((c) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[Number(c)]).join(""));

export default function NumericalFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [sel, setSel] = useUrlState<RouteId>("f4route", "M4-r0", routes.map((r) => r.route));
  const [view, setView] = useUrlState("f4view", "error", ["error", "elements"] as const);
  const tip = useTooltip();
  const route = routes.find((r) => r.route === sel)!;
  const W = 760;
  const H = 520;
  const mx = 40;
  const cell = 36;
  const x = log10([1e-6, 1e-3], [330, W - 30]);
  const ex = (v: number) => 330 + (v / 450) * (W - 360);
  const rowY = (i: number) => 64 + i * 24;
  const atol = routes[0].atol;

  return (
    <FigureFrame
      number={4}
      title="Numerical qualification of the 18 original model-repeat routes"
      svgRef={svg}
      units="Maximum absolute difference in raw output units (outputs mix N/kg and m/s, so values are not physical magnitudes); 512 rows × 2 outputs = 1,024 saved-array elements per route."
      interpretation={
        <p>
          The recovered CPU implementation is recorded as exactly equal to the original CPU outputs on all
          18 routes. Against the archived GPU arrays, M0–M3 pass the unchanged elementwise tolerance
          (absolute 10⁻⁵, relative 10⁻⁴) while both repeats of M4–M8 fail it, with 88 to 443 failing
          elements where the count was tabulated. CPU parity therefore does not establish compatibility
          with the historical GPU environment.
        </p>
      }
      limitations={[
        "Private qualification shown as a public summary: original checkpoints, preprocessing values and inference arrays are not public and cannot be rerun from this site.",
        "These are deterministic comparisons, not accuracy scores; the site creates no new score.",
        "The cause of the GPU-array differences is not established.",
        "Failing-element counts for M1–M3 were not tabulated in the record (shown as —).",
      ]}
      table={{
        caption: "Recorded route qualification (public summary of private records). inference_rerun is false for every route.",
        columns: ["Route", "CPU source", "Archived GPU", "Absolute tol.", "Relative tol.", "Max abs. difference", "Failing elements", "Rerun from public files"],
        rows: routes.map((r) => [r.route, r.cpuSource, r.savedCuda === "pass" ? "Within tolerance" : "Outside tolerance", r.atol, r.rtol, r.maxAbsoluteError, r.failingElements, r.inferenceRerun ? "yes" : "no"]),
      }}
      json={routes}
      readout={
        <>
          <strong>Route {route.route}:</strong> CPU source exact · archived GPU{" "}
          {route.savedCuda === "pass" ? "within" : "outside"} tolerance · max abs. difference {sci(route.maxAbsoluteError)} ·{" "}
          {route.failingElements === null ? "failing elements not tabulated" : `${route.failingElements} of 1,024 elements failing`}
        </>
      }
    >
      <div className="pub-controls">
        <Segmented
          label="Panel"
          value={view}
          onChange={setView}
          options={[
            { value: "error", label: "Max absolute difference (log)" },
            { value: "elements", label: "Failing elements" },
          ]}
        />
      </div>
      <div className="pub-chart" ref={tip.host} tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby="fig4-svg-title" className="pub-svg">
          <title id="fig4-svg-title">
            Route matrix of CPU-source equality and archived GPU tolerance status for 18 routes, with recorded maximum absolute differences.
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (a) Recorded status
          </text>
          <text x={330} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            {view === "error" ? "(b) Maximum absolute difference vs archived GPU" : "(c) Failing elements of 1,024"}
          </text>
          {["CPU source", "Archived GPU"].map((h, j) => (
            <text key={h} x={mx + 110 + j * (cell + 50) + cell / 2} y={50} textAnchor="middle" fontFamily={SANS} fontSize={10.5} fill={MUTED}>
              {h}
            </text>
          ))}
          {view === "error" ? (
            <>
              <AxisX scale={x} y={rowY(18) + 4} values={[1e-6, 1e-5, 1e-4, 1e-3]} format={(v) => POW[Math.round(-Math.log10(v))]} grid={[56, rowY(18) + 4]} label="Recorded maximum absolute difference (log scale)" />
              <line x1={x(atol)} x2={x(atol)} y1={44} y2={rowY(18) + 4} stroke={INK} strokeDasharray="5 3" />
              <text x={x(atol) + 4} y={42} fontFamily={SANS} fontSize={10} fill={INK}>
                absolute tolerance 10⁻⁵
              </text>
            </>
          ) : (
            <AxisX scale={Object.assign((v: number) => ex(v), { domain: [0, 450] as [number, number], range: [330, W - 30] as [number, number] })} y={rowY(18) + 4} values={[0, 100, 200, 300, 400]} grid={[56, rowY(18) + 4]} label="Failing elements (— not tabulated)" />
          )}
          {routes.map((r, i) => {
            const y = rowY(i);
            const isSel = r.route === sel;
            const col = r.savedCuda === "pass" ? PASS : FAIL;
            const pick = () => setSel(r.route);
            return (
              <g
                key={r.route}
                role="button"
                tabIndex={0}
                aria-pressed={isSel}
                onClick={pick}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    pick();
                  }
                }}
                onMouseEnter={(e) => tip.show(e, `${r.route}: max |Δ| ${r.maxAbsoluteError.toExponential(4)}; failing ${r.failingElements ?? "not tabulated"}`)}
                onMouseLeave={tip.hide}
                className="pub-node"
              >
                <title>{`${r.model} · ${r.repeat} ${r.savedCuda === "pass" ? "PASS" : "FAIL"}: route ${r.route}, CPU source exact; archived GPU ${r.savedCuda === "pass" ? "within" : "outside"} tolerance; maximum absolute difference ${r.maxAbsoluteError.toExponential(3)}; failing elements ${r.failingElements ?? "not tabulated"}`}</title>
                <rect x={4} y={y - 11} width={W - 8} height={22} fill={isSel ? "#e9eef9" : i % 2 ? "#faf8f1" : "#fffdf7"} />
                <text x={mx} y={y + 4} fontFamily={SANS} fontSize={11.5} fill={INK} fontWeight={isSel ? 700 : 400}>
                  {r.model} · {r.repeat}
                </text>
                <rect x={mx + 110} y={y - 8} width={cell} height={16} fill={PASS} />
                <text x={mx + 110 + cell / 2} y={y + 4} textAnchor="middle" fontFamily={SANS} fontSize={10} fill="#fffdf7" fontWeight={700}>
                  EXACT
                </text>
                <rect x={mx + 196} y={y - 8} width={cell} height={16} fill={col} />
                <text x={mx + 196 + cell / 2} y={y + 4} textAnchor="middle" fontFamily={SANS} fontSize={10} fill="#fffdf7" fontWeight={700}>
                  {r.savedCuda === "pass" ? "PASS" : "FAIL"}
                </text>
                {view === "error" ? (
                  <>
                    <line x1={330} x2={x(r.maxAbsoluteError)} y1={y} y2={y} stroke={GRID} />
                    <circle cx={x(r.maxAbsoluteError)} cy={y} r={5.5} fill={col} stroke="#fffdf7" strokeWidth={1.5} />
                  </>
                ) : r.failingElements === null ? (
                  <text x={334} y={y + 4} fontFamily={SANS} fontSize={11} fill={MUTED}>
                    — not tabulated
                  </text>
                ) : (
                  <>
                    <rect x={330} y={y - 6} width={Math.max(1, ex(r.failingElements) - 330)} height={12} fill={col} />
                    <text x={ex(r.failingElements) + 6} y={y + 4} fontFamily={SANS} fontSize={10.5} fill={INK}>
                      {r.failingElements}
                    </text>
                  </>
                )}
              </g>
            );
          })}
        </svg>
        {tip.node}
      </div>
      <div className="pub-legend">
        <span>
          <span className="pub-swatch" style={{ background: PASS }} aria-hidden="true" /> exact / within recorded tolerance
        </span>
        <span>
          <span className="pub-swatch" style={{ background: FAIL }} aria-hidden="true" /> outside recorded tolerance
        </span>
        <span>Text labels carry status; colour is secondary.</span>
      </div>
    </FigureFrame>
  );
}
