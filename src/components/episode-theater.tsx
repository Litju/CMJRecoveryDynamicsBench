"use client";
import { useEffect, useState } from "react";
import { ArrowDown, ArrowUpRight, Eye, LockKeyhole, Pause, Play, RotateCcw } from "lucide-react";
import exhibit from "@/data/exhibition.json";
import { sourceLink } from "@/lib/science";
import { decay } from "@/lib/decay.mjs";

export default function EpisodeTheater() {
  const [step, setStep] = useState(2);
  const [playing, setPlaying] = useState(false);
  const [perspective, setPerspective] = useState("model");
  const [layer, setLayer] = useState("predictor");
  const event = exhibit.events[step];
  const activeLayer = exhibit.layers.find(l => l.id === layer)!;
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(() => setStep(s => Math.min(s + 1, 5)), 1600);
    return () => clearInterval(timer);
  }, [playing]);
  useEffect(() => { if (step === 5) setPlaying(false); }, [step]);
  useEffect(() => {
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const stop = () => setPlaying(false);
    const hide = () => { if (document.hidden) stop(); };
    media.addEventListener("change", stop);
    document.addEventListener("visibilitychange", hide);
    return () => { media.removeEventListener("change", stop); document.removeEventListener("visibilitychange", hide); };
  }, []);
  const choose = (index: number) => { setStep(index); setPlaying(false); };
  const reset = () => { choose(2); setPerspective("model"); setLayer("predictor"); };
  const path = Array.from({ length: 73 }, (_, h) => `${h ? 'L' : 'M'}${430 + h * 6.4},${265 - decay(h, .7, .3) * 150}`).join(' ');
  return (
    <section id="world" className="shell section story-act world-act" aria-labelledby="world-title">
      <div className="eyebrow"><span className="section-number">I / INSIDE THE WORLD</span> THE EPISODE THEATER</div>
      <div className="exhibit-heading"><h2 id="world-title" className="editorial-heading">The world knows more.<br /><span>The model must know less.</span></h2><p>Walk through one conceptual episode. Move past the forecast origin. See what changes—and what the model is still forbidden to use.</p></div>
      <div className="episode-panel">
        <div className="episode-toolbar">
          <span className="panel-label">01 / ONE EXPOSURE · THREE HORIZONS</span>
          <fieldset className="perspective-control"><legend className="sr-only">Episode perspective</legend><div className="segmented">
            <button aria-pressed={perspective === 'model'} onClick={() => setPerspective('model')}><LockKeyhole size={14} /> Model at origin</button>
            <button aria-pressed={perspective === 'observer'} onClick={() => setPerspective('observer')}><Eye size={14} /> Later observer</button>
          </div></fieldset>
        </div>
        <div className="episode-scene" data-perspective={perspective} data-layer={layer}>
          <div className="episode-scene-label"><span>INFORMATION AVAILABLE AT ORIGIN</span><span>CURRENT FUTURE · HELD OUT</span></div>
          <svg viewBox="0 0 1000 330" role="img" aria-labelledby="episode-svg-title episode-svg-desc">
            <title id="episode-svg-title">A conceptual episode and its forecast boundary</title>
            <desc id="episode-svg-desc">Four prior episodes and a pre-exposure baseline are available. The origin divides known inputs from future assessments at 24, 48 and 72 hours. The curve is an arbitrary two-mode mathematical illustration, not a generated sample.</desc>
            <defs><linearGradient id="episode-glow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#a9f5dc" stopOpacity=".16" /><stop offset="1" stopColor="#a9f5dc" stopOpacity="0" /></linearGradient></defs>
            {[95,180,265].map(y => <line key={y} x1="35" x2="960" y1={y} y2={y} stroke="#2d3c3d" strokeDasharray="3 8" />)}
            <rect x="430" y="30" width="510" height="260" fill="#a9f5dc" opacity=".025" />
            <line x1="430" x2="430" y1="35" y2="295" stroke="#a9f5dc" strokeDasharray="5 5" />
            <text x="445" y="52" fill="#a9f5dc" fontSize="12">FORECAST BOUNDARY / t = 0</text>
            {[0,1,2,3].map(i => <g key={i} opacity={layer === 'predictor' ? 1 : .5}><rect x={48+i*38} y={175-i%2*15} width="24" height={65+i%2*15} rx="4" fill="#28463e" stroke="#7ebba7" /><line x1={55+i*38} x2={65+i*38} y1="195" y2="195" stroke="#a9f5dc" /></g>)}
            <text x="44" y="273" fill="#a6b0ae" fontSize="12">4 PRIOR RECORDS</text>
            <g><path d="M235 240 L235 200 L260 184 L285 200 L285 240 Z" fill="#28463e" stroke="#a9f5dc" /><text x="223" y="273" fill="#a6b0ae" fontSize="12">BASELINE</text></g>
            <path d="M400 240 L420 240 L430 100 L440 240 L460 240" fill="none" stroke="#a9f5dc" strokeWidth="2" />
            <text x="394" y="315" fill="#a9f5dc" fontSize="12">EXPOSURE</text>
            {layer === 'world' && <g><path d={`${path} L891 265 L430 265 Z`} fill="url(#episode-glow)" /><path d={path} fill="none" stroke="#aaa5ef" strokeWidth="2" /><text x="560" y="112" fill="#c6c1ff" fontSize="13">ILLUSTRATIVE y(t) = 0.7e⁻ᵗ/²⁴ + 0.3e⁻ᵗ/⁸⁴</text><text x="560" y="133" fill="#a6b0ae" fontSize="12">arbitrary units · not a generated response</text></g>}
            {[24,48,72].map((h, i) => {
              const revealed = perspective === 'observer' && step >= i+3;
              return <g key={h} opacity={revealed ? 1 : .42}><line x1={600+i*160} x2={600+i*160} y1="190" y2="270" stroke={revealed ? '#a9f5dc' : '#a6b0ae'} strokeDasharray={revealed ? undefined : '3 5'} /><circle cx={600+i*160} cy="225" r="17" fill="#172522" stroke={revealed ? '#a9f5dc' : '#a6b0ae'} /><text x={600+i*160} y="230" textAnchor="middle" fill="#eef2ef" fontSize="14">{revealed ? '✓' : '?'}</text><text x={600+i*160} y="292" textAnchor="middle" fill="#eef2ef" fontSize="13">{h} h</text></g>;
            })}
            <circle cx={event.position*10} cy="75" r="5" fill="#a9f5dc" />
          </svg>
          <p className="episode-boundary" aria-live="polite">{perspective === 'model' ? 'Origin view: future outcomes are withheld at every timeline position.' : 'Observer view: later assessments can be revealed. They remain excluded from the original forecast.'}</p>
        </div>
        <div className="episode-events" role="group" aria-label="Episode events">
          {exhibit.events.map((e,i) => <button key={e.id} onClick={() => choose(i)} aria-pressed={step === i} data-event={e.id} data-predictor={e.available}><span className="event-dot">{e.available ? '•' : <LockKeyhole size={12} />}</span><strong>{e.label}</strong><small>{e.time === null ? 'schematic spacing' : e.time === 0 ? 'information cutoff' : `${e.time} hours`}</small></button>)}
        </div>
        <div className="episode-transport"><button className="button secondary" aria-pressed={playing} onClick={() => { if(step === 5) setStep(0); setPlaying(p => !p); }}>{playing ? <Pause size={14}/> : <Play size={14}/>} {playing ? 'Pause episode' : 'Play episode'}</button><label className="sr-only" htmlFor="episode-time">Episode timeline</label><input id="episode-time" type="range" min="0" max="5" value={step} aria-valuetext={event.label} onChange={e => choose(Number(e.target.value))}/><button className="reset-button" onClick={reset}><RotateCcw size={14}/> Reset episode</button></div>
        <div className="episode-caption" aria-live="polite" aria-atomic="true"><span className="eyebrow">SCENE {String(step+1).padStart(2,'0')} / {event.available ? 'AVAILABLE AT ORIGIN' : 'TARGET ONLY'}</span><h3>{event.title}</h3><p>{event.text}</p></div>
      </div>
      <div className="layer-exhibit">
        <div role="group" aria-label="Information layers" className="layer-choices">{exhibit.layers.map((l,i) => <button key={l.id} aria-pressed={layer === l.id} onClick={() => setLayer(l.id)}><span className="mono">0{i+1}</span>{l.label}<span aria-hidden="true">↗</span></button>)}</div>
        <article className="layer-detail" aria-live="polite"><span className="eyebrow">PEEL BACK A LAYER / {activeLayer.label.toUpperCase()}</span><h3>{activeLayer.title}</h3><p>{activeLayer.text}</p><a className="quiet-link" href={sourceLink(activeLayer.source)}>Inspect the source <ArrowUpRight size={14}/></a></article>
      </div>
      <details className="methods-sheet"><summary>Methods & evidence · the complete predictor budget</summary><div className="feature-budget">{exhibit.predictors.map(p => <article key={p.id}><strong>{p.count}</strong><h4>{p.label}</h4><p>{p.text}</p></article>)}</div><p className="method-note">1 + 3 + 2 + 8 + (4 × 17) = 82 public fields → 84 encoded ridge columns. The known horizon is one-hot encoded. Labels and identity keys are excluded. Current-episode future outcomes never become prior history for this query.</p><p className="method-note">In the active observation contract, force and net impulse integrate the same concentric phase: J/m = (F̄/m − g)T, g = 9.80665 m/s². Each of three valid trials has 65 trace nodes; assessment means are used. No raw trial trace is supplied by this exhibit.</p><a className="quiet-link" href={sourceLink(exhibit.source)}>Frozen feature and split protocol ↗</a></details>
      <div className="world-cards-heading"><span className="eyebrow">SAME RESEARCH PROGRAM / DIFFERENT ASSUMPTIONS</span><h3>Change the world. Change what you can claim.</h3></div>
      <div className="world-cards">{exhibit.worlds.map(w => <a href={`?formulation=${w.id}#lineage`} key={w.id}><span className="small-tag">{w.category}</span><h4>{w.label} <ArrowUpRight size={16}/></h4><p>{w.text}</p></a>)}</div>
      <p className="story-caption">{exhibit.scope} The scene shows information flow; it performs no inference. The preseason family asks a different H72 / D7 question.</p>
      <a href="#lineage" className="quiet-link chapter-next">Follow the scientific branches <ArrowDown size={16}/></a>
    </section>
  );
}
