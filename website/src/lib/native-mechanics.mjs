// Analytical schematic: constant mass, linear force, supplied events; no detector.
export function mechanics(duration, mass = 75, gravity = 9.80665) {
  const samples = Array.from({ length: 41 }, (_, i) => ({
    time: (duration * i) / 40,
    force: mass * (gravity + 8 - (4 * i) / 40),
  }));
  const gross = samples
    .slice(1)
    .reduce(
      (sum, s, i) =>
        sum + ((s.time - samples[i].time) * (s.force + samples[i].force)) / 2,
      0,
    );
  return {
    samples,
    force: gross / (mass * duration),
    impulse: gross / mass - gravity * duration,
  };
}
