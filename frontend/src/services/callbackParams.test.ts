import { describe, expect, it } from "vitest";

import { readCallbackParams } from "./callbackParams";

describe("readCallbackParams", () => {
  it("reads code and state from the OAuth landing path", () => {
    expect(readCallbackParams("/callback", "?code=abc&state=xyz")).toEqual({
      code: "abc",
      state: "xyz",
    });
  });

  it("tolerates a trailing slash", () => {
    expect(readCallbackParams("/callback/", "?code=abc&state=xyz")?.code).toBe("abc");
  });

  it("returns null on any other path", () => {
    expect(readCallbackParams("/", "?code=abc&state=xyz")).toBeNull();
    expect(readCallbackParams("/playlists", "")).toBeNull();
  });

  it("keeps empty strings when the reply is incomplete", () => {
    expect(readCallbackParams("/callback", "?error=access_denied")).toEqual({
      code: "",
      state: "",
    });
  });
});
