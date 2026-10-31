const { test, expect } = require("@playwright/test");

test("real local service executes a synthetic fixture", async ({ page }, testInfo) => {
  test.skip(!process.env.LAB_LIVE_TOKEN, "Set LAB_LIVE_TOKEN and start the local inference service");
  await page.goto("/");
  await page.getByLabel("Local access token").fill(process.env.LAB_LIVE_TOKEN);
  await page.getByRole("button", { name: /connect/i }).click();
  await expect(page.getByText("CONNECTED", { exact: true })).toBeVisible();
  await page.getByLabel("Model family").selectOption("M0");
  await page.getByLabel("Execution mode").selectOption("synthetic_demo");
  await page.getByLabel("Observation selection").selectOption("training-0");
  const response = page.waitForResponse((value) => value.url() === "http://127.0.0.1:8765/v1/predict" && value.request().method() === "POST");
  await page.getByRole("button", { name: /run research inference/i }).click();
  expect((await response).ok()).toBeTruthy();
  await expect(page.locator("#result-kind")).toContainText("NOT A RECOVERED PREDICTION");
  await expect(page.locator("#force")).not.toHaveText("—");
  await expect(page.locator("#impulse")).not.toHaveText("—");
  await expect(page.locator("#result-provenance")).toHaveText("synthetic-weights");
  if (process.env.LAB_SCREENSHOT_DIR) await page.screenshot({ path: `${process.env.LAB_SCREENSHOT_DIR}/live-${testInfo.project.name}.png`, fullPage: true });
  await page.getByRole("button", { name: "Disconnect" }).click();
  await expect(page.getByLabel("Local access token")).toHaveValue("");
});

test("all eighteen candidate/repeat routes preserve live response identity", async ({ page }) => {
  test.skip(!process.env.LAB_LIVE_TOKEN, "Start tests/research_lab_service.py with LAB_LIVE_TOKEN");
  test.setTimeout(180000);
  await page.goto("/");
  await page.getByLabel("Local access token").fill(process.env.LAB_LIVE_TOKEN);
  await page.getByRole("button", { name: /connect/i }).click();
  await expect(page.getByText("CONNECTED", { exact: true })).toBeVisible();
  const identities = new Set();
  for (let candidate = 0; candidate < 9; candidate++) {
    for (let repeat = 0; repeat < 2; repeat++) {
      await page.getByLabel("Model family").selectOption(`M${candidate}`);
      await page.getByLabel("Final repeat").selectOption(String(repeat));
      await page.getByLabel("Observation selection").selectOption(`training-${repeat}`);
      const pending = page.waitForResponse(response => response.url().endsWith("/v1/predict") && response.request().method() === "POST");
      await page.getByRole("button", { name: /run research inference/i }).click();
      const response = await pending;
      expect(response.ok()).toBeTruthy();
      const result = await response.json();
      expect([result.candidate, result.repeat, result.observation_id, result.horizon]).toEqual([`M${candidate}`, repeat, `training-${repeat}`, repeat ? "D7" : "H72"]);
      expect(result.outputs.map(({ target, unit }) => [target, unit])).toEqual([
        ["relative_mean_concentric_force", "N/kg"], ["relative_concentric_net_impulse", "m/s"],
      ]);
      expect(result.provenance).toBe("synthetic-weights");
      expect(result.qualification.cpu_source).toBe("not_applicable_synthetic_weights");
      expect(result.cuda_evidence).toBe("not_applicable");
      await expect(page.locator("#result-identity")).toHaveText(result.identity);
      await expect(page.locator("#result-origin")).toHaveText(`Origin-1 / ${result.horizon}`);
      identities.add(result.identity);
    }
  }
  expect(identities.size).toBe(18);
  await page.getByLabel("Observation selection").selectOption("training-2");
  await page.getByRole("button", { name: /run research inference/i }).click();
  await expect(page.getByRole("alert")).toContainText("BASIS_AUTHORITY_UNAVAILABLE");
  await page.getByLabel("Execution mode").selectOption("original");
  await expect(page.getByRole("button", { name: /run research inference/i })).toBeDisabled();
});
