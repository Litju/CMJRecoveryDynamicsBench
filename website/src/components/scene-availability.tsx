"use client";
import {
  Component,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
const messages = {
  waiting: "The 3D figure loads when it enters view.",
  reduced: "Reduced motion is enabled. The exact 2D view remains interactive.",
  unavailable: "WebGL is unavailable. Use the exact data and 2D views.",
  ready: "",
  lost: "The graphics context was lost. Exact values and 2D views remain available.",
};
export function useWebGL() {
  const ref = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<keyof typeof messages>("waiting");
  useEffect(() => {
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    let near = false;
    const check = () => {
      if (media.matches) {
        setStatus("reduced");
        return;
      }
      if (!near) {
        setStatus("waiting");
        return;
      }
      try {
        const context = document.createElement("canvas").getContext("webgl2");
        setStatus(context ? "ready" : "unavailable");
        context?.getExtension("WEBGL_lose_context")?.loseContext();
      } catch {
        setStatus("unavailable");
      }
    };
    const observer = new IntersectionObserver(
      ([entry]) => {
        near = entry.isIntersecting;
        check();
      },
      { rootMargin: "250px" },
    );
    if (ref.current) observer.observe(ref.current);
    media.addEventListener("change", check);
    return () => {
      observer.disconnect();
      media.removeEventListener("change", check);
    };
  }, []);
  const onUnavailable = useCallback(() => setStatus("lost"), []);
  return {
    ref,
    ready: status === "ready",
    fallback:
      status === "reduced" || status === "unavailable" || status === "lost",
    reason: messages[status],
    onUnavailable,
  };
}
export class SceneBoundary extends Component<
  { children: ReactNode; fallback: ReactNode; onError: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onError();
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}
