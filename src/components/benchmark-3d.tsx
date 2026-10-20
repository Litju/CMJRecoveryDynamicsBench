"use client";
import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import {
  cell,
  horizons,
  models,
  type ModelId,
  type RootId,
  type Outcome,
} from "@/lib/science";
import { useWebGL, SceneBoundary } from "./scene-availability";
import { CameraControls, type CameraPose } from "./camera-controls";
const Scene = dynamic(() => import("./benchmark-scene"), {
  ssr: false,
  loading: () => <p className="scene-loading">Preparing the 3D comparison…</p>,
});
export type BenchmarkDatum = {
  key: string;
  model: ModelId;
  modelIndex: number;
  cellIndex: number;
  horizon: number;
  outcome: Outcome;
  nrmse: number;
  color: string;
  name: string;
};
export default function Benchmark3D({
  root,
  model,
  horizon,
  outcome,
  onSelect,
}: {
  root: RootId;
  model: ModelId;
  horizon: number;
  outcome: Outcome;
  onSelect: (entry: BenchmarkDatum) => void;
}) {
  const { ref, ready, reason, onUnavailable, fallback: showData } = useWebGL();
  const [pose, setPose] = useState<CameraPose>([9, 8, 11]);
  const [drag, setDrag] = useState(false);
  const [zoom, setZoom] = useState(42);
  const [hovered, setHovered] = useState<string | null>(null);
  const entries = useMemo(
    () =>
      models.flatMap((m, modelIndex) =>
        horizons.flatMap((h, hi) =>
          (["force", "impulse"] as const).map((o, oi) => ({
            key: `${m.id}/${h}/${o}`,
            model: m.id,
            modelIndex,
            cellIndex: hi * 2 + oi,
            horizon: h,
            outcome: o,
            nrmse: cell(m.id, root, h, o).nrmse,
            color: m.color,
            name: m.name,
          })),
        ),
      ),
    [root],
  );
  const selected = `${model}/${horizon}/${outcome}`;
  const inspection = entries.find(
    (e) => e.key === (ready && hovered ? hovered : selected),
  )!;
  const fallback = (
    <div className="benchmark-3d-fallback">
      <strong>Exact values remain available.</strong>
      <p>{reason}</p>
      <p>Use the linked matrix below or return to the 2D horizon plot.</p>
    </div>
  );
  return (
    <div className="benchmark-3d" ref={ref} data-testid="benchmark-3d">
      <div className="scene-heading">
        <span>24 SOURCE-BACKED CELLS</span>
        <strong>
          {root === "mean" ? "Across-root mean" : `Test root ${root}`} · NRMSE ↓
        </strong>
      </div>
      <CameraControls
        onView={(p) => {
          setPose(p);
          setZoom(42);
        }}
        drag={drag}
        onDrag={() => setDrag((v) => !v)}
        zoom={zoom}
        onZoom={setZoom}
        disabled={!ready}
      />
      <div
        className="benchmark-canvas"
        role="group"
        aria-label="Three-dimensional comparison: height is cell NRMSE, columns are outcome/horizon cells and depth separates four models. Exact values are in the linked matrix."
      >
        <SceneBoundary fallback={fallback} onError={onUnavailable}>
          {ready ? (
            <Scene
              entries={entries}
              selected={selected}
              pose={pose}
              drag={drag}
              zoom={zoom}
              onInspect={setHovered}
              onUnavailable={onUnavailable}
              onSelect={onSelect}
            />
          ) : (
            fallback
          )}
        </SceneBoundary>
      </div>
      <div className="scene-readout" aria-live="polite" aria-atomic="true">
        <span>
          {inspection.name} · H{inspection.horizon}{" "}
          {inspection.outcome === "force" ? "force" : "net impulse"}
        </span>
        <strong data-testid="scene-cell-score">
          {inspection.nrmse.toFixed(6)}
        </strong>
        <small>Cell NRMSE · unitless</small>
      </div>
      <div className="chart-legend scene-legend">
        {models.map((m) => (
          <span key={m.id}>
            <i style={{ background: m.color }} />
            {m.short}
          </span>
        ))}
      </div>
      <p className="scene-explanation">
        Each solid bar is one cell score, measured from zero. Hover to inspect;
        tap or click a bar to select its model, horizon and outcome. The
        orthographic view limits perspective scaling; rotation can still obscure
        bars. The exact matrix supports direct comparison.
      </p>
      <details className="scene-matrix" open={showData}>
        <summary>Exact 3D data · select any of the 24 cells</summary>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Exact 3D comparison matrix"
        >
          <table>
            <caption>
              {root === "mean"
                ? "Arithmetic mean of root-specific cell NRMSEs"
                : `Recorded cell NRMSEs for root ${root}`}{" "}
              · lower is better
            </caption>
            <thead>
              <tr>
                <th scope="col">Target cell</th>
                {models.map((m) => (
                  <th key={m.id} scope="col">
                    {m.short}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {horizons.flatMap((h) =>
                (["force", "impulse"] as const).map((o) => (
                  <tr key={`${h}/${o}`}>
                    <th scope="row">
                      H{h} {o === "force" ? "force" : "impulse"}
                    </th>
                    {models.map((m) => {
                      const entry = entries.find(
                        (e) => e.key === `${m.id}/${h}/${o}`,
                      )!;
                      return (
                        <td key={m.id}>
                          <button
                            aria-label={`${m.short} H${h} ${o}`}
                            aria-pressed={selected === entry.key}
                            onClick={() => onSelect(entry)}
                            data-cell={entry.key}
                          >
                            {entry.nrmse.toFixed(6)}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </details>
      <p className="scene-explanation">
        The plot shows discrete evaluation cells, not an athlete trajectory. It
        adds no confidence intervals. The reported intervals below describe
        aggregate NRMSE and paired differences from zero.
      </p>
    </div>
  );
}
