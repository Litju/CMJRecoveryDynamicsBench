"use client";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import { Vector3, Quaternion } from "three";
import { CameraRig, ContextGuard, SceneLabel, SceneLine } from "./scene-primitives";
import { plotTheme as theme } from "@/lib/plot-theme.mjs";
import { responsePaths } from "@/lib/response-geometry.mjs";
import { decay } from "@/lib/decay.mjs";
import { journeyBars } from "@/lib/journey";
import { lineage } from "@/lib/story";
function Joint({ position, size = 0.1 }: {
    position: [
        number,
        number,
        number
    ];
    size?: number;
}) {
    return <mesh position={position}><sphereGeometry args={[size, 20, 12]}/><meshStandardMaterial color={theme.ink}/></mesh>;
}
function Bone({ from, to }: {
    from: [
        number,
        number,
        number
    ];
    to: [
        number,
        number,
        number
    ];
}) {
    const direction = new Vector3(...to).sub(new Vector3(...from));
    const length = direction.length();
    const midpoint = new Vector3(...from).add(new Vector3(...to)).multiplyScalar(0.5);
    const rotation = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), direction.normalize());
    return <mesh position={midpoint} quaternion={rotation}><cylinderGeometry args={[0.065, 0.065, length, 12]}/><meshStandardMaterial color={theme.ink} roughness={0.8}/></mesh>;
}
export default function JourneyScene({ kind, progress, drag, onUnavailable, onModel, onFormulation }: {
    kind: string;
    progress: number;
    drag: boolean;
    onUnavailable: () => void;
    onModel: (id: string) => void;
    onFormulation: (id: string) => void;
}) {
    const paths = useMemo(() => responsePaths(0.7, 0.3), []);
    const time = Math.round(progress * 168);
    const hip = 2.3 + progress * 0.6;
    const knee = 1.5 + progress * 0.3;
    const pose: [
        number,
        number,
        number
    ] = useMemo(() => [8 + progress * 5, 7 + progress * 2, 14 - progress * 4], [progress]);
    return <Canvas orthographic frameloop="demand" dpr={[1, 1.5]} camera={{ position: [9, 8, 11], zoom: 42, near: 0.1, far: 100 }} gl={{ antialias: true, powerPreference: "low-power" }} onCreated={({ gl }) => gl.setClearColor(theme.surface, 1)}>
    <CameraRig pose={pose} drag={drag} zoom={45}/><ContextGuard onUnavailable={onUnavailable}/>
    <ambientLight intensity={1.5}/><directionalLight position={[3, 9, 5]} intensity={2}/>
    <mesh position={[0, -0.13, 0]}><boxGeometry args={[10, 0.2, 6]}/><meshStandardMaterial color="#e5e5da" roughness={1}/></mesh>
    {[-4, -2, 0, 2, 4].map((x) => <SceneLine key={x} points={[[x, 0, -2.6], [x, 0, 2.6]]} color={theme.grid}/>)}
    {kind === "measurement" && <group position={[0, -0.01, 0]}>
      <mesh position={[0, 0.16, 0]}><boxGeometry args={[3.2, 0.3, 2.4]}/><meshStandardMaterial color={theme.cobalt} roughness={0.6}/></mesh>
      {[-1, 1].map((x) => <group key={x}><mesh position={[x * 0.5, 0.38, 0.1]}><boxGeometry args={[0.32, 0.15, 0.7]}/><meshStandardMaterial color={theme.ink}/></mesh><Bone from={[x * 0.5, 0.5, 0]} to={[x * (0.8 - progress * 0.25), knee, -0.3]}/><Bone from={[x * (0.8 - progress * 0.25), knee, -0.3]} to={[0, hip, 0]}/><Joint position={[x * (0.8 - progress * 0.25), knee, -0.3]}/></group>)}
      <Bone from={[0, hip, 0]} to={[0, hip + 1.6, 0]}/><Joint position={[0, hip + 2, 0]} size={0.35}/>
      {[-1, 1].map((x) => <group key={x}><Bone from={[0, hip + 1.2, 0]} to={[x * 1.2, hip + 0.8, 0.2]}/><Bone from={[x * 1.2, hip + 0.8, 0.2]} to={[x * 1.6, hip + 1.4 + progress * 0.3, 0]}/></group>)}
      <mesh position={[2, 1.9, 0]}><cylinderGeometry args={[0.045, 0.045, 3, 12]}/><meshStandardMaterial color={theme.cobalt}/></mesh><mesh position={[2, 3.6, 0]}><coneGeometry args={[0.18, 0.4, 16]}/><meshStandardMaterial color={theme.cobalt}/></mesh>
      <SceneLabel text="GROUND REACTION FORCE" position={[2, 4.3, 0]} width={3.7} color={theme.cobalt}/><SceneLabel text="SCHEMATIC / FORCE PLATE" position={[0, -0.3, 2.5]} width={4}/>
    </group>}
    {kind === "response" && <group>
      {paths.map((row) => { const color = row.id === "total" ? theme.text : row.id === "fast" ? theme.fast : theme.slow; return <group key={row.id}><SceneLine points={row.points} color={color}/><SceneLabel text={row.label} position={[4.8, 0.2, row.z]} width={1.8} color={color}/></group>; })}
      <SceneLine points={[[time / 21 - 4, 0, -2], [time / 21 - 4, 3.2, -2], [time / 21 - 4, 3.2, 2], [time / 21 - 4, 0, 2]]} color={theme.ochre}/>
      <Joint position={[time / 21 - 4, decay(time, 0.7, 0.3) * 3, -1.6]} size={0.1}/>
      <SceneLabel text={`${time} h / ILLUSTRATIVE`} position={[0, 3.8, 0]} width={4}/>
      {[0, 48, 96, 168].map((t) => <SceneLabel key={t} text={`${t}h`} position={[t / 21 - 4, 0, 2.7]} width={0.7}/>)}
    </group>}
    {kind === "lineage" && <group>{Array.from({ length: 8 }, (_, i) => <group key={i} position={[(i - 3.5) * 1.1, 0, (i % 2) * 1.5 - 0.75]}><mesh onClick={(e) => { e.stopPropagation(); if (e.delta < 5)
        onFormulation(lineage[i].id); }} position={[0, 0.4, 0]}><boxGeometry args={[0.7, 0.8, 0.7]}/><meshStandardMaterial color={i === 7 ? theme.slow : theme.fast} roughness={0.65}/></mesh><SceneLabel text={`0${i + 1}`} position={[0, 1.2, 0]} width={0.65}/>{lineage[i].parent && <SceneLine points={[[0, 0.4, 0], [(lineage.findIndex((n) => n.id === lineage[i].parent) - i) * 1.1, 0.4, ((lineage.findIndex((n) => n.id === lineage[i].parent) % 2) - (i % 2)) * 1.5]]} color={theme.muted}/>}</group>)}<SceneLabel text="FORMULATIONS / NOT A LEADERBOARD" position={[0, 2.6, 0]} width={6}/></group>}
    {kind === "benchmark" && <group>{journeyBars.map((m, i) => <group key={m.id} position={[(i - 1.5) * 2, 0, 0]}><mesh onClick={(e) => { e.stopPropagation(); if (e.delta < 5)
        onModel(m.id); }} position={[0, m.value / 2, 0]}><boxGeometry args={[0.9, m.value, 1]}/><meshStandardMaterial color={m.color} roughness={0.55}/></mesh><SceneLabel text={m.value.toFixed(4)} position={[0, m.value + 0.5, 0]} width={1.4} color={m.color}/><SceneLabel text={m.short} position={[0, 0, 1.5]} width={1.6}/></group>)}<SceneLabel text="24 h FORCE / NRMSE / LOWER IS BETTER" position={[0, 5.2, 0]} width={6}/>{[0, 1, 2, 3, 4].map((v) => <group key={v}><SceneLine points={[[-4, v, -1], [-4, v, 1]]} color={theme.grid}/><SceneLabel text={`${v}`} position={[-4.5, v, 1]} width={0.5}/></group>)}</group>}
  </Canvas>;
}
