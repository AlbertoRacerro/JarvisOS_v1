import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import type { Navigate } from "../app/AppLink";
import type { AppRouteDefinition } from "../app/routes";
import type { StageSelection } from "../app/selection";
import {
  applyAppearancePreference,
  applyResolvedAppearance,
  readAppearancePreference,
  subscribeToSystemAppearance,
  writeAppearancePreference,
  type AppearancePreference
} from "../theme";
import AnalysisDock from "./shell/AnalysisDock";
import ContextualNavigator from "./shell/ContextualNavigator";
import ContextualSidecar from "./shell/ContextualSidecar";
import Rail from "./shell/Rail";
import TopBar from "./shell/TopBar";

type LayoutProps = Readonly<{
  route: AppRouteDefinition;
  navigate: Navigate;
  selection: StageSelection | null;
  children: ReactNode;
}>;

function Layout({ route, navigate, selection, children }: LayoutProps) {
  const [appearance, setAppearance] = useState<AppearancePreference>(() => readAppearancePreference());
  const [navigatorOpen, setNavigatorOpen] = useState(false);
  const [sidecarOpen, setSidecarOpen] = useState(false);
  const [dockOpen, setDockOpen] = useState(false);
  const mainRef = useRef<HTMLElement>(null);
  const navigatorToggleRef = useRef<HTMLButtonElement>(null);
  const sidecarToggleRef = useRef<HTMLButtonElement>(null);
  const dockToggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    applyAppearancePreference(appearance);
    return subscribeToSystemAppearance(appearance, applyResolvedAppearance);
  }, [appearance]);

  useEffect(() => {
    setNavigatorOpen(false);
    setSidecarOpen(false);
    setDockOpen(false);
    document.title = `${route.title} · JarvisOS`;
    const frame = window.requestAnimationFrame(() => mainRef.current?.focus());
    return () => window.cancelAnimationFrame(frame);
  }, [route.id, route.title]);

  const onAppearanceChange = (preference: AppearancePreference) => {
    writeAppearancePreference(preference);
    applyAppearancePreference(preference);
    setAppearance(preference);
  };

  const closeNavigator = useCallback(() => {
    setNavigatorOpen(false);
    window.requestAnimationFrame(() => navigatorToggleRef.current?.focus());
  }, []);

  const closeSidecar = useCallback(() => {
    setSidecarOpen(false);
    window.requestAnimationFrame(() => sidecarToggleRef.current?.focus());
  }, []);

  const closeDock = useCallback(() => {
    setDockOpen(false);
    window.requestAnimationFrame(() => dockToggleRef.current?.focus());
  }, []);

  return (
    <div className="application-shell">
      <a className="shell-skip-link" href="#app-main">Skip to main content</a>
      <TopBar
        title={route.title}
        appearance={appearance}
        onAppearanceChange={onAppearanceChange}
        toggles={[
          {
            id: "navigator",
            label: navigatorOpen ? "Hide navigator" : "Show navigator",
            expanded: navigatorOpen,
            controls: "shell-navigator",
            ref: navigatorToggleRef,
            onToggle: () => setNavigatorOpen((current) => !current)
          },
          {
            id: "sidecar",
            label: sidecarOpen ? "Hide context" : "Show context",
            expanded: sidecarOpen,
            controls: "shell-sidecar",
            ref: sidecarToggleRef,
            onToggle: () => setSidecarOpen((current) => !current)
          },
          {
            id: "analysis",
            label: dockOpen ? "Hide analysis" : "Show analysis",
            expanded: dockOpen,
            controls: "shell-analysis-dock",
            ref: dockToggleRef,
            onToggle: () => setDockOpen((current) => !current)
          }
        ]}
      />
      <Rail current={route.primaryNav} navigate={navigate} />
      <div className="shell-workspace">
        <ContextualNavigator
          open={navigatorOpen}
          currentStage={route.stageKind}
          navigate={navigate}
          onClose={closeNavigator}
        />
        <main id="app-main" className="shell-main" ref={mainRef} tabIndex={-1}>
          {children}
        </main>
        <ContextualSidecar open={sidecarOpen} selection={selection} onClose={closeSidecar} />
      </div>
      <AnalysisDock open={dockOpen} onClose={closeDock} />
    </div>
  );
}

export default Layout;
