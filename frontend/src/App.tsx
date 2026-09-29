import { useEffect, useState } from "react";

interface HealthPayload {
  status: string;
  service: string;
  environment: string;
}

/** Application shell. Real views are added in F4 (frontend base). */
export function App(): React.JSX.Element {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetch("/api/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json() as Promise<HealthPayload>;
      })
      .then((payload) => {
        if (!cancelled) {
          setHealth(payload);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "unknown error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="app-shell">
      <h1>MigMusic</h1>
      <p className="app-shell__tagline">
        Reproductor de música con lista doblemente enlazada
      </p>
      <p className="app-shell__status" data-testid="api-status">
        {health
          ? `API ${health.status} · ${health.environment}`
          : (error ?? "Consultando la API…")}
      </p>
    </main>
  );
}
