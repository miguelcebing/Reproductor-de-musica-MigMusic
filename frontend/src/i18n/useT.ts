/** React hook around the dictionaries (`CONS-006`). */

import { useCallback } from "react";

import { useSettingsStore } from "../state/settingsStore";
import { translate, type MessageKey, type MessageParams } from "./messages";

/** Bound translator: always renders in the language the user picked. */
export function useT(): (key: MessageKey, params?: MessageParams) => string {
  const language = useSettingsStore((state) => state.language);
  return useCallback(
    (key: MessageKey, params?: MessageParams) => translate(language, key, params),
    [language],
  );
}
