"use client";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import * as THREE from "three";
import { decay } from "@/lib/decay.mjs";
function Plate({ time }: { time: number }) {
  const field = useMemo(() => {
    const p: number[] = [];
    for (let x = -2.8; x <= 2.8; x += 0.16)
      for (let z = -2.6; z <= 2.6; z += 0.16) {
        const r = Math.sqrt(x * x + z * z);
        const y =
          0.35 +
          1.9 * Math.exp(-r * r * 0.65) * decay(time, 0.7, 0.3) +
          0.09 * Math.sin(r * 5);
        p.push(x, y, z);
      }
    return new Float32Array(p);
  }, [time]);
  const edges = useMemo(
    () => new THREE.EdgesGeometry(new THREE.BoxGeometry(4.25, 0.22, 3.15)),
    [],
  );
  return (
    <group rotation={[0, -0.35 + time / 550, 0]}>
      <mesh position={[0, -0.25, 0]}>
        <boxGeometry args={[4.35, 0.18, 3.25]} />
        <meshStandardMaterial
          color="#080f14"
          metalness={0.9}
          roughness={0.25}
        />
      </mesh>
      <mesh>
        <boxGeometry args={[4.25, 0.22, 3.15]} />
        <meshStandardMaterial
          color="#1d3539"
          metalness={0.75}
          roughness={0.32}
        />
      </mesh>
      <lineSegments geometry={edges}>
        <lineBasicMaterial color="#a9f5dc" transparent opacity={0.85} />
      </lineSegments>
      <gridHelper
        args={[4.2, 20, "#8ac9b6", "#315356"]}
        position={[0, 0.12, 0]}
        scale={[1, 1, 0.73]}
      />
      {[-1.7, 1.7].flatMap((x) =>
        [-1.1, 1.1].map((z) => (
          <mesh key={`${x}/${z}`} position={[x, -0.45, z]}>
            <cylinderGeometry args={[0.15, 0.13, 0.3, 20]} />
            <meshStandardMaterial
              color="#3f6467"
              metalness={0.9}
              roughness={0.2}
            />
          </mesh>
        )),
      )}
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[field, 3]} />
        </bufferGeometry>
        <pointsMaterial
          size={0.024}
          color="#c4ffe5"
          transparent
          opacity={0.65}
          sizeAttenuation
        />
      </points>
      {[0, 1, 2].map((i) => (
        <mesh
          key={i}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, 0.35 + i * 0.32, 0]}
        >
          <torusGeometry args={[1.1 + i * 0.5, 0.006, 5, 100]} />
          <meshBasicMaterial
            color={i === 1 ? "#acaaf0" : "#97e9d6"}
            transparent
            opacity={0.42 - i * 0.07}
          />
        </mesh>
      ))}
      <mesh position={[0, 0.25, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.15, 0.17, 48]} />
        <meshBasicMaterial color="#c4ffe5" side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}
export default function InstrumentScene({ time }: { time: number }) {
  return (
    <Canvas
      frameloop="demand"
      dpr={[1, 1.5]}
      camera={{ position: [7, 6.2, 8], fov: 29 }}
      gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}
      onCreated={({ gl }) => {
        gl.setClearColor(0x000000, 0);
      }}
    >
      <ambientLight intensity={1.7} />
      <directionalLight position={[3, 8, 4]} color="#b3ffe2" intensity={3} />
      <pointLight position={[-4, 3, -2]} color="#ada4f3" intensity={15} />
      <Plate time={time} />
    </Canvas>
  );
}
