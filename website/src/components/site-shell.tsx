import type { ReactNode } from "react";
import { Activity, ArrowUpRight, FileText, Github } from "lucide-react";
import { brand } from "@/lib/brand";
import flagship from "@/data/flagship.json";
import {
  CITATION_URL,
  PAPER,
  REPOSITORY,
  RELEASE_URL,
  figure as figureMeta,
  manuscript,
} from "@/lib/manuscript";

export const AREAS = [
  { href: "/", key: "overview", label: "The science" },
  { href: "/results/", key: "results", label: "Results" },
  { href: "/models/", key: "models", label: "Architectures" },
  { href: "/methods/", key: "methods", label: "Methods" },
  { href: "/evidence/", key: "evidence", label: "Verification" },
  { href: "/paper/", key: "paper", label: "Research paper" },
] as const;
export type AreaKey = (typeof AREAS)[number]["key"];

export function SiteHeader({ current }: { current: AreaKey }) {
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to research
      </a>
      <header className="site-header">
        <div className="shell nav-inner">
          <a href="/" className="wordmark">
            <span className="brand-symbol">
              <Activity size={21} />
            </span>
            {brand.name}
            <span className="edition">RESEARCH COMPANION</span>
          </a>
          <nav aria-label="Main navigation" className="area-nav">
            {AREAS.map((a) => (
              <a key={a.key} href={a.href} aria-current={a.key === current ? "page" : undefined}>
                {a.label}
              </a>
            ))}
          </nav>
          <div className="header-actions">
            <a className="paper-nav" href={flagship.files[0].href} aria-label="Paper PDF">
              <FileText size={15} aria-hidden="true" />
              <span>Paper PDF</span>
            </a>
            <a
              className="source-nav"
              aria-label="View scientific source on GitHub"
              href={REPOSITORY}
              target="_blank"
              rel="noreferrer"
            >
              <Github size={16} />
              <span>Source</span>
              <ArrowUpRight size={14} />
            </a>
          </div>
        </div>
      </header>
    </>
  );
}

export function SiteFooter() {
  return (
    <footer className="shell footer">
      <div>
        <a href="/" className="footer-brand">
          <Activity size={20} />
          {brand.name}
        </a>
        <p>Open methods. Traceable evidence.</p>
        <p className="footer-status">
          Companion to unsubmitted research drafts. Computational and synthetic study; not peer reviewed; no journal publication or DOI.
        </p>
      </div>
      <div className="footer-links">
        <a href={flagship.files[0].href}>
          Flagship paper (PDF) <ArrowUpRight size={13} />
        </a>
        <a href={PAPER.href}>
          Companion reconstruction paper (PDF) <ArrowUpRight size={13} />
        </a>
        <a href={CITATION_URL}>
          Software citation v{manuscript.paper.releaseVersion} <ArrowUpRight size={13} />
        </a>
        <a href={RELEASE_URL}>
          Release v{manuscript.paper.releaseVersion} <ArrowUpRight size={13} />
        </a>
        <a href={`${REPOSITORY}/blob/v${manuscript.paper.releaseVersion}/LICENSE`}>
          Scientific source license <ArrowUpRight size={13} />
        </a>
        <a href="/evidence/#citations">How to cite</a>
      </div>
      <p className="footer-credit">
        The cited scientific software is by Julio Rodriguez.
        <br />
        Its Apache-2.0 license excludes external datasets and third-party materials.
      </p>
    </footer>
  );
}

export function PageIntro({
  eyebrow,
  title,
  children,
  figures,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
  figures?: number[];
}) {
  return (
    <section className="shell pub-intro" aria-labelledby="page-title">
      <p className="pub-eyebrow">{eyebrow}</p>
      <h1 id="page-title">{title}</h1>
      <div className="pub-lede">{children}</div>
      {figures && (
        <nav className="pub-figure-index" aria-label="Figures on this page">
          {figures.map((n) => {
            const f = figureMeta(n);
            return (
              <a key={n} href={`#${f.id}`}>
                <span>Fig. {n}</span> {f.question}
              </a>
            );
          })}
        </nav>
      )}
    </section>
  );
}

export function Chapter({ id, title, kicker, children }: { id?: string; title: string; kicker?: string; children: ReactNode }) {
  return (
    <section className="shell pub-chapter" id={id} aria-labelledby={id ? `${id}-heading` : undefined}>
      {kicker && <p className="pub-eyebrow">{kicker}</p>}
      <h2 id={id ? `${id}-heading` : undefined}>{title}</h2>
      {children}
    </section>
  );
}
