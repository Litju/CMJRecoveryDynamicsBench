// Client-side exports of already-displayed, source-backed values. No new values are computed.
export type Cell = string | number | boolean | null;
export interface DataTable {
  caption: string;
  columns: string[];
  rows: Cell[][];
}

const csvCell = (v: Cell) => {
  if (v === null) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
export const toCSV = (t: DataTable) =>
  [t.columns, ...t.rows].map((r) => r.map(csvCell).join(",")).join("\n") + "\n";

export function download(name: string, body: string, type: string) {
  const url = URL.createObjectURL(new Blob([body], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

const NS = "http://www.w3.org/2000/svg";

/** Compose panel SVGs (`svg[data-panel]`) of a responsive small-multiple into one grid SVG. */
function compose(container: Element): SVGSVGElement {
  const panels = [...container.querySelectorAll<SVGSVGElement>("svg[data-panel]")];
  const cols = Number(container.getAttribute("data-cols") ?? 2);
  const w = Math.max(...panels.map((p) => p.viewBox.baseVal.width));
  const h = Math.max(...panels.map((p) => p.viewBox.baseVal.height));
  const out = document.createElementNS(NS, "svg");
  const rows = Math.ceil(panels.length / cols);
  out.setAttribute("viewBox", `0 0 ${w * cols} ${h * rows}`);
  const bg = document.createElementNS(NS, "rect");
  bg.setAttribute("width", "100%");
  bg.setAttribute("height", "100%");
  bg.setAttribute("fill", "#fffdf7");
  out.appendChild(bg);
  panels.forEach((p, i) => {
    const c = p.cloneNode(true) as SVGSVGElement;
    c.setAttribute("x", String((i % cols) * w));
    c.setAttribute("y", String(Math.floor(i / cols) * h));
    c.setAttribute("width", String(p.viewBox.baseVal.width));
    c.setAttribute("height", String(p.viewBox.baseVal.height));
    out.appendChild(c);
  });
  return out;
}

/** Serialize a figure SVG. Presentation is set as attributes, so the file is self-contained. */
export function serializeSVG(node: Element, title: string, provenance: string) {
  const svg = node instanceof SVGSVGElement ? node : compose(node);
  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("font-family", "Georgia, 'Times New Roman', serif");
  const { width, height } = svg.viewBox.baseVal;
  if (width && height) {
    clone.setAttribute("width", String(width));
    clone.setAttribute("height", String(height));
  }
  clone.querySelectorAll("[data-export-ignore]").forEach((n) => n.remove());
  const desc = document.createElementNS(NS, "desc");
  desc.textContent = `${title}. ${provenance}`;
  clone.insertBefore(desc, clone.firstChild);
  return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(clone)}\n`;
}
