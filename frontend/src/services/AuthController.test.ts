import { beforeEach, describe, expect, it } from "vitest";

import { ApiClient, type FetchLike } from "./apiClient";
import { AuthController } from "./AuthController";
import { useAuthStore } from "../state/authStore";
import { useToastStore } from "../state/toastStore";

interface Stub {
  fetchImpl: FetchLike;
  calls: { url: string; init?: RequestInit | undefined }[];
  navigate: (url: string) => void;
  visited: string[];
}

function stub(status: number, body: unknown): Stub {
  const calls: { url: string; init?: RequestInit | undefined }[] = [];
  const visited: string[] = [];
  return {
    calls,
    visited,
    navigate: (url) => visited.push(url),
    fetchImpl: (url, init) => {
      calls.push({ url, init });
      return Promise.resolve(
        new Response(status === 204 ? null : JSON.stringify(body), {
          status,
          headers: { "content-type": "application/json" },
        }),
      );
    },
  };
}

function controller(s: Stub): AuthController {
  return new AuthController(ApiClient.fromOrigin("https://app.test", s.fetchImpl), {
    language: () => "es",
    navigate: s.navigate,
  });
}

beforeEach(() => {
  useAuthStore.getState().reset();
  useToastStore.getState().reset();
});

describe("AuthController", () => {
  it("marks the session as linked when the backend says so", async () => {
    const s = stub(200, { authenticated: true });
    await expect(controller(s).refresh()).resolves.toBe(true);
    expect(useAuthStore.getState().status).toBe("linked");
  });

  it("falls back to anonymous when the status call fails", async () => {
    const failing: Stub = {
      ...stub(0, {}),
      fetchImpl: () => Promise.reject(new Error("offline")),
    };
    const auth = controller(failing);
    await expect(auth.refresh()).resolves.toBe(false);
    expect(useAuthStore.getState().status).toBe("anonymous");
    expect(useToastStore.getState().toasts[0]?.kind).toBe("error");
  });

  it("navigates to the backend login route", () => {
    const s = stub(200, {});
    controller(s).login();
    expect(s.visited).toEqual(["https://app.test/api/auth/spotify/login"]);
  });

  it("stores the link and toasts after a successful callback", async () => {
    const s = stub(200, { authenticated: true });
    const outcome = await controller(s).handleCallback("code", "state");
    expect(outcome).toEqual({ ok: true });
    expect(useAuthStore.getState().status).toBe("linked");
    expect(useToastStore.getState().toasts.at(-1)?.kind).toBe("success");
    expect(JSON.parse(String(s.calls[0]?.init?.body))).toEqual({
      code: "code",
      state: "state",
    });
  });

  it("reports a readable message when the callback exchange fails", async () => {
    const failing: Stub = {
      ...stub(0, {}),
      fetchImpl: () => Promise.reject(new Error("state mismatch")),
    };
    const outcome = await controller(failing).handleCallback("code", "state");
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toBe("state mismatch");
    expect(useAuthStore.getState().status).toBe("anonymous");
  });

  it("clears the link even when the logout request fails", async () => {
    const s = stub(204, {});
    const auth = controller(s);
    useAuthStore.getState().setStatus("linked");
    await auth.logout();
    expect(s.calls[0]?.init?.method).toBe("POST");
    expect(useAuthStore.getState().status).toBe("anonymous");
  });
});
