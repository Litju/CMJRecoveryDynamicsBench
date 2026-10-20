"use client";
import { useEffect, useRef } from "react";
import { usePlotArea, useXAxisInverseDataSnapScale } from "recharts";

export function PlotSelection({ onSelect }: { onSelect: (value: unknown) => void }) {
  const ref = useRef<SVGGElement>(null);
  const plot = usePlotArea();
  const invert = useXAxisInverseDataSnapScale();
  useEffect(() => {
    const svg = ref.current?.ownerSVGElement;
    if (!svg || !plot || !invert) return;
    // Recharts' chart click callback loses its active label; use its actual axis scale.
    const pick = (event: MouseEvent) => {
      const matrix = svg.getScreenCTM();
      if (!matrix) return;
      const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
      if (point.x >= plot.x && point.x <= plot.x + plot.width &&
          point.y >= plot.y && point.y <= plot.y + plot.height) {
        onSelect(invert(point.x));
      }
    };
    svg.addEventListener("click", pick);
    return () => svg.removeEventListener("click", pick);
  }, [plot, invert, onSelect]);
  return <g ref={ref} aria-hidden="true" />;
}
