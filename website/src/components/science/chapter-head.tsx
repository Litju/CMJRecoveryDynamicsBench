import type { ReactNode } from "react";

export const CHAPTERS = [
  { id: "ch1", n: 1, label: "What a jump measures", q: "What does a countermovement jump measure?" },
  { id: "ch2", n: 2, label: "After exposure", q: "What happens after training exposure?" },
  { id: "ch3", n: 3, label: "Modeling it", q: "How do we model that process?" },
  { id: "ch4", n: 4, label: "The experiment", q: "How was the synthetic experiment designed?" },
  { id: "ch5", n: 5, label: "What was predicted", q: "What did the models actually predict?" },
  { id: "ch6", n: 6, label: "Conclusions", q: "What can we conclude?" },
  { id: "ch7", n: 7, label: "Verification", q: "How was the research verified?" },
] as const;

export default function ChapterHead({ id, children }: { id: (typeof CHAPTERS)[number]["id"]; children?: ReactNode }) {
  const c = CHAPTERS.find((x) => x.id === id)!;
  return (
    <section id={id} className="shell sci-chapter-head" aria-labelledby={`${id}-title`}>
      <p className="pub-eyebrow">Chapter {c.n} of 7</p>
      <h2 id={`${id}-title`} className="editorial-heading">
        {c.q}
      </h2>
      {children && <div className="pub-lede">{children}</div>}
    </section>
  );
}
