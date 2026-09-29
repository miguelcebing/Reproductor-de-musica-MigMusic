/** Shared constants used across player components. */

import type { RepeatMode } from "../domain/types";

/** The three repeat modes in the order the button cycles through them. */
export const REPEAT_CYCLE: readonly RepeatMode[] = ["off", "one", "all"];