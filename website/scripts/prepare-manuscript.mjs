// Compile the manuscript-linked figure fixture from the hash-pinned V3 package.
// Reads only committed public files; performs no fitting, scoring, resampling or inference.
import { createHash } from "node:crypto";
import {
  copyFileSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../", import.meta.url));
const manifest = JSON.parse(
  readFileSync(
    new URL("../source/manuscript-manifest.json", import.meta.url),
    "utf8",
  ),
);
const pkg = manifest.package; // docs/manuscript/v3
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");

function artifactDigests() {
  const bytes = readFileSync(root + manifest.artifactManifest.path);
  assert.equal(
    sha256(bytes),
    manifest.artifactManifest.sha256,
    "V3 ARTIFACT_SHA256SUMS drift",
  );
  return Object.fromEntries(
    bytes
      .toString("utf8")
      .trim()
      .split("\n")
      .map((line) => {
        const [digest, path] = line.split("  ");
        return [path, digest];
      }),
  );
}

const digests = artifactDigests();
function read(relative) {
  assert.ok(
    manifest.files.includes(relative),
    `Unpinned manuscript input: ${relative}`,
  );
  const bytes = readFileSync(`${root}${pkg}/${relative}`);
  assert.equal(sha256(bytes), digests[relative], `Manuscript drift: ${relative}`);
  return bytes;
}
const text = (relative) => read(relative).toString("utf8");
const json = (relative) => JSON.parse(text(relative));
function csv(relative) {
  const [header, ...lines] = text(relative).trim().split(/\r?\n/);
  const keys = header.split(",");
  return lines.map((line) => {
    const cells = line.split(",");
    assert.equal(cells.length, keys.length, `${relative}: ragged row`);
    return Object.fromEntries(keys.map((k, i) => [k, cells[i]]));
  });
}

// ---- TeX caption extraction ------------------------------------------------
function braceGroup(source, start) {
  assert.equal(source[start], "{");
  let depth = 0;
  for (let i = start; i < source.length; i++) {
    if (source[i] === "\\") {
      i++;
      continue;
    }
    if (source[i] === "{") depth++;
    else if (source[i] === "}" && --depth === 0)
      return [source.slice(start + 1, i), i + 1];
  }
  throw new Error("Unbalanced TeX group");
}
const UNITS = {
  "\\kilogram": "kg",
  "\\newton": "N",
  "\\second": "s",
  "\\Nkg": "N/kg",
  "\\mps": "m/s",
  "\\meter\\per\\second\\squared": "m/s²",
};
export function texToText(tex) {
  let s = tex
    .replace(/\\SI\{([^}]*)\}\{([^}]*)\}/g, (_, v, u) => {
      assert.ok(u in UNITS, `Unknown unit ${u}`);
      return `${v} ${UNITS[u]}`;
    })
    .replace(/\\si\{([^}]*)\}/g, (_, u) => {
      assert.ok(u in UNITS, `Unknown unit ${u}`);
      return UNITS[u];
    })
    .replace(/\\ident\{([^}]*)\}/g, "$1")
    .replace(/\\\(|\\\)/g, "")
    .replace(/10\^\{-5\}/g, "10⁻⁵")
    .replace(/\s*\\leq\s*/g, " ≤ ")
    .replace(/\\pi\s*/g, "π")
    .replace(/\\sin/g, " sin")
    .replace(/\\,/g, " ")
    .replace(/\\%/g, "%")
    .replace(/---/g, "—")
    .replace(/--/g, "–")
    .replace(/~/g, " ")
    .replace(/\\_/g, "_")
    .replace(/\s+/g, " ")
    .trim();
  assert.ok(!/[\\{}]/.test(s), `Unconverted TeX in caption: ${s}`);
  return s;
}
function captions(tex) {
  const out = {};
  let at = 0;
  while ((at = tex.indexOf("\\EvidenceFigure{", at)) >= 0) {
    const [file, a] = braceGroup(tex, at + "\\EvidenceFigure".length);
    const [caption, b] = braceGroup(tex, a);
    const [label] = braceGroup(tex, b);
    const n = Number(/Fig(\d+)\.pdf$/.exec(file)[1]);
    out[n] = { label, caption: texToText(caption) };
    at = b;
  }
  return out;
}
function abstract(tex) {
  const m = /\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}/.exec(tex);
  return texToText(m[1]);
}
function researchQuestions(tex) {
  const out = [...tex.matchAll(/\\textbf\{(RQ\d) — ([^}]*)\.\}\s*(.+)$/gm)].map((m) => ({
    id: m[1],
    title: m[2],
    question: texToText(m[3]),
  }));
  assert.deepEqual(out.map((q) => q.id), ["RQ1", "RQ2", "RQ3"]);
  return out;
}
function pageInventory(markdown) {
  const figures = {};
  let page = null;
  for (const line of markdown.split("\n")) {
    const p = /^- \*\*Page (\d+):\*\*/.exec(line);
    if (p) page = Number(p[1]);
    const f = /^\s+- \*\*Fig\. (\d+):\*\* (.+)$/.exec(line);
    if (f) figures[Number(f[1])] = { page, question: f[2].trim() };
  }
  return figures;
}

