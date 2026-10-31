const { test, expect } = require("@playwright/test");
const version = "gate7-lab-v1";
const cors = { "Access-Control-Allow-Origin": "http://127.0.0.1:3000", "Access-Control-Allow-Headers": "X-Lab-Token, Content-Type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Content-Type": "application/json" };
const models = Array.from({ length: 18 }, (_, i) => ({ candidate: `M${Math.floor(i / 2)}`, repeat: i % 2, available: false, qualification: "CPU_SOURCE_QUALIFIED", input_contract: "raw" }));
const observations = [{ id: "training-0", label: "Synthetic training origin", origin: "Example origin", horizon: "H72", source: "synthetic", availability: "available", basis_availability: "unavailable" }];

test.beforeEach(async ({ page }) => {
  await page.route("http://127.0.0.1:8765/v1/**", async (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
    const url = new URL(request.url());
    if (request.headers()["x-lab-token"] !== "local-test-token") return route.fulfill({ status: 401, headers: cors, body: JSON.stringify({ version, error: { code: "UNAUTHORIZED", message: "Access denied." } }) });
    if (url.pathname.endsWith("/health")) return route.fulfill({ headers: cors, body: JSON.stringify({ version, status: "ok" }) });
    if (url.pathname.endsWith("/capabilities")) return route.fulfill({ headers: cors, body: JSON.stringify({ version, models, observations }) });
    const body = request.postDataJSON();
    if (body.candidate === "M8") return route.fulfill({ status: 422, headers: cors, body: JSON.stringify({ version, error: { code: "BASIS_AUTHORITY_UNAVAILABLE", message: "Authenticated basis is unavailable." } }) });
    return route.fulfill({ headers: cors, body: JSON.stringify({ version, kind: "synthetic_demo", candidate: body.candidate, repeat: body.repeat, observation_id: body.observation_id, origin: "Example origin", horizon: "H72", outputs: [{ target: "relative_mean_concentric_force", unit: "N/kg", value: -0.25 }, { target: "relative_concentric_net_impulse", unit: "m/s", value: 0.03 }], qualification: { cpu_source: "not_applicable_synthetic_weights", cuda_comparison: "not_applicable_synthetic_weights" }, provenance: "synthetic-weights", identity: "synthetic-example" }) });
  });
});

test("connect, execute, inspect, refuse and recover without retaining the token", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Recovery, examined." })).toBeVisible();
  await expect(page.getByLabel("Model family")).toBeDisabled();
  await page.getByLabel("Local access token").fill("wrong");
  await page.getByRole("button", { name: /connect/i }).click();
  await expect(page.getByRole("status").filter({ hasText: "UNAUTHORIZED" })).toBeVisible();
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await expect(page.getByText("CONNECTED", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Model family").locator("option")).toHaveCount(9);
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.locator("#result-kind")).toBeVisible();
  await expect(page.locator("#force")).toHaveText("-0.25");
  await expect(page.locator("#force")).toHaveAccessibleName("RELATIVE MEAN CONCENTRIC FORCE N/kg");
  await expect(page.locator("#impulse")).toHaveAccessibleName("RELATIVE CONCENTRIC NET IMPULSE m/s");
  await expect(page.locator("#result-status")).toHaveAttribute("aria-live", "polite");
  await expect(page.locator("#impulse")).toHaveText("0.03");
  await expect(page.locator("#cpu-status")).toHaveText("Not applicable — synthetic weights");
  await page.getByLabel("Model family").selectOption("M8");
  await expect(page.locator("#availability-text")).toContainText("Basis authority is unavailable");
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByRole("alert")).toContainText("BASIS_AUTHORITY_UNAVAILABLE");
  await page.getByLabel("Execution mode").selectOption("original");
  await expect(page.getByText("Original checkpoint is unavailable", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: /run research inference/i })).toBeDisabled();
  await page.getByRole("button", { name: "Disconnect" }).click();
  await expect(page.getByLabel("Local access token")).toHaveValue("");
  expect(await page.evaluate(() => JSON.stringify({ local: localStorage, session: sessionStorage, url: location.href }))).not.toContain("local-test-token");
});

test("keyboard navigation and layout fit", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Local access token")).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  if (process.env.LAB_SCREENSHOT_DIR) await page.screenshot({ path: `${process.env.LAB_SCREENSHOT_DIR}/${testInfo.project.name}.png`, fullPage: true });
});


test("loading state prevents duplicate execution", async ({ page }) => {
  await page.route("http://127.0.0.1:8765/v1/predict", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const body = route.request().postDataJSON();
    await route.fulfill({ headers: cors, body: JSON.stringify({ version, kind: "synthetic_demo", candidate: body.candidate, repeat: body.repeat, observation_id: body.observation_id, origin: "Example origin", horizon: "H72", outputs: [{ target: "relative_mean_concentric_force", unit: "N/kg", value: 0 }, { target: "relative_concentric_net_impulse", unit: "m/s", value: 0 }], qualification: { cpu_source: "not_applicable_synthetic_weights", cuda_comparison: "not_applicable_synthetic_weights" }, provenance: "synthetic-weights", identity: "synthetic-example" }) });
  });
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByRole("button", { name: "Running inference…" })).toBeDisabled();
  await expect(page.locator("#result-status")).toHaveText("COMPLETE");
});

test("the initial screen has no automatically detectable accessibility violations", async ({ page }) => {
  const AxeBuilder = require("@axe-core/playwright").default;
  await page.goto("/");
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations.map(({ id, nodes }) => ({ id, targets: nodes.map((node) => node.target) }))).toEqual([]);
});

