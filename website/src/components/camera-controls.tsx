"use client";
export type CameraPose = [number, number, number];
export function CameraControls({
  onView,
  drag,
  onDrag,
  zoom,
  onZoom,
  disabled = false,
}: {
  onView: (pose: CameraPose) => void;
  drag: boolean;
  onDrag: () => void;
  zoom: number;
  onZoom: (zoom: number) => void;
  disabled?: boolean;
}) {
  return (
    <fieldset className="scene-controls" disabled={disabled}>
      <legend>3D camera · keyboard, pointer & touch</legend>
      <div className="scene-view-buttons">
        <button onClick={() => onView([9, 8, 11])}>Isometric view</button>
        <button onClick={() => onView([0, 5, 14])}>Front view</button>
        <button onClick={() => onView([0, 16, 0.01])}>Overhead view</button>
        <button onClick={onDrag} aria-pressed={drag}>
          {drag ? "Disable drag rotation" : "Enable drag rotation"}
        </button>
      </div>
      <label>
        Scene scale{" "}
        <input
          type="range"
          aria-label="3D scene scale"
          min="28"
          max="65"
          value={zoom}
          onChange={(e) => onZoom(Number(e.target.value))}
        />
      </label>
      <small>
        {drag
          ? "Drag the figure to orbit; disable rotation to scroll through it on touch."
          : "Use the view buttons or enable drag rotation. Page scrolling stays available."}
      </small>
    </fieldset>
  );
}
