"use client";
import { useState } from "react";
import {
  ArrowDown,
  ArrowUpRight,
  Footprints,
  Activity,
  Timer,
  Layers3,
} from "lucide-react";
import context from "@/data/context.json";
import { sourceLink } from "@/lib/science";

const readings = [
  {
    id: "force",
    label: "01 / Mean force",
    title: "How forcefully was the push expressed?",
    unit: "N/kg",
    symbol: "F̄ / m",
    formula: "Mean relative force = (1 / T) ∫ (F(t) / m) dt",
    what: "The force plate records vertical ground-reaction force. Divide by body mass and average over the concentric push-off phase.",
    why: "It describes the average force expressed during that phase. It is a mechanical measurement, not a direct measurement of fatigue or readiness.",
    how: "Use one consistently defined phase. Here, concentric onset is the lowest centre-of-mass point where vertical velocity changes from non-positive to positive; the phase ends at take-off.",
  },
  {
    id: "impulse",
    label: "02 / Net impulse",
    title: "What was the net effect of that push over time?",
    unit: "m/s",
    symbol: "J / m",
    formula: "J / m = ∫ (F(t) / m − g) dt = (F̄ / m − g) T",
    what: "Subtract gravitational acceleration from the force-per-mass signal, then integrate over the same concentric phase. Time is part of this measurement.",
    why: "Two pushes with the same mean force can produce different net impulses if their durations differ. This quantity captures the net change in vertical velocity over the phase.",
    how: "Force and impulse must describe the same movement interval. The phase-consistent formulation enforces that relationship, rather than constructing unrelated scalar outcomes.",
  },
  {
    id: "innovation",
    label: "03 / Change from baseline",
    title: "What changed after the exposure?",
    unit: "same units as the outcome",
    symbol: "ΔY(h)",
    formula: "Innovation at horizon h = assessment(h) − pre-exposure baseline",
    what: "The prediction target is a difference from a dedicated pre-exposure assessment. There is one force innovation and one net-impulse innovation at each requested horizon.",
    why: "Predicting change asks a more specific question than predicting an absolute measurement: what does this known exposure and observed history tell us about the later assessment?",
    how: "The active synthetic observation averages three valid paired trials per assessment. The same baseline is the reference for H24, H48 and H72. Zero innovation means no change from baseline, not zero force.",
  },
] as const;

