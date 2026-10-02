/** Spotify login/logout use cases (`SPOTIFY-007`).

 * The browser never sees tokens: it only talks to our backend, which owns
 * the refresh cycle. This controller flips the observable link status and
 * owns the navigation into the OAuth flow.
 */

import { ApiClient, failureMessage } from "./apiClient";
import { useAuthStore } from "../state/authStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface AuthControllerOptions {
  readonly language: () => Language;
  /** Seam for tests; defaults to a full page navigation. */
  readonly navigate?: (url: string) => void;
}

/** Result of the OAuth callback exchange, with a human-readable failure. */
export interface CallbackOutcome {
  readonly ok: boolean;
  readonly message?: string;
}

export class AuthController {
  private readonly api: ApiClient;
  private readonly language: () => Language;
  private readonly navigate: (url: string) => void;

  constructor(api: ApiClient, options: AuthControllerOptions) {
    this.api = api;
    this.language = options.language;
    this.navigate = options.navigate ?? ((url) => window.location.assign(url));
  }

  /** Ask the backend whether this session still holds Spotify tokens. */
  async refresh(): Promise<boolean> {
    useAuthStore.getState().setStatus("checking");
    try {
      const status = await this.api.spotifyStatus();
      this.setLinked(status.authenticated);
      return status.authenticated;
    } catch (cause) {
      this.setLinked(false);
      this.fail(cause, "state.offline");
      return false;
    }
  }

  /** Send the browser to `GET /api/auth/spotify/login`. */
  login(): void {
    this.navigate(this.api.spotifyLoginUrl());
  }

  /** Finish the flow after Spotify bounced the user back to `/callback`. */
  async handleCallback(code: string, state: string): Promise<CallbackOutcome> {
    try {
      const result = await this.api.spotifyCallback(code, state);
      this.setLinked(result.authenticated);
      if (!result.authenticated) {
        return { ok: false, message: "Spotify rejected the callback" };
      }
      this.toast("success", "spotify.connected");
      return { ok: true };
    } catch (cause) {
      this.setLinked(false);
      const message = failureMessage(cause, this.language());
      this.fail(cause, "toast.error");
      return { ok: false, message };
    }
  }

  /** Drop the Spotify session even if the revoke request fails. */
  async logout(): Promise<void> {
    try {
      await this.api.spotifyLogout();
      this.toast("success", "spotify.disconnected");
    } catch (cause) {
      this.fail(cause, "toast.error");
    }
    this.setLinked(false);
  }

  private setLinked(authenticated: boolean): void {
    useAuthStore.getState().setStatus(authenticated ? "linked" : "anonymous");
  }

  private fail(cause: unknown, fallback: MessageKey): void {
    this.toast("error", fallback, { message: failureMessage(cause, this.language()) });
  }

  private toast(kind: "success" | "error", key: MessageKey, params?: Record<string, string | number>): void {
    useToastStore.getState().push(kind, translate(this.language(), key, params));
  }
}
