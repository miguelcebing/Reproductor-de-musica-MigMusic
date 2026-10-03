import { afterEach, describe, expect, it, vi } from "vitest";

import { getDeviceId } from "./deviceId";

/** Minimal `localStorage` stand-in backed by a Map (vitest runs in node). */
function stubStorage(): Map<string, string> {
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => void values.set(key, value),
  });
  return values;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getDeviceId", () => {
  it("still returns an id when there is no storage (ephemeral)", () => {
    vi.stubGlobal("localStorage", undefined);

    expect(getDeviceId()).toBeTruthy();
  });

  it("mints an id once and reuses it afterwards", () => {
    stubStorage();

    const first = getDeviceId();
    const second = getDeviceId();

    expect(first).toBeTruthy();
    expect(second).toBe(first);
  });

  it("keeps an id that is already stored", () => {
    const values = stubStorage();
    values.set("mig_device_id", "device-from-last-week");

    expect(getDeviceId()).toBe("device-from-last-week");
  });

  it("falls back to a stable ephemeral id when storage throws (private mode)", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => {
        throw new Error("denied");
      },
      setItem: () => {
        throw new Error("denied");
      },
    });

    const first = getDeviceId();

    expect(first).toBeTruthy();
    expect(getDeviceId()).toBe(first);
  });
});
