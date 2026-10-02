/** One-shot screen that finishes the OAuth flow on `/callback` (`F6`).

 * Spotify lands the browser here with `?code=…&state=…`; the SPA forwards
 * both to the backend (which owns the exchange) and returns home.
 */

import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@heroui/react";

import { useT } from "../../i18n/useT";
import type { AuthController } from "../../services/AuthController";
import styles from "./Feedback.module.css";

export interface SpotifyCallbackProps {
  readonly code: string;
  readonly state: string;
  readonly auth: AuthController;
  /** Seam for tests; defaults to a full page reload. */
  readonly navigate?: (url: string) => void;
}

export function SpotifyCallback({
  code,
  state,
  auth,
  navigate,
}: SpotifyCallbackProps): React.JSX.Element {
  const t = useT();
  const [error, setError] = useState<string | null>(null);
  const goHome = useMemo(
    () => navigate ?? ((url: string) => window.location.replace(url)),
    [navigate],
  );
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    let cancelled = false;
    void auth.handleCallback(code, state).then((outcome) => {
      if (cancelled) return;
      if (outcome.ok) {
        goHome("/");
        return;
      }
      setError(outcome.message ?? "unknown_error");
    });
    return () => {
      cancelled = true;
    };
  }, [auth, code, state, goHome]);

  return (
    <main className={styles.callback} data-testid="spotify-callback">
      <section className={styles.callbackCard}>
        <h1 className={styles.callbackTitle}>{t("spotify.working")}</h1>
        {error ? (
          <>
            <p className={styles.callbackError} role="alert">
              {t("spotify.failed", { message: error })}
            </p>
            <div className={styles.callbackActions}>
              <Button
                type="button"
                variant="primary"
                onPress={() => goHome("/")}
                data-testid="callback-home"
              >
                {t("dialog.cancel")}
              </Button>
            </div>
          </>
        ) : (
          <p className={styles.callbackHint}>{t("spotify.searching")}</p>
        )}
      </section>
    </main>
  );
}
