import { useCallback, useEffect, useState } from "react";

import type { Navigate, NavigateOptions } from "./AppLink";
import { resolveRoute, type ResolvedRoute } from "./routes";

function readCurrentRoute(): ResolvedRoute {
  return resolveRoute(window.location.pathname);
}

export function useAppRouter(): Readonly<{ resolved: ResolvedRoute; navigate: Navigate }> {
  const [resolved, setResolved] = useState<ResolvedRoute>(() => readCurrentRoute());

  const synchronize = useCallback((replaceCanonical = false) => {
    const next = readCurrentRoute();
    if (next.shouldReplace || replaceCanonical) {
      window.history.replaceState({}, "", next.canonicalPath);
    }
    setResolved({ ...next, shouldReplace: false });
  }, []);

  useEffect(() => {
    synchronize();
    const onPopState = () => synchronize();
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, [synchronize]);

  const navigate = useCallback<Navigate>((href: string, options?: NavigateOptions) => {
    const destination = new URL(href, window.location.href);
    if (destination.origin !== window.location.origin) {
      window.location.assign(destination.href);
      return;
    }

    const next = resolveRoute(destination.pathname);
    const target = `${next.canonicalPath}${destination.search}${destination.hash}`;
    if (options?.replace) {
      window.history.replaceState({}, "", target);
    } else if (target !== `${window.location.pathname}${window.location.search}${window.location.hash}`) {
      window.history.pushState({}, "", target);
    }
    setResolved({ ...next, shouldReplace: false });
  }, []);

  return { resolved, navigate };
}
