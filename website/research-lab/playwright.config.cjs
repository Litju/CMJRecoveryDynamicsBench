const { defineConfig, devices } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "./tests",
  timeout: 30000,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:3000", headless: true },
  webServer: {
    command: `python3 -m http.server 3000 --bind 127.0.0.1 --directory ${__dirname}`,
    url: "http://127.0.0.1:3000",
    reuseExistingServer: false,
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" } },
  ],
});