// ---- Figure data ------------------------------------------------------------
const MODEL_ORDER = [
  "zero_innovation",
  "training_constant",
  "ridge_full",
  "structured_full",
];
const FORCE = "relative_peak_mean_force_innovation";
const IMPULSE = "net_impulse_innovation";
const HORIZONS = ["H24", "H48", "H72"];
const CELLS = [FORCE, IMPULSE].flatMap((o) => HORIZONS.map((h) => `${h}/${o}`));
const ROOTS = ["A", "B", "C"];
const ROOT_IDS = ["test_root_1", "test_root_2", "test_root_3"]; // receipt order A, B, C
const rootLetter = (id) => {
  const i = ROOT_IDS.indexOf(id);
  assert.ok(i >= 0, `Unknown evaluation root ${id}`);
  return ROOTS[i];
};

// Display names copied from the manuscript figure generator (checked in tests).
const WORLD_NAME = {
  event_time_adaptation_recovery: "event-time adaptation",
  fitness_fatigue_impulse_response: "fitness–fatigue response",
  biexponential_episode_response: "biexponential episode response",
  correlated_exposure_response: "correlated exposure response",
  threshold_response: "threshold response",
  fixed_mode_discrepancy_response: "fixed-mode discrepancy",
};
const OBSERVATION_NAME = {
  camp_history: "camp-history observations",
  rich_monitoring: "rich-monitoring observations",
  episode_summary: "paired-trial summaries",
  phase_consistent_force_impulse: "phase-consistent force trace",
};

function genealogy(lineage, methods) {
  return lineage.map((item) => {
    const m = methods[item.id];
    const native = m.task.includes("D7");
    return {
      id: item.id,
      label: item.label,
      status: item.status,
      parent: item.parent,
      question: item.question,
      change: item.change,
      disposition: item.disposition,
      source: item.source,
      lane: native ? "camp-state" : "episode-response",
      horizons: native ? ["H72", "D7"] : HORIZONS,
      world: WORLD_NAME[m.world],
      observation: OBSERVATION_NAME[m.observation],
      task: m.task,
      limitation: m.limitation,
      modelEvidence: m.modelEvidence,
    };
  });
}

