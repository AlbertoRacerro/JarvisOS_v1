export type PrimaryNavId = "home" | "design" | "runs" | "engineering-data" | "review" | "settings";

export type StageKind = "model" | "results" | "review" | "flowsheet";

export type RouteId =
  | "home"
  | "design-model"
  | "design-results"
  | "design-flowsheet"
  | "runs"
  | "engineering-data"
  | "review"
  | "settings"
  | "legacy-domain-foundation"
  | "legacy-ai-draft"
  | "legacy-system-status"
  | "legacy-dev-local-chat"
  | "not-found";

export type AppRouteDefinition = Readonly<{
  id: RouteId;
  path: string;
  title: string;
  primaryNav?: PrimaryNavId;
  stageKind?: StageKind;
  legacy?: true;
  devOnly?: true;
}>;

export const PRODUCTION_ROUTES: readonly AppRouteDefinition[] = [
  { id: "home", path: "/home", title: "Home", primaryNav: "home" },
  { id: "design-model", path: "/design/model", title: "Model", primaryNav: "design", stageKind: "model" },
  { id: "design-results", path: "/design/results", title: "Results", primaryNav: "design", stageKind: "results" },
  { id: "design-flowsheet", path: "/design/flowsheet", title: "Flowsheet", primaryNav: "design", stageKind: "flowsheet" },
  { id: "runs", path: "/runs", title: "Runs", primaryNav: "runs" },
  { id: "engineering-data", path: "/engineering-data", title: "Engineering Data", primaryNav: "engineering-data" },
  { id: "review", path: "/review", title: "Review", primaryNav: "review", stageKind: "review" },
  { id: "settings", path: "/settings", title: "Settings", primaryNav: "settings" },
  {
    id: "legacy-domain-foundation",
    path: "/legacy/domain-foundation",
    title: "Domain Foundation",
    legacy: true
  },
  { id: "legacy-ai-draft", path: "/legacy/ai-draft", title: "AI Draft", legacy: true },
  { id: "legacy-system-status", path: "/legacy/system-status", title: "System Status", legacy: true }
] as const;

export const DEV_ROUTE: AppRouteDefinition = {
  id: "legacy-dev-local-chat",
  path: "/legacy/dev-local-chat",
  title: "Development Local Chat",
  legacy: true,
  devOnly: true
};

export const PRIMARY_NAV_ITEMS = [
  { id: "home", label: "Home", href: "/home" },
  { id: "design", label: "Design", href: "/design/model" },
  { id: "runs", label: "Runs", href: "/runs" },
  { id: "engineering-data", label: "Engineering Data", href: "/engineering-data" },
  { id: "review", label: "Review", href: "/review" },
  { id: "settings", label: "Settings", href: "/settings" }
] as const satisfies readonly Readonly<{ id: PrimaryNavId; label: string; href: string }>[];

export const DESIGN_STAGE_ITEMS = [
  { kind: "model", label: "Model", href: "/design/model" },
  { kind: "results", label: "Results", href: "/design/results" },
  { kind: "flowsheet", label: "Flowsheet", href: "/design/flowsheet" }
] as const satisfies readonly Readonly<{ kind: Exclude<StageKind, "review">; label: string; href: string }>[];

export type ResolvedRoute = Readonly<{
  route: AppRouteDefinition;
  canonicalPath: string;
  shouldReplace: boolean;
}>;

export function normalizePathname(pathname: string): string {
  const pathOnly = pathname.split(/[?#]/, 1)[0] ?? "/";
  if (pathOnly === "/" || pathOnly.length === 0) return "/";
  const trimmed = pathOnly.replace(/^\/+|\/+$/g, "");
  return trimmed ? `/${trimmed}` : "/";
}

export function resolveRoute(pathname: string, devEnabled = import.meta.env.DEV): ResolvedRoute {
  const normalized = normalizePathname(pathname);

  if (normalized === "/") {
    return {
      route: PRODUCTION_ROUTES[0],
      canonicalPath: "/home",
      shouldReplace: true
    };
  }

  const route = PRODUCTION_ROUTES.find((candidate) => candidate.path === normalized) ??
    (devEnabled && DEV_ROUTE.path === normalized ? DEV_ROUTE : undefined);

  if (route) {
    return {
      route,
      canonicalPath: route.path,
      shouldReplace: normalized !== pathname
    };
  }

  return {
    route: { id: "not-found", path: normalized, title: "Page not found" },
    canonicalPath: normalized,
    shouldReplace: normalized !== pathname
  };
}
