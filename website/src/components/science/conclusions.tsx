import { fmt, manuscript, sixCellScore } from "@/lib/manuscript";

const a = (key: string) => manuscript.data.ablations.variants.find((v) => v.key === key)!.mean;

export default function Conclusions() {
  return (
    <section id="conclusions" className="shell sci-conclusions" aria-labelledby="conclusions-title">
      <h3 id="conclusions-title">What the synthetic findings support</h3>
      <ul>
        <li>
          Both fitted reference models cut error sharply relative to the zero baseline ({fmt(sixCellScore("zero_innovation", "mean"), 2)}) and training
          mean ({fmt(sixCellScore("training_constant", "mean"), 2)}): ridge {fmt(sixCellScore("ridge_full", "mean"), 2)}, structured{" "}
          {fmt(sixCellScore("structured_full", "mean"), 2)}.
        </li>
        <li>
          Current exposure and prior-episode history carried the usable signal ({fmt(a("ridge_no_current_exposure"), 3)} and{" "}
          {fmt(a("ridge_no_prior_history"), 3)} without them); participant context changed ridge NRMSE by 0.000076.
        </li>
        <li>Error rose with horizon for the fitted models, and impulse was harder to predict than force at every horizon.</li>
        <li>Between 24 and 96 training camps the error barely moved; all selected penalties sit at the lower edge of the grid.</li>
      </ul>
      <h3>What they do not</h3>
      <ul>
        <li>They are not athlete accuracy: all data come from one simulator, and the three roots differ only by seed.</li>
        <li>The 24 h and 84 h modes are assumptions, so nothing here measures biological recovery.</li>
        <li>Nine original networks were not scored; the progression in Chapter 3 is a design rationale only.</li>
        <li>Recorded intervals are descriptive (16 camps per root) and compare with the zero baseline only.</li>
      </ul>
      <p className="pub-muted">
        Open questions: weaker regularization, other generators, a pre-specified comparison of the original architectures,
        and any real-data validation, none of which this study performs.
      </p>
    </section>
  );
}
