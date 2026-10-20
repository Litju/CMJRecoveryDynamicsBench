import { test } from "node:test";
import assert from "node:assert/strict";
import { responsePaths } from "../src/lib/response-geometry.mjs";
import { decay } from "../src/lib/decay.mjs";
test("3D response curves preserve exact time, amplitudes, component sums and categorical lanes", () => {
  for (const [a, b] of [
    [0.7, 0.3],
    [0.7, 0],
    [0, 0.3],
    [0, 0],
    [-0.7, 0.3],
    [1.5, -1.5],
  ]) {
    const rows = responsePaths(a, b);
    assert.deepEqual(
      rows.map((r) => r.id),
      ["total", "fast", "slow"],
    );
    assert.deepEqual(
      rows.map((r) => r.z),
      [-1.6, 0, 1.6],
    );
    for (let t = 0; t <= 168; t++) {
      for (const row of rows) {
        assert.equal(row.points.length, 169);
        assert.equal(row.points[t][0], t / 21 - 4);
        assert.equal(row.points[t][2], row.z);
      }
      assert.equal(rows[0].points[t][1], decay(t, a, b) * 3);
      assert.equal(rows[1].points[t][1], a * Math.exp(-t / 24) * 3);
      assert.equal(rows[2].points[t][1], b * Math.exp(-t / 84) * 3);
      assert(
        Math.abs(
          rows[0].points[t][1] - rows[1].points[t][1] - rows[2].points[t][1],
        ) < 1e-12,
      );
    }
  }
});
