export type AppearancePreference = "system" | "light" | "dark";
export type ResolvedAppearance = "light" | "dark";
export type AccentPreset = "microalgae" | "leaf-chlorophyll" | "lagoon" | "custom";

export type AccentPreference = Readonly<{
  preset: AccentPreset;
  customHex?: string;
}>;

export const APPEARANCE_STORAGE_KEY = "jarvisos:appearance:v1";
export const APPEARANCE_OPTIONS: readonly AppearancePreference[] = ["system", "light", "dark"];
export const ACCENT_STORAGE_KEY = "jarvisos:accent:v1";
export const VISUAL_PREFERENCE_EVENT = "jarvisos:visual-preference-change";
export const DEFAULT_ACCENT_HEX = "#528B68";
export const ACCENT_PRESETS: Readonly<Record<Exclude<AccentPreset, "custom">, string>> = {
  microalgae: DEFAULT_ACCENT_HEX,
  "leaf-chlorophyll": "#5F8F52",
  lagoon: "#4F938A"
};
export const ACCENT_OPTIONS: readonly AccentPreset[] = [
  "microalgae",
  "leaf-chlorophyll",
  "lagoon",
  "custom"
];

const ACCENT_FOREGROUND_LIGHT = "#FFFFFF";
const ACCENT_FOREGROUND_DARK = "#000000";

function isAppearancePreference(value: unknown): value is AppearancePreference {
  return value === "system" || value === "light" || value === "dark";
}

function isAccentPreset(value: unknown): value is AccentPreset {
  return ACCENT_OPTIONS.includes(value as AccentPreset);
}

export function normalizeAccentHex(value: string): string | null {
  const normalized = value.trim().toUpperCase();
  return /^#[0-9A-F]{6}$/.test(normalized) ? normalized : null;
}

function srgbChannelToLinear(channel: number): number {
  const normalized = channel / 255;
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex: string): number {
  const normalized = normalizeAccentHex(hex) ?? DEFAULT_ACCENT_HEX;
  const red = srgbChannelToLinear(Number.parseInt(normalized.slice(1, 3), 16));
  const green = srgbChannelToLinear(Number.parseInt(normalized.slice(3, 5), 16));
  const blue = srgbChannelToLinear(Number.parseInt(normalized.slice(5, 7), 16));
  return (0.2126 * red) + (0.7152 * green) + (0.0722 * blue);
}

function contrastRatio(firstHex: string, secondHex: string): number {
  const first = relativeLuminance(firstHex);
  const second = relativeLuminance(secondHex);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

export function accentForegroundHex(seedHex: string): string {
  const normalized = normalizeAccentHex(seedHex) ?? DEFAULT_ACCENT_HEX;
  const lightContrast = contrastRatio(normalized, ACCENT_FOREGROUND_LIGHT);
  const darkContrast = contrastRatio(normalized, ACCENT_FOREGROUND_DARK);
  return lightContrast >= darkContrast ? ACCENT_FOREGROUND_LIGHT : ACCENT_FOREGROUND_DARK;
}

function safeStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function notifyVisualPreferenceChange(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(VISUAL_PREFERENCE_EVENT));
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
  if (storage) {
    try {
      storage.setItem(APPEARANCE_STORAGE_KEY, preference);
    } catch {
      // Appearance persistence is best-effort and carries no application authority.
    }
  }
  notifyVisualPreferenceChange();
}

export function readAccentPreference(): AccentPreference {
  const storage = safeStorage();
  if (!storage) return { preset: "microalgae" };
  try {
    const raw = storage.getItem(ACCENT_STORAGE_KEY);
    if (!raw) return { preset: "microalgae" };
    const parsed = JSON.parse(raw) as { preset?: unknown; customHex?: unknown };
    if (!isAccentPreset(parsed.preset)) return { preset: "microalgae" };
    if (parsed.preset !== "custom") return { preset: parsed.preset };
    if (typeof parsed.customHex !== "string") return { preset: "microalgae" };
    const customHex = normalizeAccentHex(parsed.customHex);
    return customHex ? { preset: "custom", customHex } : { preset: "microalgae" };
  } catch {
    return { preset: "microalgae" };
  }
}

export function writeAccentPreference(preference: AccentPreference): AccentPreference {
  const safePreference = preference.preset === "custom"
    ? (() => {
      const customHex = normalizeAccentHex(preference.customHex ?? "");
      return customHex ? { preset: "custom" as const, customHex } : { preset: "microalgae" as const };
    })()
    : isAccentPreset(preference.preset)
      ? { preset: preference.preset }
      : { preset: "microalgae" as const };
  const storage = safeStorage();
  if (storage) {
    try {
      storage.setItem(ACCENT_STORAGE_KEY, JSON.stringify(safePreference));
    } catch {
      // Accent persistence is visual-only best effort.
    }
  }
  notifyVisualPreferenceChange();
  return safePreference;
}

export function accentHex(preference: AccentPreference): string {
  if (preference.preset === "custom") {
    return normalizeAccentHex(preference.customHex ?? "") ?? DEFAULT_ACCENT_HEX;
  }
  return ACCENT_PRESETS[preference.preset] ?? DEFAULT_ACCENT_HEX;
}

export function applyAccentPreference(preference: AccentPreference): AccentPreference {
  const safePreference = preference.preset === "custom"
    ? (() => {
      const customHex = normalizeAccentHex(preference.customHex ?? "");
      return customHex ? { preset: "custom" as const, customHex } : { preset: "microalgae" as const };
    })()
    : isAccentPreset(preference.preset)
      ? { preset: preference.preset }
      : { preset: "microalgae" as const };
  if (typeof document === "undefined") return safePreference;
  const root = document.documentElement;
  const seed = accentHex(safePreference);
  root.dataset.accent = safePreference.preset;
  root.style.setProperty("--accent-seed", seed);
  root.style.setProperty("--color-accent-on", accentForegroundHex(seed));
  return safePreference;
}

export function applyStoredAccent(): AccentPreference {
  const preference = readAccentPreference();
  applyAccentPreference(preference);
  return preference;
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

export function applyStoredVisualPreferences(): void {
  applyStoredAppearance();
  applyStoredAccent();
}

export function subscribeToVisualPreferenceUpdates(listener: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener(VISUAL_PREFERENCE_EVENT, listener);
  return () => window.removeEventListener(VISUAL_PREFERENCE_EVENT, listener);
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
