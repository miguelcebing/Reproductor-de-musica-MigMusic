/** Add-music modal with Local/Spotify tabs and a position picker (`UX-003`). */

import { useEffect, useRef, useState } from "react";

import type { TrackPosition } from "../../domain/types";
import { useT } from "../../i18n/useT";
import styles from "./Queue.module.css";
import { CloseIcon } from "./icons";

export type { TrackPosition };

export interface AddTrackDialogProps {
  readonly open: boolean;
  readonly songsLength: number;
  readonly onClose: () => void;
  readonly onSubmit: (files: File[], position: TrackPosition) => void;
}

export function AddTrackDialog({
  open,
  songsLength,
  onClose,
  onSubmit,
}: AddTrackDialogProps): React.JSX.Element | null {
  const t = useT();
  const [tab, setTab] = useState<"local" | "spotify">("local");
  const [files, setFiles] = useState<readonly File[]>([]);
  const [positionKind, setPositionKind] = useState<"start" | "end" | "index">("end");
  const [index, setIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent): void => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    dialogRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const maxIndex = Math.max(0, songsLength - 1);
  const boundedIndex = Math.min(index, maxIndex);

  const submit = (): void => {
    if (files.length === 0) {
      setError(t("dialog.noFiles"));
      return;
    }
    const position: TrackPosition =
      positionKind === "start"
        ? { kind: "start" }
        : positionKind === "index"
          ? { kind: "index", index: boundedIndex }
          : { kind: "end" };
    onSubmit([...files], position);
    setFiles([]);
    setError(null);
    onClose();
  };

  return (
    <div
      className={styles.dialogBackdrop}
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-track-title"
        tabIndex={-1}
        ref={dialogRef}
        data-testid="add-dialog"
      >
        <div className={styles.playlistBar}>
          <h2 className={styles.dialogTitle} id="add-track-title">
            {t("dialog.addTitle")}
          </h2>
          <button
            type="button"
            className={styles.button}
            aria-label={t("dialog.close")}
            onClick={onClose}
            data-testid="dialog-close"
          >
            <CloseIcon width={16} height={16} />
          </button>
        </div>

        <div className={styles.tabs} role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === "local"}
            className={`${styles.tab} ${tab === "local" ? styles.tabActive : ""}`}
            onClick={() => setTab("local")}
            data-testid="tab-local"
          >
            {t("dialog.tabLocal")}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "spotify"}
            className={`${styles.tab} ${tab === "spotify" ? styles.tabActive : ""}`}
            onClick={() => setTab("spotify")}
            data-testid="tab-spotify"
          >
            {t("dialog.tabSpotify")}
          </button>
        </div>

        {tab === "local" ? (
          <>
            <label className={styles.field}>
              {t("dialog.files")}
              <input
                type="file"
                multiple
                accept="audio/mpeg,audio/wav,.mp3,.wav"
                data-testid="file-input"
                onChange={(event) => {
                  setFiles(Array.from(event.target.files ?? []));
                  setError(null);
                }}
              />
            </label>
            <p className={styles.hint}>{t("dialog.filesHint")}</p>

            <fieldset className={styles.field}>
              <legend>{t("dialog.position")}</legend>
              <div className={styles.positions}>
                {(["start", "end", "index"] as const).map((kind) => (
                  <button
                    key={kind}
                    type="button"
                    className={`${styles.position} ${
                      positionKind === kind ? styles.positionActive : ""
                    }`}
                    aria-pressed={positionKind === kind}
                    onClick={() => setPositionKind(kind)}
                    data-testid={`position-${kind}`}
                  >
                    {kind === "start"
                      ? t("dialog.positionStart")
                      : kind === "end"
                        ? t("dialog.positionEnd")
                        : t("dialog.positionIndex")}
                  </button>
                ))}
              </div>
              {positionKind === "index" && (
                <input
                  type="number"
                  min={0}
                  max={maxIndex}
                  value={boundedIndex}
                  aria-label={t("dialog.positionIndex")}
                  onChange={(event) => setIndex(Number(event.target.value))}
                />
              )}
            </fieldset>
          </>
        ) : (
          <p className={styles.hint} data-testid="spotify-missing">
            {t("dialog.spotifyMissing")}
          </p>
        )}

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        <div className={styles.dialogActions}>
          <button type="button" className={styles.button} onClick={onClose}>
            {t("dialog.cancel")}
          </button>
          <button
            type="button"
            className={`${styles.button} ${styles.buttonPrimary}`}
            onClick={submit}
            data-testid="dialog-submit"
          >
            {t("dialog.submit")}
          </button>
        </div>
      </div>
    </div>
  );
}
