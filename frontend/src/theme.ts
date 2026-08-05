export type AppearancePreference = "system" | "light" | "dark";
export type ResolvedAppearance = "light" | "dark";

export const APPEARANCE_STORAGE_KEY = "jarvisos:appearance:v1";
export const APPEARANCE_OPTIONS: readonly AppearancePreference[] = ["system", "light", "dark"];

function isAppearancePreference(value: unknown): value is AppearancePreference {
  return value === "system" || value === "light" || value === "dark";
}

function safeStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function safeColorSchemeQuery(): MediaQueryList | null {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return null;
  try {
    return window.matchMedia("(prefers-color-scheme: dark)");
  } catch {
    return null;
  }
}

export function readAppearancePreference(): AppearancePreference {
  const storage = safeStorage();
  if (!storage) return "system";
  try {
    const value = storage.getItem(APPEARANCE_STORAGE_KEY);
    return isAppearancePreference(value) ? value : "system";
  } catch {
    return "system";
  }
}

export function writeAppearancePreference(preference: AppearancePreference): void {
  const storage = safeStorage();
  if (!storage) return;
  try {
    storage.setItem(APPEARANCE_STORAGE_KEY, preference);
  } catch {
    // Appearance persistence is best-effort and carries no application authority.
  }
}

export function resolveAppearance(preference: AppearancePreference): ResolvedAppearance {
  if (preference === "light" || preference === "dark") return preference;
  return safeColorSchemeQuery()?.matches ? "dark" : "light";
}

export function applyResolvedAppearance(resolved: ResolvedAppearance): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.dataset.theme = resolved;
  root.style.colorScheme = resolved;
}

export function applyAppearancePreference(preference: AppearancePreference): ResolvedAppearance {
  const resolved = resolveAppearance(preference);
  applyResolvedAppearance(resolved);
  return resolved;
}

export function applyStoredAppearance(): AppearancePreference {
  const preference = readAppearancePreference();
  applyAppearancePreference(preference);
  return preference;
}

export function subscribeToSystemAppearance(
  preference: AppearancePreference,
  onChange: (resolved: ResolvedAppearance) => void
): () => void {
  if (preference !== "system") return () => undefined;
  const query = safeColorSchemeQuery();
  if (!query) return () => undefined;

  const listener = (event: MediaQueryListEvent | MediaQueryList) => {
    onChange(event.matches ? "dark" : "light");
  };

  if (typeof query.addEventListener === "function") {
    query.addEventListener("change", listener);
    return () => query.removeEventListener("change", listener);
  }

  query.addListener(listener);
  return () => query.removeListener(listener);
}
