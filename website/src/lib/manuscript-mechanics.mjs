// Analytical force–time signal of manuscript Fig. 5. Not athlete data.
// F(t) = mg + A·sin(πt / 2tp) for 0 ≤ t ≤ tp; F(t) = (mg + A)·[1 − (t − tp)/(T − tp)] for tp < t ≤ T.

/** @param {{mass:number,gravity:number,amplitude:number,peakTime:number,duration:number}} p */
export function analyticalForce(t, p) {
  const weight = p.mass * p.gravity;
  if (t <= p.peakTime)
    return weight + p.amplitude * Math.sin((Math.PI * t) / (2 * p.peakTime));
  return (weight + p.amplitude) * (1 - (t - p.peakTime) / (p.duration - p.peakTime));
}

/** Evenly spaced samples over the concentric interval [0, T]. */
export function sampleForce(p, samples) {
  return Array.from({ length: samples }, (_, i) => {
    const t = (p.duration * i) / (samples - 1);
    return { t, force: analyticalForce(t, p) };
  });
}

/** Trapezoid quantities on the same 5,501-point grid as the manuscript generator. */
export function forceQuantities(p, samples) {
  const pts = sampleForce(p, samples);
  const weight = p.mass * p.gravity;
  let gross = 0;
  let net = 0;
  let peak = -Infinity;
  for (let i = 0; i < pts.length; i++) {
    peak = Math.max(peak, pts[i].force);
    if (i === 0) continue;
    const dt = pts[i].t - pts[i - 1].t;
    gross += (dt * (pts[i].force + pts[i - 1].force)) / 2;
    net += (dt * (pts[i].force - weight + pts[i - 1].force - weight)) / 2;
  }
  return {
    grossAreaNs: gross,
    meanForceN: gross / p.duration,
    meanForceNPerKg: gross / p.duration / p.mass,
    peakForceN: peak,
    peakForceNPerKg: peak / p.mass,
    netImpulseMPerS: net / p.mass,
  };
}

/** Cumulative gravity-adjusted net impulse (m/s) from onset to time t. */
export function cumulativeNetImpulse(p, t, samples = 1101) {
  const end = Math.min(Math.max(t, 0), p.duration);
  if (end === 0) return 0;
  const weight = p.mass * p.gravity;
  let net = 0;
  let prev = analyticalForce(0, p) - weight;
  for (let i = 1; i < samples; i++) {
    const ti = (end * i) / (samples - 1);
    const cur = analyticalForce(ti, p) - weight;
    net += ((end / (samples - 1)) * (prev + cur)) / 2;
    prev = cur;
  }
  return net / p.mass;
}
