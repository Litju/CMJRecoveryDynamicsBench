import contracts from "@/data/lineage.json";

export type Formulation = {
  id: string;
  label: string;
  question: string;
  status: "SUPERSEDED" | "RETIRED" | "PROPOSED" | "ACTIVE_CANDIDATE";
  parent: string | null;
  change: string;
  disposition: string;
  source: string;
};
export const lineage = contracts as Formulation[];

// Reconstruction evidence is independent of scientific disposition and new study results.
export const reconstruction = {
  chain: "PARTIALLY_REPRODUCIBLE",
  historical: (id: string) =>
    [
      "preliminary_post_exposure_recovery",
      "threshold_response_recovery",
    ].includes(id)
      ? "NOT_REPRODUCIBLE"
      : "HISTORICAL_EVIDENCE_ONLY",
  milestones: [
    {
      stage: "M1–M2",
      title: "Identify the question",
      text: "Lineage and reproduction contracts separate data, models, evaluation and historical results.",
    },
    {
      stage: "M3–M6",
      title: "Reconstruct the evidence",
      text: "Executable adapters are distinguished from result-only evidence. Different worlds and targets cannot form one leaderboard.",
    },
    {
      stage: "M8",
      title: "Run fresh public paths",
      text: "Eight synthetic generator paths and sixteen train/validation streams verified. No exact historical numeric model replay.",
    },
  ],
  source: "docs/M8_REPRODUCIBILITY_MATRIX.md",
};
export const experiments = [
  {
    title: "Retired rich-history study",
    text: "A new zero/ridge comparison on a 24-cell raw-progress diagnostic. A separate experiment, never ranked with active NRMSE.",
    source: "docs/M8_REFERENCE_MODEL_STUDY.md",
  },
  {
    title: "Active fixed-mode study",
    text: "A new four-model comparison, with three independent same-generator roots and six outcome/horizon cells.",
    source: "docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md",
  },
];
export const acts = [
  { id: "question", label: "Setting & signal" },
  { id: "world", label: "An episode" },
  { id: "lineage", label: "Research history" },
  { id: "experiment", label: "The experiment" },
  { id: "remaining", label: "Limits & lab" },
] as const;
