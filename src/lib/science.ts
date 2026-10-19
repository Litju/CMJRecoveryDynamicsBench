import fixture from "@/data/results.json";
export const data = fixture;
export const models = [
  {
    id: "zero_innovation",
    name: "Zero innovation",
    short: "Zero",
    color: "#a6b1b8",
    description:
      "Persistence on the innovation scale. Predicts zero change from the pre-index baseline.",
  },
  {
    id: "training_constant",
    name: "Training constant",
    short: "Constant",
    color: "#e8be6c",
    description:
      "A training-fitted mean for each outcome and horizon. No validation means enter the predictions.",
  },
  {
    id: "ridge_full",
    name: "Full ridge",
    short: "Ridge",
    color: "#92bbf3",
    description:
      "Cellwise ridge using the complete 82-field public predictor schema, encoded into 84 numeric columns.",
  },
  {
    id: "structured_full",
    name: "Fixed-mode structured",
    short: "Structured",
    color: "#f19a7c",
    description:
      "Training-fitted coefficients on public exposure primitives and fixed 24 h / 84 h exponential bases. No oracle states.",
  },
] as const;
export type ModelId = (typeof models)[number]["id"];
export type RootId = "mean" | "A" | "B" | "C";
export type Outcome = "force" | "impulse";
export const horizons = [24, 48, 72] as const;
export const sourceLink = (path: string) =>
  `${data.provenance.repository}/blob/${data.provenance.commit}/${path}`;
export function cellKey(horizon: number, outcome: Outcome) {
  return `H${horizon}/${outcome === "force" ? "relative_peak_mean_force_innovation" : "net_impulse_innovation"}`;
}
export function cell(
  model: ModelId,
  root: RootId,
  horizon: number,
  outcome: Outcome,
) {
  const key = cellKey(horizon, outcome);
  const cells = data.roots
    .filter((r) => root === "mean" || r.id === root)
    .map((r) => r.models[model].cells.find((c) => c.cell === key)!);
  const mean = (field: "nrmse" | "rmse" | "truth_population_sd") =>
    cells.reduce((s, c) => s + c[field], 0) / cells.length;
  return {
    nrmse: mean("nrmse"),
    rmse: mean("rmse"),
    truthSd: mean("truth_population_sd"),
    rows: cells.reduce((s, c) => s + c.rows, 0),
  };
}
export function aggregate(model: ModelId, root: RootId) {
  return root === "mean"
    ? data.models[model].acrossRoots.root_mean_nrmse
    : data.roots.find((r) => r.id === root)!.models[model].mean_six_cell_nrmse;
}
export const format = (n: number, digits = 4) => n.toFixed(digits);
