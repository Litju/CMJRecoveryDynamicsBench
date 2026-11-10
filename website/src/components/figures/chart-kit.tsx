"use client";
// Shared SVG chart primitives for manuscript-linked figures. Presentation is set as
// SVG attributes so exported files keep it; CSS only styles the surrounding HTML.
import { useCallback, useRef, useState, type ReactNode } from "react";
import { plotTheme } from "@/lib/plot-theme.mjs";

export const INK = plotTheme.ink;
export const MUTED = plotTheme.muted;
export const GRID = plotTheme.grid;
export const SURFACE = plotTheme.surface;
export const FONT = "Georgia, 'Times New Roman', serif";
export const SANS = "Geist, 'Segoe UI', Arial, sans-serif";

export type Scale = ((v: number) => number) & { domain: [number, number]; range: [number, number] };
export function linear(domain: [number, number], range: [number, number]): Scale {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const f = ((v: number) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0)) as Scale;
  f.domain = domain;
  f.range = range;
  return f;
}
export function log10(domain: [number, number], range: [number, number]): Scale {
  const inner = linear([Math.log10(domain[0]), Math.log10(domain[1])], range);
  const f = ((v: number) => inner(Math.log10(v))) as Scale;
  f.domain = domain;
  f.range = range;
  return f;
}
export function ticks(min: number, max: number, count = 5) {
  const step0 = (max - min) / count;
  const mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= step0) ?? mag * 10;
  const out: number[] = [];
  for (let v = Math.ceil(min / step - 1e-9) * step; v <= max + 1e-9; v += step)
    out.push(Number(v.toFixed(10)));
  return out;
}

export function Marker({
  shape,
  x,
  y,
  r = 5,
  fill,
  stroke = SURFACE,
  strokeWidth = 1.5,
  opacity = 1,
}: {
  shape: "circle" | "square" | "triangle" | "diamond";
  x: number;
  y: number;
  r?: number;
  fill: string;
  stroke?: string;
  strokeWidth?: number;
  opacity?: number;
}) {
  const common = { fill, stroke, strokeWidth, opacity };
  if (shape === "square")
    return <rect x={x - r * 0.88} y={y - r * 0.88} width={r * 1.76} height={r * 1.76} {...common} />;
  if (shape === "triangle")
    return (
      <polygon
        points={`${x},${y - r * 1.15} ${x + r * 1.05},${y + r * 0.7} ${x - r * 1.05},${y + r * 0.7}`}
        {...common}
      />
    );
  if (shape === "diamond")
    return <polygon points={`${x},${y - r * 1.2} ${x + r * 1.2},${y} ${x},${y + r * 1.2} ${x - r * 1.2},${y}`} {...common} />;
  return <circle cx={x} cy={y} r={r} {...common} />;
}

export function AxisX({
  scale,
  y,
  values,
  format = (v) => String(v),
  label,
  grid,
}: {
  scale: Scale;
  y: number;
  values: number[];
  format?: (v: number) => string;
  label?: string;
  grid?: [number, number];
}) {
  const [x0, x1] = scale.range;
  return (
    <g fontFamily={SANS} fontSize={11} fill={MUTED}>
      {grid &&
        values.map((v) => (
          <line key={`g${v}`} x1={scale(v)} x2={scale(v)} y1={grid[0]} y2={grid[1]} stroke={GRID} strokeWidth={1} />
        ))}
      <line x1={Math.min(x0, x1)} x2={Math.max(x0, x1)} y1={y} y2={y} stroke={INK} strokeWidth={1} />
      {values.map((v) => (
        <g key={v}>
          <line x1={scale(v)} x2={scale(v)} y1={y} y2={y + 4} stroke={INK} />
          <text x={scale(v)} y={y + 16} textAnchor="middle">
            {format(v)}
          </text>
        </g>
      ))}
      {label && (
        <text x={(x0 + x1) / 2} y={y + 34} textAnchor="middle" fill={INK} fontSize={12}>
          {label}
        </text>
      )}
    </g>
  );
}

