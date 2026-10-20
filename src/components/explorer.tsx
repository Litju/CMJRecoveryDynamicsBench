"use client";
import { PlotSelection } from "./plot-selection";
import { useEffect, useState } from "react";
import { IntervalPlot } from "./experiment-methods";
import Benchmark3D from "./benchmark-3d";
import { plotTheme as theme, plotTooltip } from "@/lib/plot-theme.mjs";
import {
  ArrowDownRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Download,
  SlidersHorizontal,
} from "lucide-react";
import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  ReferenceLine,
} from "recharts";
import {
  aggregate,
  cell,
  cellKey,
  data,
  format,
  horizons,
  models,
  sourceLink,
  type ModelId,
  type RootId,
  type Outcome,
} from "@/lib/science";
export default function Explorer() {
  const [model, setModel] = useState<ModelId>("ridge_full");
  const [compare, setCompare] = useState<ModelId>("zero_innovation");
  const [root, setRoot] = useState<RootId>("mean");
  const [horizon, setHorizon] = useState(24);
  const [outcome, setOutcome] = useState<Outcome>("force");
  const [plotMode, setPlotMode] = useState("2d");
  const [metric, setMetric] = useState<"nrmse" | "rmse">("nrmse");
  useEffect(() => {
    const inspect = (event: Event) => {
      const selected = models.find((m) => m.id === (event as CustomEvent<unknown>).detail);
      if (!selected) return;
      setModel(selected.id);
      setRoot("mean");
      setHorizon(24);
      setOutcome("force");
      setMetric("nrmse");
    };
    window.addEventListener("cmj:inspect-model", inspect);
    return () => window.removeEventListener("cmj:inspect-model", inspect);
  }, []);
  const selected = models.find((m) => m.id === model)!;
  const comparison = models.find((m) => m.id === compare)!;
  const current = cell(model, root, horizon, outcome);
  const summary = aggregate(model, root);
  const delta = summary - aggregate(compare, root);
  const variability = data.models[model].acrossRoots;
  const selection = data.models[model].selection;
  const unit = outcome === "force" ? "N/kg" : "m/s";
  const chart = horizons.map((h) => ({
    horizon: `H${h}`,
    selected: cell(model, root, h, outcome)[metric],
    comparison: cell(compare, root, h, outcome)[metric],
  }));
  const cellVariation =
    variability.cell_nrmse_across_roots[
      cellKey(
        horizon,
        outcome,
      ) as keyof typeof variability.cell_nrmse_across_roots
    ];
  return (
    <section
      id="explorer"
      className="shell section"
      aria-labelledby="explorer-title"
    >
      <div className="section-top">
        <div className="eyebrow">
          <span className="section-number">III / DETAIL</span> THE BENCHMARK
          EXPLORER
        </div>
        <span className="live-label">
          <span className="status-dot" /> FROZEN RESULTS · LIVE INTERACTION
        </span>
      </div>
      <div className="section-heading">
        <div>
          <h2 id="explorer-title">
            Look closer. <span>Compare fairly.</span>
          </h2>
          <p>
            Four reference models. Six target cells. One public synthetic
            formulation.
          </p>
        </div>
        <a
          href={sourceLink("docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md")}
          className="quiet-link"
        >
          Study & protocol <ArrowUpRight size={16} />
        </a>
      </div>
      <div className="explorer-panel">
        <aside className="explorer-controls" aria-label="Benchmark controls">
          <div className="panel-label">
            <SlidersHorizontal size={14} /> CONFIGURE VIEW
          </div>
          <fieldset>
            <legend>Reference model</legend>
            <div className="model-options">
              {models.map((m, i) => (
                <button
                  key={m.id}
                  type="button"
                  aria-pressed={model === m.id}
                  onClick={() => setModel(m.id)}
                  data-model-id={m.id}
                  className={`model-option ${model === m.id ? "selected" : ""}`}
                >
                  <span className="model-number">0{i + 1}</span>
                  <span>{m.name}</span>
                  <span className="model-check">
                    {model === m.id ? (
                      <Check size={14} />
                    ) : (
                      <span className="empty-check" />
                    )}
                  </span>
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Forecast horizon</legend>
            <div className="segmented">
              {horizons.map((h) => (
                <button
                  key={h}
                  aria-pressed={horizon === h}
                  onClick={() => setHorizon(h)}
                >
                  H{h}
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Outcome</legend>
            <div className="segmented">
              <button
                aria-pressed={outcome === "force"}
                onClick={() => setOutcome("force")}
              >
                Force
              </button>
              <button
                aria-pressed={outcome === "impulse"}
                onClick={() => setOutcome("impulse")}
              >
                Net impulse
              </button>
            </div>
          </fieldset>
          <div className="select-wrap">
            <label className="select-label" htmlFor="root-select">
              Public test population
            </label>
            <select
              id="root-select"
              value={root}
              onChange={(e) => setRoot(e.target.value as RootId)}
            >
              <option value="mean">Across-root mean</option>
              {["A", "B", "C"].map((r) => (
                <option key={r} value={r}>
                  Test root {r}
                </option>
              ))}
            </select>
            <ChevronDown size={15} />
          </div>
          <div className="select-wrap">
            <label className="select-label" htmlFor="compare-select">
              Compare against
            </label>
            <select
              id="compare-select"
              value={compare}
              onChange={(e) => setCompare(e.target.value as ModelId)}
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
            <ChevronDown size={15} />
          </div>
          <p className="control-note">
            Independent seeds from the <strong>same generator</strong>. These
            are synthetic populations, not separate empirical worlds.
          </p>
        </aside>
        <div className="explorer-results">
          <div className="results-heading">
            <div>
              <span className="panel-label">ACTIVE CANDIDATE</span>
              <h3>Fixed-mode discrepancy recovery</h3>
            </div>
            <span className="small-tag">RES-526</span>
          </div>
          <div className="metric-strip" aria-live="polite" aria-atomic="true">
            <div className="primary-metric">
              <span>
                Six-cell mean NRMSE <span className="direction">↓</span>
              </span>
              <strong data-testid="aggregate-score">{format(summary)}</strong>
              <small>
                {root === "mean"
                  ? "Mean of three root scores"
                  : `Test root ${root}`}{" "}
                · lower is better
              </small>
            </div>
            <div>
              <span>
                {`H${horizon}`} {outcome === "force" ? "force" : "net impulse"}{" "}
                NRMSE
              </span>
              <strong data-testid="cell-score">{format(current.nrmse)}</strong>
              <small>Cell-specific normalization · unitless</small>
            </div>
            <div>
              <span>{`H${horizon}`} RMSE</span>
              <strong data-testid="cell-rmse">
                {format(current.rmse)}
                <em>{unit}</em>
              </strong>
              <small>Baseline-relative innovation</small>
            </div>
          </div>
          <div className="chart-title">
            <div>
              <h4>
                {plotMode === "3d"
                  ? "All six cells · four models"
                  : `${outcome === "force" ? "Force" : "Net impulse"} across horizons`}
              </h4>
              <p>
                {root === "mean"
                  ? "Arithmetic mean of root-specific metrics"
                  : `Independent test root ${root}`}{" "}
                · lower is better
              </p>
            </div>
            {plotMode === "2d" && (
              <div
                className="segmented metric-toggle"
                aria-label="Chart metric"
              >
                <button
                  onClick={() => setMetric("nrmse")}
                  aria-pressed={metric === "nrmse"}
                >
                  NRMSE
                </button>
                <button
                  onClick={() => setMetric("rmse")}
                  aria-pressed={metric === "rmse"}
                >
                  RMSE
                </button>
              </div>
            )}
          </div>
          <div
            className="plot-view-switch"
            role="group"
            aria-label="Benchmark presentation"
          >
            <button
              aria-pressed={plotMode === "2d"}
              onClick={() => setPlotMode("2d")}
            >
              2D horizon plot
            </button>
            <button
              aria-pressed={plotMode === "3d"}
              onClick={() => setPlotMode("3d")}
            >
              3D comparison
            </button>
          </div>
          {plotMode === "3d" ? (
            <Benchmark3D
              root={root}
              model={model}
              horizon={horizon}
              outcome={outcome}
              onSelect={(entry) => {
                setModel(entry.model);
                setHorizon(entry.horizon);
                setOutcome(entry.outcome);
              }}
            />
          ) : (
            <>
              <div
                className="chart"
                role="group"
                aria-label={`${metric.toUpperCase()} comparison by horizon; exact values available in the table below`}
              >
                <span className="axis-unit">
                  {metric === "nrmse" ? "NRMSE · UNITLESS" : `RMSE · ${unit}`}
                </span>
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <LineChart
                    data={chart}
                    margin={{ top: 32, right: 24, left: 0, bottom: 10 }}
                    accessibilityLayer
                  >
                    <CartesianGrid
                      stroke={theme.grid}
                      strokeDasharray="3 6"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="horizon"
                      tick={{ fill: theme.muted, fontSize: 12 }}
                      tickLine={false}
                      axisLine={false}
                      dy={8}
                    />
                    <YAxis
                      width={43}
                      tick={{ fill: theme.muted, fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      domain={[0, "auto"]}
                      tickFormatter={(v) =>
                        Number(v).toFixed(metric === "nrmse" ? 1 : 2)
                      }
                    />
                    <Tooltip
                      contentStyle={plotTooltip}
                      labelFormatter={(label) => `${label} · ${outcome === "force" ? "Force" : "Net impulse"} · ${metric.toUpperCase()} · ${root === "mean" ? "Across-root mean" : `Root ${root}`}`}
                      labelStyle={{ color: theme.text }}
                      itemStyle={{ color: theme.text }}
                      formatter={(value, name) => [
                        `${Number(value).toFixed(6)}${metric === "rmse" ? ` ${unit}` : ""}`,
                        name,
                      ]}
                      cursor={{ stroke: theme.ochre, strokeDasharray: "3 6" }}
                    />
                    <ReferenceLine
                      x={`H${horizon}`}
                      stroke={theme.ochre}
                      strokeDasharray="4 6"
                    />
                    <Line
                      type="linear"
                      dataKey="comparison"
                      name={comparison.name}
                      stroke={comparison.color}
                      strokeWidth={1.5}
                      strokeDasharray="5 5"
                      dot={{ r: 4, fill: theme.surface, strokeWidth: 2 }}
                      isAnimationActive={false}
                    />
                    <Line
                      type="linear"
                      dataKey="selected"
                      name={selected.name}
                      stroke={selected.color}
                      strokeWidth={2.5}
                      dot={{ r: 5, fill: theme.surface, strokeWidth: 2 }}
                      activeDot={{ r: 7 }}
                      isAnimationActive={false}
                    />
                    <PlotSelection onSelect={(value) => {
                      const h = horizons.find((h) => `H${h}` === value);
                      if (h) setHorizon(h);
                    }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="chart-legend">
                <span>
                  <i style={{ background: selected.color }} />
                  {selected.name}
                </span>
                <span>
                  <i
                    className="dashed"
                    style={{ background: comparison.color }}
                  />
                  {comparison.name}
                </span>
                <span className="chart-hint">
                  Click or tap a horizon to select. Discrete cells, not a recovery trajectory
                </span>
              </div>
            </>
          )}
          <div className="comparison-note">
            <ArrowDownRight size={18} />
            <span>
              <strong>
                {delta > 0 ? "+" : ""}
                {format(delta)}
              </strong>{" "}
              six-cell NRMSE difference vs {comparison.name.toLowerCase()}
              <small>
                Negative favors the selected model. Horizon and outcome filters
                do not change the six-cell aggregate.
              </small>
            </span>
          </div>
        </div>
      </div>
      <div className="detail-grid">
        <div className="cell-panel">
          <div className="detail-title">
            <h3>The six-cell ledger</h3>
            <span className="panel-label">SELECT A ROW TO EXPLORE</span>
          </div>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Six-cell metric ledger"
          >
            <table className="cell-table">
              <caption className="sr-only">
                Selected model metrics by horizon and outcome for{" "}
                {root === "mean" ? "across-root mean" : `root ${root}`}.
                Comparison NRMSE shown for {comparison.name}.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Target cell</th>
                  <th scope="col">NRMSE ↓</th>
                  <th scope="col">RMSE ↓</th>
                  <th scope="col">vs. {comparison.short}</th>
                </tr>
              </thead>
              <tbody>
                {horizons.flatMap((h) =>
                  (["force", "impulse"] as const).map((o) => {
                    const value = cell(model, root, h, o);
                    const diff = value.nrmse - cell(compare, root, h, o).nrmse;
                    const active = horizon === h && outcome === o;
                    return (
                      <tr
                        key={`${h}/${o}`}
                        className={active ? "active-row" : ""}
                      >
                        <th scope="row">
                          <button
                            onClick={() => {
                              setHorizon(h);
                              setOutcome(o);
                            }}
                            aria-pressed={active}
                          >
                            <span className="row-dot" />H{h}
                            <span className="outcome-name">
                              {o === "force" ? "Force" : "Net impulse"}
                            </span>
                          </button>
                        </th>
                        <td>{format(value.nrmse)}</td>
                        <td>
                          {format(value.rmse)}{" "}
                          <small>{o === "force" ? "N/kg" : "m/s"}</small>
                        </td>
                        <td className={diff <= 0 ? "favorable" : ""}>
                          {diff > 0 ? "+" : ""}
                          {format(diff)}
                        </td>
                      </tr>
                    );
                  }),
                )}
              </tbody>
            </table>
          </div>
          <p className="table-note">
            Each root has 4,000 observations per cell. Across-root RMSE and
            NRMSE are averaged separately; no force/impulse RMSE aggregation.
          </p>
        </div>
        <div className="model-panel">
          <span className="panel-label">BEHIND THE RESULT</span>
          <h3>{selected.name}</h3>
          <p>{selected.description}</p>
          <div className="model-facts">
            <div>
              <span>Selected alpha</span>
              <strong>
                {selection ? selection.selected_alpha : "Not applicable"}
              </strong>
            </div>
            <div>
              <span>Training rows</span>
              <strong>{data.training.rows.toLocaleString("en-US")}</strong>
            </div>
            <div>
              <span>Cell root-to-root SD</span>
              <strong>{format(cellVariation.root_sample_sd_nrmse, 6)}</strong>
            </div>
          </div>
          {selection ? (
            <p className="method-note">
              α = 0.01 sits on the lower boundary of [0.01, 0.1, 1, 10, 100].
              Selection used development only; scaling and coefficients used
              training only.
            </p>
          ) : (
            <p className="method-note">
              No alpha selection for this baseline. Constants, where used, are
              fitted on training labels separately by outcome and horizon.
            </p>
          )}
          <a
            href={sourceLink("docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md")}
            className="quiet-link"
          >
            Inspect the model protocol <ArrowUpRight size={14} />
          </a>
        </div>
      </div>
      <details className="uncertainty" open>
        <summary>
          Root variability & reported uncertainty <ChevronDown size={16} />
        </summary>
        <div className="uncertainty-content">
          <IntervalPlot model={model} root={root} />
          <p>
            Aggregate six-cell NRMSE for <strong>{selected.name}</strong>.
            Across-root sample SD:{" "}
            <strong>{format(variability.root_sample_sd_nrmse, 6)}</strong>;
            range: {format(variability.root_min_nrmse)}–
            {format(variability.root_max_nrmse)}. Intervals use 5,000 paired
            resamples of 16 whole camps per root; they are descriptive and may
            be coarse. No pooled across-root confidence interval is reported.
          </p>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Root uncertainty table"
          >
            <table>
              <caption className="sr-only">
                Per-root aggregate scores and camp-bootstrap intervals
              </caption>
              <thead>
                <tr>
                  <th scope="col">Root</th>
                  <th scope="col">Six-cell NRMSE</th>
                  <th scope="col">95% camp-bootstrap interval</th>
                  <th scope="col">Δ vs zero · 95% interval</th>
                  <th scope="col">Valid resamples</th>
                </tr>
              </thead>
              <tbody>
                {data.roots
                  .filter((r) => root === "mean" || r.id === root)
                  .map((r) => {
                    const m = r.models[model];
                    return (
                      <tr key={r.id}>
                        <th scope="row">
                          {r.id}
                          <span className="root-seed">{r.seed}</span>
                        </th>
                        <td>{format(m.mean_six_cell_nrmse, 6)}</td>
                        <td>
                          [
                          {m.bootstrap.mean_six_cell_nrmse_95_percentile_interval
                            .map((v) => format(v))
                            .join(", ")}
                          ]
                        </td>
                        <td>
                          [
                          {m.bootstrap.paired_nrmse_delta_vs_zero_95_percentile_interval
                            .map((v) => format(v))
                            .join(", ")}
                          ]
                        </td>
                        <td>
                          {m.bootstrap.valid_replicates.toLocaleString("en-US")}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
          <p className="table-note">
            Intervals describe each model and its paired difference from zero;
            the comparison selector above does not rebase these intervals.
          </p>
        </div>
      </details>
      <div className="data-footnote">
        <span>
          NRMSE = cell RMSE / cell truth population SD (ddof = 0). Six-cell
          score = equal-weight mean.
        </span>
        <a
          href="/data/results.json"
          download="recovery-observatory-results.json"
        >
          <Download size={14} /> Download data + provenance
        </a>
      </div>
    </section>
  );
}
