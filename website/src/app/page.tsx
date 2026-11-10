import { ArrowDown, ArrowUpRight } from "lucide-react";
import { brand } from "@/lib/brand";
import { CITATION_URL } from "@/lib/manuscript";
import { SiteFooter, SiteHeader } from "@/components/site-shell";
import ResearchOverview from "@/components/research-overview";
import { data, sourceLink } from "@/lib/science";
import Explorer from "@/components/explorer";
import RecoveryLab from "@/components/recovery-lab";
import Evidence from "@/components/evidence";
import Lineage from "@/components/lineage";
import EpisodeTheater from "@/components/episode-theater";
import ScrollJourney from "@/components/scroll-journey";
import StoryProgress from "@/components/story-progress";
import {
  Question,
  Experiment,
  Remaining,
  QuickRoute,
  ResearchCover,
} from "@/components/research-story";
import Gate7Atlas, { ResearchTour } from "@/components/gate7-atlas";
export default function Home() {
  return (
    <>
      <SiteHeader current="overview" />
      <main id="main">
        <ResearchOverview />
        <ScrollJourney>
        <section id="intro" className="hero shell" aria-labelledby="hero-title">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="status-dot" />
              {brand.eyebrow}
            </div>
            <div className="hero-discipline">
              MACHINE LEARNING / SPORTS SCIENCE
            </div>
            <h2 id="hero-title" className="hero-heading">
              One jump.
              <br />
              Three days.
              <br />
              <span>What changes?</span>
            </h2>
            <p className="hero-description">
              After a training exposure, can we forecast how mean concentric
              force and net impulse will change? An open research program about
              measurement, hidden dynamics and the limits of prediction.
            </p>
            <p className="hero-byline">
              <span>UPSTREAM RESEARCH SOFTWARE BY</span> Julio Rodriguez{" "}
              <a
                href={CITATION_URL}
                aria-label="Current research software citation (v1.1.0)"
              >
                ↗
              </a>
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
          <ResearchCover />
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
            <span className="strip-label">FIXED EVALUATION ROOTS</span>
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
        <ResearchTour />
        <QuickRoute />
        <Question />
        <EpisodeTheater />
        <Lineage />
        <Experiment />
        <Explorer />
        <Remaining />
        <RecoveryLab />
        <Evidence />
        </ScrollJourney>
        <Gate7Atlas />
      </main>
      <SiteFooter />
    </>
  );
}
