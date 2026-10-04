/** Full-screen lyrics view for the current track (`F13`).
 *
 * Opens from the player and fills the screen with the lyrics in a large,
 * readable type. When the provider returned timed (LRC) lines, the current
 * line is highlighted and scrolled into view as the song advances; otherwise
 * the plain text is shown. Text is rendered as JSX (never HTML), so provider
 * content cannot inject markup.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ModalBackdrop,
  ModalCloseTrigger,
  ModalContainer,
  ModalDialog,
  ModalRoot,
} from "@heroui/react";

import type { LyricLine, Song } from "../../domain/types";
import type { LyricsController, LyricsResult } from "../../services/LyricsController";
import { usePlaybackStore } from "../../state/playbackStore";
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

/** Index of the line playing at `position`, or -1 before the first one. */
function activeLineIndex(lines: readonly LyricLine[], position: number): number {
  let active = -1;
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].time <= position) active = index;
    else break;
  }
  return active;
}

export function LyricsPanel({
  open,
  song,
  controller,
  onClose,
}: LyricsPanelProps): React.JSX.Element {
  const t = useT();
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  // Position ticks once a second in the store; subscribing here keeps the
  // rest of the tree from re-rendering for the highlight.
  const position = usePlaybackStore((s) => s.playback?.position ?? 0);
  const lineRefs = useRef<Array<HTMLParagraphElement | null>>([]);

  useEffect(() => {
    if (!open) return;
    if (!song) {
      setState({ kind: "ready", result: { status: "empty" } });
      return;
    }
    let cancelled = false;
    setState({ kind: "loading" });
    void controller.forSong(song).then((result) => {
      if (!cancelled) setState({ kind: "ready", result });
    });
    return () => {
      cancelled = true;
    };
  }, [open, song, controller]);

  const lyrics = state.kind === "ready" && state.result.status === "ok" ? state.result.lyrics : null;
  const lines = useMemo<readonly LyricLine[]>(() => lyrics?.lines ?? [], [lyrics]);
  const synced = lyrics?.synced === true && lines.length > 0;
  const active = useMemo(
    () => (synced ? activeLineIndex(lines, position) : -1),
    [synced, lines, position],
  );

  // Keep the active line centred while the song plays.
  useEffect(() => {
    if (active < 0) return;
    lineRefs.current[active]?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [active]);

  const handleOpenChange = (nextOpen: boolean): void => {
    if (!nextOpen) onClose();
  };

  return (
    <ModalRoot isOpen={open} onOpenChange={handleOpenChange}>
      <ModalBackdrop>
        <ModalContainer placement="center" scroll="inside" size="full">
          <ModalDialog className={styles.dialog} data-testid="lyrics-dialog">
            <header className={styles.header}>
              <div className={styles.headings}>
                <h2 className={styles.title} data-testid="lyrics-title">
                  {song ? song.title : t("lyrics.title")}
                </h2>
                {song && <p className={styles.subtitle}>{song.artist}</p>}
              </div>
              <ModalCloseTrigger
                aria-label={t("lyrics.close")}
                className={styles.close}
                data-testid="lyrics-close"
              />
            </header>
            <div className={styles.body} data-testid="lyrics-body">
              {state.kind === "loading" && (
                <p className={styles.status}>{t("lyrics.loading")}</p>
              )}
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
              {lyrics && !synced && (
                <pre className={styles.plain} data-testid="lyrics-text">
                  {lyrics.text}
                </pre>
              )}
              {synced && (
                <div className={styles.lines} data-testid="lyrics-text">
                  {lines.map((line, index) => (
                    <p
                      key={`${line.time}-${index}`}
                      ref={(element) => {
                        lineRefs.current[index] = element;
                      }}
                      className={`${styles.line} ${index === active ? styles.lineActive : ""}`}
                      data-active={index === active}
                    >
                      {line.text}
                    </p>
                  ))}
                </div>
              )}
              {lyrics && (
                <p className={styles.credit}>
                  {t("lyrics.credit", {
                    source: t(`lyrics.source.${lyrics.source}` as MessageKey),
                  })}
                </p>
              )}
            </div>
          </ModalDialog>
        </ModalContainer>
      </ModalBackdrop>
    </ModalRoot>
  );
}
