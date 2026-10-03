/** Lyrics modal for the current track (`F13`).
 *
 * Opens from the player, asks `LyricsController` for the lyrics of the song
 * that is playing, and shows a loading, empty or error state. The text is
 * rendered as JSX text (never HTML), so provider content cannot inject markup.
 */

import { useEffect, useState } from "react";
import {
  ModalBackdrop,
  ModalBody,
  ModalCloseTrigger,
  ModalContainer,
  ModalDialog,
  ModalHeader,
  ModalHeading,
  ModalRoot,
} from "@heroui/react";

import type { Song } from "../../domain/types";
import type { LyricsController, LyricsResult } from "../../services/LyricsController";
import { useT } from "../../i18n/useT";
import type { MessageKey } from "../../i18n/messages";
import styles from "./Lyrics.module.css";

export interface LyricsPanelProps {
  readonly open: boolean;
  readonly song: Song | null;
  readonly controller: LyricsController;
  readonly onClose: () => void;
}

type PanelState =
  | { readonly kind: "loading" }
  | { readonly kind: "ready"; readonly result: LyricsResult };

export function LyricsPanel({
  open,
  song,
  controller,
  onClose,
}: LyricsPanelProps): React.JSX.Element {
  const t = useT();
  const [state, setState] = useState<PanelState>({ kind: "loading" });

  // Load whenever the panel opens or the track changes while it is open.
  useEffect(() => {
    if (!open || !song) return;
    let cancelled = false;
    setState({ kind: "loading" });
    void controller.forSong(song).then((result) => {
      if (!cancelled) setState({ kind: "ready", result });
    });
    return () => {
      cancelled = true;
    };
  }, [open, song, controller]);

  const handleOpenChange = (nextOpen: boolean): void => {
    if (!nextOpen) onClose();
  };

  return (
    <ModalRoot isOpen={open} onOpenChange={handleOpenChange}>
      <ModalBackdrop>
        <ModalContainer placement="center" scroll="inside" size="lg">
          <ModalDialog className={styles.dialog} data-testid="lyrics-dialog">
            <ModalHeader className={styles.header}>
              <ModalHeading className={styles.title}>
                {song ? `${t("lyrics.title")} · ${song.title}` : t("lyrics.title")}
              </ModalHeading>
              <ModalCloseTrigger
                aria-label={t("lyrics.close")}
                className={styles.close}
                data-testid="lyrics-close"
              />
            </ModalHeader>
            <ModalBody className={styles.body} data-testid="lyrics-body">
              {state.kind === "loading" && <p className={styles.status}>{t("lyrics.loading")}</p>}
              {state.kind === "ready" && state.result.status === "empty" && (
                <p className={styles.status} data-testid="lyrics-empty">
                  {t("lyrics.empty")}
                </p>
              )}
              {state.kind === "ready" && state.result.status === "error" && (
                <p className={styles.status} role="alert">
                  {t("lyrics.error")}
                </p>
              )}
              {state.kind === "ready" && state.result.status === "ok" && (
                <>
                  <pre className={styles.text} data-testid="lyrics-text">
                    {state.result.lyrics.text}
                  </pre>
                  <p className={styles.credit}>
                    {t("lyrics.credit", {
                      source: t(`lyrics.source.${state.result.lyrics.source}` as MessageKey),
                    })}
                  </p>
                </>
              )}
            </ModalBody>
          </ModalDialog>
        </ModalContainer>
      </ModalBackdrop>
    </ModalRoot>
  );
}
