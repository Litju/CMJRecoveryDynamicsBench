"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import { useWebGL, SceneBoundary } from "./scene-availability";
import { CameraControls, type CameraPose } from "./camera-controls";
import { plotTheme as theme } from "@/lib/plot-theme.mjs";
import { MoveUpRight } from "lucide-react";
import { decay, decaySeries } from "@/lib/decay.mjs";
const Scene = dynamic(() => import("./instrument-scene"), {
  ssr: false,
  loading: () => (
    <p className="scene-loading">Preparing the 3D response curves…</p>
  ),
});
function InstrumentFallback({
  time = 24,
  fast = 0.7,
  slow = 0.3,
}: {
  time?: number;
  fast?: number;
  slow?: number;
}) {
  const series = decaySeries(fast, slow);
  return (
    <div
      className="instrument-fallback response-fallback"
      data-testid="instrument-fallback"
    >
      <svg
        viewBox="0 0 620 330"
        role="img"
        aria-label="Exact two-dimensional mathematical fallback. Response against time in hours."
      >
        {[0, 0.5, 1].map((v) => (
          <g key={v}>
            <line
              x1="50"
              x2="572"
              y1={275 - v * 220}
              y2={275 - v * 220}
              stroke={theme.grid}
            />
            <text
              x="37"
              y={279 - v * 220}
              textAnchor="end"
              fill={theme.muted}
              fontSize="11"
            >
              {v.toFixed(1)}
            </text>
          </g>
        ))}
        {[0, 24, 48, 72, 96, 120, 144, 168].map((t) => (
          <g key={t}>
            <line
              x1={50 + t * 3.1}
              x2={50 + t * 3.1}
              y1="35"
              y2="275"
              stroke={theme.grid}
            />
            <text
              x={50 + t * 3.1}
              y="300"
              fill={theme.muted}
              fontSize="11"
              textAnchor="middle"
            >
              {t}h
            </text>
          </g>
        ))}
        {(["total", "fast", "slow"] as const).map((id) => (
          <path
            key={id}
            d={series
              .map(
                (p, i) =>
                  `${i ? "L" : "M"}${50 + p.time * 3.1},${275 - p[id] * 220}`,
              )
              .join(" ")}
            fill="none"
            stroke={
              id === "total"
                ? theme.text
                : id === "fast"
                  ? theme.fast
                  : theme.slow
            }
            strokeWidth={id === "total" ? 2.5 : 1.5}
          />
        ))}
        <line
          x1={50 + time * 3.1}
          x2={50 + time * 3.1}
          y1="35"
          y2="275"
          stroke={theme.ochre}
          strokeDasharray="4 4"
        />
        <text x="50" y="20" fill={theme.muted} fontSize="11">
          RESPONSE / ARBITRARY UNITS
        </text>
      </svg>
    </div>
  );
}
export default function HeroInstrument() {
  const {
    ref: instrument,
    ready: render3d,
    reason,
    onUnavailable,
  } = useWebGL();
  const [pose, setPose] = useState<CameraPose>([9, 8, 11]);
  const [drag, setDrag] = useState(false);
  const [zoom, setZoom] = useState(42);
  const [time, setTime] = useState(24);
  const [mode, setMode] = useState("both");
  const fast = mode === "slow" ? 0 : 0.7;
  const slow = mode === "fast" ? 0 : 0.3;
  return (
    <div className="hero-instrument" ref={instrument}>
      <div className="instrument-top">
        <span>
          <span className="status-dot" /> SIGNAL STUDY 001
        </span>
        <span>ILLUSTRATIVE / SYNTHETIC</span>
      </div>
      <div
        className="instrument-visual"
        role="group"
        aria-label="Interactive three-dimensional mathematical response curves. Exact values are displayed below."
      >
        <div className="instrument-cross cross-top">+</div>
        <div className="instrument-cross cross-bottom">+</div>
        <SceneBoundary
          onError={onUnavailable}
          fallback={<InstrumentFallback time={time} fast={fast} slow={slow} />}
        >
          {render3d ? (
            <Scene
              time={time}
              fast={fast}
              slow={slow}
              pose={pose}
              drag={drag}
              zoom={zoom}
              onSelectTime={setTime}
              onUnavailable={onUnavailable}
            />
          ) : (
            <InstrumentFallback time={time} fast={fast} slow={slow} />
          )}
        </SceneBoundary>
        <div className="instrument-coordinate">
          X / ELAPSED HOURS
          <br />Y / RESPONSE
          <br />Z / MODE
        </div>
        <div className="instrument-annotation">
          <span className="annotation-line" />
          TWO FIXED MODES
          <br />
          <strong>
            24 h <span>×</span> 84 h
          </strong>
        </div>
        <span className="instrument-index">
          FIG. 01 <MoveUpRight size={13} />
        </span>
      </div>
      <div className="chart-legend response-legend">
        <span>
          <i style={{ background: theme.text }} />
          Combined
        </span>
        <span>
          <i style={{ background: theme.fast }} />
          24 h mode
        </span>
        <span>
          <i style={{ background: theme.slow }} />
          84 h mode
        </span>
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
        disabled={!render3d}
      />
      {!render3d && <p className="scene-fallback-note">{reason}</p>}
      <fieldset className="hero-mode">
        <legend>Isolate a mathematical mode</legend>
        <div className="segmented">
          {[
            ["both", "Both modes"],
            ["fast", "24 h only"],
            ["slow", "84 h only"],
          ].map(([id, label]) => (
            <button
              key={id}
              aria-pressed={mode === id}
              onClick={() => setMode(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>
      <div className="instrument-scrub">
        <div>
          <label htmlFor="hero-time">SCRUB THE ILLUSTRATION</label>
          <output htmlFor="hero-time">
            {String(time).padStart(3, "0")} <span>h</span>
          </output>
        </div>
        <input
          id="hero-time"
          type="range"
          min="0"
          max="168"
          value={time}
          onChange={(e) => setTime(Number(e.target.value))}
          aria-valuetext={`${time} illustrative hours`}
        />
        <div className="scrub-ticks">
          <span>00 h</span>
          <span>84 h</span>
          <span>168 h</span>
        </div>
      </div>
      <p className="instrument-caption">
        <output data-testid="hero-response">
          {decay(time, fast, slow).toFixed(4)}
        </output>{" "}
        arbitrary units · y(t) = {fast}e⁻ᵗ/²⁴ + {slow}e⁻ᵗ/⁸⁴.
        <br />X is elapsed hours; Y is the mathematical response; Z separates
        the three curves. Click a curve to select its elapsed hour. Click a
        curve to select its elapsed hour. Not measured motion or model
        predictions.
      </p>
    </div>
  );
}