export function AxisY({
  scale,
  x,
  values,
  format = (v) => String(v),
  label,
  grid,
}: {
  scale: Scale;
  x: number;
  values: number[];
  format?: (v: number) => string;
  label?: string;
  grid?: [number, number];
}) {
  const [y0, y1] = scale.range;
  return (
    <g fontFamily={SANS} fontSize={11} fill={MUTED}>
      {grid &&
        values.map((v) => (
          <line key={`g${v}`} x1={grid[0]} x2={grid[1]} y1={scale(v)} y2={scale(v)} stroke={GRID} strokeWidth={1} />
        ))}
      <line x1={x} x2={x} y1={Math.min(y0, y1)} y2={Math.max(y0, y1)} stroke={INK} />
      {values.map((v) => (
        <g key={v}>
          <line x1={x - 4} x2={x} y1={scale(v)} y2={scale(v)} stroke={INK} />
          <text x={x - 7} y={scale(v) + 4} textAnchor="end">
            {format(v)}
          </text>
        </g>
      ))}
      {label && (
        <text
          transform={`translate(${x - 44} ${(y0 + y1) / 2}) rotate(-90)`}
          textAnchor="middle"
          fill={INK}
          fontSize={12}
        >
          {label}
        </text>
      )}
    </g>
  );
}

/** Hover/focus tooltip positioned inside the chart container. */
export function useTooltip() {
  const host = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<{ x: number; y: number; body: ReactNode } | null>(null);
  const show = useCallback((event: { clientX: number; clientY: number }, body: ReactNode) => {
    const box = host.current?.getBoundingClientRect();
    if (!box) return;
    setTip({ x: event.clientX - box.left, y: event.clientY - box.top, body });
  }, []);
  const showAt = useCallback((el: Element, body: ReactNode) => {
    const box = host.current?.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    if (!box) return;
    setTip({ x: r.left + r.width / 2 - box.left, y: r.top - box.top, body });
  }, []);
  const hide = useCallback(() => setTip(null), []);
  const node = tip ? (
    <div
      className="pub-tooltip"
      role="status"
      style={{
        left: Math.min(Math.max(tip.x, 90), (host.current?.clientWidth ?? 400) - 90),
        top: tip.y,
      }}
    >
      {tip.body}
    </div>
  ) : null;
  return { host, show, showAt, hide, node };
}

export function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: ReactNode; title?: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="pub-segmented" role="group" aria-label={label}>
      <span className="pub-control-label" aria-hidden="true">
        {label}
      </span>
      <div>
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            aria-pressed={value === o.value}
            title={o.title}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function Toggles<T extends string>({
  label,
  values,
  options,
  onChange,
}: {
  label: string;
  values: T[];
  options: { value: T; label: string; color: string }[];
  onChange: (v: T[]) => void;
}) {
  return (
    <div className="pub-segmented" role="group" aria-label={label}>
      <span className="pub-control-label" aria-hidden="true">
        {label}
      </span>
      <div>
        {options.map((o) => {
          const on = values.includes(o.value);
          return (
            <button
              key={o.value}
              type="button"
              aria-pressed={on}
              onClick={() => {
                const next = on ? values.filter((v) => v !== o.value) : [...values, o.value];
                if (next.length) onChange(options.map((x) => x.value).filter((v) => next.includes(v)));
              }}
            >
              <span className="pub-swatch" style={{ background: o.color }} aria-hidden="true" />
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function RootLegend() {
  return (
    <svg width={210} height={18} role="img" aria-label="Evaluation root markers: A circle, B square, C triangle">
      {(["A", "B", "C"] as const).map((r, i) => (
        <g key={r} transform={`translate(${i * 62 + 8} 9)`}>
          <Marker shape={(["circle", "square", "triangle"] as const)[i]} x={0} y={0} r={5} fill={INK} />
          <text x={11} y={4} fontFamily={SANS} fontSize={11} fill={INK}>
            root {r}
          </text>
        </g>
      ))}
    </svg>
  );
}
