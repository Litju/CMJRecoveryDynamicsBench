// Compile the flagship-paper fixture from the hash-pinned v4 package and publish its PDFs.
// Reads only committed public files; performs no fitting, scoring, resampling or inference.
import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../", import.meta.url));
const manifest = JSON.parse(readFileSync(new URL("../source/flagship-manifest.json", import.meta.url), "utf8"));
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const pkg = manifest.package;

const sums = readFileSync(root + manifest.artifactManifest.path);
assert.equal(sha256(sums), manifest.artifactManifest.sha256, "v4 ARTIFACT_SHA256SUMS drift; re-pin source/flagship-manifest.json");
const digests = Object.fromEntries(
  sums.toString("utf8").trim().split("\n").map((line) => {
    const [digest, path] = line.split("  ");
    return [path, digest];
  }),
);
const read = (relative) => {
  const bytes = readFileSync(`${root}${pkg}/${relative}`);
  assert.equal(sha256(bytes), digests[relative], `Flagship drift: ${relative}`);
  return bytes;
};

export function compile() {
  const tex = read("manuscript.tex").toString("utf8");
  const abstract = tex
    .match(/\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}/)[1]
    .replace(/\s+/g, " ")
    .replace(/--/g, "–")
    .trim();
  const title = tex.match(/\\title\{([^}]+)\}/)[1];
  const files = manifest.files.map((f) => {
    const bytes = read(f.file);
    assert.equal(sha256(bytes), f.sha256, `Pinned digest mismatch: ${f.file}`);
    assert.equal(bytes.length, f.bytes);
    return { ...f, href: `/paper/flagship/${f.file}`, path: `${pkg}/${f.file}` };
  });
  return {
    title,
    abstract,
    status: "Owner-review draft. Not peer reviewed, not submitted to a journal or preprint server, no DOI. A computational and synthetic study: no athlete was measured.",
    package: pkg,
    artifactManifestSha256: manifest.artifactManifest.sha256,
    files,
    figurePages: manifest.figurePages,
    sectionPages: manifest.sectionPages,
  };
}

const out = new URL("../src/data/flagship.json", import.meta.url);
const serialize = (data) => `${JSON.stringify(data, null, 2)}\n`;
function publish() {
  const dir = new URL("../public/paper/flagship/", import.meta.url);
  mkdirSync(dir, { recursive: true });
  for (const f of manifest.files) {
    read(f.file);
    copyFileSync(`${root}${pkg}/${f.file}`, new URL(f.file, dir));
  }
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const expected = serialize(compile());
  if (process.argv.includes("--check")) assert.equal(readFileSync(out, "utf8"), expected, "flagship.json is stale; run npm run data:flagship");
  else writeFileSync(out, expected);
  publish();
  console.log(`Flagship package verified (${manifest.files.length} PDFs, manifest ${manifest.artifactManifest.sha256.slice(0, 12)}).`);
}
