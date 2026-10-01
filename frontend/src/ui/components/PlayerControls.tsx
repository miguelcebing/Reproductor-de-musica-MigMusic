/** Transport buttons (`PLAYER-001/002`, `FEAT-001-d`). */

import type { RepeatMode, SkipDirection } from "../../domain/types";
import { useT } from "../../i18n/useT";
import styles from "./Player.module.css";
import { AnimatePresence, motion } from "framer-motion";
import { IconButton } from "./IconButton";
import { BackIcon, ForwardIcon, NextIcon, PauseIcon, PlayIcon, PreviousIcon, RepeatIcon, ShuffleIcon } from "./icons";

export interface PlayerControlsProps {
  readonly playing: boolean;
  readonly disabled: boolean;
  readonly canPrevious: boolean;
  readonly canNext: boolean;
  readonly shuffle: boolean;
  readonly repeat: RepeatMode;
  readonly skipSeconds: number;
  readonly onTogglePlay: () => void;
  readonly onPrevious: () => void;
  readonly onNext: () => void;
  readonly onSkip: (direction: SkipDirection) => void;
  readonly onToggleShuffle: () => void;
  readonly onCycleRepeat: () => void;
}

export function PlayerControls({
  playing,
  disabled,
  canPrevious,
  canNext,
  shuffle,
  repeat,
  skipSeconds,
  onTogglePlay,
  onPrevious,
  onNext,
  onSkip,
  onToggleShuffle,
  onCycleRepeat,
}: PlayerControlsProps): React.JSX.Element {
  const t = useT();

  return (
    <div className={styles.controls} role="group" aria-label={t("player.controls")}>
      <IconButton
        label={t("player.shuffle")}
        onClick={onToggleShuffle}
        active={shuffle}
        disabled={disabled}
        testId="shuffle"
      >
        <ShuffleIcon />
      </IconButton>

      <IconButton
        label={t("player.backward", { seconds: skipSeconds })}
        onClick={() => onSkip("backward")}
        disabled={disabled}
        testId="skip-backward"
      >
        <BackIcon />
      </IconButton>

      <IconButton
        label={t("player.previous")}
        onClick={onPrevious}
        disabled={disabled || !canPrevious}
        testId="previous"
      >
        <PreviousIcon />
      </IconButton>

      <IconButton
        label={playing ? t("player.pause") : t("player.play")}
        onClick={onTogglePlay}
        disabled={disabled}
        primary
        testId="play-pause"
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={playing ? "pause" : "play"}
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.7 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            style={{ display: "inline-flex" }}
          >
            {playing ? <PauseIcon width={26} height={26} /> : <PlayIcon width={26} height={26} />}
          </motion.span>
        </AnimatePresence>
      </IconButton>

      <IconButton
        label={t("player.next")}
        onClick={onNext}
        disabled={disabled || !canNext}
        testId="next"
      >
        <NextIcon />
      </IconButton>

      <IconButton
        label={t("player.forward", { seconds: skipSeconds })}
        onClick={() => onSkip("forward")}
        disabled={disabled}
        testId="skip-forward"
      >
        <ForwardIcon />
      </IconButton>

      <IconButton
        label={`${t("player.repeat")}: ${repeat}`}
        onClick={onCycleRepeat}
        active={repeat !== "off"}
        disabled={disabled}
        testId="repeat"
      >
        <RepeatIcon />
      </IconButton>
    </div>
  );
}
