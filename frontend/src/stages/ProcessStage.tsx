import {
  ArrowsOut,
  ArrowClockwise,
  ArrowCounterClockwise,
  CheckCircle,
  Copy,
  CursorClick,
  FlowArrow,
  Hand,
  LinkBreak,
  MagnifyingGlassPlus,
  MagicWand,
  Play,
  PlusCircle,
  SelectionAll,
  Trash
} from "@phosphor-icons/react";

import type { PrimaryStageProps } from "./registry";

type FutureTool = Readonly<{
  label: string;
  icon: typeof CursorClick;
}>;

const futureTools: readonly FutureTool[] = [
  { label: "Select", icon: CursorClick },
  { label: "Pan", icon: Hand },
  { label: "Add equipment", icon: PlusCircle },
  { label: "Connect", icon: FlowArrow },
  { label: "Disconnect", icon: LinkBreak },
  { label: "Multi-select", icon: SelectionAll },
  { label: "Duplicate", icon: Copy },
  { label: "Delete", icon: Trash },
  { label: "Fit view", icon: ArrowsOut },
  { label: "Zoom", icon: MagnifyingGlassPlus },
  { label: "Undo", icon: ArrowCounterClockwise },
  { label: "Redo", icon: ArrowClockwise },
  { label: "Auto-layout", icon: MagicWand },
  { label: "Validate", icon: CheckCircle },
  { label: "Solve", icon: Play }
];

const equipmentGroups = [
  ["Flow", "Material stream", "Energy stream", "Mixer", "Splitter"],
  ["Heat", "Heater", "Cooler", "Heat exchanger"],
  ["Pressure", "Pump", "Compressor", "Valve"],
  ["Reaction", "Reactor"],
  ["Separation", "Separator", "Column"]
] as const;

function ProcessStage({ navigate }: PrimaryStageProps) {
  const unavailableReason = "Future Process authoring control — unavailable until server-owned topology/evaluator authority is integrated.";

  return (
    <section className="process-stage design-stage" aria-labelledby="process-stage-title">
      <header className="design-stage__header process-stage__header">
        <div className="design-stage__title-row">
          <div>
            <p className="eyebrow">Design</p>
            <h1 id="process-stage-title">Process workspace</h1>
            <p className="panel-subtitle">
              Process topology editing will activate only when server-owned Process and evaluator contracts are integrated.
            </p>
          </div>
          <span className="design-stage__truth-state">Topology · Unavailable</span>
        </div>
        <nav className="design-stage__tabs" aria-label="Design workspaces">
          <button type="button" className="is-active" aria-current="page">Process</button>
          <button type="button" onClick={() => navigate("/design/bluecad")}>BLUECAD</button>
        </nav>
      </header>

      <div className="process-stage__workbench">
        <div className="process-stage__toolbar" aria-label="Process tools">
          {futureTools.map(({ label, icon: Icon }) => (
            <button
              key={label}
              type="button"
              className="process-stage__tool"
              disabled
              title={unavailableReason}
              aria-label={`${label} unavailable: ${unavailableReason}`}
            >
              <Icon size={17} aria-hidden="true" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        <aside className="process-stage__palette" aria-label="Process equipment">
          <div className="process-stage__palette-head">
            <strong>Process equipment</strong>
            <span>Future palette</span>
          </div>
          <div className="process-stage__palette-search" aria-disabled="true">Search equipment…</div>
          <div className="process-stage__palette-filters" aria-label="Equipment categories">
            {['All', 'Flow', 'Heat', 'Separation', 'Reaction'].map((label) => (
              <span key={label} className={label === 'All' ? 'is-active' : undefined}>{label}</span>
            ))}
          </div>
          <div className="process-stage__palette-list">
            {equipmentGroups.map(([group, ...items]) => (
              <section key={group}>
                <h2>{group}</h2>
                <div className="process-stage__palette-grid">
                  {items.map((item) => (
                    <button key={item} type="button" disabled title={unavailableReason}>{item}</button>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </aside>

        <div className="process-stage__canvas" role="region" aria-label="Process canvas">
          <div className="process-stage__canvas-meta" aria-hidden="true">
            <span>Snap · unavailable</span><span>Routing · unavailable</span><span>Server-owned semantics</span>
          </div>
          <div className="process-stage__canvas-empty">
            <strong>No process topology is loaded.</strong>
            <p className="panel-subtitle">
              This canvas becomes authoritative only after Process backends are connected. No topology is fabricated in the frontend.
            </p>
            <span className="process-stage__empty-badge">Visual scaffold</span>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ProcessStage;
