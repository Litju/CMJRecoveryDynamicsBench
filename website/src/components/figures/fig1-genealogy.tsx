"use client";
import { useRef } from "react";
import FigureFrame from "./figure-frame";
import { INK, MUTED, SANS, Segmented } from "./chart-kit";
import { STATUS_COLOR, STATUS_LABEL, manuscript } from "@/lib/manuscript";
import { useUrlState } from "@/lib/use-url-state";

const nodes = manuscript.data.genealogy;
type NodeId = (typeof nodes)[number]["id"];
// Card positions follow the manuscript Fig. 1 generator (mm → px, ×4.2, y flipped);
// cards are 4 mm wider for legibility, so the last column moves 6 mm right.
const S = 4.2;
const MM: Record<string, [number, number]> = {
  initial_preseason_camp_recovery: [8, 80],
  canonical_preseason_camp_recovery: [54, 80],
  rich_history_camp_recovery: [8, 50],
  preliminary_post_exposure_recovery: [8, 12],
  phase_consistent_post_exposure_recovery: [54, 12],
  correlated_exposure_recovery: [100, 12],
  threshold_response_recovery: [146, 25],
  fixed_mode_discrepancy_recovery: [146, 1],
};
const CW = 40 * S;
const CH = 20 * S;
const pos = (id: string) => {
  const [x, y] = MM[id];
  return { x: x * S, y: (108 - y - 20) * S };
};
const W = 188 * S;
const H = 108 * S;
const STATUSES = ["all", "SUPERSEDED", "RETIRED", "PROPOSED", "ACTIVE_CANDIDATE"] as const;

