/** Resolves API URLs for every environment without duplicating origin logic. */

/** Development uses the Vite proxy; production goes through Vercel's /api rewrite. */
export function resolveApiBaseUrl(origin: string): string {
  if (typeof origin !== "string" || origin.length === 0) {
    throw new TypeError("origin must be a non-empty string");
  }
  return `${origin.replace(/\/+$/, "")}/api`;
}

/** Build the URL for an API route, keeping exactly one slash between segments. */
export function apiUrl(base: string, path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base.replace(/\/+$/, "")}${normalizedPath}`;
}
