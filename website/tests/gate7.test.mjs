import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { compile } from "../scripts/prepare-gate7.mjs";
import { mechanics } from "../src/lib/native-mechanics.mjs";
test("Gate7 compiler is deterministic, pinned and separate from M8 scores", () => {
  const data = compile();
  assert.deepEqual(data, compile());
  assert.deepEqual(
    data,
    JSON.parse(
      readFileSync(new URL("../src/data/gate7.json", import.meta.url)),
    ),
  );
  assert.equal(data.models.flatMap((m) => m.repeats).length, 18);
  assert.equal(
    data.models.filter((m) => m.cuda === "Outside recorded tolerance").length,
    5,
  );
  assert.deepEqual(
    data.windows.slice(1).map((w) => [w.start, w.end]),
    [
      [66, 78],
      [156, 180],
    ],
  );
  assert.equal(JSON.stringify(data).includes("nrmse"), false);
  assert.equal(data.experiment, "engineering reconstruction");
  for (const s of data.sources) assert.match(s.sha256, /^[a-f0-9]{64}$/);
});
test("linear force trapezoid agrees with analytical integral and mass normalization", () => {
  for (const duration of [0.2, 0.4, 0.6])
    for (const mass of [60, 75, 100]) {
      const m = mechanics(duration, mass);
      assert.ok(Math.abs(m.force - 15.80665) < 1e-12);
      assert.ok(Math.abs(m.impulse - 6 * duration) < 1e-12);
      assert.ok(Math.abs(m.force - 9.80665 - m.impulse / duration) < 1e-12);
    }
});

test('presentation payload contains no restricted artifact or machine locator', () => {
  const data = JSON.stringify(compile());
  for (const forbidden of [/\/home\//, /private-verification/, /checkpoint_bytes/, /saved_predictions/, /\.pt"/, /\.pkl"/]) assert.doesNotMatch(data, forbidden);
});
