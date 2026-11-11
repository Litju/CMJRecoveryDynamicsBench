import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { compile } from "../scripts/prepare-flagship.mjs";

const committed = JSON.parse(readFileSync(new URL("../src/data/flagship.json", import.meta.url), "utf8"));
const manuscript = JSON.parse(readFileSync(new URL("../src/data/manuscript.json", import.meta.url), "utf8"));

test("flagship fixture is the deterministic compile of the pinned v4 package", () => {
  assert.deepEqual(compile(), committed);
});

test("the paper's headline scores equal the Observatory's recorded aggregates", () => {
  const a = manuscript.data.sixCell.aggregates;
  for (const [key, text] of [
    ["zero_innovation", "2.430659"],
    ["training_constant", "1.036038"],
    ["ridge_full", "0.736270"],
    ["structured_full", "0.773316"],
  ]) {
    assert.equal(a[key].mean.toFixed(6), text);
    assert.ok(committed.abstract.includes(text), `${text} missing from the flagship abstract`);
  }
});

test("the flagship keeps the synthetic and not-scored boundaries", () => {
  assert.match(committed.abstract, /not scored|were not scored/);
  assert.match(committed.abstract, /modeling assumptions, not measured recovery constants/);
  assert.match(committed.status, /no athlete was measured/);
  assert.equal(committed.files.length, 3);
});
