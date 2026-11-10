import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { compile, serialize, texToText } from "../scripts/prepare-manuscript.mjs";
import {
  analyticalForce,
  cumulativeNetImpulse,
  forceQuantities,
} from "../src/lib/manuscript-mechanics.mjs";

const fixture = JSON.parse(
  readFileSync(new URL("../src/data/manuscript.json", import.meta.url)),
);
const sha = (url) =>
  createHash("sha256").update(readFileSync(url)).digest("hex");
const d = fixture.data;

test("fixture is deterministic, committed and duplicated byte-for-byte for download", () => {
  const expected = serialize(compile());
  assert.equal(expected, serialize(compile()));
  assert.equal(
    readFileSync(new URL("../src/data/manuscript.json", import.meta.url), "utf8"),
    expected,
  );
  assert.equal(
    readFileSync(new URL("../public/data/manuscript.json", import.meta.url), "utf8"),
    expected,
  );
});

test("the four recorded aggregate NRMSE values are unchanged", () => {
  const a = d.sixCell.aggregates;
  assert.equal(a.zero_innovation.mean.toFixed(6), "2.430659");
  assert.equal(a.training_constant.mean.toFixed(6), "1.036038");
  assert.equal(a.ridge_full.mean.toFixed(6), "0.736270");
  assert.equal(a.structured_full.mean.toFixed(6), "0.773316");
  // The paper's abstract reports the same values.
  for (const v of ["2.430659", "1.036038", "0.736270", "0.773316"])
    assert.ok(fixture.paper.abstract.includes(v), v);
});

test("site fixtures are byte-identical to the manuscript's figure inputs S16–S18", () => {
  const inputs = Object.fromEntries(fixture.inputs.map((i) => [i.path, i.sha256]));
  const pairs = [
    ["../src/data/gate7.json", "S16_gate7.json"],
    ["../src/data/lineage.json", "S17_lineage.json"],
    ["../src/data/formulation-methods.json", "S18_formulation-methods.json"],
  ];
  for (const [site, source] of pairs)
    assert.equal(
      sha(new URL(site, import.meta.url)),
      inputs[`docs/manuscript/v3/evidence/release_sources/${source}`],
      site,
    );
});

test("six-cell values aggregate correctly: equal-weight cells, root means, ddof=1 SD", () => {
  const { cells, aggregates, models } = d.sixCell;
  assert.equal(cells.length, 6);
  for (const m of models) {
    for (const c of cells) {
      const v = c.models[m];
      assert.equal(v.roots.length, 3);
      const mean = v.roots.reduce((s, r) => s + r.nrmse, 0) / 3;
      assert.ok(Math.abs(mean - v.mean) < 1e-12, `${m} ${c.cell}`);
      const sd = Math.sqrt(v.roots.reduce((s, r) => s + (r.nrmse - mean) ** 2, 0) / 2);
      assert.ok(Math.abs(sd - v.sampleSd) < 1e-12);
      for (const r of v.roots) {
        assert.equal(r.rows, 4000);
        assert.ok(Math.abs(r.rmse / r.truthSd - r.nrmse) < 1e-12, "NRMSE = RMSE / population SD");
      }
    }
    // Root six-cell score = mean of its six cell NRMSE values; aggregate = mean of roots.
    for (let i = 0; i < 3; i++) {
      const rootScore = cells.reduce((s, c) => s + c.models[m].roots[i].nrmse, 0) / 6;
      assert.ok(Math.abs(rootScore - aggregates[m].roots[i]) < 1e-12);
    }
    const across = aggregates[m].roots.reduce((s, v) => s + v, 0) / 3;
    assert.ok(Math.abs(across - aggregates[m].mean) < 1e-12);
  }
  assert.deepEqual(
    cells.map((c) => c.unit),
    ["N/kg", "N/kg", "N/kg", "m/s", "m/s", "m/s"],
  );
  // The legacy registered key is preserved for the force cells.
  assert.ok(cells.slice(0, 3).every((c) => c.cell.endsWith("/relative_peak_mean_force_innovation")));
});

test("Fig. 7 caption claim: ridge is lower in all 18 root-cell comparisons (0.025–0.047)", () => {
  const diffs = d.sixCell.cells.flatMap((c) =>
    [0, 1, 2].map(
      (i) => c.models.structured_full.roots[i].nrmse - c.models.ridge_full.roots[i].nrmse,
    ),
  );
  assert.equal(diffs.length, 18);
  assert.equal(Math.min(...diffs).toFixed(3), "0.025");
  assert.equal(Math.max(...diffs).toFixed(3), "0.047");
  assert.ok(fixture.figures[6].caption.includes("0.025 to 0.047"));
});

