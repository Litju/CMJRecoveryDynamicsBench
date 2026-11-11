import { ArrowDown, ArrowUpRight } from "lucide-react";
import { brand } from "@/lib/brand";
import { CITATION_URL } from "@/lib/manuscript";
import { SiteFooter, SiteHeader } from "@/components/site-shell";
import Explorer from "@/components/explorer";
import RecoveryLab from "@/components/recovery-lab";
import Evidence from "@/components/evidence";
import Lineage from "@/components/lineage";
import EpisodeTheater from "@/components/episode-theater";
import ScrollJourney from "@/components/scroll-journey";
import StoryProgress from "@/components/story-progress";
import { Question, Experiment, Remaining, ResearchCover } from "@/components/research-story";
import Gate7Atlas, { ResearchTour } from "@/components/gate7-atlas";
import ScienceOverview from "@/components/science/science-overview";
import ChapterHead from "@/components/science/chapter-head";
import ForceTimeExhibit from "@/components/science/force-time-exhibit";
import ResponseExhibit from "@/components/science/response-exhibit";
import ArchitectureProgression from "@/components/science/architecture-progression";
import Conclusions from "@/components/science/conclusions";

export default function Home() {
  return (
    <>
      <SiteHeader current="overview" />
      <main id="main">
        <ScienceOverview />
        <ScrollJourney>
          <section id="intro" className="hero shell" aria-labelledby="hero-title">
            <div className="hero-copy">
              <div className="eyebrow">
                <span className="status-dot" />
                {brand.eyebrow}
              </div>
              <div className="hero-discipline">MACHINE LEARNING / SPORTS SCIENCE</div>
              <h2 id="hero-title" className="hero-heading">
                One jump.
                <br />
                Three days.
                <br />
                <span>What changes?</span>
              </h2>
              <p className="hero-description">
                After a training exposure, can we forecast how mean concentric force and net impulse will change? A
                controlled synthetic study of measurement, response dynamics and the limits of prediction.
              </p>
              <p className="hero-byline">
                <span>UPSTREAM RESEARCH SOFTWARE BY</span> Julio Rodriguez{" "}
                <a href={CITATION_URL} aria-label="Current research software citation (v1.1.0)">
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
                <span className="tiny-cross">+</span> PUBLIC SYNTHETIC RESEARCH <span className="tag-divider">/</span> NO HUMAN DATA
              </div>
            </div>
            <ResearchCover />
          </section>
          <StoryProgress />

          <ChapterHead id="ch1">
            <p>
              Force plates record the vertical force of a jump. Two numbers summarize the push: the gross mean force
              over the concentric phase and the net impulse after removing body weight. Peak force is different.
            </p>
          </ChapterHead>
          <div className="shell">
            <ForceTimeExhibit />
          </div>
          <Question />

          <ChapterHead id="ch2">
            <p>
              The forecasting question is how these outcomes change one, two and three days after a training exposure.
              In the synthetic world the answer is a fixed two-mode mathematical response; the exhibit below is that
              assumption, not observed recovery.
            </p>
          </ChapterHead>
          <div className="shell">
            <ResponseExhibit />
          </div>
          <EpisodeTheater />
          <RecoveryLab />

          <ChapterHead id="ch3">
            <p>
              Nine original neural families encode the problem with increasing structure: raw features, prior-episode
              history, recurrence, horizon awareness and a schedule basis.
            </p>
          </ChapterHead>
          <ArchitectureProgression />

          <ChapterHead id="ch4">
            <p>
              One synthetic generator, 96 training camps, 16 development camps, three evaluation roots, three
              horizons, two outcomes, four evaluated reference models and a strict leakage boundary.
            </p>
          </ChapterHead>
          <Experiment />

          <ChapterHead id="ch5">
            <p>
              The four-model benchmark is the central quantitative result. Every cell, root and model is explorable
              below; the figures with bootstrap intervals, ablations and training-camp diagnostics are on the{" "}
              <a href="/results/">results page</a>.
            </p>
          </ChapterHead>
          <Explorer />

          <ChapterHead id="ch6">
            <p>What the controlled findings support, and what they do not.</p>
          </ChapterHead>
          <Conclusions />
          <Remaining />

          <ChapterHead id="ch7">
            <p>
              Supporting evidence: reconstruction of the original architectures, numerical qualification of 18 routes,
              source provenance and the immutable software release (
              <a href={CITATION_URL}>v1.1.0</a>). It supports reproducibility, not predictive validity.
            </p>
          </ChapterHead>
          <ResearchTour />
          <Lineage />
          <Evidence />
        </ScrollJourney>
        <Gate7Atlas />
      </main>
      <SiteFooter />
    </>
  );
}
