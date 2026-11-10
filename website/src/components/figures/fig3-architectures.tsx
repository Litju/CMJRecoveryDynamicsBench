"use client";
import { useRef } from "react";
import FigureFrame from "./figure-frame";
import { AxisX, INK, MUTED, SANS, linear, useTooltip, GRID } from "./chart-kit";
import { fmtInt, manuscript, signed } from "@/lib/manuscript";
import { atlasLink, familyNames } from "@/lib/model-families";
import { plotTheme } from "@/lib/plot-theme.mjs";
import { useUrlState } from "@/lib/use-url-state";

const { components, families } = manuscript.data.architectures;
const IDS = families.map((f) => f.id);
type FamilyId = (typeof IDS)[number];

function Picker({ label, value, onChange, id }: { label: string; value: string; onChange: (v: FamilyId) => void; id: string }) {
  return (
    <div className="pub-segmented">
      <label className="pub-control-label" htmlFor={id}>
        {label}
      </label>
      <select id={id} className="pub-select" value={value} onChange={(e) => onChange(e.target.value as FamilyId)}>
        {families.map((f) => (
          <option key={f.id} value={f.id}>
            {f.id} · {familyNames[f.id]}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function ArchitectureFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [a, setA] = useUrlState<FamilyId>("f3a", "M8", IDS);
  const [b, setB] = useUrlState<FamilyId>("f3b", "M4", IDS);
  const tip = useTooltip();
  const A = families.find((f) => f.id === a)!;
  const B = families.find((f) => f.id === b)!;
  const added = A.components.filter((c) => !B.components.includes(c));
  const removed = B.components.filter((c) => !A.components.includes(c));
  const label = (id: string) => components.find((c) => c.id === id)!.label;

  const W = 760;
  const cx0 = 300;
  const cw = 46;
  const top = 56;
  const rh = 26;
  const barTop = top + components.length * rh + 64;
  const bx = linear([0, 11000], [cx0, cx0 + cw * 9]);
  const H = barTop + 9 * 22 + 50;

  return (
    <FigureFrame
      number={3}
      title="Recovered neural architectures M0–M8 and parameter counts"
      svgRef={svg}
      units="Recorded trainable parameter count per family; widths are node counts. Both repeats (r0, r1) of a family share its topology and count."
      interpretation={
        <p>
          M0–M2 use only a raw feedforward backbone. M3 adds a pointwise history encoder; M4 replaces it with
          a 32-unit GRU; M5 adds a horizon embedding; M6 and M7 project two or all five schedule-basis
          values; M8 adds a bias-free 5 → 2 basis head. Parameter counts rise from 1,346 to 10,796. Comparing{" "}
          {a} with {b}: {added.length ? `${a} adds ${added.map(label).join("; ")}` : `${a} adds no component`}
          {removed.length ? `, and lacks ${removed.map(label).join("; ")}` : ""}; parameter difference{" "}
          {signed(A.parameters - B.parameters, 0)}.
        </p>
      }
      limitations={[
        "Architecture complexity does not establish predictive superiority; the historical families have no public predictive score here.",
        "Parameter counts are a private qualification record summarised publicly; original weights are not public.",
        "The schedule basis needs history and plans genuinely known at the forecast origin; a synthetic plan does not prove prospective availability.",
      ]}
      table={{
        caption: "Recorded architecture contracts per family (both repeats share topology and parameter count).",
        columns: ["Family", "Public name", "Repeats", "Parameters", "Inputs", "Architecture", "Outputs", "CPU source", "Archived GPU"],
        rows: families.map((f) => [f.id, familyNames[f.id], f.repeats.join(", "), f.parameters, f.inputs, f.architecture, f.output, f.cpuSource, f.savedCuda]),
      }}
      json={manuscript.data.architectures}
      readout={
        <>
          <strong>
            {a} {familyNames[a]}
          </strong>{" "}
          {fmtInt(A.parameters)} parameters · {A.architecture}
          {" · vs "}
          <strong>{b}</strong> {fmtInt(B.parameters)} ({signed(A.parameters - B.parameters, 0)})
        </>
      }
    >
      <div className="pub-controls">
        <Picker id="f3-a" label="Inspect" value={a} onChange={setA} />
        <Picker id="f3-b" label="Compare with" value={b} onChange={setB} />
      </div>
      <div className="pub-chart" ref={tip.host} tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="fig3-svg-title" className="pub-svg">
          <title id="fig3-svg-title">
            Component inclusion matrix for M0 to M8 and recorded trainable parameter counts from 1,346 to 10,796.
          </title>
          <rect width={W} height={H} fill="#fffdf7" />
          <text x={8} y={20} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (a) Components by family
          </text>
          {families.map((f, j) => {
            const hl = f.id === a || f.id === b;
            return (
              <g key={f.id}>
                {hl && <rect x={cx0 + j * cw + 2} y={top - 22} width={cw - 4} height={components.length * rh + 26} fill={f.id === a ? "#e5ebf7" : "#f6e6e1"} />}
                <text
                  x={cx0 + j * cw + cw / 2}
                  y={top - 8}
                  textAnchor="middle"
                  fontFamily={SANS}
                  fontSize={12}
                  fontWeight={hl ? 700 : 400}
                  fill={INK}
                  className="pub-clickable"
                  onClick={() => setA(f.id)}
                >
                  {f.id}
                </text>
              </g>
            );
          })}
          {components.map((c, i) => {
            const y = top + i * rh;
            return (
              <g key={c.id}>
                <line x1={8} x2={cx0 + cw * 9} y1={y + rh} y2={y + rh} stroke={GRID} />
                <text x={cx0 - 10} y={y + 17} textAnchor="end" fontFamily={SANS} fontSize={11} fill={INK}>
                  {c.label}
                </text>
                {families.map((f, j) => {
                  const has = f.components.includes(c.id);
                  return (
                    <g key={f.id} onMouseEnter={(e) => tip.show(e, `${f.id}: ${has ? "includes" : "does not include"} ${c.label}`)} onMouseLeave={tip.hide}>
                      <rect x={cx0 + j * cw + 4} y={y + 3} width={cw - 8} height={rh - 6} fill="transparent" />
                      {has ? (
                        <rect x={cx0 + j * cw + cw / 2 - 7} y={y + rh / 2 - 7} width={14} height={14} rx={2} fill={f.id === a ? plotTheme.ridge : f.id === b ? plotTheme.structured : INK} />
                      ) : (
                        <circle cx={cx0 + j * cw + cw / 2} cy={y + rh / 2} r={2} fill={GRID} />
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}
          <text x={8} y={barTop - 30} fontFamily={SANS} fontSize={13} fontWeight={700} fill={INK}>
            (b) Recorded trainable parameters
          </text>
          <AxisX scale={bx} y={barTop + 9 * 22} values={[0, 2000, 4000, 6000, 8000, 10000]} format={(v) => fmtInt(v)} grid={[barTop - 12, barTop + 9 * 22]} />
          {families.map((f, i) => {
            const y = barTop + i * 22;
            const col = f.id === a ? plotTheme.ridge : f.id === b ? plotTheme.structured : "#8a949a";
            return (
              <g key={f.id}>
                <text x={cx0 - 10} y={y + 4} textAnchor="end" fontFamily={SANS} fontSize={11} fill={INK}>
                  {f.id} · {familyNames[f.id]}
                </text>
                <rect x={cx0} y={y - 6} width={bx(f.parameters) - cx0} height={12} fill={col} />
                <text x={bx(f.parameters) + 6} y={y + 4} fontFamily={SANS} fontSize={10.5} fill={INK}>
                  {fmtInt(f.parameters)}
                </text>
              </g>
            );
          })}
        </svg>
        {tip.node}
      </div>
      <div className="pub-detail">
        {[A, B].map((f) => (
          <div key={f.id} className="pub-compare-card">
            <h4>
              {f.id} · {familyNames[f.id]}
            </h4>
            <dl className="pub-dl">
              <dt>Inputs</dt>
              <dd>{f.inputs}</dd>
              <dt>Architecture</dt>
              <dd>{f.architecture}</dd>
              {f.hidden && (
                <>
                  <dt>Hidden layers</dt>
                  <dd>{f.hidden} → 2</dd>
                </>
              )}
              {f.concatenatedWidth && (
                <>
                  <dt>Concatenated width</dt>
                  <dd>{f.concatenatedWidth}</dd>
                </>
              )}
              <dt>Outputs</dt>
              <dd>{f.output}</dd>
              <dt>Repeats</dt>
              <dd>
                {f.repeats.join(" and ")} — {fmtInt(f.parameters)} parameters each
              </dd>
              <dt>Qualification</dt>
              <dd>
                CPU: {f.cpuSource}; archived GPU: {f.savedCuda}
              </dd>
            </dl>
            <a className="pub-inline-link" href={atlasLink(f.id)}>
              Open {f.id} in the model atlas →
            </a>
          </div>
        ))}
      </div>
      <p className="pub-hint" style={{ color: MUTED }}>
        Blue marks the inspected family, vermilion the comparison family.
      </p>
    </FigureFrame>
  );
}
