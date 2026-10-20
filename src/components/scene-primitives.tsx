"use client";
import { useEffect, useMemo, useRef } from "react";
import { useThree } from "@react-three/fiber";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import * as THREE from "three";
import { plotTheme } from "@/lib/plot-theme.mjs";
import type { CameraPose } from "./camera-controls";
export function CameraRig({
  pose,
  drag,
  zoom,
}: {
  pose: CameraPose;
  drag: boolean;
  zoom: number;
}) {
  const { camera, gl, invalidate, size } = useThree();
  const controls = useRef<OrbitControls | null>(null);
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
    camera.position.set(...pose);
    camera.lookAt(0, 1, 0);
    controls.current?.update();
    invalidate();
  }, [camera, pose, invalidate]);
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
}: {
  text: string;
  position: [number, number, number];
  color?: string;
  width?: number;
}) {
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
  if (!texture) return null;
  return (
    <sprite
      position={position}
      scale={[
        Math.min(0.38 / 80, width / texture.image.width) * texture.image.width,
        Math.min(0.38 / 80, width / texture.image.width) * 80,
        1,
      ]}
    >
      <spriteMaterial map={texture} transparent depthTest={false} />
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
