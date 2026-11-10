// Descriptive public names for the recovered M0–M8 families, shared by the model
// atlas and the manuscript figures. Original identifiers stay in technical details.
export const familyNames: Record<string, string> = {
  M0: "Compact feedforward",
  M1: "Wide feedforward",
  M2: "Deep feedforward",
  M3: "History encoder",
  M4: "Recurrent history",
  M5: "Horizon-aware recurrent",
  M6: "Two-basis recurrent",
  M7: "Five-basis recurrent",
  M8: "Additive basis model",
};
export const familySlug = (id: string) =>
  familyNames[id].toLowerCase().replace(/[^a-z0-9]+/g, "-");
/** Deep link into the original model atlas on the overview page. */
export const atlasLink = (id: string, run = 1) =>
  `/?architecture=${familySlug(id)}&run=${run}#model-atlas`;
