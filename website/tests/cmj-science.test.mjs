import test from "node:test";
import assert from "node:assert/strict";
import { G, impulseRange, innovation, response, trial } from "../src/lib/cmj-science.mjs";

// Reference values come from the simulator's own Python routines (realize_concentric_trial,
// fixed_mode_response) evaluated at the same inputs.
test("trial matches the simulator", () => {
  const t = trial(20, 2.7);
  assert.ok(Math.abs(t.duration - 0.26487857279500854) < 1e-12);
  assert.ok(Math.abs(t.peak - 25.82154261913697) < 1e-9);
  assert.ok(Math.abs(t.meanForce - 20) < 1e-9);
  assert.ok(Math.abs(t.netImpulse - 2.7) < 1e-9);
  assert.equal(t.force.length, 65);
});

test("mean force is gross, net impulse subtracts gravity, and peak differs from the mean", () => {
  const t = trial(22, 3.1);
  assert.ok(Math.abs(t.netImpulse - (t.meanForce - G) * t.duration) < 1e-9);
  assert.ok(t.peak > t.meanForce);
  assert.ok(Math.abs(t.peak - t.continuousPeak) < 0.01 * t.continuousPeak);
});

test("duration support is enforced", () => {
  assert.throws(() => trial(20, 0.1), RangeError);
  assert.throws(() => trial(9, 1), RangeError);
  const [lo, hi] = impulseRange(20);
  assert.ok(Math.abs(lo - 0.075 * (20 - G)) < 1e-12 && Math.abs(hi - 0.8 * (20 - G)) < 1e-12);
  assert.doesNotThrow(() => trial(20, lo));
  assert.doesNotThrow(() => trial(20, hi));
});

test("fixed-mode response matches the simulator", () => {
  assert.ok(Math.abs(response(0, 0.04, 0.03) + 0.07) < 1e-15);
  assert.ok(Math.abs(response(24, 0.04, 0.03) - -0.037259496439116274) < 1e-15);
  assert.ok(Math.abs(response(48, 0.04, 0.03) - -0.022354954989697286) < 1e-15);
  assert.ok(Math.abs(response(72, 0.04, 0.03) - -0.014722668105023057) < 1e-15);
  assert.ok(Math.abs(innovation(20, 24, 0.04, 0.03) - 20 * -0.037259496439116274) < 1e-12);
  assert.throws(() => response(-1, 0.04, 0.03), RangeError);
});
