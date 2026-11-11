"use client";
import { useEffect, useState } from "react";
import { CHAPTERS } from "@/components/science/chapter-head";

export default function StoryProgress() {
  const [active, setActive] = useState<string>("ch1");
  useEffect(() => {
    // Every section of the story belongs to one of the seven chapters.
    const owner: Record<string, string> = {
      question: "ch1",
      world: "ch2",
      lab: "ch2",
      "architecture-progression": "ch3",
      experiment: "ch4",
      explorer: "ch5",
      conclusions: "ch6",
      remaining: "ch6",
      lineage: "ch7",
      evidence: "ch7",
    };
    const ids = [...CHAPTERS.map(({ id }) => id as string), ...Object.keys(owner)];
    const sections = ids.map((id) => document.getElementById(id)).filter(Boolean) as HTMLElement[];
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActive(owner[entry.target.id] ?? entry.target.id);
            entry.target.setAttribute("data-entered", "true");
          }
        }
      },
      { rootMargin: "-15% 0px -55% 0px" },
    );
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);
  return (
    <nav className="story-progress" aria-label="Research story chapters">
      <div className="shell">
        {CHAPTERS.map((c) => (
          <a key={c.id} href={`#${c.id}`} aria-current={active === c.id ? "step" : undefined}>
            <span>0{c.n}</span> {c.label}
          </a>
        ))}
      </div>
    </nav>
  );
}