function design(study) {
  const split = (d) => ({
    camps: d.camps,
    episodes: d.episodes,
    rows: d.rows,
    split: d.split,
    seedKind: d.seed_kind,
    participants: d.grouping_keys.participant_key.unique_values,
    queries: d.grouping_keys.query_key.unique_values,
    labels: Object.keys(d.labels).sort(),
  });
  const fc = study.feature_contract;
  return {
    training: split(study.data.training),
    development: split(study.data.development),
    roots: study.independent_test_roots.map((r) => ({
      id: rootLetter(r.root_id),
      sourceId: r.root_id,
      ...split(r.data),
    })),
    horizons: HORIZONS,
    contract: {
      sourceFields: fc.source_fields,
      encodedFields: fc.encoded_fields,
      groupingKeysAsPredictors: fc.grouping_keys_as_predictors,
      targetLabelsAsPredictors: fc.target_labels_as_predictors,
      targetTimeFields: fc.target_time_or_post_query_fields,
      horizonEncoding: fc.horizon_encoding,
      preprocessing: fc.numeric_preprocessing,
    },
    campUnit: study.protocol.camp_unit_identity,
  };
}

// Component inclusion follows the Fig. 3 caption and the recorded architecture strings.
const COMPONENTS = [
  { id: "backbone", label: "Raw feedforward backbone (39 features)", from: 0 },
  { id: "pointwise", label: "Pointwise history encoder (4 × 4)", from: 3, until: 3 },
  { id: "gru", label: "32-unit GRU history encoder", from: 4 },
  { id: "pooling", label: "Mean and latest-value pooling", from: 3 },
  { id: "horizon", label: "Two-entry, 8-dimensional horizon embedding", from: 5 },
  { id: "basis2", label: "Schedule-basis projection (first two of five values)", from: 6, until: 6 },
  { id: "basis5", label: "Schedule-basis projection (all five values)", from: 7 },
  { id: "basisHead", label: "Bias-free 5 → 2 linear basis head", from: 8 },
];
const HIDDEN = { M0: "39 → 32", M1: "39 → 64", M2: "39 → 64 → 64" };
const CONCAT = { M3: 128, M4: 128, M5: 136, M6: 152, M7: 152, M8: 152 };

function architectures(rows) {
  const families = [...new Set(rows.map((r) => r.model))];
  return families.map((model, i) => {
    const repeats = rows.filter((r) => r.model === model);
    assert.equal(repeats.length, 2);
    assert.equal(repeats[0].parameters, repeats[1].parameters);
    assert.equal(repeats[0].architecture, repeats[1].architecture);
    return {
      id: model,
      parameters: Number(repeats[0].parameters),
      repeats: repeats.map((r) => r.repeat),
      inputs: repeats[0].inputs,
      architecture: repeats[0].architecture,
      output: repeats[0].output,
      cpuSource: repeats[0].cpu_source,
      savedCuda: repeats[0].saved_cuda,
      hidden: HIDDEN[model] ?? null,
      concatenatedWidth: CONCAT[model] ?? null,
      components: COMPONENTS.filter(
        (c) => i >= c.from && (c.until === undefined || i <= c.until),
      ).map((c) => c.id),
    };
  });
}

function routes(rows) {
  return rows.map((r) => ({
    route: r.route,
    model: r.route.split("-")[0],
    repeat: r.route.split("-")[1],
    cpuSource: r.cpu_source,
    savedCuda: r.saved_cuda === "Pass" ? "pass" : "fail",
    atol: Number(r.atol),
    rtol: Number(r.rtol),
    maxAbsoluteError: Number(r.max_absolute_error),
    failingElements:
      r.failing_elements === "not tabulated" ? null : Number(r.failing_elements),
    selectionIdentity: r.selection_identity,
    rights: r.rights,
    inferenceRerun: r.inference_rerun === "True",
  }));
}

