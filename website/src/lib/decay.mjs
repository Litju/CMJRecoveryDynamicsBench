export function decay(t, fastAmplitude, slowAmplitude) {
  return fastAmplitude * Math.exp(-t / 24) + slowAmplitude * Math.exp(-t / 84);
}
export function decaySlope(t, fastAmplitude, slowAmplitude) {
  return (
    (-fastAmplitude / 24) * Math.exp(-t / 24) -
    (slowAmplitude / 84) * Math.exp(-t / 84)
  );
}
export function decayIntegral(t, fastAmplitude, slowAmplitude) {
  return (
    24 * fastAmplitude * (1 - Math.exp(-t / 24)) +
    84 * slowAmplitude * (1 - Math.exp(-t / 84))
  );
}
export const decaySeries = (fast, slow) =>
  Array.from({ length: 169 }, (_, t) => ({
    time: t,
    fast: fast * Math.exp(-t / 24),
    slow: slow * Math.exp(-t / 84),
    total: decay(t, fast, slow),
    slope: decaySlope(t, fast, slow),
    integral: decayIntegral(t, fast, slow),
  }));
