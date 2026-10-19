"use client";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import * as THREE from "three";
import { decay } from "@/lib/decay.mjs";
type SceneProps = { time: number; fast: number; slow: number };
function Plate({ time, fast, slow }: SceneProps) {
  const field = useMemo(() => {
    const p: number[] = [];
    for (let x = -2.8; x <= 2.8; x += 0.16)
      for (let z = -2.6; z <= 2.6; z += 0.16) {
        const r = Math.sqrt(x * x + z * z);
        const y =
          0.35 + 1.9 * Math.exp(-r * r * 0.65) * decay(time, fast, slow);
        p.push(x, y, z);
      }
    return new Float32Array(p);
  }, [time, fast, slow]);
  const edges = useMemo(
    () => new THREE.EdgesGeometry(new THREE.BoxGeometry(4.25, 0.22, 3.15)),
    [],
  );
  return (
    <group rotation={[0, -0.35, 0]}>
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
        <lineBasicMaterial color="#a6c6f3" transparent opacity={0.85} />
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
          color="#bcd7fa"
          transparent
          opacity={0.65}
          sizeAttenuation
        />
      </points>
      {[fast * Math.exp(-time / 24), slow * Math.exp(-time / 84)].map(
        (contribution, i) => (
          <mesh
            key={i}
            rotation={[-Math.PI / 2, 0, 0]}
            position={[0, 0.35 + contribution * 1.9, 0]}
          >
            <torusGeometry args={[1.1 + i * 0.5, 0.006, 5, 100]} />
            <meshBasicMaterial
              color={i === 1 ? "#f1a486" : "#9abcef"}
              transparent
              opacity={0.42 - i * 0.07}
            />
          </mesh>
        ),
      )}
      <mesh position={[0, 0.25, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.15, 0.17, 48]} />
        <meshBasicMaterial color="#bcd7fa" side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}
export default function InstrumentScene({ time, fast, slow }: SceneProps) {
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
      <directionalLight position={[3, 8, 4]} color="#bdd7f4" intensity={3} />
      <pointLight position={[-4, 3, -2]} color="#efb18d" intensity={15} />
      <Plate time={time} fast={fast} slow={slow} />
    </Canvas>
  );
}
