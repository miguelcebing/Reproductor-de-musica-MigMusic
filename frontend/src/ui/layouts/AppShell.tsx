/** Application shell: header, centred content column and toast stack. */

import type { ReactNode } from "react";

import { useT } from "../../i18n/useT";
import type { Language } from "../../i18n/messages";
import type { Theme } from "../../state/settingsStore";
import { SpaceBackdrop } from "../background/SpaceBackdrop";
import { ToastContainer } from "../components/ToastContainer";
import type { Toast } from "../../state/toastStore";
import styles from "./AppShell.module.css";

export interface AppShellProps {
  readonly theme: Theme;
  readonly language: Language;
  readonly nodesVisible: boolean;
  readonly toasts: readonly Toast[];
  readonly onToggleTheme: () => void;
  readonly onToggleLanguage: () => void;
  readonly onToggleNodes: () => void;
  readonly onDismissToast: (id: number) => void;
  readonly children: ReactNode;
}

export function AppShell({
  theme,
  language,
  nodesVisible,
  toasts,
  onToggleTheme,
  onToggleLanguage,
  onToggleNodes,
  onDismissToast,
  children,
}: AppShellProps): React.JSX.Element {
  const t = useT();

  return (
    <div className={styles.shell}>
      <SpaceBackdrop />
      <header className={styles.header}>
        <div>
          <p className={styles.brand}>
            MigMusic <span className={styles.tagline}>{t("app.tagline")}</span>
          </p>
        </div>
        <span className={styles.spacer} />
        <div className={styles.headerActions}>
          <button
            type="button"
            onClick={onToggleLanguage}
            aria-label={t("header.language")}
            data-testid="language-toggle"
          >
            {language.toUpperCase()}
          </button>
          <button
            type="button"
            onClick={onToggleTheme}
            aria-label={t("header.theme")}
            data-testid="theme-toggle"
          >
            {theme === "dark" ? "☾" : "☀"}
          </button>
          <button
            type="button"
            onClick={onToggleNodes}
            aria-pressed={nodesVisible}
            aria-label={t("header.nodes")}
            data-testid="nodes-toggle"
          >
            {"<>"}
          </button>
        </div>
      </header>

      <main className={styles.main}>{children}</main>

      <ToastContainer toasts={toasts} onDismiss={onDismissToast} />
    </div>
  );
}
