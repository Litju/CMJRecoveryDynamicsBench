"use client";
import dynamic from "next/dynamic";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { SceneBoundary, useWebGL } from "./scene-availability";
import { sourceLink } from "@/lib/science";
import { plotTheme as theme } from "@/lib/plot-theme.mjs";
import { decaySeries } from "@/lib/decay.mjs";
import { chapters, journeyBars } from "@/lib/journey";
import { lineage } from "@/lib/story";
const Scene = dynamic(() => import("./journey-scene"), { ssr: false });
function Diagram({ kind }: {
    kind: string;
}) {
    const paths = decaySeries(0.7, 0.3);
    return <svg className="journey-fallback" viewBox="0 0 440 300" role="img" aria-label={kind === "benchmark" ? "Four sourced 24 hour force NRMSE values. Lower is better." : "Scientific schematic. No measured athlete data."}>
    {kind === "benchmark" ? journeyBars.map((m, i) => <g key={m.id}><rect x={65 + i * 85} y={245 - m.value * 40} width="44" height={m.value * 40} fill={m.color}/><text x={87 + i * 85} y={230 - m.value * 40} textAnchor="middle" fill={theme.text} fontSize="12">{m.value.toFixed(4)}</text><text x={87 + i * 85} y="267" textAnchor="middle" fill={theme.muted} fontSize="11">{m.short}</text></g>) : kind === "response" ? (["total", "fast", "slow"] as const).map((key) => <path key={key} d={paths.map((p, i) => `${i ? "L" : "M"}${40 + p.time * 2.1},${240 - p[key] * 180}`).join(" ")} stroke={key === "total" ? theme.text : theme[key]} fill="none" strokeWidth="3"/>) : kind === "lineage" ? Array.from({ length: 8 }, (_, i) => <g key={i}>{lineage[i].parent && <line x1={50 + lineage.findIndex((n) => n.id === lineage[i].parent) * 46} x2={50 + i * 46} y1={150 + (lineage.findIndex((n) => n.id === lineage[i].parent) % 2) * 35} y2={150 + (i % 2) * 35} stroke={theme.grid}/>}<circle cx={50 + i * 46} cy={150 + (i % 2) * 35} r="13" fill={i === 7 ? theme.slow : theme.fast}/><text x={50 + i * 46} y="215" fill={theme.muted} textAnchor="middle" fontSize="12">0{i + 1}</text></g>) : <g stroke={theme.ink} fill="none" strokeWidth="5"><path d="M160 230h120l25 20H135Z" fill={theme.grid}/><circle cx="220" cy="75" r="19"/><path d="M220 95v60l-35 35 10 35m25-70 35 35-10 35m-25-115-45 25m45-25 45 25"/><path d="M300 220V100m-12 15 12-15 12 15" stroke={theme.fast}/><text x="315" y="160" fill={theme.fast} stroke="none" fontSize="15">F</text></g>}
  </svg>;
}
export default function ScrollJourney({ children }: {
    children: ReactNode;
}) {
    const [position, setPosition] = useState({ chapter: 0, progress: 0, total: 0 });
    const [drag, setDrag] = useState(false);
    const [paused, setPaused] = useState(false);
    const [frozenProgress, setFrozenProgress] = useState(0);
    const root = useRef<HTMLDivElement>(null);
    const { ref, ready, reason, onUnavailable } = useWebGL();
    useEffect(() => {
        let frame = 0;
        const update = () => {
            frame = 0;
            const readingEdge = window.innerWidth <= 1100
                ? (ref.current?.getBoundingClientRect().bottom ?? 280) + 32
                : window.innerHeight * 0.35;
            const y = window.scrollY + readingEdge;
            const sections = chapters.map((c) => document.getElementById(c.id));
            let index = 0;
            sections.forEach((section, i) => { if (section && section.getBoundingClientRect().top + window.scrollY <= y)
                index = i; });
            const current = sections[index];
            const next = sections[index + 1];
            const start = current ? current.getBoundingClientRect().top + window.scrollY : 0;
            const end = next ? next.getBoundingClientRect().top + window.scrollY : document.documentElement.scrollHeight;
            setPosition({ chapter: index, progress: Math.max(0, Math.min(1, (y - start) / Math.max(1, end - start))), total: Math.max(0, Math.min(1, window.scrollY / Math.max(1, document.documentElement.scrollHeight - window.innerHeight))) });
        };
        const schedule = () => { if (!frame)
            frame = requestAnimationFrame(update); };
        const reveal = new IntersectionObserver((entries) => entries.forEach((entry) => { if (entry.isIntersecting)
            entry.target.setAttribute("data-entered", "true"); }), { threshold: 0.05 });
        root.current?.querySelectorAll("section, .quick-route").forEach((section) => reveal.observe(section));
        window.addEventListener("scroll", schedule, { passive: true });
        window.addEventListener("resize", schedule);
        update();
        return () => { cancelAnimationFrame(frame); reveal.disconnect(); window.removeEventListener("scroll", schedule); window.removeEventListener("resize", schedule); };
    }, []);
    const chapter = chapters[position.chapter];
    const progress = paused || drag ? frozenProgress : position.progress;
    return <div className="scroll-journey" ref={root}>
    <aside className="journey-stage" aria-label="Scroll-driven scientific exhibition" ref={ref} data-chapter={chapter.id} data-progress={position.progress}>
      <div className="journey-stage-heading"><span>CMJ / FIELD NOTES</span><span>{String(position.chapter + 1).padStart(2, "0")} / 09</span></div>
      <h2>{chapter.title}</h2>
      <div className="journey-viewport" role="group" aria-label={`${chapter.label}: interactive 3D scientific illustration`}>
        <SceneBoundary onError={onUnavailable} fallback={<Diagram kind={chapter.kind}/>}>{ready ? <Scene kind={chapter.kind} progress={progress} drag={drag} onUnavailable={onUnavailable} onModel={(id) => {
                document.querySelector<HTMLButtonElement>(`#explorer button[data-model-id="${id}"]`)?.click();
                document.getElementById("explorer")?.scrollIntoView({ block: "start" });
            }} onFormulation={(id) => {
                const button = document.querySelector<HTMLButtonElement>(`[data-formulation="${id}"] > button`);
                button?.click();
                button?.scrollIntoView({ block: "center" });
            }}/> : <Diagram kind={chapter.kind}/>}</SceneBoundary>
        <span className="journey-visual-note">{chapter.kind === "benchmark" ? "24 h FORCE · NRMSE · THREE-ROOT MEAN" : chapter.kind === "response" ? "MATHEMATICAL ILLUSTRATION · NOT FITTED DATA" : chapter.kind === "lineage" ? "EIGHT CONTRACTS · FIVE DOCUMENTED EDGES" : "SCHEMATIC APPARATUS · NO HUMAN DATA"}</span>
      </div>
      <div className="journey-stage-copy"><p>{chapter.note}</p><a href={sourceLink(chapter.source)}>Inspect the source ↗</a></div>
      <div className="journey-interactions"><span>{ready ? "SCROLL TO EXPLORE" : reason}</span><button aria-pressed={paused} onClick={() => { setFrozenProgress(progress); setPaused(!paused); setDrag(false); }} disabled={!ready}>{paused ? "Resume motion" : "Pause motion"}</button><button aria-pressed={drag} onClick={() => { setFrozenProgress(progress); setDrag(!drag); }} disabled={!ready}>{drag ? "Release scene" : "Rotate scene"}</button></div>
      <nav className="journey-index" aria-label="Exhibition chapters">{chapters.map((c, i) => <a href={`#${c.id}`} key={c.id} aria-current={i === position.chapter ? "step" : undefined}><span>{String(i + 1).padStart(2, "0")}</span>{c.label}</a>)}</nav>
      <div className="journey-progress" aria-hidden="true"><span style={{ transform: `scaleX(${position.total})` }}/></div>
    </aside>
    <div className="journey-content">{children}</div>
  </div>;
}
