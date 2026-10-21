"use client";
import { Canvas } from "@react-three/fiber";
import { useMemo, useEffect } from "react";
import * as THREE from "three";
import { decay } from "@/lib/decay.mjs";
import { responsePaths } from "@/lib/response-geometry.mjs";
import { plotTheme as theme } from "@/lib/plot-theme.mjs";
import {
  SceneLighting,
  CameraRig,
  SceneLabel,
  SceneLine,
  ContextGuard,
} from "./scene-primitives";
import type { CameraPose } from "./camera-controls";
type SceneProps = {
  time: number;
  fast: number;
  slow: number;
  pose: CameraPose;
  drag: boolean;
  zoom: number;
  onSelectTime: (time: number) => void;
  onUnavailable: () => void;
};
function ResponseCurve({
  points,
  color,
  onSelectTime,
}: {
  points: number[][];
  color: string;
  onSelectTime: (time: number) => void;
}) {
  const { geometry, hitArea } = useMemo(() => {
    const curve = new THREE.CatmullRomCurve3(
      points.map((p) => new THREE.Vector3(p[0], p[1], p[2])),
    );
    return {
      geometry: new THREE.TubeGeometry(curve, 168, 0.03, 8, false),
      hitArea: new THREE.TubeGeometry(curve, 168, 0.16, 6, false),
    };
  }, [points]);
  useEffect(() => () => { geometry.dispose(); hitArea.dispose(); }, [geometry, hitArea]);
  return (
    <group>
      <mesh geometry={geometry} castShadow>
        <meshStandardMaterial color={color} roughness={0.7} />
      </mesh>
      {/* A wider invisible target makes the thin scientific curve easier to pick. */}
      <mesh
        geometry={hitArea}
        onClick={(event) => {
          event.stopPropagation();
          if (event.delta < 5)
            onSelectTime(
              Math.max(0, Math.min(168, Math.round((event.point.x + 4) * 21))),
            );
        }}
      >
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
    </group>
  );
}
export default function InstrumentScene({
  time,
  fast,
  slow,
  pose,
  drag,
  zoom,
  onSelectTime,
  onUnavailable,
}: SceneProps) {
  const paths = useMemo(() => responsePaths(fast, slow), [fast, slow]);
  const x = time / 21 - 4;
  const colors = { total: theme.text, fast: theme.fast, slow: theme.slow };
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
      <mesh receiveShadow position={[0, -0.09, 0]}>
        <boxGeometry args={[9.5, 0.14, 5.6]} />
        <meshStandardMaterial color={theme.panel} roughness={1} />
      </mesh>
      {[0, 24, 48, 72, 96, 120, 144, 168].map((t) => (
        <group key={t}>
          <SceneLine
            points={[
              [t / 21 - 4, 0, -2.1],
              [t / 21 - 4, 0, 2.1],
            ]}
            color={theme.grid}
          />
          <SceneLabel
            compact={t % 48 === 0 || t === 168}
            text={`${t}h`}
            position={[t / 21 - 4, 0.02, 2.4]}
            width={0.7}
          />
        </group>
      ))}
      {[0, 0.5, 1].map((v) => (
        <group key={v}>
          <SceneLine
            points={[
              [-4.2, v * 3, -2.1],
              [-4.2, v * 3, 2.1],
            ]}
            color={theme.grid}
          />
          <SceneLabel
            text={v.toFixed(1)}
            position={[-4.7, v * 3, 2.1]}
            width={0.6}
          />
        </group>
      ))}
      <SceneLine
        points={[
          [-4.2, 0, 2.1],
          [-4.2, 3.3, 2.1],
        ]}
        color={theme.muted}
      />
      {paths.map((row) => {
        const color = colors[row.id as keyof typeof colors];
        const value =
          row.id === "total"
            ? decay(time, fast, slow)
            : row.id === "fast"
              ? fast * Math.exp(-time / 24)
              : slow * Math.exp(-time / 84);
        return (
          <group key={row.id}>
            <ResponseCurve
              points={row.points}
              color={color}
              onSelectTime={onSelectTime}
            />
            <SceneLine
              points={[
                [-4, 0, row.z],
                [4, 0, row.z],
              ]}
              color={theme.grid}
            />
            <SceneLabel
              compact={false}
              text={row.label}
              position={[5, 0, row.z]}
              color={color}
              width={1.6}
            />
            <mesh castShadow position={[x, value * 3, row.z]}>
              <sphereGeometry args={[0.075, 16, 12]} />
              <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={0.18}
              />
            </mesh>
            <SceneLine
              points={[
                [x, 0, row.z],
                [x, value * 3, row.z],
              ]}
              color={color}
            />
          </group>
        );
      })}
      <mesh position={[x, 1.5, 0]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[4.2, 3]} />
        <meshBasicMaterial
          color={theme.ochre}
          transparent
          opacity={0.065}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
      <SceneLabel compact={false} text="TIME / HOURS" position={[0, -0.18, 3]} width={2} />
      <SceneLabel
        compact={false}
        text="RESPONSE / ARBITRARY UNITS"
        position={[-2, 4.8, 0]}
        width={3.6}
      />
    </Canvas>
  );
}
