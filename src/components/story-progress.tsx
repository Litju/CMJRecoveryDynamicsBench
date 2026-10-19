"use client";
import { useEffect, useState } from "react";
import { acts } from "@/lib/story";

export default function StoryProgress() {
  const [active, setActive] = useState<string>("question");
  useEffect(() => {
    const sectionActs: Record<string, string> = {
      explorer: "experiment",
      lab: "remaining",
      evidence: "remaining",
    };
    const sections = [
      ...acts.map(({ id }) => id),
      ...Object.keys(sectionActs),
    ].map((id) => document.getElementById(id)!);
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActive(sectionActs[entry.target.id] ?? entry.target.id);
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
        {acts.map((act, i) => (
          <a
            key={act.id}
            href={`#${act.id}`}
            aria-current={active === act.id ? "step" : undefined}
          >
            <span>0{i + 1}</span> {act.label}
          </a>
        ))}
      </div>
    </nav>
  );
}
