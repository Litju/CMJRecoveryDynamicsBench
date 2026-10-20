import { test } from "node:test";
import assert from "node:assert/strict";
import {
  decay,
  decaySlope,
  decayIntegral,
  decaySeries,
} from "../src/lib/decay.mjs";
test("signed lab curves, analytic slope and integral obey exact mathematical identities", () => {
  for (const [a, b] of [
    [0.7, 0.3],
    [-0.7, 0.3],
    [-0.5, 0.5],
    [0, 0],
    [1.5, -1.5],
  ]) {
    assert.equal(decay(0, a, b), a + b);
    assert.equal(decayIntegral(0, a, b), 0);
    for (const t of [0, 24, 48, 72, 84, 168]) {
      const epsilon = 0.001;
      const numericalSlope =
        (decay(t + epsilon, a, b) - decay(t - epsilon, a, b)) / (2 * epsilon);
      assert(Math.abs(numericalSlope - decaySlope(t, a, b)) < 1e-9);
      const areaSlope =
        (decayIntegral(t + epsilon, a, b) - decayIntegral(t - epsilon, a, b)) /
        (2 * epsilon);
      assert(Math.abs(areaSlope - decay(t, a, b)) < 1e-9);
      const row = decaySeries(a, b)[t];
      assert.equal(row.total, decay(t, a, b));
      assert.equal(row.slope, decaySlope(t, a, b));
      assert.equal(row.integral, decayIntegral(t, a, b));
      assert(Math.abs(row.fast + row.slow - row.total) < 1e-12);
    }
  }
});
