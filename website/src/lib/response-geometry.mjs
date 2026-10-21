import { decaySeries } from "./decay.mjs";
export const responseRows = [
  { id: "total", label: "Combined", z: -1.6 },
  { id: "fast", label: "24 h mode", z: 0 },
  { id: "slow", label: "84 h mode", z: 1.6 },
];
export function responsePaths(fast, slow) {
  const series = decaySeries(fast, slow);
  return responseRows.map((row) => ({
    ...row,
    points: series.map((p) => [p.time / 21 - 4, p[row.id] * 3, row.z]),
  }));
}
