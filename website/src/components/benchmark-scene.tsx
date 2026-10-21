"use client";
import { Canvas } from "@react-three/fiber";
import { useState } from "react";
import { models } from "@/lib/science";
import { plotTheme as theme } from "@/lib/plot-theme.mjs";
import {
  SceneLighting,
  CameraRig,
  SceneLabel,
  SceneLine,
  ContextGuard,
} from "./scene-primitives";
import type { CameraPose } from "./camera-controls";
import type { BenchmarkDatum } from "./benchmark-3d";
export default function BenchmarkScene({
  entries,
  selected,
  pose,
  drag,
  zoom,
  onInspect,
  onSelect,
  onUnavailable,
}: {
  entries: BenchmarkDatum[];
  selected: string;
  pose: CameraPose;
  drag: boolean;
  zoom: number;
  onInspect: (key: string | null) => void;
  onSelect: (entry: BenchmarkDatum) => void;
  onUnavailable: () => void;
}) {
  const [hovered, setHovered] = useState<string | null>(null);
  const maximum = Math.ceil(Math.max(...entries.map((e) => e.nrmse)));
  return (
    <Canvas
      shadows
      orthographic
      frameloop="demand"
      dpr={[1, 1.5]}
      camera={{ position: [9, 8, 11], zoom: 42, near: 0.1, far: 100 }}
      gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}
      onCreated={({ gl }) => gl.setClearColor(theme.surface, 1)}
    >
      <CameraRig pose={pose} drag={drag} zoom={zoom} />
      <ContextGuard onUnavailable={onUnavailable} />
      <SceneLighting />
      <mesh receiveShadow position={[0, -0.1, 0]}>
        <boxGeometry args={[9.6, 0.16, 6.6]} />
        <meshStandardMaterial color={theme.panel} roughness={1} />
      </mesh>
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <group key={i}>
          <SceneLine
            points={[
              [(i - 2.5) * 1.2, 0, -2.7],
              [(i - 2.5) * 1.2, 0, 2.7],
            ]}
            color={theme.grid}
          />
          <SceneLabel
            text={`${[24, 24, 48, 48, 72, 72][i]}h ${i % 2 ? "I" : "F"}`}
            position={[(i - 2.5) * 1.2, 0.02, 3]}
            width={1}
          />
        </group>
      ))}
      {models.map((m, i) => (
        <group key={m.id}>
          <SceneLine
            points={[
              [-3.7, 0, (i - 1.5) * 1.4],
              [3.7, 0, (i - 1.5) * 1.4],
            ]}
            color={theme.grid}
          />
          <SceneLabel
            compact={false}
            text={m.short}
            color={m.color}
            position={[4.5, 0.05, (i - 1.5) * 1.4]}
            width={1.6}
          />
        </group>
      ))}
      {Array.from({ length: maximum + 1 }, (_, v) => (
        <group key={v}>
          <SceneLine
            points={[
              [-3.8, v, -2.7],
              [-3.8, v, 2.7],
            ]}
            color={theme.grid}
          />
          <SceneLabel text={String(v)} position={[-4.25, v, 2.7]} width={0.5} />
        </group>
      ))}
      <SceneLine
        points={[
          [-3.8, 0, 2.7],
          [-3.8, maximum + 0.2, 2.7],
        ]}
        color={theme.muted}
      />
      <SceneLabel
        compact={false}
        text="CELL NRMSE"
        position={[-2.3, maximum + 0.55, 0]}
        width={2.2}
      />
      {entries.map((entry) => (
        <mesh
          castShadow
          receiveShadow
          key={entry.key}
          name={entry.key}
          position={[
            (entry.cellIndex - 2.5) * 1.2,
            entry.nrmse / 2,
            (entry.modelIndex - 1.5) * 1.4,
          ]}
          onPointerOver={(e) => {
            e.stopPropagation();
            setHovered(entry.key);
            onInspect(entry.key);
          }}
          onPointerOut={() => {
            setHovered(null);
            onInspect(null);
          }}
          onClick={(e) => {
            e.stopPropagation();
            if (e.delta < 5) onSelect(entry);
          }}
        >
          <boxGeometry args={[0.65, entry.nrmse, 0.65]} />
          <meshStandardMaterial
            color={entry.color}
            roughness={0.65}
            metalness={0}
            emissive={entry.color}
            emissiveIntensity={
              selected === entry.key ? 0.2 : hovered === entry.key ? 0.12 : 0
            }
          />
          {selected === entry.key && <SceneLine color={theme.text} points={[
            [-0.33, entry.nrmse / 2 + 0.01, -0.33],
            [0.33, entry.nrmse / 2 + 0.01, -0.33],
            [0.33, entry.nrmse / 2 + 0.01, 0.33],
            [-0.33, entry.nrmse / 2 + 0.01, 0.33],
            [-0.33, entry.nrmse / 2 + 0.01, -0.33],
          ]} />}
        </mesh>
      ))}
    </Canvas>
  );
}
