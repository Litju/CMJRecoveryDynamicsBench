"use client";
import type { ReactNode, RefObject } from "react";
import { ArrowUpRight, Download, FileText } from "lucide-react";
import {
  figure as figureMeta,
  paperPage,
  section,
  sourceAt,
  manuscript,
} from "@/lib/manuscript";
import { download, serializeSVG, toCSV, type DataTable } from "@/lib/figure-export";

export interface FigureProps {
  number: number;
  title: string;
  /** Interactive chart and its controls. */
  children: ReactNode;
  interpretation: ReactNode;
  limitations: string[];
  units: string;
  table: DataTable;
  json: unknown;
  /** An SVG, or a container of `svg[data-panel]` small multiples. */
  svgRef?: RefObject<Element | null>;
  /** Short status of the current selection, announced politely. */
  readout?: ReactNode;
}


export default function FigureFrame({
  number,
  title,
  children,
  interpretation,
  limitations,
  units,
  table,
  json,
  svgRef,
  readout,
}: FigureProps) {
  const meta = figureMeta(number);
  const sec = section(meta.section);
  const base = `observatory-fig${number}`;
  const provenance = `Recovery Observatory figure ${number}; manuscript Fig. ${number}, p. ${meta.page}. Values from ${manuscript.paper.package} (ARTIFACT_SHA256SUMS ${manuscript.paper.artifactManifestSha256}).`;
  const exportJSON = () =>
    download(
      `${base}.json`,
      `${JSON.stringify(
        {
          figure: number,
          title,
          question: meta.question,
          units,
          provenance,
          receipt: meta.receipt
            ? { path: meta.receipt.path, sha256: meta.receipt.sha256, numericalTest: meta.receipt.numericalTest }
            : null,
          data: json,
        },
        null,
        2,
      )}\n`,
      "application/json",
    );
  const exportCSV = () => download(`${base}.csv`, toCSV(table), "text/csv");
  const exportSVG = () => {
    if (svgRef?.current)
      download(`${base}.svg`, serializeSVG(svgRef.current, `Figure ${number}. ${title}`, provenance), "image/svg+xml");
  };
  return (
    <figure className="pub-figure" id={meta.id} aria-labelledby={`${meta.id}-title`} data-figure={number}>
      <header className="pub-figure-head">
        <p className="pub-kicker">
          <span>Figure {number}</span>
          <a href={paperPage(meta.page)} className="pub-page-link">
            Manuscript Fig. {number} · p. {meta.page}
          </a>
        </p>
        <h3 id={`${meta.id}-title`}>{title}</h3>
        <p className="pub-question">
          <span className="pub-label">Question</span> {meta.question}
        </p>
      </header>
      <div className="pub-figure-body">{children}</div>
      {readout && (
        <div className="pub-readout" aria-live="polite">
          {readout}
        </div>
      )}
      <figcaption className="pub-figcaption">
        <div className="pub-interpretation">
          <span className="pub-label">Interpretation</span>
          <div>{interpretation}</div>
        </div>
        <div className="pub-limits">
          <span className="pub-label">Limitations</span>
          <ul>
            {limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </div>
        <p className="pub-units">
          <span className="pub-label">Units</span> {units}
        </p>
      </figcaption>
      <details className="pub-details">
        <summary>Data table · {table.rows.length} rows</summary>
        <div className="pub-table-scroll" tabIndex={0} role="region" aria-label={`Figure ${number} data table`}>
          <table className="pub-table">
            <caption>{table.caption}</caption>
            <thead>
              <tr>
                {table.columns.map((c) => (
                  <th key={c} scope="col">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((r, i) => (
                <tr key={i}>
                  {r.map((v, j) =>
                    j === 0 ? (
                      <th key={j} scope="row">
                        {v === null ? "—" : String(v)}
                      </th>
                    ) : (
                      <td key={j} className={typeof v === "number" ? "num" : undefined}>
                        {v === null ? "—" : String(v)}
                      </td>
                    ),
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <details className="pub-details">
        <summary>Manuscript caption and evidence</summary>
        <p className="pub-caption-text">{meta.caption}</p>
        {meta.receipt && (
          <dl className="pub-receipt">
            <dt>Population</dt>
            <dd>{meta.receipt.population}</dd>
            <dt>Metric</dt>
            <dd>{meta.receipt.metric}</dd>
            <dt>Grouping</dt>
            <dd>{meta.receipt.grouping}</dd>
            <dt>Sample sizes</dt>
            <dd>{meta.receipt.sampleSizes}</dd>
            <dt>Uncertainty</dt>
            <dd>{meta.receipt.uncertainty}</dd>
            <dt>Recorded check</dt>
            <dd>
              <code>{meta.receipt.numericalTest}</code> — passed
            </dd>
            <dt>Sources</dt>
            <dd>
              <ul className="pub-source-list">
                {meta.receipt.releaseSources.map((s) => (
                  <li key={s.id}>
                    <a href={sourceAt(s.packaged)} target="_blank" rel="noreferrer">
                      {s.id} · {s.path}
                    </a>{" "}
                    <code title="SHA-256">{s.sha256.slice(0, 12)}…</code>
                  </li>
                ))}
                {meta.receipt.localData.map((s) => (
                  <li key={s.path}>
                    <a href={sourceAt(s.path)} target="_blank" rel="noreferrer">
                      {s.path.split("/").pop()}
                    </a>{" "}
                    <code title="SHA-256">{s.sha256.slice(0, 12)}…</code>
                  </li>
                ))}
              </ul>
            </dd>
          </dl>
        )}
      </details>
      <footer className="pub-figure-foot">
        <a href={paperPage(meta.page)}>
          <FileText size={14} aria-hidden="true" /> {sec.title} (p. {sec.page})
        </a>
        {meta.receipt ? (
          <a href={sourceAt(meta.receipt.path)} target="_blank" rel="noreferrer">
            Figure receipt <ArrowUpRight size={13} aria-hidden="true" />
          </a>
        ) : (
          <a href={sourceAt(`${manuscript.paper.package}/evidence/release_sources/S17_lineage.json`)} target="_blank" rel="noreferrer">
            Lineage source <ArrowUpRight size={13} aria-hidden="true" />
          </a>
        )}
        <a href={sourceAt(meta.files[1].path)} target="_blank" rel="noreferrer">
          Static manuscript figure <ArrowUpRight size={13} aria-hidden="true" />
        </a>
        <span className="pub-export" role="group" aria-label={`Export figure ${number}`}>
          {svgRef && (
            <button type="button" onClick={exportSVG}>
              <Download size={13} aria-hidden="true" /> SVG
            </button>
          )}
          <button type="button" onClick={exportCSV}>
            <Download size={13} aria-hidden="true" /> CSV
          </button>
          <button type="button" onClick={exportJSON}>
            <Download size={13} aria-hidden="true" /> JSON
          </button>
        </span>
      </footer>
    </figure>
  );
}
