import type { NextConfig } from "next";
// trailingSlash emits /paper/index.html etc., so focused routes work on any static host.
const config: NextConfig = { output: "export", poweredByHeader: false, trailingSlash: true };
export default config;
