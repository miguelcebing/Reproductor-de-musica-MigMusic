/** Debounce a changing value (`PERF`): wait for a pause before reacting.

 * Used by live-search inputs so a keystroke every 40 ms does not trigger a
 * filter/network pass every time; the value settles ~300 ms after typing stops.
 */

import { useEffect, useState } from "react";

export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
