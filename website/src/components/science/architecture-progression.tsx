import { fmtInt, manuscript } from "@/lib/manuscript";

const ADDS: Record<string, string> = {
  M0: "Raw-feature MLP, 32 hidden units",
  M1: "Wider MLP, 64 hidden units",
  M2: "Second hidden layer",
  M3: "Pointwise encoder of 4 prior episodes, mean + latest pooling",
  M4: "GRU reads the history in order",
  M5: "Learned forecast-horizon embedding",
  M6: "Two public-schedule basis values",
  M7: "All five basis values",
  M8: "Bias-free linear head on the basis",
};

export default function ArchitectureProgression() {
  const families = manuscript.data.architectures.families;
  const max = Math.max(...families.map((f) => f.parameters));
  return (
    <section id="architecture-progression" className="shell sci-progression" aria-labelledby="arch-prog-title">
      <h3 id="arch-prog-title">Nine original neural families: what each design choice adds</h3>
      <p className="pub-status" role="note" data-testid="architecture-banner">
        Structure only. These nine networks were <strong>not</strong> compared for predictive accuracy: no public
        experiment scored them, and no NRMSE on this site belongs to M0–M8. The four models that were scored are shown
        in Chapter 5.
      </p>
      <ol className="sci-prog-list">
        {families.map((f) => (
          <li key={f.id}>
            <span className="sci-prog-id">{f.id}</span>
            <div className="sci-prog-body">
              <p>
                <strong>{ADDS[f.id]}</strong>
              </p>
              <p className="pub-muted">{f.inputs}</p>
              <div className="sci-prog-bar" role="img" aria-label={`${fmtInt(f.parameters)} parameters`}>
                <span style={{ width: `${(f.parameters / max) * 100}%` }} />
              </div>
            </div>
            <span className="sci-prog-params">{fmtInt(f.parameters)} parameters</span>
          </li>
        ))}
      </ol>
      <p className="pub-muted">
        Each family has two recorded repeats (18 routes). The history, GRU, horizon and basis stages are structural
        choices; what each would contribute to forecast accuracy was not tested here.{" "}
        <a href="/models/#architectures">Interactive architecture figure</a> · <a href="#model-atlas">model atlas</a>
      </p>
    </section>
  );
}
