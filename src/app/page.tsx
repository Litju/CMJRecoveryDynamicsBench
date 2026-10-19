import { ArrowDown, ArrowUpRight, Activity, Github } from "lucide-react";
import { brand } from "@/lib/brand";
import { data, sourceLink } from "@/lib/science";
import HeroInstrument from "@/components/hero-instrument";
import Explorer from "@/components/explorer";
import RecoveryLab from "@/components/recovery-lab";
import Evidence from "@/components/evidence";
import Lineage from "@/components/lineage";
import EpisodeTheater from "@/components/episode-theater";
import StoryProgress from "@/components/story-progress";
import { Question, Experiment, Remaining, QuickRoute } from "@/components/research-story";
export default function Home() {
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to research
      </a>
      <header className="site-header">
        <div className="shell nav-inner">
          <a href="#" className="wordmark" aria-label={`${brand.name} home`}>
            <span className="brand-symbol">
              <Activity size={21} />
            </span>
            {brand.shortName}
            <span className="edition">RESEARCH / 01</span>
          </a>
          <nav aria-label="Main navigation">
            <a href="#world">Synthetic world</a>
            <a href="#lineage">Research lineage</a>
            <a href="#explorer">Benchmark</a>
            <a href="#lab">Recovery lab</a>
            <a href="#evidence">Evidence</a>
          </nav>
          <a
            className="source-nav"
            aria-label="View scientific source on GitHub"
            href={data.provenance.repository}
            target="_blank"
            rel="noreferrer"
          >
            <Github size={16} />
            <span>View source</span>
            <ArrowUpRight size={14} />
          </a>
        </div>
      </header>
      <main id="main">
        <section className="hero shell" aria-labelledby="hero-title">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="status-dot" />
              {brand.eyebrow}
            </div>
            <h1 id="hero-title">
              Recovery.
              <br />
              Under a<br />
              <span>different lens.</span>
            </h1>
            <p className="hero-description">
              A jump is measured in a moment. Recovery evolves for days.
              Explore how an open, synthetic countermovement-jump research
              program turns that question into a testable forecast.
            </p>
            <div className="hero-actions">
              <a href="#question" className="button primary">
                Start the story <ArrowDown size={16} />
              </a>
              <a href="#explorer" className="quiet-link">
                Explore benchmark <ArrowUpRight size={15} />
              </a>
            </div>
            <div className="scope-tag">
              <span className="tiny-cross">+</span> PUBLIC SYNTHETIC RESEARCH{" "}
              <span className="tag-divider">/</span> NO HUMAN DATA
            </div>
          </div>
          <HeroInstrument />
        </section>
        <div className="shell research-strip" aria-label="Study at a glance">
          <div>
            <span className="strip-label">PUBLIC FORMULATIONS</span>
            <strong>
              08<span> connected by contracts</span>
            </strong>
          </div>
          <div>
            <span className="strip-label">FORECAST HORIZONS</span>
            <strong>
              24 / 48 / 72<span> hours</span>
            </strong>
          </div>
          <div>
            <span className="strip-label">INDEPENDENT TEST ROOTS</span>
            <strong>
              03<span> same generator</span>
            </strong>
          </div>
          <div>
            <span className="strip-label">SCIENTIFIC SOURCE</span>
            <a
              href={sourceLink(
                "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json",
              )}
              target="_blank"
              rel="noreferrer"
            >
              <strong className="mono">
                {data.provenance.commit.slice(0, 7)} <ArrowUpRight size={15} />
              </strong>
              <span className="frozen-label">Immutable snapshot</span>
            </a>
          </div>
        </div>
        <StoryProgress />
        <QuickRoute />
        <Question />
        <EpisodeTheater />
        <Lineage />
        <Experiment />
        <Explorer />
        <Remaining />
        <RecoveryLab />
        <Evidence />
      </main>
      <footer className="shell footer">
        <div>
          <a href="#" className="footer-brand">
            <Activity size={20} />
            {brand.name}
          </a>
          <p>A provisional identity. A reproducible foundation.</p>
        </div>
        <div className="footer-links">
          <a href={sourceLink("CITATION.cff")}>
            Citation <ArrowUpRight size={13} />
          </a>
          <a href={sourceLink("LICENSE")}>
            Apache-2.0 software <ArrowUpRight size={13} />
          </a>
          <a href={data.provenance.repository}>
            Scientific source <ArrowUpRight size={13} />
          </a>
        </div>
        <p className="footer-credit">
          Research software by Julio Rodriguez.
          <br />
          Original code license excludes external datasets and third-party
          materials.
        </p>
      </footer>
    </>
  );
}
