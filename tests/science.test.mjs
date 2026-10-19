import { test } from "node:test";
import assert from "node:assert/strict";
import {
  transform,
  serialize,
  read,
  modelIds,
} from "../scripts/prepare-data.mjs";
import { decay, decaySeries } from "../src/lib/decay.mjs";
const p = transform();
const near = (a, b) => assert(Math.abs(a - b) < 1e-12, `${a} != ${b}`);
test("committed fixtures are deterministic and checksum pinned", () => {
  assert.equal(serialize(), read("src/data/results.json"));
  assert.equal(serialize(), read("public/data/results.json"));
  assert.equal(
    p.provenance.resultsSha256,
    "cd991366c30a29723318b034bcbacff357544eff8d529678fcdcd849b0f08ce9",
  );
});
test("exact reported aggregate values and every cell mapping", () => {
  const expected = [
    2.4306587299637386, 1.0360383571026839, 0.7362702601870649,
    0.7733155792833424,
  ];
  modelIds.forEach((id, i) => {
    near(p.models[id].acrossRoots.root_mean_nrmse, expected[i]);
    const values = p.roots.map((r) => r.models[id].mean_six_cell_nrmse);
    const mean = values.reduce((a, b) => a + b) / 3;
    near(mean, expected[i]);
    near(
      Math.sqrt(values.reduce((s, v) => s + (v - mean) ** 2, 0) / 2),
      p.models[id].acrossRoots.root_sample_sd_nrmse,
    );
    for (const r of p.roots) {
      const m = r.models[id];
      assert.deepEqual(
        m.cells.map((c) => c.cell),
        p.protocol.registered_cells,
      );
      near(
        m.mean_six_cell_nrmse,
        m.cells.reduce((s, c) => s + c.rmse / c.truth_population_sd, 0) / 6,
      );
      near(
        m.paired_nrmse_delta_vs_zero,
        m.mean_six_cell_nrmse - r.models.zero_innovation.mean_six_cell_nrmse,
      );
      assert.equal(m.bootstrap.valid_replicates, 5000);
      assert(
        m.bootstrap.mean_six_cell_nrmse_95_percentile_interval[0] <
          m.bootstrap.mean_six_cell_nrmse_95_percentile_interval[1],
      );
    }
    for (const [key, stats] of Object.entries(
      p.models[id].acrossRoots.cell_nrmse_across_roots,
    )) {
      const v = p.roots.map(
        (r) => r.models[id].cells.find((c) => c.cell === key).nrmse,
      );
      near(v.reduce((a, b) => a + b) / 3, stats.root_mean_nrmse);
      assert.deepEqual(v, stats.root_values);
    }
  });
});
test("frozen training/development selection and scientific boundaries", () => {
  assert.deepEqual(p.protocol.alpha_grid, [0.01, 0.1, 1, 10, 100]);
  for (const id of ["ridge_full", "structured_full"]) {
    const s = p.models[id].selection;
    assert.equal(s.selected_alpha, 0.01);
    assert.equal(
      s.alpha_scores.toSorted(
        (a, b) =>
          a.development_mean_six_cell_nrmse - b.development_mean_six_cell_nrmse,
      )[0].alpha,
      s.selected_alpha,
    );
  }
  assert.equal(p.featureContract.grouping_keys_as_predictors, false);
  assert.equal(p.featureContract.target_labels_as_predictors, false);
  assert.equal(p.formulations.length, 8);
  assert.deepEqual(p.retiredStudy, {
    reportedPrimaryRawProgress: 0.1759,
    reportedPaired95Interval: [0.1531, 0.189],
  });
  assert.deepEqual(
    p.roots.map((r) => r.seed),
    [
      "res-526-public-eval-root-a-2026-10-18",
      "res-526-public-eval-root-b-2026-10-18",
      "res-526-public-eval-root-c-2026-10-18",
    ],
  );
  assert.equal(
    p.formulations.filter((f) => f.status === "Active candidate").length,
    1,
  );
  assert.equal(p.training.rows, 72000);
  assert.deepEqual(
    p.roots.map((r) => r.id),
    ["A", "B", "C"],
  );
});
test("illustration uses exactly two fixed exponential modes and reset anchors", () => {
  near(decay(0, 0.7, 0.3), 1);
  near(decay(24, 1, 0), Math.exp(-1));
  near(decay(84, 0, 1), Math.exp(-1));
  assert.equal(decay(10, 0, 0), 0);
  const series = decaySeries(0.7, 0.3);
  assert.equal(series.length, 169);
  for (let i = 1; i < series.length; i++)
    assert(series[i].total < series[i - 1].total);
  near(series[72].total, decay(72, 0.7, 0.3));
});
