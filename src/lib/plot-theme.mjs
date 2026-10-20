// Shared by SVG, Recharts and WebGL so scientific colours keep the same meaning.
export const plotTheme = {
  paper: "#f3f0e7",
  ink: "#202c33",
  cobalt: "#2854b8",
  terracotta: "#b6422b",
  surface: "#192b35",
  panel: "#21343e",
  grid: "#465e6b",
  muted: "#bdcbd3",
  text: "#f4f0e7",
  fast: "#a6c6f3",
  slow: "#f1a486",
  ochre: "#e8be6c",
  zero: "#a6b1b8",
  ridge: "#92bbf3",
  structured: "#f19a7c",
};
export const plotTooltip = {
  background: plotTheme.panel,
  border: `1px solid ${plotTheme.grid}`,
  borderRadius: 0,
  color: plotTheme.text,
  fontFamily: "inherit",
  fontSize: 12,
  padding: "12px 14px",
  boxShadow: "4px 4px 0 #12212a",
};