test("rejects a response for a different horizon", async ({ page }) => {
  await page.route("http://127.0.0.1:8765/v1/predict", async (route) => {
    const body = route.request().postDataJSON();
    await route.fulfill({ headers: cors, body: JSON.stringify({ version, kind: "synthetic_demo", candidate: body.candidate, repeat: body.repeat, observation_id: body.observation_id, origin: "Example origin", horizon: "D7", outputs: [{ target: "relative_mean_concentric_force", unit: "N/kg", value: 0 }, { target: "relative_concentric_net_impulse", unit: "m/s", value: 0 }] }) });
  });
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByRole("alert")).toContainText("did not match");
  await expect(page.locator("#result")).toBeHidden();
});

test("reports a lost service and reconnects", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.route("http://127.0.0.1:8765/v1/predict", (route) => route.abort("connectionfailed"));
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByText("NOT CONNECTED", { exact: true })).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "Cannot reach the local service" })).toBeVisible();
  await page.unroute("http://127.0.0.1:8765/v1/predict");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.locator("#result-status")).toHaveText("COMPLETE");
  const AxeBuilder = require("@axe-core/playwright").default;
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations.map(({ id }) => id)).toEqual([]);
});

test("disconnect cancels an in-flight prediction and permits a new connection", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.route("http://127.0.0.1:8765/v1/predict", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    await route.abort().catch(() => {});
  });
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByRole("button", { name: "Running inference…" })).toBeDisabled();
  await page.getByRole("button", { name: "Disconnect" }).click();
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await expect(page.getByRole("button", { name: /run research inference/i })).toBeEnabled();
  await page.waitForTimeout(1300);
  await expect(page.getByRole("button", { name: /run research inference/i })).toBeEnabled();
  await expect(page.locator("#result-status")).toHaveText("AWAITING RUN");
});

test("a stalled response times out with reconnect guidance", async ({ page }) => {
  await page.clock.install();
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  let release;
  const stalled = new Promise((resolve) => { release = resolve; });
  await page.route("http://127.0.0.1:8765/v1/predict", async (route) => {
    await stalled;
    await route.abort().catch(() => {});
  });
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByRole("button", { name: "Running inference…" })).toBeDisabled();
  await page.clock.fastForward(30001);
  await expect(page.getByText("NOT CONNECTED", { exact: true })).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "timed out" })).toBeVisible();
  release();
});


test("small nonzero innovations stay visible and fit the viewport", async ({ page }) => {
  await page.route("http://127.0.0.1:8765/v1/predict", async (route) => {
    const body = route.request().postDataJSON();
    await route.fulfill({ headers: cors, body: JSON.stringify({ version, kind: "synthetic_demo", candidate: body.candidate, repeat: body.repeat, observation_id: body.observation_id, origin: "Example origin", horizon: "H72", outputs: [{ target: "relative_mean_concentric_force", unit: "N/kg", value: 0.000000123456789 }, { target: "relative_concentric_net_impulse", unit: "m/s", value: -0.00000004 }] }) });
  });
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.locator("#force")).toHaveText("1.23456789e-7");
  await expect(page.locator("#impulse")).toHaveText("-4e-8");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});


test("displayed precision preserves a float32 value", async ({ page }) => {
  const original = 0.10000206530094147;
  await page.route("http://127.0.0.1:8765/v1/predict", async (route) => {
    const body = route.request().postDataJSON();
    await route.fulfill({ headers: cors, body: JSON.stringify({ version, kind: "synthetic_demo", candidate: body.candidate, repeat: body.repeat, observation_id: body.observation_id, origin: "Example origin", horizon: "H72", outputs: [{ target: "relative_mean_concentric_force", unit: "N/kg", value: original }, { target: "relative_concentric_net_impulse", unit: "m/s", value: 0 }] }) });
  });
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.locator("#force")).toHaveText("0.100002065");
  expect(Math.fround(Number(await page.locator("#force").innerText()))).toBe(Math.fround(original));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});

test("original CPU qualification does not hide a failed saved-CUDA comparison", async ({ page }) => {
  await page.route("http://127.0.0.1:8765/v1/capabilities", route => route.fulfill({
    headers: cors,
    body: JSON.stringify({ version, models: models.map(model => ({ ...model, available: true })), observations: observations.map(observation => ({ ...observation, basis_availability: "authorized" })) }),
  }));
  await page.route("http://127.0.0.1:8765/v1/predict", route => {
    const body = route.request().postDataJSON();
    return route.fulfill({ headers: cors, body: JSON.stringify({
      version, kind: "original_checkpoint", candidate: body.candidate, repeat: body.repeat,
      observation_id: body.observation_id, origin: "Example origin", horizon: "H72",
      outputs: [{ target: "relative_mean_concentric_force", unit: "N/kg", value: 0.1 }, { target: "relative_concentric_net_impulse", unit: "m/s", value: -0.1 }],
      qualification: { cpu_source: "qualified", cuda_comparison: "failed" },
      cuda_evidence: "cpu_vs_saved_cuda_not_gpu_replay", provenance: "test-double", identity: "test-double",
    }) });
  });
  await page.goto("/");
  await page.getByLabel("Local access token").fill("local-test-token");
  await page.getByRole("button", { name: /connect/i }).click();
  await page.getByLabel("Model family").selectOption("M8");
  await page.getByLabel("Execution mode").selectOption("original");
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.locator("#cpu-status")).toHaveText("CPU source qualified");
  await expect(page.locator("#cuda-status")).toHaveText("Failed tolerance");
  await expect(page.locator("#result-provenance")).toHaveText("test-double");
});
