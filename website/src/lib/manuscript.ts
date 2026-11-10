// Typed access to the hash-pinned manuscript fixture. Selectors only re-read or
// difference recorded values; nothing here fits, scores or resamples a model.
import fixture from "@/data/manuscript.json";
import { plotTheme } from "./plot-theme.mjs";

export const manuscript = fixture;
export type FigureMeta = (typeof fixture.figures)[number];
export type SixCell = (typeof fixture.data.sixCell.cells)[number];
export type ModelKey = "zero_innovation" | "training_constant" | "ridge_full" | "structured_full";
export type RootKey = "A" | "B" | "C";

export const REPOSITORY = "https://github.com/Litju/CMJRecoveryDynamicsBench";
/** Main commit that integrated the V3 package (identical package digests). */
export const PACKAGE_COMMIT = fixture.paper.packageCommit;
export const RELEASE_COMMIT = fixture.paper.releaseCommit;
export const RELEASE_URL = `${REPOSITORY}/releases/tag/v${fixture.paper.releaseVersion}`;
export const CITATION_URL = `${REPOSITORY}/blob/v${fixture.paper.releaseVersion}/CITATION.cff`;
export const sourceAt = (path: string, commit = PACKAGE_COMMIT) =>
  `${REPOSITORY}/blob/${commit}/${path}`;
export const treeAt = (path: string, commit = PACKAGE_COMMIT) =>
  `${REPOSITORY}/tree/${commit}/${path}`;

export const paperFile = (id: "illustrated" | "review" | "supplement") =>
  fixture.paper.files.find((f) => f.id === id)!;
export const PAPER = paperFile("illustrated");
export const paperPage = (page: number) => `${PAPER.href}#page=${page}`;
export const section = (id: string) => fixture.paper.sections.find((s) => s.id === id)!;
export const figure = (n: number) => fixture.figures[n - 1];

export const MODELS: {
  key: ModelKey;
  label: string;
  short: string;
  color: string;
  description: string;
}[] = [
  {
    key: "zero_innovation",
    label: "Zero innovation",
    short: "Zero",
    color: plotTheme.zero,
    description: "Predicts no change from the pre-index baseline.",
  },
  {
    key: "training_constant",
    label: "Training mean",
    short: "Mean",
    color: plotTheme.ochre,
    description: "Training-fitted mean for each outcome and horizon.",
  },
  {
    key: "ridge_full",
    label: "Ridge regression",
    short: "Ridge",
    color: plotTheme.ridge,
    description: "Cellwise ridge on the complete 82-field public predictor schema.",
  },
  {
    key: "structured_full",
    label: "Structured comparator",
    short: "Structured",
    color: plotTheme.structured,
    description: "Fixed 24 h / 84 h exponential bases on public exposure primitives.",
  },
];
export const modelMeta = (key: string) => MODELS.find((m) => m.key === key)!;
export const ROOTS: RootKey[] = ["A", "B", "C"];
export const ROOT_SHAPE: Record<RootKey, "circle" | "square" | "triangle"> = {
  A: "circle",
  B: "square",
  C: "triangle",
};

export const OUTCOMES = {
  force: {
    label: "Mean concentric-force innovation",
    short: "Mean concentric force",
    unit: "N/kg",
    definition:
      "Criterion-assessment minus baseline-assessment gross time-mean concentric force per unit body mass; each assessment averages three simulated trials. Not peak force and not net impulse. Registered key: relative_peak_mean_force_innovation.",
  },
  impulse: {
    label: "Net-impulse innovation",
    short: "Net impulse",
    unit: "m/s",
    definition:
      "Criterion-assessment minus baseline-assessment gravity-adjusted concentric net impulse per unit mass. Registered key: net_impulse_innovation.",
  },
} as const;
export type OutcomeKey = keyof typeof OUTCOMES;

export const cellOf = (horizon: string, outcome: OutcomeKey) =>
  fixture.data.sixCell.cells.find((c) => c.horizon === horizon && c.outcome === outcome)!;

/** Recorded NRMSE for a model in a cell: a single root, or the stored across-root mean. */
export function cellValue(cell: SixCell, model: ModelKey, root: RootKey | "mean") {
  const v = cell.models[model];
  return root === "mean" ? v.mean : v.roots[ROOTS.indexOf(root)].nrmse;
}
/** Stored equal-weight six-cell score for one root, or the across-root mean. */
export function sixCellScore(model: ModelKey, root: RootKey | "mean") {
  const a = fixture.data.sixCell.aggregates[model];
  return root === "mean" ? a.mean : a.roots[ROOTS.indexOf(root)];
}

export const fmt = (v: number, digits = 4) => v.toFixed(digits);
export const fmtInt = (v: number) => v.toLocaleString("en-US");
export const signed = (v: number, digits = 4) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(digits)}`;

export const STATUS_LABEL: Record<string, string> = {
  SUPERSEDED: "Superseded",
  RETIRED: "Retired",
  PROPOSED: "Proposed",
  ACTIVE_CANDIDATE: "Active candidate",
};
export const STATUS_COLOR: Record<string, string> = {
  SUPERSEDED: "#586773",
  RETIRED: plotTheme.structured,
  PROPOSED: plotTheme.ochre,
  ACTIVE_CANDIDATE: "#1f7a6d",
};
