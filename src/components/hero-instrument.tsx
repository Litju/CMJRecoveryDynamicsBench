"use client";
import dynamic from "next/dynamic";
import { Component, useEffect, useRef, useState, type ReactNode } from "react";
import { MoveUpRight } from "lucide-react";
import { decay } from "@/lib/decay.mjs";
const Scene = dynamic(() => import("./instrument-scene"), {
  ssr: false,
  loading: () => <InstrumentFallback />,
});
function InstrumentFallback() {
  return (
    <div className="instrument-fallback" data-testid="instrument-fallback">
      <div className="plate-orbit orbit-one" />
      <div className="plate-orbit orbit-two" />
      <div className="fallback-plate">
        <div className="plate-grid" />
        <span className="plate-core" />
      </div>
      <div className="fallback-shadow" />
    </div>
  );
}
class SceneBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? <InstrumentFallback /> : this.props.children;
  }
}
export default function HeroInstrument() {
  const instrument = useRef<HTMLDivElement>(null);
  const [time, setTime] = useState(24);
  const [render3d, setRender3d] = useState(false);
  const [mode, setMode] = useState("both");
  const fast = mode === "slow" ? 0 : 0.7;
  const slow = mode === "fast" ? 0 : 0.3;
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let nearViewport = false;
    const enable = () => {
      if (!nearViewport || media.matches) {
        setRender3d(false);
        return;
      }
      try {
        const context = document.createElement("canvas").getContext("webgl2");
        setRender3d(!!context);
        context?.getExtension("WEBGL_lose_context")?.loseContext();
      } catch {
        setRender3d(false);
      }
    };
    const observer = new IntersectionObserver(
      ([entry]) => {
        nearViewport = entry.isIntersecting;
        enable();
      },
      { rootMargin: "250px" },
    );
    if (instrument.current) observer.observe(instrument.current);
    media.addEventListener("change", enable);
    return () => {
      observer.disconnect();
      media.removeEventListener("change", enable);
    };
  }, []);
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
        role="img"
        aria-label="Illustrative abstract force plate with exponential impulse field; not measured motion"
      >
        <div className="instrument-cross cross-top">+</div>
        <div className="instrument-cross cross-bottom">+</div>
        <SceneBoundary>
          {render3d ? (
            <Scene time={time} fast={fast} slow={slow} />
          ) : (
            <InstrumentFallback />
          )}
        </SceneBoundary>
        <div className="instrument-coordinate">
          X / FORCE
          <br />Y / RESPONSE
          <br />T / TIME
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
        <br />
        Height follows the equation; spatial geometry is decorative. Not
        measured motion or model predictions.
      </p>
    </div>
  );
}
