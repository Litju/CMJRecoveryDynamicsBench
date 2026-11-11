// Analytical CMJ measurement and fixed-mode response helpers for the Observatory exhibits.
// Mirrors the synthetic simulator (phase_consistent_force_impulse.py and
// fixed_mode_discrepancy_response.py). Pure arithmetic: no fitting, scoring or resampling.
export const G = 9.80665; // m/s^2
export const NODES = 65;
export const DURATION_SUPPORT = [0.075, 0.8]; // s
export const FAST_MODE_H = 24;
export const SLOW_MODE_H = 84;
export const AMPLITUDE_SUPPORT = { fast: [0.01, 0.08], slow: [0, 0.08] };
export const HORIZONS = [24, 48, 72];

/** Valid net-impulse range (m/s) for a mean force, from the simulator's duration support. */
export function impulseRange(meanForce) {
  const net = meanForce - G;
  if (!(net > 0)) return null;
  return [DURATION_SUPPORT[0] * net, DURATION_SUPPORT[1] * net];
}

/** Half-sine concentric trial on 65 nodes with exact gross mean force and net impulse. */
export function trial(meanForce, netImpulse) {
  const range = impulseRange(meanForce);
  if (!range || !(netImpulse >= range[0] && netImpulse <= range[1])) {
    throw new RangeError("duration escaped the simulator support");
  }
  const duration = netImpulse / (meanForce - G);
  const times = Array.from({ length: NODES }, (_, i) => (duration * i) / (NODES - 1));
  const shape = times.map((_, i) => Math.sin((Math.PI * i) / (NODES - 1)));
  const trapz = (v) => v.slice(1).reduce((s, x, i) => s + ((v[i] + x) / 2) * (times[i + 1] - times[i]), 0);
  const shapeMean = trapz(shape) / duration;
  const force = shape.map((s) => G + ((meanForce - G) * s) / shapeMean);
  return {
    duration,
    times,
    force,
    peak: Math.max(...force),
    continuousPeak: G + (Math.PI / 2) * (meanForce - G),
    meanForce: trapz(force) / duration,
    netImpulse: trapz(force.map((f) => f - G)),
  };
}

/** r(tau) = -a_f exp(-tau/24) - a_s exp(-tau/84): fixed mathematical response modes. */
export function response(tau, fast, slow) {
  if (!(tau >= 0)) throw new RangeError("tau must be non-negative");
  return -fast * Math.exp(-tau / FAST_MODE_H) - slow * Math.exp(-tau / SLOW_MODE_H);
}

/** Expected additive innovation (N/kg) for a baseline truth, before measurement noise. */
export const innovation = (baseline, tau, fast, slow) => baseline * response(tau, fast, slow);
