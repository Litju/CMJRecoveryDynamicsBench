import type { Metadata } from "next";
import { Chapter, PageIntro, SiteFooter, SiteHeader } from "@/components/site-shell";
import SixCellFigure from "@/components/figures/fig6-six-cell";
import HeatmapFigure from "@/components/figures/fig7-heatmap";
import BootstrapFigure from "@/components/figures/fig8-bootstrap";
import AblationFigure from "@/components/figures/fig9-ablations";
import { fmt, manuscript } from "@/lib/manuscript";

export const metadata: Metadata = {
  title: "Experimental results — Recovery Observatory",
  description: "Interactive, source-backed results of the public fixed-mode synthetic benchmark.",
};

export default function ResultsPage() {
  const a = manuscript.data.sixCell.aggregates;
  return (
    <>
      <SiteHeader current="results" />
      <main id="main" className="pub-page">
        <PageIntro eyebrow="Experimental results · RQ3" title="Public synthetic benchmark results" figures={[6, 7, 8, 9]}>
          <p>
            Four reference models were scored on three fixed evaluation roots drawn from one public synthetic
            generator, across six outcome–horizon cells (H24, H48, H72 × mean concentric-force innovation and
            net-impulse innovation). Recorded mean six-cell NRMSE: zero innovation {fmt(a.zero_innovation.mean, 6)},
            training mean {fmt(a.training_constant.mean, 6)}, ridge regression {fmt(a.ridge_full.mean, 6)},
            structured comparator {fmt(a.structured_full.mean, 6)}. Lower is better.
          </p>
          <p className="pub-status" role="note">
            These are descriptive synthetic results. They do not estimate the predictive performance of the
            historical neural models or of any method on athletes, and they are separate from the native H72/D7
            four-cell evaluation.
          </p>
        </PageIntro>
        <Chapter id="performance" title="Model comparison across cells" kicker="Results · RQ3">
          <SixCellFigure />
          <HeatmapFigure />
        </Chapter>
        <Chapter id="uncertainty" title="Recorded uncertainty, ablations and sample size" kicker="Results · uncertainty">
          <BootstrapFigure />
          <AblationFigure />
        </Chapter>
        <Chapter title="Explore every benchmark view">
          <p>
            The original benchmark explorer, with all 96 model × root × horizon × outcome views, RMSE and truth SD,
            is on the overview page: <a href="/#explorer">open the benchmark explorer</a>.
          </p>
        </Chapter>
      </main>
      <SiteFooter />
    </>
  );
}
