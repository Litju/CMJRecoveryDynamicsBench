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
