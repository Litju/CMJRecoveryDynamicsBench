(() => {
  "use strict";
  const API = "http://127.0.0.1:8765/v1";
  const VERSION = "gate7-lab-v1";
  const $ = (id) => document.getElementById(id);
  const elements = Object.fromEntries([
    "connect-form", "token", "connect", "connection-state", "connection-message", "controls",
    "candidate", "repeat", "mode", "mode-note", "observation", "observation-note", "origin",
    "horizon", "source", "availability", "availability-text", "predict", "prediction-form",
    "prediction-error", "result-status", "empty-result", "result", "result-kind", "force",
    "impulse", "result-model", "result-origin", "result-identity", "result-provenance", "input-contract", "cpu-status", "cuda-status",
    "qualification-text",
  ].map((id) => [id, $(id)]));
  let token = "";
  let capabilities = null;
  let busy = false;
  let revision = 0;

  function text(id, value) { elements[id].textContent = value; }
  function describe(value) {
    if (typeof value === "string" || typeof value === "number") return String(value);
    return "Not provided";
  }
  function qualificationLabel(value) {
    return ({ qualified: "CPU source qualified", CPU_SOURCE_QUALIFIED: "CPU source qualified", pass: "Passed tolerance", failed: "Failed tolerance", not_applicable_synthetic_weights: "Not applicable — synthetic weights" })[value] || describe(value);
  }
  function resetResult() {
    revision += 1;
    elements.result.hidden = true;
    elements["empty-result"].hidden = false;
    text("result-status", "AWAITING RUN");
    text("prediction-error", "");
  }
  function selectedObservation() {
    return capabilities?.observations.find((item) => item.id === elements.observation.value);
  }
  function selectedModel() {
    return capabilities?.models.find((item) => item.candidate === elements.candidate.value && item.repeat === Number(elements.repeat.value));
  }
  function update() {
    const mode = elements.mode.value;
    const model = selectedModel();
    const observation = selectedObservation();
    const original = mode === "original";
    text("mode-note", original
      ? "Runs only an explicitly authorized, locally configured original checkpoint."
      : "Demonstration weights are synthetic. Results are not recovered model predictions.");
    text("origin", observation ? describe(observation.origin) : "—");
    text("horizon", observation ? describe(observation.horizon) : "—");
    text("source", observation ? describe(observation.source) : "—");
    text("observation-note", observation ? `Input availability: ${describe(observation.availability)}. Basis authority: ${describe(observation.basis_availability)}.` : "No observations are available.");
    const contracts = { raw: "Raw features", raw_history: "Raw features and history", raw_history_horizon: "Raw features, history and horizon", raw_history_horizon_basis: "Raw features, history, horizon and authenticated basis" };
    text("input-contract", contracts[model?.input_contract] || "Not provided");
    if (elements.result.hidden) {
      const qualified = model?.qualification === "CPU_SOURCE_QUALIFIED";
      text("cpu-status", !original ? "Not applicable — synthetic weights" : qualificationLabel(model?.qualification));
      text("cuda-status", !original ? "Not applicable — synthetic weights" : qualified ? (Number(elements.candidate.value.slice(1)) < 4 ? "Passed tolerance" : "Failed tolerance") : "Not provided");
    }
    text("qualification-text", "CPU source fidelity and comparison with saved CUDA predictions are separate. A comparison is not an authentic GPU replay or predictive validation.");
    const blocked = !observation || (original && model?.available !== true);
    elements.availability.className = `availability ${blocked ? "blocked" : "ready"}`;
    text("availability-text", !observation ? "No authorized input is available." : blocked
      ? "Original checkpoint is unavailable for this model and repeat."
      : original ? "Original checkpoint configured. The service will verify input and basis authority."
      : "Synthetic demonstration selected. The service will validate required inputs.");
    elements.predict.disabled = busy || !token || blocked;
  }
  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: { "X-Lab-Token": token, ...(options.body ? { "Content-Type": "application/json" } : {}) },
      cache: "no-store",
    });
    let value;
    try { value = await response.json(); } catch { throw new Error("The local service returned an invalid response."); }
    if (!response.ok) {
      const error = value?.error;
      throw new Error(error && typeof error.code === "string" && typeof error.message === "string"
        ? `${error.code}: ${error.message}` : "The local service refused the request.");
    }
    if (value?.version !== VERSION) throw new Error("The local service returned an incompatible contract version.");
    return value;
  }
  function populate(items) {
    const select = elements.observation;
    select.replaceChildren();
    for (const item of items) {
      if (!item || typeof item.id !== "string") continue;
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = `${describe(item.label || item.id)} · ${describe(item.horizon)} · ${describe(item.source)}`;
      select.append(option);
    }
  }
  function disconnect(message = "Disconnected. The token was cleared.") {
    token = "";
    capabilities = null;
    elements.token.value = "";
    elements.token.disabled = false;
    elements.controls.disabled = true;
    elements.connect.textContent = "Connect ↗";
    elements["connection-state"].classList.remove("connected");
    text("connection-state", "NOT CONNECTED");
    elements["connection-message"].dataset.error = message !== "Disconnected. The token was cleared." ? "true" : "false";
    text("connection-message", message);
    resetResult();
    update();
  }
  for (let index = 0; index <= 8; index += 1) {
    const option = document.createElement("option");
    option.value = `M${index}`;
    option.textContent = `M${index}`;
    elements.candidate.append(option);
  }
  elements["connect-form"].addEventListener("submit", async (event) => {
    event.preventDefault();
    if (token) { disconnect(); return; }
    token = elements.token.value;
    if (!token) return;
    elements.connect.disabled = true;
    text("connection-message", "Connecting to the local service…");
    try {
      const health = await request("/health");
      const data = await request("/capabilities");
      if (health.status !== "ok" || !Array.isArray(data.observations) || !Array.isArray(data.models)) {
        throw new Error("The service did not provide valid capabilities.");
      }
      capabilities = data;
      elements.token.value = "";
      elements.token.disabled = true;
      populate(data.observations);
      elements.controls.disabled = false;
      elements.connect.textContent = "Disconnect";
      elements["connection-state"].classList.add("connected");
      text("connection-state", "CONNECTED");
      elements["connection-message"].dataset.error = "false";
      text("connection-message", "Connected. Select a model and observation to continue.");
      update();
    } catch (error) {
      disconnect(error instanceof Error ? error.message : "Could not connect to the local service.");
    } finally { elements.connect.disabled = false; }
  });
  for (const id of ["candidate", "repeat", "mode", "observation"]) {
    elements[id].addEventListener("change", () => { resetResult(); update(); });
  }
  elements["prediction-form"].addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || !token || !selectedObservation()) return;
    const expected = { version: VERSION, candidate: elements.candidate.value, repeat: Number(elements.repeat.value), observation_id: elements.observation.value, mode: elements.mode.value };
    const current = ++revision;
    busy = true;
    resetResult();
    const requestRevision = revision;
    text("result-status", "RUNNING");
    elements.predict.textContent = "Running inference…";
    update();
    try {
      const data = await request("/predict", { method: "POST", body: JSON.stringify(expected) });
      if (requestRevision !== revision || current + 1 !== revision) return;
      const force = data.outputs?.find((item) => item.target === "relative_mean_concentric_force" && item.unit === "N/kg");
      const impulse = data.outputs?.find((item) => item.target === "relative_concentric_net_impulse" && item.unit === "m/s");
      if (data.candidate !== expected.candidate || data.repeat !== expected.repeat || data.observation_id !== expected.observation_id || data.kind !== (expected.mode === "original" ? "original_checkpoint" : "synthetic_demo") || !Number.isFinite(force?.value) || !Number.isFinite(impulse?.value)) {
        throw new Error("The response did not match the requested model, input or output contract.");
      }
      text("force", force.value.toFixed(4));
      text("impulse", impulse.value.toFixed(4));
      text("result-kind", data.kind === "original_checkpoint" ? "ORIGINAL TRAINED CHECKPOINT" : "SYNTHETIC-WEIGHT DEMONSTRATION · NOT A RECOVERED PREDICTION");
      text("result-model", `${data.candidate} / r${data.repeat}`);
      text("result-origin", `${describe(data.origin)} / ${describe(data.horizon)}`);
      text("result-identity", describe(data.identity));
      text("result-provenance", describe(data.provenance));
      text("cpu-status", qualificationLabel(data.qualification?.cpu_source));
      text("cuda-status", qualificationLabel(data.qualification?.cuda_comparison));
      elements["empty-result"].hidden = true;
      elements.result.hidden = false;
      text("result-status", "COMPLETE");
    } catch (error) {
      if (requestRevision === revision) {
        text("prediction-error", error instanceof Error ? error.message : "Inference could not be completed.");
        text("result-status", "REFUSED");
      }
    } finally {
      busy = false;
      elements.predict.textContent = "Run research inference ↗";
      update();
    }
  });
  update();
})();