export default function MeasurementExhibit() {
  const [selected, setSelected] =
    useState<(typeof readings)[number]["id"]>("force");
  const reading = readings.find((r) => r.id === selected)!;
  const curve = Array.from(
    { length: 65 },
    (_, i) =>
      `${i ? "L" : "M"}${55 + i * 8},${175 - 95 * Math.sin((Math.PI * i) / 64)}`,
  ).join(" ");
  return (
    <div className="measurement-exhibit" id="measurement">
      <div className="measurement-intro">
        <span className="eyebrow">THE APPARATUS / THE OBSERVABLES</span>
        <h3>
          A force plate.
          <br />
          <em>Two connected measurements.</em>
        </h3>
        <p>
          A countermovement jump starts with a downward movement, followed by an
          upward push and take-off. This benchmark focuses on the concentric
          push: from the lowest point to leaving the plate.
        </p>
      </div>
      <div className="apparatus-chain" aria-label="Measurement process">
        <div>
          <Footprints size={28} />
          <span>01 / PERFORM</span>
          <strong>Countermovement jump</strong>
          <small>Lower, push upward, take off.</small>
        </div>
        <ArrowDown className="chain-arrow" size={20} />
        <div>
          <Activity size={28} />
          <span>02 / RECORD</span>
          <strong>Vertical force over time</strong>
          <small>Force plate → force / body mass.</small>
        </div>
        <ArrowDown className="chain-arrow" size={20} />
        <div>
          <Timer size={28} />
          <span>03 / DEFINE</span>
          <strong>One concentric interval</strong>
          <small>Both outcomes use the same phase.</small>
        </div>
        <ArrowDown className="chain-arrow" size={20} />
        <div>
          <Layers3 size={28} />
          <span>04 / AGGREGATE</span>
          <strong>Three valid paired trials</strong>
          <small>Assessment = arithmetic means.</small>
        </div>
      </div>
      <div className="measurement-workbench">
        <div
          className="measurement-tabs"
          role="group"
          aria-label="What are we measuring?"
        >
          {readings.map((r) => (
            <button
              key={r.id}
              aria-pressed={selected === r.id}
              onClick={() => setSelected(r.id)}
            >
              {r.label}
              <ArrowUpRight size={14} />
            </button>
          ))}
        </div>
        <div className={`measurement-reading reading-${selected}`}>
          <div className="measurement-plot">
            <div className="measurement-plot-heading">
              <span>
                {selected === "innovation"
                  ? "THE FORECAST TARGET"
                  : "THE SAME PUSH-OFF PHASE"}
              </span>
              <strong>
                {reading.symbol}
                <small>{reading.unit}</small>
              </strong>
            </div>
            {selected !== "innovation" ? (
              <svg
                viewBox="0 0 640 265"
                role="img"
                aria-label={`Schematic force-time diagram, not an athlete trial. ${selected === "force" ? "Mean force averages the force over the phase." : "The area above the gravity reference represents net impulse."}`}
              >
                {[55, 115, 175, 225].map((y) => (
                  <line
                    key={y}
                    x1="55"
                    x2="570"
                    y1={y}
                    y2={y}
                    stroke="#c9cec9"
                    strokeDasharray="2 5"
                  />
                ))}
                <path
                  d={
                    selected === "force"
                      ? `M55 225 L55 175 ${curve.replace("M", "L")} L567 225 Z`
                      : `${curve} L55 175 Z`
                  }
                  fill={selected === "force" ? "#dce5f6" : "#f6ded4"}
                />
                <line x1="55" x2="567" y1="175" y2="175" stroke="#656b72" />
                <path
                  d={curve}
                  fill="none"
                  stroke={selected === "force" ? "#2854b8" : "#b6422b"}
                  strokeWidth="3"
                />
                {selected === "force" && (
                  <line
                    x1="55"
                    x2="567"
                    y1="114.5"
                    y2="114.5"
                    stroke="#2854b8"
                    strokeDasharray="6 5"
                  />
                )}
                <text
                  x="570"
                  y="170"
                  textAnchor="end"
                  fill="#545b63"
                  fontSize="12"
                >
                  gravity reference g
                </text>
                <text x="55" y="247" fill="#545b63" fontSize="12">
                  Concentric onset
                </text>
                <text
                  x="567"
                  y="247"
                  textAnchor="end"
                  fill="#545b63"
                  fontSize="12"
                >
                  Take-off
                </text>
                <text x="10" y="35" fill="#545b63" fontSize="11">
                  F/m
                </text>
                <text
                  x="320"
                  y="263"
                  textAnchor="middle"
                  fill="#545b63"
                  fontSize="11"
                >
                  Normalised phase time · schematic shape
                </text>
              </svg>
            ) : (
              <div className="innovation-diagram">
                <div>
                  <span>AT H24 / H48 / H72</span>
                  <strong>
                    Y<sub>horizon</sub>
                  </strong>
                  <small>Held out at forecast time</small>
                </div>
                <span className="innovation-minus">−</span>
                <div>
                  <span>BEFORE EXPOSURE</span>
                  <strong>
                    Y<sub>baseline</sub>
                  </strong>
                  <small>Already observed</small>
                </div>
                <p>ΔY = later assessment − baseline</p>
              </div>
            )}
            <p className="measurement-schematic-note">
              {selected === "innovation"
                ? "Symbolic label construction. No individual measurements or predictions are shown."
                : "Illustrative normalised half-sine shape; no recorded trial, generated sample or fitted prediction is shown."}
            </p>
          </div>
          <article
            className="measurement-explanation"
            aria-live="polite"
            aria-atomic="true"
          >
            <span className="eyebrow">WHAT / WHY / HOW</span>
            <h4>{reading.title}</h4>
            <dl>
              <dt>What is it?</dt>
              <dd>{reading.what}</dd>
              <dt>Why keep it?</dt>
              <dd>{reading.why}</dd>
              <dt>How is it constructed here?</dt>
              <dd>{reading.how}</dd>
            </dl>
          </article>
          <p className="measurement-equation" aria-live="polite">
            {reading.formula}
          </p>
        </div>
      </div>
      <div className="measurement-footnote">
        <span>
          g = {context.gravity} m/s². The synthetic contract uses{" "}
          {context.trials} valid paired trials with {context.traceNodes} nodes
          per trial. The force–impulse identity applies per trial; assessments
          average the three outcomes separately.
        </span>
        <a href={sourceLink(context.source)}>
          Inspect the observation law <ArrowUpRight size={13} />
        </a>
      </div>
      <div className="measurement-takeaway">
        <strong>
          A measurement is an observable. Recovery is an interpretation.
        </strong>
        <p>
          A change can reflect response, measurement variability and the
          assumptions of the world producing it. This project tests forecasting
          under explicit synthetic assumptions; it does not turn a jump into an
          athlete diagnosis.
        </p>
      </div>
    </div>
  );
}

export function ExposureContext() {
  const [selected, setSelected] = useState("volume");
  const group = context.exposures.find((e) => e.id === selected)!;
  return (
    <div className="exposure-context">
      <div>
        <span className="eyebrow">
          WHAT DOES “TRAINING EXPOSURE” MEAN HERE?
        </span>
        <h3>
          A session becomes
          <br />
          <em>eight public descriptors.</em>
        </h3>
        <p>
          Duration, running distances, changes of speed and perceived effort
          describe the current exposure. The model is given those recorded
          descriptors; the generator's hidden response effects stay hidden.
        </p>
        <a className="quiet-link" href={sourceLink(context.exposureSource)}>
          Inspect the exposure construction ↗
        </a>
      </div>
      <div className="exposure-glossary">
        <div role="group" aria-label="Training exposure dimensions">
          {context.exposures.map((e) => (
            <button
              key={e.id}
              aria-pressed={selected === e.id}
              onClick={() => setSelected(e.id)}
            >
              {e.label}
            </button>
          ))}
        </div>
        <article aria-live="polite" aria-atomic="true">
          <span className="eyebrow">{group.label.toUpperCase()}</span>
          <p>{group.text}</p>
          <dl>
            {group.fields.map((f) => (
              <div key={f.name}>
                <dt>{f.label}</dt>
                <dd>
                  {f.unit}
                  <code>{f.name}</code>
                </dd>
              </div>
            ))}
          </dl>
        </article>
      </div>
    </div>
  );
}