export default function GenealogyFigure() {
  const svg = useRef<SVGSVGElement>(null);
  const [selected, setSelected] = useUrlState<NodeId>(
    "f1node",
    "fixed_mode_discrepancy_recovery",
    nodes.map((n) => n.id),
  );
  const [status, setStatus] = useUrlState("f1status", "all", STATUSES);
  const node = nodes.find((n) => n.id === selected)!;
  const parent = nodes.find((n) => n.id === node.parent);
  const children = nodes.filter((n) => n.parent === node.id);
  const edges = nodes.filter((n) => n.parent);
  const unresolved = nodes.filter((n) => !n.parent);

  return (
    <FigureFrame
      number={1}
      title="Genealogy of the eight recorded scientific formulations"
      svgRef={svg}
      units="Not quantitative. Arrows are recorded parent links, not a calendar timeline."
      interpretation={
        <p>
          The archive records eight formulations in two experimental contexts: camp-state tasks with
          H72/D7 targets and episode-response tasks with H24/H48/H72 targets. Five direct parent links are
          recorded. Three formulations have no recorded direct scientific parent; the figure marks them
          with a dashed stub and “?” rather than inferring one. Only the fixed-mode discrepancy formulation
          is an active candidate, and that status is not an accepted metric or scorer.
        </p>
      }
      limitations={[
        "Only parent edges present in the pinned lineage contract are drawn; no relationship is inferred from names, dates or similarity.",
        "Historical formulations have partial replay authority: some adapters, checkpoints and evaluators remain unavailable.",
        "Camp-state and episode-response tasks have different targets and horizons; their scores are not comparable.",
      ]}
      table={{
        caption: "Recorded formulations, status, experimental context and registered parent.",
        columns: ["Formulation", "Scientific identifier", "Status", "Context", "Horizons", "Response world", "Observation", "Registered parent"],
        rows: nodes.map((n) => [
          n.label,
          n.id,
          STATUS_LABEL[n.status],
          n.lane,
          n.horizons.join(" / "),
          n.world,
          n.observation,
          n.parent ?? "Not recorded",
        ]),
      }}
      json={nodes}
      readout={
        <>
          <strong>{node.label}</strong> · {STATUS_LABEL[node.status]} ·{" "}
          {parent ? <>parent: {parent.label}</> : <>direct parent not recorded</>}
          {children.length > 0 && <> · children: {children.map((c) => c.label).join(", ")}</>}
        </>
      }
    >
      <div className="pub-controls">
        <Segmented
          label="Status"
          value={status}
          onChange={setStatus}
          options={STATUSES.map((s) => ({ value: s, label: s === "all" ? "All" : STATUS_LABEL[s] }))}
        />
      </div>
      <div className="pub-chart" tabIndex={0} role="region" aria-label="Chart area; scrolls horizontally on narrow screens">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby="fig1-svg-title" className="pub-svg">
          <title id="fig1-svg-title">
            Formulation genealogy: eight formulations, five recorded parent links and three unresolved direct parents.
          </title>
          <defs>
            <marker id="fig1-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill={INK} />
            </marker>
          </defs>
          <rect width={W} height={H} fill="#fffdf7" />
          <rect x={0} y={0} width={W} height={250} fill="#f4f2ea" />
          <rect x={0} y={258} width={W} height={H - 258} fill="#eef1f3" />
          <text x={8} y={18} fontFamily={SANS} fontSize={12.5} fontWeight={700} fill={INK}>
            Camp-state tasks · H72 and D7 targets
          </text>
          <text x={8} y={276} fontFamily={SANS} fontSize={12.5} fontWeight={700} fill={INK}>
            Episode-response tasks · H24, H48 and H72 targets
          </text>
          {edges.map((n) => {
            const p = pos(n.parent!);
            const c = pos(n.id);
            const sx = p.x + CW;
            const sy = p.y + CH / 2;
            const ex = c.x - 2;
            const ey = c.y + CH / 2;
            const mx = (sx + ex) / 2;
            const on = selected === n.id || selected === n.parent;
            return (
              <path
                key={n.id}
                d={`M${sx},${sy} C${mx},${sy} ${mx},${ey} ${ex},${ey}`}
                fill="none"
                stroke={INK}
                strokeWidth={on ? 2.4 : 1.2}
                markerEnd="url(#fig1-arrow)"
              />
            );
          })}
          {unresolved.map((n) => {
            const c = pos(n.id);
            return (
              <g key={`u-${n.id}`}>
                <line x1={c.x - 22} x2={c.x} y1={c.y + CH / 2} y2={c.y + CH / 2} stroke={STATUS_COLOR.RETIRED} strokeWidth={1.6} strokeDasharray="4 3" />
                <text x={c.x - 20} y={c.y + CH / 2 - 5} fontFamily={SANS} fontSize={13} fontWeight={700} fill={STATUS_COLOR.RETIRED}>
                  ?
                </text>
              </g>
            );
          })}
          {nodes.map((n) => {
            const { x, y } = pos(n.id);
            const col = STATUS_COLOR[n.status];
            const isSel = n.id === selected;
            const faded = status !== "all" && status !== n.status;
            return (
              <g
                key={n.id}
                role="button"
                tabIndex={0}
                aria-pressed={isSel}
                onClick={() => setSelected(n.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setSelected(n.id);
                  }
                }}
                className="pub-node"
                opacity={faded ? 0.28 : 1}
              >
                <title>{`${n.label}, ${STATUS_LABEL[n.status]}: ${n.parent ? `recorded parent ${nodes.find((m) => m.id === n.parent)!.label}` : "direct scientific parent not recorded"}`}</title>
                <rect x={x} y={y} width={CW} height={CH} rx={4} fill="#fffdf7" stroke={col} strokeWidth={isSel ? 3 : 1.4} />
                <rect x={x} y={y + 4} width={5} height={CH - 8} fill={col} />
                <text x={x + 12} y={y + 18} fontFamily={SANS} fontSize={11.2} fontWeight={700} fill={INK}>
                  {n.label}
                </text>
                <text x={x + 12} y={y + 33} fontFamily={SANS} fontSize={10} fontWeight={700} fill={col} letterSpacing={0.6}>
                  {STATUS_LABEL[n.status].toUpperCase()}
                </text>
                <text x={x + 12} y={y + 48} fontFamily={SANS} fontSize={9.8} fill={INK}>
                  {n.world}
                </text>
                <text x={x + 12} y={y + 61} fontFamily={SANS} fontSize={9.8} fill={MUTED}>
                  {n.observation}
                </text>
                <text x={x + 12} y={y + 76} fontFamily={SANS} fontSize={10} fill={INK}>
                  {n.horizons.join(" · ")}
                </text>
              </g>
            );
          })}
          <text x={440} y={130} fontFamily={SANS} fontSize={11} fill={MUTED}>
            <tspan x={440} dy={0}>Solid arrows: direct parent links recorded</tspan>
            <tspan x={440} dy={15}>in the published lineage (5 of 8).</tspan>
            <tspan x={440} dy={15}>? and dashed stubs: direct scientific parent</tspan>
            <tspan x={440} dy={15}>not recorded (3 of 8).</tspan>
          </text>
        </svg>
      </div>
      <div className="pub-detail" aria-live="polite">
        <h4>{node.label}</h4>
        <p className="pub-detail-q">{node.question}</p>
        <dl className="pub-dl">
          <dt>Status</dt>
          <dd>{STATUS_LABEL[node.status]} — {node.disposition}</dd>
          <dt>Recorded change</dt>
          <dd>{node.change}</dd>
          <dt>Task</dt>
          <dd>{node.task}</dd>
          <dt>Model evidence</dt>
          <dd>{node.modelEvidence}</dd>
          <dt>Limitation</dt>
          <dd>{node.limitation}</dd>
          <dt>Scientific identifier</dt>
          <dd>
            <code>{node.id}</code> · <code>{node.source}</code>
          </dd>
        </dl>
      </div>
    </FigureFrame>
  );
}
