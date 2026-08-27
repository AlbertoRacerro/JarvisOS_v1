import {
  ArrowsOut,
  ArrowClockwise,
  ArrowCounterClockwise,
  Circle,
  Cube,
  CursorClick,
  Export,
  Hand,
  MagnifyingGlass,
  MagnifyingGlassPlus,
  Ruler,
  Selection,
  SketchLogo,
  SquaresFour
} from "@phosphor-icons/react";

import BluecadWorkbench from "../components/bluecad/BluecadWorkbench";
import type { PrimaryStageProps } from "./registry";

const bluecadPresentationTools = [
  ["Select", CursorClick],
  ["Orbit", ArrowClockwise],
  ["Pan", Hand],
  ["Measure", Ruler],
  ["Sketch", SketchLogo],
  ["Circle", Circle],
  ["Extrude", Cube],
  ["Pattern", SquaresFour],
  ["Fit view", ArrowsOut],
  ["Zoom", MagnifyingGlassPlus],
  ["Undo", ArrowCounterClockwise],
  ["Redo", ArrowClockwise],
  ["Section", Selection],
  ["Inspect", MagnifyingGlass],
  ["Export", Export]
] as const;

function ModelStage({ onSelectionChange, onShellRegionsChange, requestShellRegionOpen, navigate }: PrimaryStageProps) {
  const futureReason = "Future BLUECAD authoring control — current accepted authority is inspect/select existing server-owned geometry only.";

  return (
    <section className="bluecad-final-stage design-stage" aria-labelledby="bluecad-final-title">
      <header className="design-stage__header bluecad-final-stage__header">
        <div className="design-stage__title-row">
          <div>
            <p className="eyebrow">Design</p>
            <h1 id="bluecad-final-title">BLUECAD workspace</h1>
            <p className="panel-subtitle">Deterministic geometry inspection and existing CAD evidence share one engineering workspace; unsupported authoring stays unavailable.</p>
          </div>
          <span className="design-stage__truth-state">Geometry · Server-owned</span>
        </div>
        <nav className="design-stage__tabs" aria-label="Design workspaces">
          <button type="button" onClick={() => navigate("/design/process")}>Process</button>
          <button type="button" className="is-active" aria-current="page">BLUECAD</button>
        </nav>
      </header>

      <div className="bluecad-final-stage__toolbar" aria-label="BLUECAD tools">
        {bluecadPresentationTools.map(([label, Icon]) => (
          <button key={label} type="button" disabled title={futureReason} aria-label={`${label} unavailable: ${futureReason}`}>
            <Icon size={17} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      <div className="bluecad-final-stage__body">
        <BluecadWorkbench
          onSelectionChange={onSelectionChange}
          onShellRegionsChange={onShellRegionsChange}
          requestShellRegionOpen={requestShellRegionOpen}
        />
      </div>
    </section>
  );
}

export default ModelStage;
