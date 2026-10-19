"use client";
import dynamic from "next/dynamic";
import { Component, useEffect, useState, type ReactNode } from "react";
import { MoveUpRight } from "lucide-react";
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
  const [time, setTime] = useState(24);
  const [render3d, setRender3d] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const enable = () => {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("webgl2");
      setRender3d(!media.matches && !!context);
      context?.getExtension("WEBGL_lose_context")?.loseContext();
    };
    const timer = window.setTimeout(enable, 650);
    media.addEventListener("change", enable);
    return () => {
      window.clearTimeout(timer);
      media.removeEventListener("change", enable);
    };
  }, []);
  return (
    <div className="hero-instrument">
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
          {render3d ? <Scene time={time} /> : <InstrumentFallback />}
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
        A mathematical visualization. Not measured motion or model predictions.
      </p>
    </div>
  );
}
