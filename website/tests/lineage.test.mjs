import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
const read = (p) => readFileSync(new URL(`../${p}`, import.meta.url), "utf8");
const nodes = JSON.parse(read("src/data/lineage.json"));
const manifest = JSON.parse(read("source/lineage/manifest.json"));

test("all eight lineage questions, statuses and parents match pinned GitHub contracts", () => {
  assert.equal(manifest.commit, "3dc4c82f0c948add6e4a9ebdebfd227933c823d3");
  assert.equal(nodes.length, 8);
  assert.equal(new Set(nodes.map((n) => n.id)).size, 8);
  for (const [name, file] of Object.entries(manifest.files)) {
    const contract = read(`source/lineage/${name}`);
    assert.equal(createHash("sha256").update(contract).digest("hex"), file.sha256);
    const definitions = contract.split("= BenchmarkDefinition(").slice(1);
    for (const definition of definitions) {
      const id = definition.match(/name="([^"]+)"/)[1];
      const node = nodes.find((n) => n.id === id);
      assert(node, id);
      assert.equal(node.source, file.path);
      assert.equal(node.status, definition.match(/status=BenchmarkStatus\.(\w+)/)[1]);
      assert.equal(node.parent, definition.match(/parent_name="([^"]+)"/)?.[1] ?? null);
      const question = [...definition.match(/research_question=\(([\s\S]*?)\),/)[1].matchAll(/"([^"]*)"/g)].map((m) => m[1]).join("");
      assert.equal(node.question, question);
    }
  }
});

test("the graph has five documented edges, a fork, and no invented retired ancestry", () => {
  assert.equal(nodes.filter((n) => n.parent).length, 5);
  const children = nodes.filter((n) => n.parent === "correlated_exposure_recovery");
  assert.deepEqual(children.map((n) => n.status), ["PROPOSED", "ACTIVE_CANDIDATE"]);
  assert.equal(nodes.find((n) => n.status === "RETIRED").parent, null);
  for (const node of nodes) {
    const seen = new Set();
    let current = node;
    while (current) {
      assert(!seen.has(current.id), "Lineage must be acyclic");
      seen.add(current.id);
      if (current.parent) assert(nodes.some((n) => n.id === current.parent));
      current = nodes.find((n) => n.id === current.parent);
    }
  }
});