function sixCell(study, csvRows) {
  assert.deepEqual(study.independent_test_roots.map((r) => r.root_id), ROOT_IDS);
  const byRoot = Object.fromEntries(
    study.independent_test_roots.map((r) => [rootLetter(r.root_id), r]),
  );
  const cells = CELLS.map((cell) => {
    const [horizon, outcome] = cell.split("/");
    return {
      cell,
      horizon,
      outcome: outcome === FORCE ? "force" : "impulse",
      unit: outcome === FORCE ? "N/kg" : "m/s",
      models: Object.fromEntries(
        MODEL_ORDER.map((model) => {
          const v = study.across_root_variability[model].cell_nrmse_across_roots[cell];
          const row = csvRows.find((r) => r.model === model && r.cell === cell);
          const roots = ROOTS.map((id) => {
            const c = byRoot[id].models[model].cells.find((x) => x.cell === cell);
            return { root: id, nrmse: c.nrmse, rmse: c.rmse, truthSd: c.truth_population_sd, rows: c.rows };
          });
          // The public CSV and the receipt must agree exactly.
          assert.deepEqual(
            [row.root_a, row.root_b, row.root_c].map(Number),
            roots.map((r) => r.nrmse),
          );
          assert.equal(Number(row.mean), v.root_mean_nrmse);
          assert.equal(Number(row.sample_sd), v.root_sample_sd_nrmse);
          return [model, { roots, mean: v.root_mean_nrmse, sampleSd: v.root_sample_sd_nrmse }];
        }),
      ),
    };
  });
  const aggregates = Object.fromEntries(
    MODEL_ORDER.map((m) => {
      const v = study.across_root_variability[m];
      return [m, { roots: v.root_values, mean: v.root_mean_nrmse, sampleSd: v.root_sample_sd_nrmse }];
    }),
  );
  return { models: MODEL_ORDER, roots: ROOTS, cells, aggregates };
}

function bootstrap(study, csvRows) {
  const proto = study.protocol.bootstrap;
  const rows = study.independent_test_roots.flatMap((r) =>
    ["ridge_full", "structured_full"].map((model) => {
      const b = r.paired_camp_bootstrap.models[model];
      const m = r.models[model];
      const c = csvRows.find((x) => x.root === rootLetter(r.root_id) && x.model === model);
      const nrmseInterval = b.mean_six_cell_nrmse_95_percentile_interval;
      const deltaInterval = b.paired_nrmse_delta_vs_zero_95_percentile_interval;
      assert.deepEqual(
        [c.nrmse_lower, c.nrmse_upper, c.paired_delta_vs_zero_lower, c.paired_delta_vs_zero_upper].map(Number),
        [...nrmseInterval, ...deltaInterval],
      );
      return {
        root: rootLetter(r.root_id),
        model,
        estimate: m.mean_six_cell_nrmse,
        interval: nrmseInterval,
        deltaVsZero: m.paired_nrmse_delta_vs_zero,
        deltaInterval,
        replicates: b.valid_replicates,
      };
    }),
  );
  return {
    rows,
    replicates: proto.replicates,
    seed: proto.seed,
    generator: proto.generator,
    interval: proto.interval,
    unit: proto.unit,
    campsPerRoot: study.independent_test_roots[0].data.camps,
    episodesPerCamp:
      study.independent_test_roots[0].data.episodes /
      study.independent_test_roots[0].data.camps,
  };
}

function ablations(study) {
  const v = study.across_root_variability;
  const pick = (key, label, family) => ({
    key,
    label,
    family,
    roots: v[key].root_values,
    mean: v[key].root_mean_nrmse,
  });
  const nested = study.protocol.ablation_variants;
  assert.deepEqual(nested, [
    "ridge_no_prior_history",
    "ridge_no_current_exposure",
    "ridge_no_participant_context",
    "structured_no_prior_history",
  ]);
  const sample = study.protocol.sample_efficiency;
  return {
    variants: [
      pick("ridge_full", "Full ridge", "ridge"),
      pick("ridge_no_prior_history", "Ridge − prior history", "ridge"),
      pick("ridge_no_current_exposure", "Ridge − current exposure", "ridge"),
      pick("ridge_no_participant_context", "Ridge − participant context", "ridge"),
      pick("structured_full", "Structured comparator (full)", "structured"),
      pick("structured_no_prior_history", "Structured − prior history", "structured"),
    ],
    nested: {
      camps: sample.camp_counts,
      hyperparameters: sample.hyperparameters,
      subsetOrder: sample.nested_subset_order,
      seed: sample.seed,
      series: ["ridge", "structured"].map((family) => ({
        family,
        points: sample.camp_counts.map((n) => ({
          camps: n,
          roots: v[`${family}_n${n}`].root_values,
          mean: v[`${family}_n${n}`].root_mean_nrmse,
        })),
      })),
    },
  };
}

