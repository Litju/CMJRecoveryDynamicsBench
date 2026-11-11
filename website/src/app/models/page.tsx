import type { Metadata } from "next";
import { Chapter, PageIntro, SiteFooter, SiteHeader } from "@/components/site-shell";
import ArchitectureFigure from "@/components/figures/fig3-architectures";
import NumericalFigure from "@/components/figures/fig4-numerical";

export const metadata: Metadata = {
  title: "Recovered models — Recovery Observatory",
  description: "Recovered M0–M8 neural architectures and the numerical qualification of 18 original routes.",
};

export default function ModelsPage() {
  return (
    <>
      <SiteHeader current="models" />
      <main id="main" className="pub-page">
        <PageIntro eyebrow="Recovered models · RQ2" title="Recovered neural models and numerical qualification" figures={[3, 4]}>
          <p>
            Nine historical neural model families (M0–M8), each with two original repeats, were reconstructed from
            public source. Their recorded CPU outputs match the recovered implementation exactly on all 18 routes;
            archived GPU outputs match within tolerance only for M0–M3.
          </p>
          <p className="pub-status" role="note">
            Original checkpoints, fitted preprocessing values and inference arrays are private and are not
            redistributed. Nothing on this page reruns a model, and no accuracy score is created. These nine
            families were not compared for predictive accuracy; the four models that were scored are on the{" "}
            <a href="/results/">results page</a>.
          </p>
        </PageIntro>
        <Chapter id="architectures" title="Architectures" kicker="Methods · neural reconstruction">
          <ArchitectureFigure />
        </Chapter>
        <Chapter id="qualification" title="Numerical qualification" kicker="Results · RQ2">
          <NumericalFigure />
        </Chapter>
        <Chapter title="Original model atlas">
          <p>
            Inspect each route&apos;s contract, CPU/GPU status, native mechanics and the authority flow in the{" "}
            <a href="/#model-atlas">original model atlas</a>. Shared links such as{" "}
            <code>/?architecture=additive-basis-model&amp;run=2#model-atlas</code> keep working.
          </p>
        </Chapter>
      </main>
      <SiteFooter />
    </>
  );
}
