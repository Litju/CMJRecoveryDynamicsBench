"use client";
// Shareable figure state in the query string, e.g. /results/?f6root=B#fig-6.
// Reads after hydration (static export has no request-time params) and writes with replaceState.
import { useCallback, useEffect, useState } from "react";

export function useUrlState<T extends string>(
  key: string,
  initial: T,
  allowed: readonly T[],
): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(initial);
  useEffect(() => {
    const read = () => {
      const v = new URLSearchParams(window.location.search).get(key) as T | null;
      setValue(v && allowed.includes(v) ? v : initial);
    };
    read();
    window.addEventListener("popstate", read);
    return () => window.removeEventListener("popstate", read);
    // allowed/initial are static per call site
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const update = useCallback(
    (next: T) => {
      setValue(next);
      const url = new URL(window.location.href);
      if (next === initial) url.searchParams.delete(key);
      else url.searchParams.set(key, next);
      window.history.replaceState(window.history.state, "", url);
    },
    [key, initial],
  );
  return [value, update];
}
