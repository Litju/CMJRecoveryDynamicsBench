import type { Metadata } from "next";
import { Chapter, PageIntro, SiteFooter, SiteHeader } from "@/components/site-shell";
import GenealogyFigure from "@/components/figures/fig1-genealogy";
import DesignFigure from "@/components/figures/fig2-design";
import BiomechanicsFigure from "@/components/figures/fig5-biomechanics";
import { OUTCOMES } from "@/lib/manuscript";

export const metadata: Metadata = {
  title: "Biomechanics and methods — Recovery Observatory",
  description: "Formulation genealogy, synthetic study design and native force–time measurement definitions.",
};

export default function MethodsPage() {
  return (
    <>
      <SiteHeader current="methods" />
      <main id="main" className="pub-page">
        <PageIntro eyebrow="Biomechanics and methods · RQ1" title="Formulations, study design and measurement" figures={[1, 2, 5]}>
          <p>
            How the historical research program is organised, how the public synthetic study is built, and what the
            force outcomes measure.
          </p>
          <dl className="pub-dl pub-terms">
            {(Object.keys(OUTCOMES) as (keyof typeof OUTCOMES)[]).map((k) => (
              <div key={k}>
                <dt>
                  {OUTCOMES[k].label} ({OUTCOMES[k].unit})
                </dt>
                <dd>{OUTCOMES[k].definition}</dd>
              </div>
            ))}
          </dl>
        </PageIntro>
        <Chapter id="lineage-figure" title="Research genealogy" kicker="Methods · formulations">
          <GenealogyFigure />
        </Chapter>
        <Chapter id="design" title="Synthetic experimental design" kicker="Methods · ADEMP design">
          <DesignFigure />
        </Chapter>
        <Chapter id="biomechanics" title="Native biomechanics" kicker="Methods · measurement">
          <BiomechanicsFigure />
        </Chapter>
        <Chapter title="More methods">
          <ul className="pub-link-list">
            <li>
              <a href="/#world">Interactive synthetic world and episode theater</a>
            </li>
            <li>
              <a href="/#lineage">Lineage explorer with parent evidence</a>
            </li>
            <li>
              <a href="/#lab">Recovery Lab (two-mode mathematical illustration)</a>
            </li>
          </ul>
        </Chapter>
      </main>
      <SiteFooter />
    </>
  );
}
