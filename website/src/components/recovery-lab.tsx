"use client";
import { PlotSelection } from "./plot-selection";
import { useEffect, useState } from "react";
import { Pause, Play, RotateCcw, FlaskConical } from "lucide-react";
import {
  ResponsiveContainer,
  Area,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ComposedChart,
} from "recharts";
import { decay, decaySeries, decaySlope, decayIntegral } from "@/lib/decay.mjs";
import { sourceLink } from "@/lib/science";
import { plotTheme as theme, plotTooltip } from "@/lib/plot-theme.mjs";
export default function RecoveryLab() {
  const [fast, setFast] = useState(0.7);
  const [slow, setSlow] = useState(0.3);
  const [time, setTime] = useState(24);
  const [playing, setPlaying] = useState(false);
  const [view, setView] = useState("response");
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(
      () => setTime((t) => (t >= 168 ? 0 : t + 1)),
      100,
    );
    return () => clearInterval(timer);
  }, [playing]);
  useEffect(() => {
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const stop = () => setPlaying(false);
    media.addEventListener("change", stop);
    const hide = () => {
      if (document.hidden) stop();
    };
    document.addEventListener("visibilitychange", hide);
    return () => {
      media.removeEventListener("change", stop);
      document.removeEventListener("visibilitychange", hide);
    };
  }, []);
  const reset = () => {
    setFast(0.7);
    setSlow(0.3);
    setTime(24);
    setPlaying(false);
    setView("response");
  };
  const series = decaySeries(fast, slow);
  return (
    <section id="lab" className="lab-section" aria-labelledby="lab-title">
      <div className="shell section">
        <div className="section-top">
          <div className="eyebrow">
            <span className="section-number">IV / LAB</span> THE RECOVERY LAB
          </div>
          <span className="illustration-tag">
            <FlaskConical size={13} /> MATHEMATICAL ILLUSTRATION
          </span>
        </div>
        <div className="section-heading">
          <div>
            <h2 id="lab-title">
              Two modes. <span>Room to experiment.</span>
            </h2>
            <p>
              Change the amplitudes. Scrub through time. See what the equation
              does.
            </p>
          </div>
        </div>
        <div className="lab-panel">
          <div className="lab-controls">
            <div className="equation-label">A TWO-TERM EXPONENTIAL</div>
            <div className="equation">
              y(t) = a e<sup>−t/24</sup> + b e<sup>−t/84</sup>
            </div>
            <p className="lab-intro">
              Two publicly described time constants, combined in a simple
              illustration. Amplitudes are arbitrary and unitless.
            </p>
            <fieldset className="lab-scenarios">
              <legend>Try a mathematical shape</legend>
              <div>
                <button
                  onClick={() => {
                    setFast(0.7);
                    setSlow(0.3);
                  }}
                >
                  Positive decay
                </button>
                <button
                  onClick={() => {
                    setFast(-0.7);
                    setSlow(0.3);
                  }}
                >
                  Opposing modes
                </button>
                <button
                  onClick={() => {
                    setFast(-0.5);
                    setSlow(0.5);
                  }}
                >
                  Cancel at origin
                </button>
              </div>
            </fieldset>
            <div className="slider-control">
              <div>
                <label htmlFor="fast-amplitude">
                  <i className="legend-dot mint" />
                  Fast amplitude <span>a</span>
                </label>
                <output htmlFor="fast-amplitude">{fast.toFixed(2)}</output>
              </div>
              <input
                id="fast-amplitude"
                type="range"
                min="-1.5"
                max="1.5"
                step="0.01"
                value={fast}
                onChange={(e) => setFast(Number(e.target.value))}
              />
              <small>24-hour time constant</small>
            </div>
            <div className="slider-control slow-slider">
              <div>
                <label htmlFor="slow-amplitude">
                  <i className="legend-dot lavender" />
                  Slow amplitude <span>b</span>
                </label>
                <output htmlFor="slow-amplitude">{slow.toFixed(2)}</output>
              </div>
              <input
                id="slow-amplitude"
                type="range"
                min="-1.5"
                max="1.5"
                step="0.01"
                value={slow}
                onChange={(e) => setSlow(Number(e.target.value))}
              />
              <small>84-hour time constant</small>
            </div>
            <div className="lab-buttons">
              <button
                className="button secondary"
                onClick={() => setPlaying((p) => !p)}
                aria-pressed={playing}
              >
                {playing ? <Pause size={15} /> : <Play size={15} />}{" "}
                {playing ? "Pause" : "Play"} time
              </button>
              <button className="reset-button" onClick={reset}>
                <RotateCcw size={15} />
                Reset
              </button>
            </div>
          </div>
          <div className="lab-plot">
            <fieldset className="lab-view">
              <legend>Inspect the equation</legend>
              <div className="segmented">
                {["response", "slope", "integral"].map((v) => (
                  <button
                    key={v}
                    aria-pressed={view === v}
                    onClick={() => setView(v)}
                  >
                    {v === "response"
                      ? "Response"
                      : v === "slope"
                        ? "Rate of change"
                        : "Accumulated area"}
                  </button>
                ))}
              </div>
            </fieldset>
            <div className="lab-plot-title">
              <span className="panel-label">
                {view === "response"
                  ? "ILLUSTRATIVE RESPONSE y(t)"
                  : view === "slope"
                    ? "RATE OF CHANGE y′(t)"
                    : "SIGNED AREA FROM 0 TO t"}
              </span>
              <div>
                <output data-testid="lab-chart-value">
                  {(view === "response"
                    ? decay(time, fast, slow)
                    : view === "slope"
                      ? decaySlope(time, fast, slow)
                      : decayIntegral(time, fast, slow)
                  ).toFixed(view === "slope" ? 6 : 4)}
                </output>
                <span> at {time} h</span>
              </div>
            </div>
            <div
              className="lab-chart"
              role="group"
              aria-label={`Two-term mathematical ${view} illustration. Exact current values and equations are displayed as text below.`}
            >
              <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <ComposedChart
                  data={series}
                  margin={{ top: 20, right: 24, bottom: 8, left: 0 }}
                  accessibilityLayer
                >
                  <CartesianGrid
                    stroke={theme.grid}
                    vertical={false}
                    strokeDasharray="3 6"
                  />
                  <XAxis
                    dataKey="time"
                    type="number"
                    domain={[0, 168]}
                    ticks={[0, 24, 48, 72, 96, 120, 144, 168]}
                    minTickGap={20}
                    interval="preserveStartEnd"
                    tickFormatter={(v) => `${v}h`}
                    stroke={theme.muted}
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis
                    domain={[(min: number) => Math.min(0, min), (max: number) => Math.max(0, max)]}
                    tickFormatter={(v) => Number(v).toLocaleString("en-US", { maximumSignificantDigits: 3 })}
                    stroke={theme.muted}
                    tickLine={false}
                    axisLine={false}
                    width={60}
                    tick={{ fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={plotTooltip}
                    labelStyle={{ color: theme.text }}
                    itemStyle={{ color: theme.text }}
                    labelFormatter={(v) => `${v} hours`}
                    formatter={(v) => Number(v).toFixed(view === "slope" ? 6 : 4)}
                    cursor={{ stroke: theme.ochre, strokeDasharray: "3 6" }}
                  />
                  <Area
                    type="monotone"
                    dataKey={view === "response" ? "total" : view}
                    name={
                      view === "response"
                        ? "Combined response"
                        : view === "slope"
                          ? "Rate · arbitrary units / h"
                          : "Area · arbitrary units × h"
                    }
                    fill={theme.fast}
                    fillOpacity={0.13}
                    stroke={theme.text}
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                  {view === "response" && (
                    <Line
                      type="monotone"
                      dataKey="fast"
                      name="24 h term"
                      stroke={theme.fast}
                      dot={false}
                      strokeDasharray="4 4"
                      strokeWidth={1.3}
                      isAnimationActive={false}
                    />
                  )}
                  {view === "response" && (
                    <Line
                      type="monotone"
                      dataKey="slow"
                      name="84 h term"
                      stroke={theme.slow}
                      dot={false}
                      strokeDasharray="4 4"
                      strokeWidth={1.3}
                      isAnimationActive={false}
                    />
                  )}
                  <ReferenceLine y={0} stroke={theme.muted} />
                  <ReferenceLine
                    x={time}
                    stroke={theme.ochre}
                    label={{
                      value: `${time} h`,
                      position: "insideTopRight",
                      fill: theme.ochre,
                      fontSize: 11,
                    }}
                  />
                  <PlotSelection onSelect={(value) => {
                    if (typeof value === "number" && value >= 0 && value <= 168) {
                      setTime(value);
                      setPlaying(false);
                    }
                  }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <p className="lab-axis-label">
              {view === "response"
                ? "Response · arbitrary units"
                : view === "slope"
                  ? "Derivative · arbitrary units per hour"
                  : "Signed integral from 0 to t · arbitrary units × hours"}
            </p>
            <p className="plot-interaction-hint">Click or tap the plot to set time. The vertical scale adapts to the shown values.</p>
            <div className="lab-time">
              <label htmlFor="lab-time">
                TIME <output htmlFor="lab-time">{time} h</output>
              </label>
              <input
                id="lab-time"
                type="range"
                min="0"
                max="168"
                value={time}
                onChange={(e) => setTime(Number(e.target.value))}
              />
            </div>
            {view === "response" && (
              <div className="chart-legend">
                <span>
                  <i style={{ background: theme.text }} />
                  Combined
                </span>
                <span>
                  <i style={{ background: theme.fast }} />
                  24 h term
                </span>
                <span>
                  <i style={{ background: theme.slow }} />
                  84 h term
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="lab-readout" aria-live="polite" aria-atomic="true">
          <div>
            <span>Current response y(t)</span>
            <strong data-testid="lab-value">
              {decay(time, fast, slow).toFixed(4)}
            </strong>
            <small>sum of the two terms · arbitrary units</small>
          </div>
          <div>
            <span>24 h contribution</span>
            <strong data-testid="fast-term">
              {(fast * Math.exp(-time / 24)).toFixed(4)}
            </strong>
            <small>a e⁻ᵗ/²⁴ · arbitrary units</small>
          </div>
          <div>
            <span>84 h contribution</span>
            <strong data-testid="slow-term">
              {(slow * Math.exp(-time / 84)).toFixed(4)}
            </strong>
            <small>b e⁻ᵗ/⁸⁴ · arbitrary units</small>
          </div>
          <div>
            <span>Instantaneous slope</span>
            <strong data-testid="lab-slope">
              {decaySlope(time, fast, slow).toFixed(6)}
            </strong>
            <small>arbitrary units / hour</small>
          </div>
          <div>
            <span>Area from 0 to {time} h</span>
            <strong data-testid="lab-integral">
              {decayIntegral(time, fast, slow).toFixed(4)}
            </strong>
            <small>signed arbitrary units × hours</small>
          </div>
        </div>
        <details className="methods-sheet">
          <summary>
            Methods & evidence · the mathematics and what it leaves out
          </summary>
          <div className="math-methods">
            <article>
              <h3>Read the derivatives</h3>
              <p className="formula-text">
                y′(t) = −(a/24)e⁻ᵗ/²⁴ − (b/84)e⁻ᵗ/⁸⁴
                <br />
                ∫₀ᵗ y(s)ds = 24a(1−e⁻ᵗ/²⁴) + 84b(1−e⁻ᵗ/⁸⁴)
              </p>
              <p>
                At t = 0, y = a + b. As t grows, both terms approach zero. A
                time constant is not a half-life: at 24 h the fast term retains
                e⁻¹ ≈ 36.8%; its half-life is 24 ln(2) ≈ 16.64 h. The 84 h term
                has a half-life of about 58.22 h.
              </p>
              <p>
                Negative amplitudes illustrate cancellation, zero crossings and
                non-monotonic shapes. This signed sandbox does not obey the
                generator’s amplitude supports. Its area is mathematical area,
                not physiological burden, training dose or a recovery score.
              </p>
            </article>
            <article>
              <h3>Assumption versus evidence</h3>
              <dl>
                <dt>Sandbox assumption</dt>
                <dd>
                  Two additive exponentials with arbitrary signed amplitudes. No
                  participant, exposure, discrepancy or noise model.
                </dd>
                <dt>Active world</dt>
                <dd>
                  Context-conditioned hidden sensitivities and correlated loads,
                  fixed modes and bounded smooth discrepancy.
                </dd>
                <dt>Fitted structured model</dt>
                <dd>
                  Training-estimated exposure coefficients and public
                  context/history. The modes are fixed mathematical choices; a
                  fit does not identify biological compartments.
                </dd>
                <dt>What the experiment supports</dt>
                <dd>
                  The structured comparator beat zero and the training constant
                  on these same-generator roots, but had higher recorded error
                  than full ridge.
                </dd>
              </dl>
              <a
                className="quiet-link"
                href={sourceLink(
                  "src/cmj_recovery_dynamics/dynamics/fixed_mode_discrepancy_response.py",
                )}
              >
                Inspect the full world law ↗
              </a>
            </article>
          </div>
        </details>
        <div className="lab-boundary">
          <span className="boundary-mark">i</span>
          <p>
            <strong>An equation, not an athlete.</strong> This is not predicted
            athlete data, a generator oracle, or reproduced learned-model
            predictions. The curve uses only the public 24-hour and 84-hour
            mathematical anchors; it is separate from the benchmark results
            above.
          </p>
        </div>
      </div>
    </section>
  );
}