test("bootstrap: six stored within-root intervals, 5,000 camp resamples, no ridge-vs-structured interval", () => {
  const b = d.bootstrap;
  assert.equal(b.rows.length, 6);
  assert.equal(b.replicates, 5000);
  assert.equal(b.seed, 49505000);
  assert.equal(b.campsPerRoot, 16);
  assert.equal(b.episodesPerCamp, 250);
  for (const r of b.rows) {
    assert.equal(r.replicates, 5000);
    assert.ok(r.interval[0] < r.estimate && r.estimate < r.interval[1]);
    assert.ok(r.deltaInterval[1] < 0, "paired interval excludes zero on the favourable side");
    assert.ok(["ridge_full", "structured_full"].includes(r.model));
  }
  assert.equal(JSON.stringify(b).includes("ridge_vs_structured"), false);
});

test("Fig. 5 analytical signal reproduces the caption quantities on the 5,501-point grid", () => {
  const p = d.mechanics;
  assert.deepEqual([p.mass, p.gravity, p.amplitude, p.peakTime, p.duration], [70, 9.80665, 1000, 0.22, 0.55]);
  const q = forceQuantities(p, p.samples);
  assert.equal(q.meanForceNPerKg.toFixed(2), "14.79");
  assert.equal(q.peakForceNPerKg.toFixed(2), "24.09");
  assert.equal(q.netImpulseMPerS.toFixed(2), "2.74");
  const caption = fixture.figures[4].caption;
  for (const v of ["14.79 N/kg", "24.09 N/kg", "2.74 m/s"]) assert.ok(caption.includes(v), v);
  // Identity: mean force (N/kg) = g + net impulse / T.
  assert.ok(Math.abs(q.meanForceNPerKg - (p.gravity + q.netImpulseMPerS / p.duration)) < 1e-9);
  assert.ok(Math.abs(analyticalForce(p.duration, p)) < 1e-9, "force reaches zero at takeoff");
  assert.ok(Math.abs(cumulativeNetImpulse(p, p.duration, 5501) - q.netImpulseMPerS) < 1e-9);
  assert.deepEqual(
    p.windows.map((w) => [w.id, w.start, w.end]),
    [["baseline", -240, -24], ["H72", 66, 78], ["D7", 156, 180]],
  );
});

test("routes, architectures, design and lineage match the receipt checks", () => {
  assert.equal(d.routes.length, 18);
  assert.equal(d.routes.filter((r) => r.cpuSource.startsWith("Exact")).length, 18);
  assert.equal(d.routes.filter((r) => r.savedCuda === "pass").length, 8);
  assert.equal(d.routes.filter((r) => r.savedCuda === "fail").length, 10);
  assert.ok(d.routes.every((r) => r.inferenceRerun === false));
  assert.ok(d.routes.filter((r) => r.savedCuda === "fail").every((r) => /^M[4-8]$/.test(r.model)));
  const fams = d.architectures.families;
  assert.deepEqual(fams.map((f) => f.id), ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]);
  assert.equal(fams[0].parameters, 1346);
  assert.equal(fams[8].parameters, 10796);
  assert.ok(fams.slice(4).every((f) => f.components.includes("gru")));
  assert.ok(fams.every((f) => f.repeats.join() === "r0,r1"));
  const { training, development, roots } = d.design;
  assert.deepEqual([training.camps, training.episodes, training.rows], [96, 24000, 72000]);
  assert.deepEqual([development.camps, development.episodes, development.rows], [16, 4000, 12000]);
  assert.deepEqual(roots.map((r) => [r.id, r.camps, r.episodes, r.rows]), [["A", 16, 4000, 12000], ["B", 16, 4000, 12000], ["C", 16, 4000, 12000]]);
  assert.ok(roots.every((r) => r.labels.includes("label.relative_mean_concentric_force_innovation")));
  assert.equal(d.design.contract.groupingKeysAsPredictors, false);
  assert.equal(d.design.contract.targetLabelsAsPredictors, false);
  assert.equal(d.genealogy.length, 8);
  assert.equal(d.genealogy.filter((g) => g.parent).length, 5, "only the five recorded parent edges");
  const ids = new Set(d.genealogy.map((g) => g.id));
  assert.ok(d.genealogy.every((g) => !g.parent || ids.has(g.parent)));
  assert.deepEqual(d.richHistory.map((r) => r.difference), [-48, 4]);
});

