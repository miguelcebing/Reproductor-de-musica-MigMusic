/** Volume slider and mute (`VIS-011`: the control reacts to hover/focus). */

import { memo } from "react";

import { useT } from "../../i18n/useT";
import styles from "./Player.module.css";
import { IconButton } from "./IconButton";
import { MuteIcon, VolumeIcon } from "./icons";

export interface VolumeControlProps {
  readonly volume: number;
  readonly muted: boolean;
  readonly onVolume: (volume: number) => void;
  readonly onToggleMute: () => void;
}

export const VolumeControl = memo(function VolumeControl({
  volume,
  muted,
  onVolume,
  onToggleMute,
}: VolumeControlProps): React.JSX.Element {
  const t = useT();
  const effective = muted ? 0 : volume;

  return (
    <div className={styles.volume}>
      <IconButton
        label={muted ? t("player.unmute") : t("player.mute")}
        onClick={onToggleMute}
        testId="mute"
      >
        {muted || effective === 0 ? <MuteIcon /> : <VolumeIcon />}
      </IconButton>
      <input
        className={styles.volumeSlider}
        type="range"
        min={0}
        max={100}
        step={1}
        value={Math.round(effective * 100)}
        aria-label={t("player.volume")}
        data-testid="volume"
        onChange={(event) => onVolume(Number(event.target.value) / 100)}
      />
    </div>
  );
});
