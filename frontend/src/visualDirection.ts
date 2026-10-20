// Issue #834 / spec 198 visual-direction exploration hook (round 2) (prototype, not authorized for merge).
// Purely presentational: sets data-jarvis-theme on <html>; no engineering state, API, routing or data is touched.
// Default (no param, nothing stored) leaves the attribute absent, so the current UI is unchanged.
// Select with ?direction=lumen2-dark|lumen2-light (Lumen v2, focused iteration) or the round-1 references
// lumen|herbarium|rhizome; ?direction=current clears the stored choice. Lumen v2 modes also set data-jarvis-family.

export const VISUAL_DIRECTIONS = ["lumen2-dark", "lumen2-light", "lumen", "herbarium", "rhizome"] as const;
export type VisualDirection = (typeof VISUAL_DIRECTIONS)[number];
export const VISUAL_DIRECTION_STORAGE_KEY = "jarvisos:visual-direction:v198b";

function isVisualDirection(value: unknown): value is VisualDirection {
  return VISUAL_DIRECTIONS.includes(value as VisualDirection);
}

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function applyVisualDirection(): VisualDirection | null {
  if (typeof window === "undefined" || typeof document === "undefined") return null;
  const store = storage();
  let requested: string | null = null;
  try {
    requested = new URLSearchParams(window.location.search).get("direction");
  } catch {
    requested = null;
  }
  try {
    if (requested !== null) {
      if (isVisualDirection(requested)) store?.setItem(VISUAL_DIRECTION_STORAGE_KEY, requested);
      else store?.removeItem(VISUAL_DIRECTION_STORAGE_KEY);
    }
  } catch {
    // Visual preference persistence is best effort.
  }
  let stored: string | null = null;
  try {
    stored = store?.getItem(VISUAL_DIRECTION_STORAGE_KEY) ?? null;
  } catch {
    stored = null;
  }
  const candidate = requested !== null ? requested : stored;
  const direction = isVisualDirection(candidate) ? candidate : null;
  const root = document.documentElement;
  if (direction) root.dataset.jarvisTheme = direction;
  else delete root.dataset.jarvisTheme;
  if (direction?.startsWith("lumen2-")) root.dataset.jarvisFamily = "lumen2";
  else delete root.dataset.jarvisFamily;
  return direction;
}
