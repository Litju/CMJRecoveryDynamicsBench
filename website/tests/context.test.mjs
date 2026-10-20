import { test } from "node:test";
import assert from "node:assert/strict";
import { read } from "../scripts/prepare-data.mjs";
const context = JSON.parse(read("src/data/context.json"));
const history = JSON.parse(read("src/data/research-history.json"));
const lineage = JSON.parse(read("src/data/lineage.json"));
test("context uses the pinned measurement construction and all eight real exposure descriptors", () => {
  const observation = read(
    "source/exhibition/phase_consistent_force_impulse.py",
  );
  assert(
    observation.includes(
      `GRAVITATIONAL_ACCELERATION_M_PER_S2 = ${context.gravity}`,
    ),
  );
  assert(observation.includes(`TRACE_NODE_COUNT = ${context.traceNodes}`));
  assert.equal(context.trials, 3);
  assert.deepEqual(context.horizons, [24, 48, 72]);
  const exposure = read("source/exhibition/correlated_exposure_response.py");
  const fields = context.exposures.flatMap((g) => g.fields.map((f) => f.name));
  assert.equal(fields.length, 8);
  assert.equal(new Set(fields).size, 8);
  for (const field of fields) assert(exposure.includes(`${field}=`), field);
  assert(exposure.includes("session_rpe_load_au=duration * rpe"));
  assert.deepEqual(
    context.references.map((r) => r.doi),
    ["10.1123/ijspp.3.2.131", "10.1123/ijspp.2013-0413"],
  );
  assert.match(context.boundary, /does not validate this generator/);
});
test("history reader covers exactly the eight contracts without changing their ancestry or status", () => {
  assert.deepEqual(
    Object.keys(history),
    lineage.map((n) => n.id),
  );
  for (const node of lineage) {
    const note = history[node.id];
    assert(
      note.turn && note.category && note.issue && note.decision && note.lesson,
      node.id,
    );
  }
  assert.match(
    history.canonical_preseason_camp_recovery.decision,
    /retaining the task and underlying world law/,
  );
  assert.match(
    history.phase_consistent_post_exposure_recovery.decision,
    /Keep the episode response law/,
  );
  assert.match(
    history.rich_history_camp_recovery.lesson,
    /direct parent remains unresolved/,
  );
  assert.match(
    history.threshold_response_recovery.lesson,
    /PROPOSED, not an accepted successor/,
  );
  assert.match(
    history.fixed_mode_discrepancy_recovery.lesson,
    /higher mean error than full ridge/,
  );
});
