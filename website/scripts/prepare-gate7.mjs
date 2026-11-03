import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url));
export const commit = "08c31e0876edea14e0eb6132d08c1b2705c1cfc9";
const paths = [
  "docs/RES-546_INFERENCE_VERIFICATION.md",
  "docs/RES-546_CPU_SOURCE_INTEGRATION_POLICY.md",
  "docs/RES-546_GATE7_M8_RECOVERY.md",
  "docs/GATE7_NATIVE_MEASUREMENT_V1.md",
  "src/cmj_recovery_dynamics/model_reproduction/checkpoint_inference.py",
  "src/cmj_recovery_dynamics/model_reproduction/checkpoint_m7.py",
  "src/cmj_recovery_dynamics/model_reproduction/checkpoint_m8_inference.py",
];
export function compile() {
  const manifest = JSON.parse(
    readFileSync(
      new URL("../source/gate7-manifest.json", import.meta.url),
      "utf8",
    ),
  );
  assert.equal(manifest.commit, commit);
  const sources = paths.map((path) => {
    const bytes = readFileSync(root + path);
    const sha256 = createHash("sha256").update(bytes).digest("hex");
    assert.equal(
      sha256,
      manifest.sources.find((s) => s.path === path)?.sha256,
      `Gate7 source drift: ${path}`,
    );
    return { path, sha256 };
  });
  const architecture = [
    "39 → 32 → 2; exact GELU",
    "39 → 64 → 2; exact GELU",
    "39 → 64 → 64 → 2; exact GELU",
    "Raw backbone + pointwise history encoder; mean/latest pooling → 128 → 2",
    "Raw backbone + 4 → 32 GRU; mean/latest pooling → 128 → 2",
    "M4 + 2 × 8 horizon embedding → 136 → 2",
    "M5 + first two basis values → 16 → 152 → 2",
    "M5 + all five basis values → 16 → 152 → 2",
    "M7 + bias-free 5 → 2 linear basis head",
  ];
  return {
    commit,
    experiment: "engineering reconstruction",
    sources,
    models: architecture.map((architecture, i) => ({
      id: `M${i}`,
      architecture,
      repeats: ["r0", "r1"],
      cpu: "Exact source parity",
      cuda: i < 4 ? "Within recorded tolerance" : "Outside recorded tolerance",
      inputs:
        i < 3
          ? "39 raw features"
          : i < 5
            ? "39 raw + 4 × 4 history"
            : i === 5
              ? "39 raw + 4 × 4 history + horizon"
              : "39 raw + 4 × 4 history + horizon + 5 basis values",
    })),
    windows: [
      { id: "baseline", start: -240, end: -24, nominal: null },
      { id: "H72", start: 66, end: 78, nominal: 72 },
      { id: "D7", start: 156, end: 180, nominal: 168 },
    ],
    units: ["N/kg", "m/s"],
    figures: [
      { id: "gate7-routes", source: paths[0], kind: "engineering" },
      { id: "gate7-architecture", source: paths[4], kind: "engineering" },
      { id: "native-force", source: paths[3], kind: "analytical schematic" },
      { id: "native-time", source: paths[3], kind: "contract" },
      { id: "gate7-flow", source: paths[1], kind: "engineering" },
    ],
  };
}
const output = new URL("../src/data/gate7.json", import.meta.url);
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const bytes = JSON.stringify(compile(), null, 2) + "\n";
  if (process.argv.includes("--check"))
    assert.equal(
      readFileSync(output, "utf8"),
      bytes,
      "Gate7 presentation data drift",
    );
  else writeFileSync(output, bytes);
}
