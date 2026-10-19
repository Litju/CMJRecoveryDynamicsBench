export function decay(t, fastAmplitude, slowAmplitude) {
  return fastAmplitude * Math.exp(-t / 24) + slowAmplitude * Math.exp(-t / 84);
}
export const decaySeries = (fast, slow) =>
  Array.from({ length: 169 }, (_, t) => ({
    time: t,
    fast: fast * Math.exp(-t / 24),
    slow: slow * Math.exp(-t / 84),
    total: decay(t, fast, slow),
  }));
