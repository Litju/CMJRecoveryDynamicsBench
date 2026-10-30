const { test, expect } = require("@playwright/test");
const version = "gate7-lab-v1";
const cors = { "Access-Control-Allow-Origin": "http://127.0.0.1:3000", "Access-Control-Allow-Headers": "X-Lab-Token, Content-Type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Content-Type": "application/json" };
const models = Array.from({ length: 18 }, (_, i) => ({ candidate: `M${Math.floor(i / 2)}`, repeat: i % 2, available: false, qualification: "CPU_SOURCE_QUALIFIED", input_contract: "raw" }));
const observations = [{ id: "training-0", label: "Synthetic training origin", origin: "Example origin", horizon: "H72", source: "synthetic", availability: "available" }];

test.beforeEach(async ({ page }) => {
  await page.route("http://127.0.0.1:8765/v1/**", async (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
    const url = new URL(request.url());
    if (request.headers()["x-lab-token"] !== "local-test-token") return route.fulfill({ status: 401, headers: cors, body: JSON.stringify({ version, error: { code: "UNAUTHORIZED", message: "Access denied." } }) });
    if (url.pathname.endsWith("/health")) return route.fulfill({ headers: cors, body: JSON.stringify({ version, status: "ok" }) });
    if (url.pathname.endsWith("/capabilities")) return route.fulfill({ headers: cors, body: JSON.stringify({ version, models, observations }) });
    const body = request.postDataJSON();
    if (body.candidate === "M8") return route.fulfill({ status: 422, headers: cors, body: JSON.stringify({ version, error: { code: "BASIS_AUTHORITY_REQUIRED", message: "Authenticated basis is unavailable." } }) });
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
  await expect(page.locator("#force")).toHaveText("-0.2500");
  await expect(page.locator("#impulse")).toHaveText("0.0300");
  await expect(page.locator("#cpu-status")).toHaveText("Not applicable — synthetic weights");
  await page.getByLabel("Model family").selectOption("M8");
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByRole("alert")).toContainText("BASIS_AUTHORITY_REQUIRED");
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
