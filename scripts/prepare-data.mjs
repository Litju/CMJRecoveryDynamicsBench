import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
export const base = new URL("../", import.meta.url);
export const read = (path) => readFileSync(new URL(path, base), "utf8");
export const hash = (value) => createHash("sha256").update(value).digest("hex");
export const modelIds = [
  "zero_innovation",
  "training_constant",
  "ridge_full",
  "structured_full",
];
export function transform() {
  const manifest = JSON.parse(read("source/manifest.json"));
  assert.equal(manifest.commit, "3dc4c82f0c948add6e4a9ebdebfd227933c823d3");
  for (const [name, file] of Object.entries(manifest.files)) {
    assert.equal(
      hash(read("source/" + name)),
      file.sha256,
      `Source checksum drift: ${name}`,
    );
  }
  const p = JSON.parse(
    read("source/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json"),
  );
  assert.equal(p.protocol.benchmark, "fixed_mode_discrepancy_recovery");
  assert.equal(p.independent_test_roots.length, 3);
  const roots = p.independent_test_roots.map((r, i) => ({
    id: ["A", "B", "C"][i],
    seed: r.root_seed,
    data: r.data,
    models: Object.fromEntries(
      modelIds.map((id) => {
        const result = r.models[id];
        assert.equal(result.cells.length, 6);
        for (const c of result.cells) {
          assert(
            Number.isFinite(c.rmse) && c.rmse >= 0 && c.truth_population_sd > 0,
          );
          assert.equal(c.rows, 4000);
          assert(Math.abs(c.rmse / c.truth_population_sd - c.nrmse) < 1e-12);
        }
        assert(
          Math.abs(
            result.cells.reduce((s, c) => s + c.nrmse, 0) / 6 -
              result.mean_six_cell_nrmse,
          ) < 1e-12,
        );
        return [
          id,
          { ...result, bootstrap: r.paired_camp_bootstrap.models[id] },
        ];
      }),
    ),
  }));
  const formulations = read("source/M8_REFERENCE_MODEL_STUDY.md")
    .split("\n")
    .filter((line) => /^\| `\w+_recovery`/.test(line))
    .map((line) => {
      const c = line.split("|").map((s) => s.trim());
      return { id: c[1].replaceAll("`", ""), status: c[2], limitation: c[4] };
    });
  assert.equal(formulations.length, 8);
  const retiredText = read("source/M8_REFERENCE_MODEL_STUDY.md").replace(
    /\s+/g,
    " ",
  );
  const retiredPrimary = retiredText.match(
    /\| Ridge, `alpha=1` \(declared primary\) \| ([0-9.]+) \|/,
  );
  const retiredInterval = retiredText.match(
    /interval was `\[([0-9.]+), ([0-9.]+)\]` \(500 of 500 valid replicates\)/,
  );
  assert(
    retiredPrimary && retiredInterval,
    "Retired-study source schema drift",
  );
  return {
    retiredStudy: {
      reportedPrimaryRawProgress: Number(retiredPrimary[1]),
      reportedPaired95Interval: retiredInterval.slice(1).map(Number),
    },
    provenance: {
      ...manifest,
      resultsSha256:
        manifest.files["M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json"].sha256,
      scientificResultsSha256: p.scientific_results_sha256,
      studyCode: p.study.study_code_sha_abbreviated,
      selectionLockSha256: p.selection_lock_sha256,
    },
    protocol: p.protocol,
    featureContract: p.feature_contract,
    training: p.data.training,
    development: p.data.development,
    roots,
    models: Object.fromEntries(
      modelIds.map((id) => [
        id,
        {
          acrossRoots: p.across_root_variability[id],
          selection: p.selection[id] ?? null,
        },
      ]),
    ),
    formulations,
    claimBoundary: p.claim_boundary,
  };
}
export function serialize() {
  return JSON.stringify(transform()) + "\n";
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const output = serialize();
  for (const path of ["src/data/results.json", "public/data/results.json"]) {
    if (process.argv.includes("--check"))
      assert.equal(read(path), output, `Stale fixture: ${path}`);
    else writeFileSync(new URL(path, base), output);
  }
  console.log(
    `Provenance verified. Fixture SHA-256 ${hash(output)} (${Buffer.byteLength(output)} bytes).`,
  );
}