function richHistory(reproduction) {
  return reproduction.runs
    .filter(
      (r) =>
        r.kind === "public_split_generation" &&
        r.run_spec.benchmark === "rich_history_camp_recovery",
    )
    .map((r) => ({
      split: r.run_spec.split,
      publicRows: r.dataset_output.row_count,
      historicalRows: r.dataset_output.m2_historical_row_count,
      difference: r.dataset_output.row_count - r.dataset_output.m2_historical_row_count,
    }));
}

// Evidence classes and claim rows reproduced from the manuscript Fig. 10 generator.
const EVIDENCE_CLASSES = [
  { id: "public-source", label: "Public source", description: "Inspectable in public source code and contracts." },
  { id: "public-regenerable", label: "Public regenerable", description: "Recomputable from public receipts without private artifacts." },
  { id: "private-summary", label: "Private summary", description: "Privately qualified; only a public summary is available." },
  { id: "not-established", label: "Not established", description: "Not supported by the preserved evidence." },
];
const EVIDENCE_ROWS = [
  ["Eight formulations; 5 parent links", "public-source"],
  ["Architecture topology, M0–M8", "public-source"],
  ["Parameter counts, 18 routes", "private-summary"],
  ["Source-CPU equality, 18/18 routes", "private-summary"],
  ["Archived-GPU comparison, 8 pass / 10 fail", "private-summary"],
  ["Six-cell benchmark, bootstrap, ablations", "public-regenerable"],
  ["Rich-history row counts (−48, +4)", "public-regenerable"],
  ["Historical split identity; GPU-difference cause", "not-established"],
  ["Rerun of private checkpoints from public files", "not-established"],
  ["Athlete validity, transport, clinical use", "not-established"],
];

const SECTIONS = [
  { id: "abstract", title: "Abstract", page: 1 },
  { id: "introduction", title: "Introduction and research questions", page: 1 },
  { id: "related-work", title: "Related work", page: 2 },
  { id: "methods", title: "Materials and methods", page: 2 },
  { id: "formulations", title: "Historical scientific formulations", page: 2 },
  { id: "neural-reconstruction", title: "Original neural model reconstruction", page: 2 },
  { id: "numerical-qualification", title: "Numerical qualification", page: 4 },
  { id: "native-measurement", title: "Native CMJ measurement and assessment construction", page: 4 },
  { id: "synthetic-design", title: "Public synthetic benchmark design (ADEMP)", page: 4 },
  { id: "statistics", title: "Statistical summaries", page: 6 },
  { id: "results", title: "Results: RQ1–RQ3", page: 7 },
  { id: "uncertainty", title: "Recorded uncertainty, ablations and sample efficiency", page: 8 },
  { id: "reproduction-limits", title: "Historical reproduction limits", page: 9 },
  { id: "discussion", title: "Discussion", page: 9 },
  { id: "limitations", title: "Limitations and threats to validity", page: 10 },
  { id: "availability", title: "Reproducibility and availability", page: 11 },
  { id: "conclusions", title: "Conclusions", page: 11 },
  { id: "data-availability", title: "Data availability statement", page: 12 },
];
const FIGURE_SECTION = {
  1: "formulations",
  2: "synthetic-design",
  3: "neural-reconstruction",
  4: "numerical-qualification",
  5: "native-measurement",
  6: "results",
  7: "results",
  8: "uncertainty",
  9: "uncertainty",
  10: "reproduction-limits",
};
const FIGURE_ROUTE = {
  1: "/methods/",
  2: "/methods/",
  3: "/models/",
  4: "/models/",
  5: "/methods/",
  6: "/results/",
  7: "/results/",
  8: "/results/",
  9: "/results/",
  10: "/evidence/",
};

