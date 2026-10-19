import { test } from 'node:test';
import assert from 'node:assert/strict';
import { read, serializeMethods, hash } from '../scripts/prepare-data.mjs';
const exhibit = JSON.parse(read('src/data/exhibition.json'));
const nodes = JSON.parse(read('src/data/lineage.json'));
const sheets = JSON.parse(read('src/data/formulation-methods.json'));
test('exhibition authorities and all diagnostic results are pinned and deterministic', () => {
  assert.equal(serializeMethods(), read('src/data/methods.json'));
  assert.equal(serializeMethods(), read('public/data/methods.json'));
  const methods = JSON.parse(serializeMethods());
  const receipt = JSON.parse(read('source/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json'));
  assert.deepEqual(methods.variants, receipt.across_root_variability);
  assert.deepEqual(methods.selection, receipt.selection);
  assert.equal(methods.sourceSha256, hash(read('source/M8_FIXED_MODE_PUBLIC_REFERENCE_RESULTS.json')));
  assert.equal(Object.keys(methods.variants).length, 17);
});
test('knowledge boundary excludes all current future assessments and preserves exactly 82 fields', () => {
  assert.equal(exhibit.predictors.reduce((sum, p) => sum + p.count, 0), 82);
  assert.deepEqual(exhibit.events.filter(e => !e.available).map(e => e.time), [24,48,72]);
  assert.deepEqual(exhibit.events.filter(e => e.available).map(e => e.id), ['history','baseline','origin']);
  assert(exhibit.events.every(e => e.time === null || e.available === (e.time <= 0)));
  assert.deepEqual(exhibit.layers.map(l => l.id), ['world','observation','predictor','scorer']);
  const observation = read('source/exhibition/phase_consistent_force_impulse.py');
  assert(observation.includes('One dedicated baseline about two hours before exposure'));
  assert(observation.includes('("training age", "strength")'));
  assert(observation.includes('TRACE_NODE_COUNT = 65'));
  assert(observation.includes('exactly three valid paired trials'));
  assert(observation.includes('return (mean_force_n_per_kg - GRAVITATIONAL_ACCELERATION_M_PER_S2) * duration_seconds'));
});
test('every methods sheet identifies the exact world and observation symbols in its source contract', () => {
  assert.deepEqual(Object.keys(sheets), nodes.map(n => n.id));
  for (const n of nodes) {
    const contract = read('source/lineage/'+n.source.split('/').at(-1));
    const sheet = sheets[n.id];
    assert(contract.includes(sheet.world.toUpperCase()), n.id+' world');
    assert(contract.includes(sheet.observation.toUpperCase()), n.id+' observation');
    assert(sheet.task && sheet.metric && sheet.relevance && sheet.limitation);
  }
  assert.match(sheets.threshold_response_recovery.metric,/twelve-cell/);
  assert.match(sheets.rich_history_camp_recovery.metric,/24-cell/);
});
