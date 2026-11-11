"use client";
import type { ReactNode, RefObject } from "react";
import { Download } from "lucide-react";
import flagship from "@/data/flagship.json";
import { download, serializeSVG, toCSV, type DataTable } from "@/lib/figure-export";

const paper = flagship.files.find((f) => f.id === "illustrated")!;
export const flagshipPage = (figure: number) =>
  `${paper.href}#page=${(flagship.figurePages as Record<string, number>)[String(figure)]}`;

export default function ExhibitFrame({
  id,
  chapter,
  figure,
  title,
  question,
  children,
  readout,
  interpretation,
  limitations,
  units,
  table,
  svgRef,
}: {
  id: string;
  chapter: string;
  /** Flagship-paper figure number this exhibit corresponds to. */
  figure: number;
  title: string;
  question: string;
  children: ReactNode;
  readout?: ReactNode;
  interpretation: ReactNode;
  limitations: string[];
  units: string;
  table: DataTable;
  svgRef?: RefObject<Element | null>;
}) {
  const provenance = `Recovery Observatory, ${chapter}; flagship paper Fig. ${figure}. Analytical illustration of the synthetic simulator; not athlete data.`;
  return (
    <figure className="pub-figure sci-exhibit" id={id} aria-labelledby={`${id}-title`} data-paper-figure={figure}>
      <header className="pub-figure-head">
        <p className="pub-kicker">
          <span>{chapter}</span>
          <a href={flagshipPage(figure)} className="pub-page-link">
            Flagship paper Fig. {figure} · p. {(flagship.figurePages as Record<string, number>)[String(figure)]}
          </a>
        </p>
        <h3 id={`${id}-title`}>{title}</h3>
        <p className="pub-question">
          <span className="pub-label">Question</span> {question}
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
        <div className="pub-table-scroll" tabIndex={0} role="region" aria-label={`${title} data table`}>
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
                        {String(v)}
                      </th>
                    ) : (
                      <td key={j} className="num">
                        {String(v)}
                      </td>
                    ),
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <div className="pub-export" role="group" aria-label="Export">
        <button type="button" onClick={() => download(`${id}.csv`, toCSV(table), "text/csv")}>
          <Download size={13} aria-hidden="true" /> CSV
        </button>
        {svgRef && (
          <button
            type="button"
            onClick={() => svgRef.current && download(`${id}.svg`, serializeSVG(svgRef.current, title, provenance), "image/svg+xml")}
          >
            <Download size={13} aria-hidden="true" /> SVG
          </button>
        )}
      </div>
    </figure>
  );
}
