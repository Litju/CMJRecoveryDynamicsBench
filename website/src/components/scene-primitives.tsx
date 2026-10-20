"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import * as THREE from "three";
import { plotTheme } from "@/lib/plot-theme.mjs";
import type { CameraPose } from "./camera-controls";
export function CameraRig({
  pose,
  drag,
  zoom,
  smooth = false,
}: {
  pose: CameraPose;
  drag: boolean;
  zoom: number;
  smooth?: boolean;
}) {
  const { camera, gl, invalidate, size } = useThree();
  const controls = useRef<OrbitControls | null>(null);
  const target = useMemo(() => new THREE.Vector3(...pose), [pose]);
  useFrame((_, delta) => {
    if (!smooth || drag || camera.position.distanceToSquared(target) < 0.000001) return;
    camera.position.lerp(target, 1 - Math.exp(-12 * Math.min(delta, 0.05)));
    camera.lookAt(0, 1, 0);
    invalidate();
  });
  useEffect(() => {
    const orbit = new OrbitControls(camera, gl.domElement);
    orbit.enableDamping = false;
    orbit.enablePan = false;
    orbit.enableZoom = false;
    orbit.minPolarAngle = 0.01;
    orbit.maxPolarAngle = Math.PI / 2 - 0.015;
    orbit.target.set(0, 1, 0);
    const requestFrame = () => invalidate();
    orbit.addEventListener("change", requestFrame);
    controls.current = orbit;
    return () => {
      orbit.removeEventListener("change", requestFrame);
      orbit.dispose();
      controls.current = null;
    };
  }, [camera, gl, invalidate]);
  useEffect(() => {
    if (!smooth) {
      camera.position.copy(target);
      camera.lookAt(0, 1, 0);
      controls.current?.update();
    }
    invalidate();
  }, [camera, target, smooth, invalidate]);
  useEffect(() => {
    if (camera instanceof THREE.OrthographicCamera) {
      camera.zoom =
        (Math.min(size.width / 12.5, size.height / 8.5) * zoom) / 42;
      camera.updateProjectionMatrix();
    }
    invalidate();
  }, [camera, zoom, size.width, size.height, invalidate]);
  useEffect(() => {
    if (controls.current) controls.current.enabled = drag;
    gl.domElement.style.touchAction = drag ? "none" : "pan-y";
    gl.domElement.style.cursor = drag ? "grab" : "crosshair";
  }, [drag, gl]);
  return null;
}
export function SceneLabel({
  text,
  position,
  color = plotTheme.muted,
  width = 1.5,
  compact = true,
}: {
  text: string;
  position: [number, number, number];
  color?: string;
  width?: number;
  compact?: boolean;
}) {
  const narrow = useThree((state) => state.size.width < 480);
  const texture = useMemo(() => {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    if (!context) return null;
    const font = "500 48px Geist, Arial";
    context.font = font;
    canvas.width = Math.ceil(context.measureText(text).width) + 32;
    canvas.height = 80;
    context.font = font;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillStyle = color;
    context.fillText(text, canvas.width / 2, 40);
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    return map;
  }, [text, color]);
  useEffect(() => () => texture?.dispose(), [texture]);
  if (!texture || (narrow && !compact)) return null;
  return (
    <sprite
      position={position}
      scale={[
        Math.min(0.46 / 80, width / texture.image.width) * texture.image.width,
        Math.min(0.46 / 80, width / texture.image.width) * 80,
        1,
      ]}
    >
      <spriteMaterial map={texture} transparent depthTest={false} toneMapped={false} />
    </sprite>
  );
}
export function SceneLine({
  points,
  color,
  width = 1,
}: {
  points: number[][];
  color: string;
  width?: number;
}) {
  const geometry = useMemo(
    () =>
      new THREE.BufferGeometry().setFromPoints(
        points.flatMap((p, i) =>
          i
            ? [
                new THREE.Vector3(
                  ...(points[i - 1] as [number, number, number]),
                ),
                new THREE.Vector3(...(p as [number, number, number])),
              ]
            : [],
        ),
      ),
    [points],
  );
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color={color} linewidth={width} />
    </lineSegments>
  );
}

export function ContextGuard({ onUnavailable }: { onUnavailable: () => void }) {
  const gl = useThree((state) => state.gl);
  useEffect(() => {
    const lose = () => onUnavailable();
    gl.domElement.addEventListener("webglcontextlost", lose);
    return () => gl.domElement.removeEventListener("webglcontextlost", lose);
  }, [gl, onUnavailable]);
  return null;
}

export function SceneLighting() {
  return <>
    <hemisphereLight args={["#fffdf7", "#b9c3cd", 1.1]} />
    <directionalLight position={[-3, 10, 6]} intensity={2} castShadow
      shadow-mapSize={[1024, 1024]} shadow-camera-left={-8} shadow-camera-right={8}
      shadow-camera-top={8} shadow-camera-bottom={-8} shadow-normalBias={0.04} />
    <directionalLight position={[5, 4, -6]} intensity={0.6} />
  </>;
}
