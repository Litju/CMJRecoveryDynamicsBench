// Shared by SVG, Recharts and WebGL so scientific colours keep the same meaning.
export const plotTheme = {
  paper: "#f3f0e7",
  ink: "#202c33",
  cobalt: "#2854b8",
  terracotta: "#b6422b",
  surface: "#fffdf7",
  panel: "#fffdf7",
  grid: "#ccd1ce",
  muted: "#566169",
  text: "#202c33",
  fast: "#2854b8",
  slow: "#b6422b",
  ochre: "#85601d",
  zero: "#586773",
  ridge: "#2854b8",
  structured: "#b6422b",
};
export const plotTooltip = {
  background: plotTheme.panel,
  border: `1px solid ${plotTheme.grid}`,
  borderRadius: 0,
  color: plotTheme.text,
  fontFamily: "inherit",
  fontSize: 12,
  padding: "12px 14px",
  boxShadow: "4px 4px 0 #dddcd2",
};
