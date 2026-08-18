import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import type { Navigate } from "../app/AppLink";
import type { AppRouteDefinition } from "../app/routes";
import type { StageSelection } from "../app/selection";
import type { ShellRegion, ShellRegionContributions } from "../stages/registry";
import { APPEARANCE_OPTIONS, applyAppearancePreference, applyResolvedAppearance, readAppearancePreference, subscribeToSystemAppearance, writeAppearancePreference, type AppearancePreference } from "../theme";
import AnalysisDock from "./shell/AnalysisDock";
import ContextualNavigator from "./shell/ContextualNavigator";
import ContextualSidecar from "./shell/ContextualSidecar";
import Rail from "./shell/Rail";
import TopBar from "./shell/TopBar";
import Button from "./ui/Button";
import Field from "./ui/Field";

type LayoutProps = Readonly<{
  route: AppRouteDefinition;
  navigate: Navigate;
  selection: StageSelection | null;
  propertiesContent?: ReactNode;
  shellRegions: ShellRegionContributions;
  shellRegionRequest: Readonly<{ region: ShellRegion; nonce: number }> | null;
  children: ReactNode;
}>;

function Layout({ route, navigate, selection, propertiesContent, shellRegions, shellRegionRequest, children }: LayoutProps) {
  const [appearance, setAppearance] = useState<AppearancePreference>(() => readAppearancePreference());
  const [navigatorOpen, setNavigatorOpen] = useState(false);
  const [sidecarOpen, setSidecarOpen] = useState(false);
  const [dockOpen, setDockOpen] = useState(false);
  const mainRef = useRef<HTMLElement>(null);
  const navigatorToggleRef = useRef<HTMLButtonElement>(null);
  const sidecarToggleRef = useRef<HTMLButtonElement>(null);
  const dockToggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => { applyAppearancePreference(appearance); return subscribeToSystemAppearance(appearance, applyResolvedAppearance); }, [appearance]);
  useEffect(() => {
    setNavigatorOpen(false); setSidecarOpen(false); setDockOpen(false);
    document.title = `${route.title} · JarvisOS`;
    const frame = window.requestAnimationFrame(() => mainRef.current?.focus());
    return () => window.cancelAnimationFrame(frame);
  }, [route.id, route.path, route.title]);
  useEffect(() => {
    if (!shellRegionRequest) return;
    if (shellRegionRequest.region === "navigator") setNavigatorOpen(true);
    if (shellRegionRequest.region === "sidecar") setSidecarOpen(true);
    if (shellRegionRequest.region === "dock") setDockOpen(true);
  }, [shellRegionRequest]);

  const onAppearanceChange = (preference: AppearancePreference) => { writeAppearancePreference(preference); applyAppearancePreference(preference); setAppearance(preference); };
  const appearanceSelect = <select aria-label="Appearance preference" value={appearance} onChange={(event) => onAppearanceChange(event.target.value as AppearancePreference)}>{APPEARANCE_OPTIONS.map((option) => <option key={option} value={option}>{option[0].toUpperCase() + option.slice(1)}</option>)}</select>;
  const closeNavigator = useCallback(() => { setNavigatorOpen(false); window.requestAnimationFrame(() => navigatorToggleRef.current?.focus()); }, []);
  const closeSidecar = useCallback(() => { setSidecarOpen(false); window.requestAnimationFrame(() => sidecarToggleRef.current?.focus()); }, []);
  const closeDock = useCallback(() => { setDockOpen(false); window.requestAnimationFrame(() => dockToggleRef.current?.focus()); }, []);
  const panelControls = <><Button ref={navigatorToggleRef} variant="ghost" aria-expanded={navigatorOpen} aria-controls="shell-navigator" onClick={() => setNavigatorOpen((current) => !current)}>{navigatorOpen ? "Hide navigator" : "Show navigator"}</Button><Button ref={sidecarToggleRef} variant="ghost" aria-expanded={sidecarOpen} aria-controls="shell-sidecar" onClick={() => setSidecarOpen((current) => !current)}>{sidecarOpen ? "Hide context" : "Show context"}</Button><Button ref={dockToggleRef} variant="ghost" aria-expanded={dockOpen} aria-controls="shell-analysis-dock" onClick={() => setDockOpen((current) => !current)}>{dockOpen ? "Hide analysis" : "Show analysis"}</Button></>;

  return <div className="application-shell"><a className="shell-skip-link" href="#app-main">Skip to main content</a><TopBar title={route.title} panelControls={panelControls} appearanceControl={<Field className="appearance-control shell-appearance-control" label="Appearance" control={appearanceSelect} />} /><Rail current={route.primaryNav} navigate={navigate} /><div className="shell-workspace"><ContextualNavigator open={navigatorOpen} currentStage={route.primaryNav === "design" ? route.stageKind : undefined} navigate={navigate} onClose={closeNavigator} content={shellRegions.navigator} /><main id="app-main" className="shell-main" ref={mainRef} tabIndex={-1}>{children}</main><ContextualSidecar open={sidecarOpen} selection={selection} onClose={closeSidecar} content={shellRegions.sidecar} propertiesContent={propertiesContent} /></div><AnalysisDock open={dockOpen} onClose={closeDock} content={shellRegions.dock} /></div>;
}

export default Layout;
