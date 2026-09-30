/** Detect the OAuth landing path (`/callback`) and read its query (`F6`). */

export interface CallbackParams {
  readonly code: string;
  readonly state: string;
}

/** Parse the Spotify reply on `/callback`; `null` when the path is not one. */
export function readCallbackParams(pathname: string, search: string): CallbackParams | null {
  if (pathname.replace(/\/+$/, "") !== "/callback") return null;
  const params = new URLSearchParams(search);
  return { code: params.get("code") ?? "", state: params.get("state") ?? "" };
}
