import type { Metadata } from "next";
import { Chapter, PageIntro, SiteFooter, SiteHeader } from "@/components/site-shell";
import EvidenceFigure from "@/components/figures/fig10-evidence";
import {
  CITATION_URL,
  REPOSITORY,
  RELEASE_COMMIT,
  RELEASE_URL,
  manuscript,
  paperPage,
  section,
  sourceAt,
} from "@/lib/manuscript";
import { data as m8 } from "@/lib/science";

export const metadata: Metadata = {
  title: "Reproducibility and evidence — Recovery Observatory",
  description: "Evidence boundary, figure-to-source mapping, pinned digests and citation identities.",
};

export default function EvidencePage() {
  const p = manuscript.paper;
  return (
    <>
      <SiteHeader current="evidence" />
      <main id="main" className="pub-page">
        <PageIntro eyebrow="Reproducibility and evidence" title="What the evidence supports, and where it comes from" figures={[10]}>
          <p>
            Every value on this site is read from hash-pinned public files. The build fails if any input digest
            changes. Nothing is fitted, scored, resampled or inferred in the browser.
          </p>
        </PageIntro>

        <Chapter id="boundary" title="Evidence boundary" kicker="Results · reproduction limits">
          <EvidenceFigure />
          <div className="pub-boundary-grid">
            <section>
              <h3>Publicly reproducible</h3>
              <p>
                Source and contracts of the eight formulations and M0–M8 architectures; the six-cell synthetic
                benchmark, its stored bootstrap intervals, ablations and nested-camp results; the rich-history
                row counts. All figures regenerate from the V3 package without training or inference.
              </p>
            </section>
            <section>
              <h3>Privately qualified, public summary only</h3>
              <p>
                Parameter counts, exact CPU-source equality on 18/18 routes and the archived-GPU comparison (8 pass,
                10 fail). The original checkpoints, fitted preprocessing values and inference arrays are not public,
                so this qualification cannot be independently repeated from public files.
              </p>
            </section>
            <section>
              <h3>Not established</h3>
              <p>
                The historical split identity (public rich-history reconstruction differs by −48 training and +4
                validation rows); the cause of the M4–M8 GPU-array differences; any public rerun of the private
                checkpoints; and athlete predictive validity, transportability or clinical use.
              </p>
            </section>
          </div>
        </Chapter>

        <Chapter id="mapping" title="Figure → manuscript → source mapping">
          <div className="pub-table-scroll" tabIndex={0} role="region" aria-label="Figure to source mapping">
            <table className="pub-table">
              <caption>Each interactive figure, its manuscript location, its recorded receipt check and its pinned sources.</caption>
              <thead>
                <tr>
                  <th scope="col">Figure</th>
                  <th scope="col">Manuscript</th>
                  <th scope="col">Receipt check</th>
                  <th scope="col">Release sources (v{p.releaseVersion})</th>
                  <th scope="col">Package data</th>
                </tr>
              </thead>
              <tbody>
                {manuscript.figures.map((f) => (
                  <tr key={f.number}>
                    <th scope="row">
                      <a href={`${f.route}#${f.id}`}>Fig. {f.number}</a>
                    </th>
                    <td>
                      <a href={paperPage(f.page)}>p. {f.page}</a> · {section(f.section).title}
                    </td>
                    <td>{f.receipt ? <code>{f.receipt.numericalTest}</code> : "Non-quantitative; lineage contract S17/S18"}</td>
                    <td>
                      {f.receipt
                        ? f.receipt.releaseSources.map((s) => (
                            <a key={s.id} href={sourceAt(s.path, RELEASE_COMMIT)} className="pub-chip" target="_blank" rel="noreferrer">
                              {s.id}
                            </a>
                          ))
                        : ["S17", "S18"].map((s) => (
                            <span key={s} className="pub-chip">
                              {s}
                            </span>
                          ))}
                    </td>
                    <td>
                      {f.receipt?.localData.length
                        ? f.receipt.localData.map((s) => <code key={s.path}>{s.path.split("/").pop()}</code>)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Chapter>

        <Chapter id="inputs" title="Pinned inputs">
          <p>
            Package <code>{p.package}</code>, integrated on <code>main</code> at commit{" "}
            <a href={sourceAt(p.package)}>
              <code>{p.packageCommit.slice(0, 12)}</code>
            </a>
            ; release sources from v{p.releaseVersion} at{" "}
            <a href={`${REPOSITORY}/tree/${RELEASE_COMMIT}`}>
              <code>{RELEASE_COMMIT.slice(0, 12)}</code>
            </a>
            .
          </p>
          <div className="pub-table-scroll" tabIndex={0} role="region" aria-label="Pinned inputs">
            <table className="pub-table">
              <caption>SHA-256 of every manuscript input read by the website build (checked against ARTIFACT_SHA256SUMS).</caption>
              <thead>
                <tr>
                  <th scope="col">Path</th>
                  <th scope="col">SHA-256</th>
                </tr>
              </thead>
              <tbody>
                {manuscript.inputs.map((i) => (
                  <tr key={i.path}>
                    <th scope="row">
                      <a href={sourceAt(i.path)} target="_blank" rel="noreferrer">
                        {i.path.replace(`${p.package}/`, "")}
                      </a>
                    </th>
                    <td>
                      <code className="pub-hash-cell">{i.sha256}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul className="pub-link-list">
            <li>
              <a href="/data/manuscript.json" download>
                Download the manuscript figure fixture (JSON)
              </a>
            </li>
            <li>
              <a href="/data/results.json" download>
                Download the historical M8 benchmark fixture (JSON)
              </a>{" "}
              — pinned to source <code>{m8.provenance.commit.slice(0, 7)}</code>
            </li>
          </ul>
        </Chapter>

        <Chapter id="reproduce" title="Reproduce the evidence">
          <p>From a checkout of the repository:</p>
          <pre className="pub-code">
            <code>{`# Verify the manuscript package and regenerate its figures (no training or inference)
cd docs/manuscript/v3 && sha256sum -c ARTIFACT_SHA256SUMS
bash reproducibility/build.sh   # see the package README for the pinned toolchain

# Rebuild and check this website's fixtures
cd website && npm ci && npm test && npm run build`}</code>
          </pre>
          <p>
            The public synthetic study itself is executable with{" "}
            <code>python -m cmj_recovery_dynamics.studies.fixed_mode_reference_study</code> (pilot → select →
            evaluate); see the <a href={sourceAt("docs/INDEX.md")}>documentation index</a>.
          </p>
        </Chapter>

        <Chapter id="citations" title="Citation identities">
          <dl className="pub-dl">
            <dt>Current software</dt>
            <dd>
              Repository-root <a href={CITATION_URL}>CITATION.cff</a>, version {p.releaseVersion};{" "}
              <a href={RELEASE_URL}>v{p.releaseVersion} release</a>. No DOI is assigned.
            </dd>
            <dt>Research paper</dt>
            <dd>V3 illustrated manuscript — unsubmitted research draft; not peer reviewed; no journal or DOI.</dd>
            <dt>Historical M8 receipts</dt>
            <dd>
              The benchmark explorer&apos;s receipts keep their original source identity,{" "}
              <a href={`${m8.provenance.repository}/blob/${m8.provenance.commit}/CITATION.cff`}>
                CITATION.cff at <code>{m8.provenance.commit.slice(0, 7)}</code>
              </a>{" "}
              (version 0.1.0). It is provenance for those receipts, not the current citation.
            </dd>
          </dl>
        </Chapter>
      </main>
      <SiteFooter />
    </>
  );
}
