import type { Metadata } from "next";
import { ArrowUpRight, Download, FileText } from "lucide-react";
import { Chapter, PageIntro, SiteFooter, SiteHeader } from "@/components/site-shell";
import {
  CITATION_URL,
  PAPER,
  RELEASE_URL,
  manuscript,
  paperPage,
  sourceAt,
  treeAt,
} from "@/lib/manuscript";

export const metadata: Metadata = {
  title: "Research paper — Recovery Observatory",
  description: manuscript.paper.title ?? undefined,
};

const kb = (bytes: number) => `${Math.round(bytes / 1024).toLocaleString("en-US")} KB`;

export default function PaperPage() {
  const p = manuscript.paper;
  return (
    <>
      <SiteHeader current="paper" />
      <main id="main" className="pub-page">
        <PageIntro eyebrow="Research paper · V3 · unsubmitted research draft" title={p.title ?? "Research paper"}>
          <p className="pub-status" role="note">
            <strong>Status:</strong> {p.status}
          </p>
          <div className="pub-actions">
            <a className="button primary" href={PAPER.href}>
              <FileText size={16} aria-hidden="true" /> Read the research paper (PDF, {PAPER.pages} pages)
            </a>
            <a className="button" href="/results/">
              Explore the interactive figures
            </a>
          </div>
        </PageIntro>

        <Chapter id="abstract" title="Abstract" kicker="Manuscript p. 1">
          <p className="pub-abstract">{p.abstract}</p>
        </Chapter>

        <Chapter id="questions" title="Research questions">
          <ol className="pub-rq-list">
            {p.researchQuestions.map((q) => (
              <li key={q.id}>
                <span className="pub-rq-id">{q.id}</span>
                <div>
                  <h3>{q.title}</h3>
                  <p>{q.question}</p>
                </div>
              </li>
            ))}
          </ol>
        </Chapter>

        <Chapter id="downloads" title="Documents">
          <div className="pub-doc-grid">
            {p.files.map((f) => (
              <article key={f.id} className="pub-doc">
                <h3>{f.label}</h3>
                <p className="pub-muted">
                  PDF · {kb(f.bytes)}
                  {f.pages ? ` · ${f.pages} pages` : ""}
                </p>
                <p className="pub-hash">
                  SHA-256 <code>{f.sha256}</code>
                </p>
                <div className="pub-doc-links">
                  <a href={f.href}>
                    <Download size={14} aria-hidden="true" /> Open PDF
                  </a>
                  <a href={sourceAt(f.path)} target="_blank" rel="noreferrer">
                    In repository <ArrowUpRight size={13} aria-hidden="true" />
                  </a>
                </div>
              </article>
            ))}
          </div>
          <p className="pub-muted">
            The PDFs are copied at build time from <code>{p.package}</code> after their digests are checked against{" "}
            <a href={sourceAt(`${p.package}/ARTIFACT_SHA256SUMS`)}>ARTIFACT_SHA256SUMS</a> (SHA-256{" "}
            <code>{p.artifactManifestSha256.slice(0, 16)}…</code>). Figures, receipts and regeneration scripts:{" "}
            <a href={treeAt(p.package)} target="_blank" rel="noreferrer">
              V3 manuscript package
            </a>
            .
          </p>
        </Chapter>

        <Chapter id="sections" title="Section guide">
          <ol className="pub-section-list">
            {p.sections.map((s) => (
              <li key={s.id}>
                <a href={paperPage(s.page)}>
                  <span>{s.title}</span>
                  <span className="pub-muted">p. {s.page}</span>
                </a>
              </li>
            ))}
          </ol>
        </Chapter>

        <Chapter id="figures" title="Figures in the paper and their interactive versions">
          <ol className="pub-figure-list">
            {manuscript.figures.map((f) => (
              <li key={f.number}>
                <span className="pub-fig-no">Fig. {f.number}</span>
                <div>
                  <p>{f.question}</p>
                  <p className="pub-fig-links">
                    <a href={`${f.route}#${f.id}`}>Interactive figure</a>
                    <a href={paperPage(f.page)}>Manuscript p. {f.page}</a>
                    <a href={sourceAt(f.files[1].path)} target="_blank" rel="noreferrer">
                      Static SVG
                    </a>
                    {f.receipt && (
                      <a href={sourceAt(f.receipt.path)} target="_blank" rel="noreferrer">
                        Receipt
                      </a>
                    )}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </Chapter>

        <Chapter id="availability" title="Data availability (from the paper)" kicker="Manuscript p. 12">
          <blockquote className="pub-quote">{p.dataAvailability}</blockquote>
        </Chapter>

        <Chapter id="cite" title="Citing this work">
          <p>
            Cite the software with the repository-root{" "}
            <a href={CITATION_URL}>CITATION.cff</a> (version {p.releaseVersion}) and the{" "}
            <a href={RELEASE_URL}>v{p.releaseVersion} release</a>. The manuscript is an unsubmitted draft; if you
            refer to it, cite it as an unpublished draft. Author names and publication declarations are pending
            owner confirmation.
          </p>
        </Chapter>
      </main>
      <SiteFooter />
    </>
  );
}
