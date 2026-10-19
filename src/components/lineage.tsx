"use client";
import { useEffect, useState } from "react";
import { ArrowDown, ArrowUpRight, GitBranch } from "lucide-react";
import {
  lineage,
  reconstruction,
  experiments,
  type Formulation,
} from "@/lib/story";
import { sourceLink } from "@/lib/science";
import methods from "@/data/formulation-methods.json";

const activeId = "fixed_mode_discrepancy_recovery";
const activePath = new Set([
  "preliminary_post_exposure_recovery",
  "phase_consistent_post_exposure_recovery",
  "correlated_exposure_recovery",
  activeId,
]);

type Selection = { selected: string; onSelect: (id: string) => void };
function FormulationDetail({
  node,
  onSelect,
}: {
  node: Formulation;
  onSelect: Selection["onSelect"];
}) {
  const parent = lineage.find((n) => n.id === node.parent);
  const method = methods[node.id as keyof typeof methods];
  return (
    <>
      <span className="eyebrow">THE QUESTION INSIDE THIS FORMULATION</span>
      <h3>{node.label}</h3>
      <code className="contract-name">{node.id}</code>
      <p className="lineage-question">{node.question}</p>
      <dl className="lineage-facts">
        <div>
          <dt>Scientific status</dt>
          <dd className={node.status === "ACTIVE_CANDIDATE" ? "mint-text" : ""}>
            {node.status}
          </dd>
        </div>
        <div>
          <dt>Direct parent</dt>
          <dd>
            {parent ? (
              <button
                className="parent-link"
                onClick={() => onSelect(parent.id)}
              >
                {parent.label} ↗
              </button>
            ) : (
              "Unresolved · no edge drawn"
            )}
          </dd>
        </div>
        <div>
          <dt>What changes</dt>
          <dd>{node.change}</dd>
        </div>
      </dl>
      <p className="formulation-relevance">{method.relevance}</p>
      <details className="methods-sheet formulation-methods" key={node.id}>
        <summary>Methods & evidence · this formulation</summary>
        <dl>
          <dt>World / dynamics family</dt>
          <dd>
            <code>{method.world}</code>
          </dd>
          <dt>Observation law</dt>
          <dd>
            <code>{method.observation}</code>
          </dd>
          <dt>Forecast task</dt>
          <dd>{method.task}</dd>
          <dt>Metric & evaluation authority</dt>
          <dd>{method.metric}</dd>
          <dt>Model execution & historical evidence</dt>
          <dd>{method.modelEvidence}</dd>
          <dt>Assumption / limitation</dt>
          <dd>{method.limitation}</dd>
        </dl>
        <p>
          A formulation defines a world, observation and task. A fitted
          predictor is a separate object. Only the active new study has the
          four-model comparison below.
        </p>
        <a href={sourceLink(reconstruction.source)} className="quiet-link">
          Inspect missing model authorities ↗
        </a>
      </details>
      <details className="lineage-evidence">
        <summary>Inspect the evidence level</summary>
        <dl>
          <dt>Public generation + result chain</dt>
          <dd>{reconstruction.chain}</dd>
          <dt>Historical numeric result</dt>
          <dd>{reconstruction.historical(node.id)}</dd>
        </dl>
        <p>
          A fresh synthetic generator runs. No exact historical score replay.
          These evidence levels do not determine scientific status.
        </p>
        <a className="quiet-link" href={sourceLink(reconstruction.source)}>
          Reproduction matrix <ArrowUpRight size={14} />
        </a>
        <a className="quiet-link" href="#evidence">
          Evidence & limitations ↓
        </a>
      </details>
      <a className="quiet-link contract-link" href={sourceLink(node.source)}>
        Read the pinned scientific contract <ArrowUpRight size={14} />
      </a>
      {node.id === activeId && (
        <div className="lineage-next">
          <a className="button primary" href="#explorer">
            Explore the active study <ArrowDown size={15} />
          </a>
          <a href="#lab">Try its mathematical anchors ↗</a>
        </div>
      )}
    </>
  );
}
function Branch({
  node,
  selected,
  onSelect,
}: { node: Formulation } & Selection) {
  const children = lineage.filter((n) => n.parent === node.id);
  return (
    <li
      className={activePath.has(node.id) ? "active-path" : ""}
      data-formulation={node.id}
      data-parent={node.parent ?? "unresolved"}
    >
      <button
        className="lineage-node"
        aria-pressed={selected === node.id}
        onClick={() => onSelect(node.id)}
        title={node.id}
      >
        <span className="node-mark" aria-hidden="true" />
        <span>
          <strong>{node.label}</strong>
          <small>{node.status.replaceAll("_", " ")}</small>
        </span>
        <span className="node-open" aria-hidden="true">
          ↗
        </span>
      </button>
      {selected === node.id && (
        <div className="mobile-lineage-detail">
          <FormulationDetail node={node} onSelect={onSelect} />
        </div>
      )}
      {children.length > 0 && (
        <ul
          className={children.length > 1 ? "branch-list fork" : "branch-list"}
        >
          {children.map((child) => (
            <Branch
              key={child.id}
              node={child}
              selected={selected}
              onSelect={onSelect}
            />
          ))}
        </ul>
      )}
    </li>
  );
}
export default function Lineage() {
  const [selected, setSelected] = useState(activeId);
  useEffect(() => {
    const restore = () => {
      const id = new URLSearchParams(location.search).get("formulation");
      setSelected(lineage.some((n) => n.id === id) ? id! : activeId);
    };
    restore();
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, []);
  const node = lineage.find((n) => n.id === selected)!;
  const select = (id: string) => {
    setSelected(id);
    const url = new URL(location.href);
    url.searchParams.set("formulation", id);
    url.hash = "lineage";
    history.pushState(null, "", url);
    // Keep parent navigation in the graph's keyboard order, including on small screens.
    document
      .querySelector<HTMLButtonElement>(`[data-formulation="${id}"] > button`)
      ?.focus();
  };
  return (
    <section
      id="lineage"
      className="shell section story-act"
      aria-labelledby="lineage-title"
    >
      <div className="eyebrow">
        <span className="section-number">ACT II</span> THE EVOLUTION{" "}
        <GitBranch size={15} />
      </div>
      <h2 id="lineage-title" className="editorial-heading">
        Eight formulations.
        <br />
        <span>More than one way to ask.</span>
      </h2>
      <p className="story-deck">
        Change a measurement. Change an exposure law. Change the question.
        <br className="desktop-break" /> Follow the contracts to see what each
        formulation actually asks.
      </p>
      <div className="graph-legend">
        <span>
          <i /> Path toward the active study
        </span>
        <span>
          Lines mean documented parentage, never dates or performance.
        </span>
      </div>
      <p className="story-caption">
        Select a branch to inspect its question, assumptions and missing
        evidence. Selection is preserved in the URL; browser Back restores the
        previous branch.
      </p>
      <div className="lineage-layout">
        <div
          className="lineage-graph"
          aria-label="Scientific formulation families"
        >
          <div className="family-heading">
            01 / PRESEASON CAMP <span>H72 · D7</span>
          </div>
          <ul className="family-tree">
            {" "}
            <Branch node={lineage[0]} selected={selected} onSelect={select} />
          </ul>
          <div className="family-heading">
            02 / POST-EXPOSURE <span>H24 · H48 · H72</span>
          </div>
          <ul className="family-tree">
            <Branch node={lineage[3]} selected={selected} onSelect={select} />
          </ul>
          <div className="family-heading unresolved-heading">
            UNRESOLVED ANCESTRY <span>NO PARENT EDGE</span>
          </div>
          <ul className="family-tree">
            <Branch node={lineage[2]} selected={selected} onSelect={select} />
          </ul>
        </div>
        <div
          className="desktop-lineage-detail"
          aria-live="polite"
          aria-atomic="true"
        >
          <FormulationDetail node={node} onSelect={select} />
        </div>
      </div>
      <div className="reconstruction">
        <div>
          <div className="eyebrow">OPEN SCIENCE / RECONSTRUCTION</div>
          <h3>
            Rebuild the path.
            <br />
            <span>Keep the gaps visible.</span>
          </h3>
          <a className="quiet-link" href={sourceLink(reconstruction.source)}>
            Inspect the reconstruction <ArrowUpRight size={14} />
          </a>
        </div>
        <div className="reconstruction-steps">
          {reconstruction.milestones.map((m) => (
            <article key={m.stage}>
              <span className="mono">{m.stage}</span>
              <h4>{m.title}</h4>
              <p>{m.text}</p>
            </article>
          ))}
        </div>
      </div>
      <div className="new-studies">
        <span className="eyebrow">
          NEW PUBLIC EXPERIMENTS ≠ HISTORICAL REPLAY
        </span>
        {experiments.map((e) => (
          <a key={e.title} href={sourceLink(e.source)}>
            <h4>
              {e.title} <ArrowUpRight size={15} />
            </h4>
            <p>{e.text}</p>
          </a>
        ))}
      </div>
    </section>
  );
}