test("ablations and nested camps come straight from the receipt and keep the evaluation roots", () => {
  const a = d.ablations;
  assert.deepEqual(a.nested.camps, [24, 48, 96]);
  assert.equal(a.variants.length, 6);
  for (const v of a.variants) {
    assert.equal(v.roots.length, 3);
    assert.ok(Math.abs(v.roots.reduce((s, x) => s + x, 0) / 3 - v.mean) < 1e-12);
  }
  assert.equal(a.variants[0].mean, d.sixCell.aggregates.ridge_full.mean);
  assert.equal(a.variants[4].mean, d.sixCell.aggregates.structured_full.mean);
});

test("figures carry questions, pages, plain-text captions and receipts; no private artifacts", () => {
  assert.equal(fixture.figures.length, 10);
  for (const f of fixture.figures) {
    assert.ok(f.question.endsWith("?"));
    assert.ok(f.page >= 1 && f.page <= 12);
    assert.ok(!/[\\{}]/.test(f.caption), `TeX left in Fig. ${f.number}`);
    assert.ok(fixture.paper.sections.some((s) => s.id === f.section));
    if (f.number > 1) assert.ok(f.receipt.numericalTest);
  }
  for (const i of fixture.inputs) assert.ok(i.path.startsWith("docs/manuscript/v3/"));
  const text = JSON.stringify(fixture);
  for (const forbidden of [".pt\"", ".ckpt", ".safetensors", "state_dict", "/home/", "private-evidence"])
    assert.equal(text.includes(forbidden), false, forbidden);
  assert.match(fixture.paper.status, /Unsubmitted research draft/);
  assert.equal(texToText("\\SI{2.74}{\\mps} and \\ident{x\\_y}"), "2.74 m/s and x_y");
});

test("interpretation claims shown beside figures hold for the recorded values", () => {
  const { cells, aggregates } = d.sixCell;
  const models = ["zero_innovation", "training_constant", "ridge_full", "structured_full"];
  // Fig. 7: ridge is lowest in every cell and in the six-cell score, for the mean and every root.
  for (const pick of [(v) => v.mean, (v) => v.roots[0].nrmse, (v) => v.roots[1].nrmse, (v) => v.roots[2].nrmse]) {
    for (const c of cells) {
      const vals = models.map((m) => pick(c.models[m]));
      assert.equal(Math.min(...vals), vals[2], c.cell);
    }
  }
  for (let i = 0; i < 3; i++)
    assert.equal(Math.min(...models.map((m) => aggregates[m].roots[i])), aggregates.ridge_full.roots[i]);
  // Fig. 6: ridge and structured below training mean, which is below zero innovation; error grows with horizon.
  for (const c of cells) {
    assert.ok(c.models.structured_full.mean < c.models.training_constant.mean);
    assert.ok(c.models.training_constant.mean < c.models.zero_innovation.mean);
  }
  for (const o of ["force", "impulse"])
    for (const m of ["ridge_full", "structured_full"]) {
      const series = ["H24", "H48", "H72"].map((h) => cells.find((c) => c.horizon === h && c.outcome === o).models[m].mean);
      assert.ok(series[0] < series[1] && series[1] < series[2], `${m} ${o}`);
    }
  // Fig. 8: within each root the stored ridge interval lies entirely below the structured interval.
  for (const r of ["A", "B", "C"]) {
    const ridge = d.bootstrap.rows.find((x) => x.root === r && x.model === "ridge_full");
    const structured = d.bootstrap.rows.find((x) => x.root === r && x.model === "structured_full");
    assert.ok(ridge.interval[1] < structured.interval[0], r);
  }
  // Fig. 4: failing-element counts for the failing routes span 88 to 443.
  const failing = d.routes.filter((r) => r.savedCuda === "fail").map((r) => r.failingElements);
  assert.deepEqual([Math.min(...failing), Math.max(...failing)], [88, 443]);
  // Fig. 9: nested subsets keep ridge below structured at every camp count.
  const [ridgeN, structN] = d.ablations.nested.series;
  ridgeN.points.forEach((p, i) => assert.ok(p.mean < structN.points[i].mean));
});