export const PAPER_FILES = [
  { id: "illustrated", label: "Full illustrated research manuscript", file: "full_illustrated_research_manuscript.pdf", pages: 12 },
  { id: "review", label: "Academic review edition", file: "academic_review_manuscript.pdf", pages: null },
  { id: "supplement", label: "Technical supplement", file: "technical_supplement.pdf", pages: null },
];

export function compile() {
  const tex = text("manuscript.tex");
  const caps = captions(tex);
  const inventory = pageInventory(text("reports/full_illustrated_page_figure_inventory.md"));
  const study = json("evidence/release_sources/S01_M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json");
  const reproduction = json("evidence/release_sources/S04_M8_PUBLIC_REPRODUCTION_RECEIPTS.json");
  const lineage = json("evidence/release_sources/S17_lineage.json");
  const methods = json("evidence/release_sources/S18_formulation-methods.json");
  const sixRows = csv("evidence/v2_audit/six_cell_results.csv");
  const uncertaintyRows = csv("evidence/v2_audit/recorded_uncertainty.csv");
  const architectureRows = csv("evidence/v2_audit/architecture_qualification.csv");
  const routeRows = csv("evidence/v2_audit/model_identity_sanitized.csv");
  const generator = text("figure_source/generate_figures.py");
  for (const label of [...Object.values(WORLD_NAME), ...Object.values(OBSERVATION_NAME), ...EVIDENCE_ROWS.map((r) => r[0])])
    assert.ok(generator.includes(label), `Generator label drift: ${label}`);
  const constants = /^MASS, GRAV, AMP, T_PEAK, DUR = (.+)$/m.exec(generator)[1].split(",").map(Number);
  const [mass, gravity, amplitude, peakTime, duration] = constants;

  const receipts = {};
  for (let n = 2; n <= 10; n++) {
    const path = `reproducibility/figure_receipts/Fig${n}.json`;
    const r = json(path);
    assert.equal(r.numerical_test.passed, true, `Fig${n} receipt check failed`);
    assert.equal(r.numerical_test.checks.new_model_execution, false);
    assert.equal(r.numerical_test.checks.new_bootstrap, false);
    receipts[n] = {
      path: `${pkg}/${path}`,
      sha256: digests[path],
      population: r.population,
      metric: r.metric,
      units: r.units,
      grouping: r.grouping,
      sampleSizes: r.sample_sizes,
      uncertainty: r.uncertainty,
      sourceIds: r.source_ids,
      numericalTest: r.numerical_test.id,
      figurePdfSha256: r.figure_pdf_sha256,
      releaseSources: Object.entries(r.input_digests.release_sources).map(([id, s]) => ({ id, path: s.path, sha256: s.sha256 })),
      localData: Object.entries(r.input_digests.local_data).map(([path, digest]) => ({ path: `${pkg}/${path}`, sha256: digest })),
    };
    for (const s of receipts[n].releaseSources) {
      const local = Object.keys(digests).find((p) => p.startsWith(`evidence/release_sources/${s.id}_`));
      assert.ok(local, `No packaged copy for ${s.id}`);
      assert.equal(digests[local], s.sha256, `Packaged ${s.id} differs from the release source digest`);
      s.packaged = `${pkg}/${local}`;
    }
  }

  const figures = Array.from({ length: 10 }, (_, i) => {
    const n = i + 1;
    return {
      number: n,
      id: `fig-${n}`,
      label: caps[n].label,
      question: inventory[n].question,
      page: inventory[n].page,
      section: FIGURE_SECTION[n],
      route: FIGURE_ROUTE[n],
      caption: caps[n].caption,
      files: ["pdf", "svg", "png"].map((ext) => ({
        ext,
        path: `${pkg}/figures/Fig${n}.${ext}`,
        sha256: digests[`figures/Fig${n}.${ext}`],
      })),
      receipt: receipts[n] ?? null,
    };
  });

  return {
    schema: "recovery-observatory/manuscript-figures/1",
    paper: {
      title: /\\title\{([^}]*)\}/.exec(tex)?.[1] ?? null,
      status: "Unsubmitted research draft: not peer reviewed, not submitted to a journal or preprint server, no DOI.",
      abstract: abstract(tex),
      researchQuestions: researchQuestions(tex),
      dataAvailability: texToText(/\\textbf\{Data availability\.\}\s*(.+)$/m.exec(tex)[1]),
      package: pkg,
      packageCommit: manifest.packageCommit,
      artifactManifestSha256: manifest.artifactManifest.sha256,
      releaseVersion: manifest.release.version,
      releaseCommit: manifest.release.commit,
      files: PAPER_FILES.map((f) => ({
        ...f,
        path: `${pkg}/${f.file}`,
        href: `/paper/${f.file}`,
        sha256: digests[f.file],
        bytes: read(f.file).length,
      })),
      sections: SECTIONS,
    },
    figures,
    data: {
      genealogy: genealogy(lineage, methods),
      design: design(study),
      architectures: { components: COMPONENTS.map(({ id, label }) => ({ id, label })), families: architectures(architectureRows) },
      routes: routes(routeRows),
      mechanics: {
        mass,
        gravity,
        amplitude,
        peakTime,
        duration,
        samples: 5501,
        windows: [
          { id: "baseline", label: "Baseline search", start: -240, end: -24, contract: "native" },
          { id: "H72", label: "H72 target", start: 66, end: 78, nominal: 72, contract: "native" },
          { id: "D7", label: "D7 target", start: 156, end: 180, nominal: 168, contract: "native" },
        ],
        syntheticQueries: [24, 48, 72],
        assessment: "Assessment = mean of 3 valid trials; baseline = mean of the 2 latest valid assessments.",
      },
      sixCell: sixCell(study, sixRows),
      bootstrap: bootstrap(study, uncertaintyRows),
      ablations: ablations(study),
      richHistory: richHistory(reproduction),
      evidence: {
        classes: EVIDENCE_CLASSES,
        rows: EVIDENCE_ROWS.map(([claim, cls]) => ({ claim, class: cls })),
      },
    },
    inputs: manifest.files.map((path) => ({ path: `${pkg}/${path}`, sha256: digests[path] })),
  };
}

const outputs = [
  new URL("../src/data/manuscript.json", import.meta.url),
  new URL("../public/data/manuscript.json", import.meta.url),
];
export const serialize = (data) => `${JSON.stringify(data, null, 2)}\n`;

function publishPapers() {
  const dir = new URL("../public/paper/", import.meta.url);
  mkdirSync(dir, { recursive: true });
  for (const f of PAPER_FILES) {
    read(f.file); // verifies the digest before copying
    copyFileSync(`${root}${pkg}/${f.file}`, new URL(f.file, dir));
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const expected = serialize(compile());
  if (process.argv.includes("--check")) {
    for (const out of outputs)
      assert.equal(
        readFileSync(out, "utf8"),
        expected,
        `${fileURLToPath(out)} is stale; run npm run data:manuscript`,
      );
  } else {
    for (const out of outputs) writeFileSync(out, expected);
  }
  publishPapers();
  console.log(
    `Manuscript provenance verified (${manifest.files.length} inputs, manifest ${manifest.artifactManifest.sha256.slice(0, 12)}). Fixture SHA-256 ${sha256(expected)}.`,
  );
}
