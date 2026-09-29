import { describe, expect, it } from "vitest";

import { apiUrl, resolveApiBaseUrl } from "./apiClient";

describe("resolveApiBaseUrl", () => {
  it("appends /api to the given origin", () => {
    expect(resolveApiBaseUrl("https://migmusic.vercel.app")).toBe(
      "https://migmusic.vercel.app/api",
    );
  });

  it("tolerates origins with a trailing slash", () => {
    expect(resolveApiBaseUrl("http://127.0.0.1:5173/")).toBe(
      "http://127.0.0.1:5173/api",
    );
  });

  it("rejects an empty origin instead of producing a broken URL", () => {
    expect(() => resolveApiBaseUrl("")).toThrow(TypeError);
  });
});

describe("apiUrl", () => {
  it("joins base and path with a single slash", () => {
    expect(apiUrl("https://example.com/api", "/health")).toBe(
      "https://example.com/api/health",
    );
  });

  it("normalizes a path that does not start with a slash", () => {
    expect(apiUrl("https://example.com/api", "health")).toBe(
      "https://example.com/api/health",
    );
  });
});
