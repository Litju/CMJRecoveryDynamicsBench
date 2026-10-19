"use client";
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
import { decay, decaySeries } from "@/lib/decay.mjs";
export default function RecoveryLab() {
  const [fast, setFast] = useState(0.7);
  const [slow, setSlow] = useState(0.3);
  const [time, setTime] = useState(24);
  const [playing, setPlaying] = useState(false);
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
  };
  const series = decaySeries(fast, slow);
  return (
    <section id="lab" className="lab-section" aria-labelledby="lab-title">
      <div className="shell section">
        <div className="section-top">
          <div className="eyebrow">
            <span className="section-number">02</span> THE RECOVERY LAB
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
                min="0"
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
                min="0"
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
            <div className="lab-plot-title">
              <span className="panel-label">ILLUSTRATIVE RESPONSE</span>
              <div>
                <output data-testid="lab-value">
                  {decay(time, fast, slow).toFixed(4)}
                </output>
                <span> at {time} h</span>
              </div>
            </div>
            <div
              className="lab-chart"
              role="group"
              aria-label="Two-term decay illustration. The current value and equation are displayed as text."
            >
              <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <ComposedChart
                  data={series}
                  margin={{ top: 15, right: 20, bottom: 8, left: 0 }}
                  accessibilityLayer
                >
                  <defs>
                    <linearGradient id="decay-fill" x1="0" x2="0" y1="0" y2="1">
                      <stop
                        offset="0%"
                        stopColor="#a9f5dc"
                        stopOpacity={0.18}
                      />
                      <stop offset="100%" stopColor="#a9f5dc" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    stroke="#2a3436"
                    vertical={false}
                    strokeDasharray="3 6"
                  />
                  <XAxis
                    dataKey="time"
                    type="number"
                    domain={[0, 168]}
                    ticks={[0, 24, 48, 72, 96, 120, 144, 168]}
                    tickFormatter={(v) => `${v}h`}
                    stroke="#a1aaa9"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis
                    domain={[0, 3]}
                    ticks={[0, 1, 2, 3]}
                    stroke="#a1aaa9"
                    tickLine={false}
                    axisLine={false}
                    width={35}
                    tick={{ fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#1b2528",
                      border: "1px solid #465651",
                      borderRadius: 8,
                      color: "#f0f4f1",
                      fontSize: 12,
                    }}
                    labelFormatter={(v) => `${v} hours`}
                    formatter={(v) => Number(v).toFixed(4)}
                  />
                  <Area
                    type="monotone"
                    dataKey="total"
                    name="Combined response"
                    fill="url(#decay-fill)"
                    stroke="#d9f7e9"
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="fast"
                    name="24 h term"
                    stroke="#a9f5dc"
                    dot={false}
                    strokeDasharray="4 4"
                    strokeWidth={1.3}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="slow"
                    name="84 h term"
                    stroke="#aaa5ef"
                    dot={false}
                    strokeDasharray="4 4"
                    strokeWidth={1.3}
                    isAnimationActive={false}
                  />
                  <ReferenceLine
                    x={time}
                    stroke="#c3f6df"
                    label={{
                      value: `${time} h`,
                      position: "insideTopRight",
                      fill: "#c3f6df",
                      fontSize: 11,
                    }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
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
            <div className="chart-legend">
              <span>
                <i style={{ background: "#d9f7e9" }} />
                Combined
              </span>
              <span>
                <i style={{ background: "#a9f5dc" }} />
                24 h term
              </span>
              <span>
                <i style={{ background: "#aaa5ef" }} />
                84 h term
              </span>
            </div>
          </div>
        </div>
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
