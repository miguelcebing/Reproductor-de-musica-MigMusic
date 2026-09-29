/** Toast stack (`UX-004`); dismissible and announced politely. */

import { useT } from "../../i18n/useT";
import type { Toast } from "../../state/toastStore";
import styles from "./Feedback.module.css";
import { CloseIcon } from "./icons";

export interface ToastContainerProps {
  readonly toasts: readonly Toast[];
  readonly onDismiss: (id: number) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps): React.JSX.Element | null {
  const t = useT();
  if (toasts.length === 0) return null;

  return (
    <div className={styles.toasts} role="status" aria-live="polite" data-testid="toasts">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`${styles.toast} ${
            toast.kind === "error" ? styles.toastError : toast.kind === "success" ? styles.toastSuccess : ""
          }`}
          data-kind={toast.kind}
        >
          <span>{toast.text}</span>
          <button
            type="button"
            className={styles.toastClose}
            aria-label={t("dialog.close")}
            onClick={() => onDismiss(toast.id)}
          >
            <CloseIcon width={14} height={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
