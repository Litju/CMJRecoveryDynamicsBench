import type { Metadata } from "next";
import { ArrowUpRight, Download, FileText } from "lucide-react";
import { Chapter, PageIntro, SiteFooter, SiteHeader } from "@/components/site-shell";
import flagship from "@/data/flagship.json";
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
  description: flagship.title,
};

const FLAGSHIP_FIGURES: { n: number; title: string; href: string; label: string }[] = [
  { n: 1, title: "Study map: measurement to synthetic benchmark", href: "/#overview", label: "Overview" },
  { n: 2, title: "Force–time definitions: mean force, peak force, net impulse", href: "/#exhibit-force-time", label: "Interactive exhibit" },
  { n: 3, title: "Three-trial assessment and baseline-relative innovation", href: "/#ch1", label: "Chapter 1" },
  { n: 4, title: "Fixed response modes of the synthetic generator", href: "/#exhibit-response", label: "Interactive exhibit" },
  { n: 5, title: "Original architectures M0–M8 and parameter counts", href: "/models/#fig-3", label: "Interactive figure" },
  { n: 6, title: "Design of the synthetic experiment", href: "/#ch4", label: "Chapter 4" },
  { n: 7, title: "Six-cell NRMSE of the four reference models", href: "/results/#fig-6", label: "Interactive figure" },
  { n: 8, title: "Model-by-cell NRMSE heatmap", href: "/results/#fig-7", label: "Interactive figure" },
  { n: 9, title: "Recorded camp-bootstrap intervals", href: "/results/#fig-8", label: "Interactive figure" },
  { n: 10, title: "Ablations and nested training camps", href: "/results/#fig-9", label: "Interactive figure" },
  { n: 11, title: "Numerical qualification of 18 routes", href: "/models/#fig-4", label: "Interactive figure" },
];
const flagshipFile = (id: string) => flagship.files.find((f) => f.id === id)!;
const flagshipPage = (page: number) => `${flagshipFile("illustrated").href}#page=${page}`;

const kb = (bytes: number) => `${Math.round(bytes / 1024).toLocaleString("en-US")} KB`;

export default function PaperPage() {
  const p = manuscript.paper;
  return (
    <>
      <SiteHeader current="paper" />
      <main id="main" className="pub-page">
        <PageIntro eyebrow="Flagship research paper · owner-review draft" title={flagship.title}>
          <p className="pub-status" role="note">
            <strong>Status:</strong> {flagship.status}
          </p>
          <div className="pub-actions">
            <a className="button primary" href={flagshipFile("illustrated").href}>
              <FileText size={16} aria-hidden="true" /> Read the flagship paper (PDF, {flagshipFile("illustrated").pages} pages)
            </a>
            <a className="button" href="/results/">
              Explore the interactive results
            </a>
          </div>
        </PageIntro>

        <Chapter id="flagship-abstract" title="Abstract" kicker="Flagship paper p. 1">
          <p className="pub-abstract">{flagship.abstract}</p>
        </Chapter>

        <Chapter id="flagship-documents" title="Flagship documents">
          <div className="pub-doc-grid">
            {flagship.files.map((f) => (
              <article key={f.id} className="pub-doc">
                <h3>{f.label}</h3>
                <p className="pub-muted">
                  PDF · {kb(f.bytes)} · {f.pages} pages
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
            Copied at build time from <code>{flagship.package}</code> after checking digests against ARTIFACT_SHA256SUMS
            (SHA-256 <code>{flagship.artifactManifestSha256.slice(0, 16)}…</code>).
          </p>
        </Chapter>

        <Chapter id="flagship-sections" title="Section guide">
          <ol className="pub-section-list">
            {Object.entries(flagship.sectionPages).map(([name, page]) => (
              <li key={name}>
                <a href={flagshipPage(page as number)}>
                  <span>{name}</span>
                  <span className="pub-muted">p. {page as number}</span>
                </a>
              </li>
            ))}
          </ol>
        </Chapter>

        <Chapter id="flagship-figures" title="Flagship figures and their interactive versions">
          <ol className="pub-figure-list">
            {FLAGSHIP_FIGURES.map((f) => (
              <li key={f.n}>
                <span className="pub-fig-no">Fig. {f.n}</span>
                <div>
                  <p>{f.title}</p>
                  <p className="pub-fig-links">
                    <a href={f.href}>{f.label}</a>
                    <a href={flagshipPage((flagship.figurePages as Record<string, number>)[String(f.n)])}>
                      Paper p. {(flagship.figurePages as Record<string, number>)[String(f.n)]}
                    </a>
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </Chapter>

        <Chapter id="companion" title="Companion paper: retrospective reconstruction (V3)" kicker="Secondary research artifact">
          <p>
            The original paper reconstructs and numerically qualifies the historical research program that the nine
            neural architectures came from. It supports Chapter 7 of this site. Its content, PDFs and deep links are
            unchanged below.
          </p>
        </Chapter>

        <Chapter id="companion-intro" title={p.title ?? "Research paper"} kicker="V3 · unsubmitted research draft">
          <p className="pub-status" role="note">
            <strong>Status:</strong> {p.status}
          </p>
          <div className="pub-actions">
            <a className="button" href={PAPER.href}>
              <FileText size={16} aria-hidden="true" /> Read the companion paper (PDF, {PAPER.pages} pages)
            </a>
          </div>
        </Chapter>

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
