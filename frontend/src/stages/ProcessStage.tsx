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
  ["Streams", "Material stream", "Energy stream"],
  ["Mixing & split", "Mixer", "Splitter"],
  ["Heat transfer", "Heater", "Cooler", "Heat exchanger"],
  ["Pressure", "Pump", "Compressor", "Valve"],
  ["Reaction & separation", "Reactor", "Separator", "Column"]
] as const;

function ProcessStage(_props: PrimaryStageProps) {
  const unavailableReason = "Future Process authoring control — unavailable until server-owned topology/evaluator authority is integrated.";

  return (
    <section className="process-stage" aria-labelledby="process-stage-title">
      <header className="page-header process-stage__header">
        <div>
          <p className="eyebrow">Process</p>
          <h1 id="process-stage-title">Process workspace</h1>
          <p className="panel-subtitle">
            Approved process-workbench composition is preserved; topology editing and solving remain unavailable until server-owned Process contracts exist.
          </p>
        </div>
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
              <Icon size={15} aria-hidden="true" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        <aside className="process-stage__palette" aria-label="Process equipment">
          <div className="process-stage__palette-head">
            <strong>Equipment</strong>
            <span>Future palette</span>
          </div>
          <div className="process-stage__palette-search" aria-disabled="true">Search equipment…</div>
          <div className="process-stage__palette-list">
            {equipmentGroups.map(([group, ...items]) => (
              <section key={group}>
                <h2>{group}</h2>
                {items.map((item) => (
                  <button key={item} type="button" disabled title={unavailableReason}>{item}</button>
                ))}
              </section>
            ))}
          </div>
        </aside>

        <div className="process-stage__canvas" role="region" aria-label="Process canvas">
          <div className="process-stage__canvas-empty">
            <strong>No process topology is loaded.</strong>
            <p className="panel-subtitle">
              The warm-grid canvas and authoring affordances are present, but no topology is fabricated in the frontend.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ProcessStage;
