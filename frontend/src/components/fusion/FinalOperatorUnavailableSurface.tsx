import { useState, type ReactNode } from "react";

import AppLink, { type Navigate } from "../../app/AppLink";

type FinalSurfaceKind =
  | "project-basis"
  | "models"
  | "literature"
  | "roadmap"
  | "calendar"
  | "brainstorm"
  | "repository"
  | "runtime";

type FinalOperatorUnavailableSurfaceProps = Readonly<{
  kind: FinalSurfaceKind;
  title: string;
  description: string;
  navigate: Navigate;
  links?: readonly Readonly<{ href: string; label: string }>[];
}>;

const unavailableReason = "This action has no accepted backend owner in the current 100f frontend-only boundary.";

const actionButton = (label: string, reason = unavailableReason) => (
  <button className="final-fusion__action" type="button" disabled title={reason} aria-label={`${label} unavailable: ${reason}`}>
    {label}
  </button>
);

function Panel({ title, children, className = "", status = "Unavailable" }: Readonly<{ title: string; children?: ReactNode; className?: string; status?: string }>) {
  return (
    <section className={`final-fusion__panel ${className}`.trim()} aria-label={title}>
      <header className="final-fusion__panel-head"><h2>{title}</h2><span>{status}</span></header>
      {children}
    </section>
  );
}

function EmptyCopy({ children }: Readonly<{ children?: ReactNode }>) {
  return <div className="final-fusion__empty">{children ?? "No truthful runtime data is available for this region."}</div>;
}

function JarvisPanel({ detail = "No exact records are available to bind into Jarvis context." }: Readonly<{ detail?: string }>) {
  return (
    <Panel title="Jarvis" className="final-fusion__jarvis">
      <div className="final-fusion__jarvis-body">
        <div className="final-fusion__context-note">Active context is explicit. Browsing this surface does not add records automatically.</div>
        <div className="final-fusion__bubble">{detail}</div>
        <div className="final-fusion__composer" aria-disabled="true"><span>Ask Jarvis about an exact selected record…</span><button type="button" disabled>Send</button></div>
      </div>
    </Panel>
  );
}

function ProjectBasisSurface({ description }: Readonly<{ description: string }>) {
  return (
    <div className="final-fusion__workbench final-fusion__workbench--memory">
      <Panel title="Project search" className="final-fusion__search-panel">
        <div className="final-fusion__searchbox">Search canonical project memory…</div>
        <div className="final-fusion__chips"><span>Basis</span><span>Models</span><span>Literature</span></div>
        <EmptyCopy>No searchable Project Basis read owner is available in this slice.</EmptyCopy>
      </Panel>
      <Panel title="Project Basis" className="final-fusion__basis">
        <div className="final-fusion__dossier-top"><strong>Canonical project basis</strong><span>Exact project records unavailable</span></div>
        <div className="final-fusion__summary-strip"><span>Objectives · Unknown</span><span>Criteria · Unknown</span><span>Constraints · Unknown</span></div>
        <div className="final-fusion__toolbar-line"><span>Compact engineering rows and bounded disclosures</span><button type="button" disabled>Collapse all</button></div>
        <div className="final-fusion__disclosures">
          {[
            "Objectives & engineering question",
            "Requirements & acceptance criteria",
            "Stable constraints & boundary conditions",
            "Standards, decisions & resources"
          ].map((label) => <div className="final-fusion__disclosure-row" key={label}><span>›</span><strong>{label}</strong><em>Unavailable</em></div>)}
        </div>
        <div className="final-fusion__inline-note">{description}</div>
      </Panel>
      <JarvisPanel detail="Project Basis proposals and revalidation require exact backend-owned records and revision identity." />
    </div>
  );
}

function ModelsSurface({ description }: Readonly<{ description: string }>) {
  const [collapsed, setCollapsed] = useState(false);
  const sections = ["Definition", "Assumptions", "Methods & Equations", "Parameters & Inputs", "Process", "BLUECAD", "Results & Validation", "Criticalities", "Sources", "Artifacts", "Runs", "Changelog / Lineage"];
  return (
    <div className="final-fusion__workbench final-fusion__workbench--models">
      <Panel title="Model versions" className="final-fusion__versions">
        <div className="final-fusion__searchbox">Filter exact versions…</div>
        <EmptyCopy>No truthful model-version inventory is available.</EmptyCopy>
        <div className="final-fusion__lineage-slot">Version lineage · Unknown</div>
      </Panel>
      <Panel title="Version dossier" className="final-fusion__model-dossier">
        <div className="final-fusion__dossier-top"><strong>Exact model / version</strong><span>Unknown</span></div>
        <div className="final-fusion__summary-strip"><span>Identity · Unknown</span><span>State · Unknown</span><span>Runs · Unknown</span><span>Evidence · Unknown</span></div>
        <div className="final-fusion__toolbar-line"><span>{description}</span><button type="button" onClick={() => setCollapsed((value) => !value)} aria-expanded={!collapsed}>{collapsed ? "Expand sections" : "Collapse all"}</button></div>
        {!collapsed && <div className="final-fusion__dossier-grid">{sections.map((label) => <section key={label}><header><strong>{label}</strong><span>Unavailable</span></header><p>No exact-version records available.</p></section>)}</div>}
        <div className="final-fusion__context-strip">Results · Runs · Lineage remain contextual to the selected exact version.</div>
      </Panel>
      <JarvisPanel detail="Select an exact model/version before asking Jarvis to reason over model evidence." />
    </div>
  );
}

function LiteratureSurface({ description }: Readonly<{ description: string }>) {
  return (
    <div className="final-fusion__workbench final-fusion__workbench--memory">
      <Panel title="Project search" className="final-fusion__search-panel">
        <div className="final-fusion__searchbox">Search project literature…</div>
        <div className="final-fusion__chips"><span>All</span><span>PDF</span><span>Image</span></div>
        <EmptyCopy>No bounded literature search owner is available.</EmptyCopy>
      </Panel>
      <Panel title="Literature" className="final-fusion__literature">
        <div className="final-fusion__library-top"><div><strong>Sources & files</strong><span>Compact list · inline multi-expand</span></div>{actionButton("Import")}</div>
        <div className="final-fusion__toolbar-line"><span>Opening a source does not silently add it to Jarvis context.</span><button type="button" disabled>Collapse all</button></div>
        <div className="final-fusion__source-list">
          <div className="final-fusion__source-empty"><strong>No literature records</strong><span>{description}</span></div>
          <div className="final-fusion__preview-skeleton"><div><strong>Expanded source detail</strong><span>Claims · values · usages · provenance</span></div><aside>Bounded preview unavailable</aside></div>
        </div>
      </Panel>
      <JarvisPanel detail="Research and extraction remain proposals until exact source evidence can be bound." />
    </div>
  );
}

function RoadmapSurface({ description, navigate }: Readonly<{ description: string; navigate: Navigate }>) {
  const [executionOpen, setExecutionOpen] = useState(true);
  return (
    <div className="final-fusion__workbench final-fusion__workbench--development">
      <Panel title="Timeline" className="final-fusion__roadmap-main">
        <div className="final-fusion__roadmap-toolbar"><div className="final-fusion__segmented"><button type="button" className="is-active" aria-current="page">Timeline</button><button type="button" onClick={() => navigate("/development/roadmap/calendar")}>Calendar</button></div><div><input aria-label="Search roadmap" placeholder="Search roadmap…" disabled />{actionButton("Add workstream")}</div></div>
        <div className="final-fusion__timeline-controls"><span>Project windows · sequencing · dependencies</span><div className="final-fusion__chips"><span>Year</span><span>Quarter</span><span>Month</span></div></div>
        <div className="final-fusion__timeline-empty"><div className="final-fusion__months">{["Scope", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map((item) => <span key={item}>{item}</span>)}</div><EmptyCopy>{description}</EmptyCopy></div>
        <section className={`final-fusion__execution ${executionOpen ? "" : "is-collapsed"}`}>
          <header><div><strong>Execution status</strong><span>Same Roadmap identities; no standalone Board.</span></div><button type="button" onClick={() => setExecutionOpen((value) => !value)} aria-expanded={executionOpen}>{executionOpen ? "Collapse" : "Expand"}</button></header>
          {executionOpen && <div className="final-fusion__execution-grid">{["Ready", "In progress", "Blocked"].map((label) => <section key={label}><header><strong>{label}</strong><span>Unknown</span></header><p>No truthful Roadmap items.</p></section>)}</div>}
        </section>
      </Panel>
      <div className="final-fusion__rightstack"><JarvisPanel detail="Roadmap additions or status changes require the future canonical planning owner." /><Panel title="Focus & filters" className="final-fusion__filters"><EmptyCopy>Filters become meaningful only when real Roadmap items exist.</EmptyCopy></Panel></div>
    </div>
  );
}

function CalendarSurface({ description, navigate }: Readonly<{ description: string; navigate: Navigate }>) {
  const [view, setView] = useState("Week");
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  return (
    <div className="final-fusion__workbench final-fusion__workbench--development">
      <Panel title="Calendar" className="final-fusion__calendar-main">
        <div className="final-fusion__calendar-toolbar"><div className="final-fusion__segmented" aria-label="Roadmap views"><button type="button" onClick={() => navigate("/development/roadmap/timeline")}>Timeline</button><button type="button" className="is-active" aria-current="page">Calendar</button></div>{actionButton("Add event")}</div>
        <div className="final-fusion__calendar-nav"><div className="final-fusion__segmented" aria-label="Calendar views">{["Day", "Week", "Month", "Agenda"].map((label) => <button key={label} type="button" className={view === label ? "is-active" : ""} onClick={() => setView(label)}>{label}</button>)}</div><button type="button" disabled>‹</button><strong>{view} · actual time allocation</strong><button type="button" disabled>›</button></div>
        <div className="final-fusion__week-head"><span>Time</span>{days.map((day) => <span key={day}>{day}<small>—</small></span>)}</div>
        <div className="final-fusion__all-day"><span>All day</span>{days.map((day) => <span key={day} />)}</div>
        <div className="final-fusion__time-grid"><div className="final-fusion__hours">{Array.from({ length: 12 }, (_, index) => <span key={index}>{String(index + 8).padStart(2, "0")}:00</span>)}</div><div className="final-fusion__day-grid"><EmptyCopy>{description}</EmptyCopy></div></div>
      </Panel>
      <div className="final-fusion__rightstack"><JarvisPanel detail="Calendar events are actual time allocation; Roadmap date spans are never synthesized into events." /><Panel title="Calendar filters" className="final-fusion__filters"><EmptyCopy>No event owner is available.</EmptyCopy></Panel></div>
    </div>
  );
}

function BrainstormSurface({ description }: Readonly<{ description: string }>) {
  return (
    <div className="final-fusion__workbench final-fusion__workbench--brainstorm">
      <Panel title="Brainstorm" className="final-fusion__brain">
        <section className="final-fusion__raw"><header><div><strong>RAW</strong><span>Non-authoritative capture</span></div><span>0</span></header><textarea disabled placeholder="Capture a raw idea…" /><div className="final-fusion__capture-tools">{actionButton("Attach")}{actionButton("Microphone")}{actionButton("Save raw")}</div><EmptyCopy>No RAW ideas exist in an accepted persistence owner.</EmptyCopy></section>
        <section className="final-fusion__reconciled"><header><div><strong>RECONCILED</strong><span>Discussion · reconciliation · explicit promotion</span></div><span>0</span></header><div className="final-fusion__searchbox">Search reconciled ideas…</div><EmptyCopy>{description}</EmptyCopy><div className="final-fusion__capture-tools">{actionButton("Reconcile")}{actionButton("Promote")}</div></section>
      </Panel>
      <JarvisPanel detail="Opening an idea never adds it to context. Context insertion remains an explicit action." />
    </div>
  );
}

function RepositorySurface({ description }: Readonly<{ description: string }>) {
  return (
    <div className="final-fusion__workbench final-fusion__workbench--coding">
      <Panel title="Repository" className="final-fusion__repo">
        <div className="final-fusion__repo-status"><div><strong>Repository identity</strong><span>Remote ref / exact SHA unavailable</span></div><span className="final-fusion__unknown">Unknown</span></div>
        <div className="final-fusion__repo-body"><section className="final-fusion__repo-card"><header><div><strong>Active development</strong><span>Exact-head lifecycle evidence</span></div><button disabled>Open PR ↗</button></header><EmptyCopy>No accepted frontend-safe repository observer is available.</EmptyCopy></section><section className="final-fusion__repo-card final-fusion__repo-inspector"><header><div><strong>Repository Inspector</strong><span>Search · result selection · bounded preview</span></div>{actionButton("Suggest modification", "Proposal owner unavailable; the frontend cannot save repository files directly.")}</header><div className="final-fusion__repo-search">Search paths, symbols and artifacts…</div><div className="final-fusion__repo-inspector-body"><aside><EmptyCopy>No repository results.</EmptyCopy></aside><section><header><strong>Preview · Architecture</strong><span>Selectable artifact, never permanent authority</span></header><EmptyCopy>{description}</EmptyCopy></section></div></section></div>
      </Panel>
      <div className="final-fusion__rightstack"><JarvisPanel detail="Repository browsing is READ/NAVIGATE only; Suggest modification remains PROPOSE." /><Panel title="Repository facts" className="final-fusion__facts"><EmptyCopy>Branch, ref, SHA and working-tree state are Unknown.</EmptyCopy></Panel></div>
    </div>
  );
}

function RuntimeSurface({ description }: Readonly<{ description: string }>) {
  return (
    <div className="final-fusion__workbench final-fusion__workbench--coding">
      <Panel title="Runtime" className="final-fusion__runtime-main">
        <div className="final-fusion__repo-status"><div><strong>JarvisOS runtime identity</strong><span>Local executed vs remote exact comparison</span></div><span className="final-fusion__unknown">Unknown</span></div>
        <div className="final-fusion__runtime-body"><section className="final-fusion__compare"><div className="final-fusion__version-card"><small>Local current · actually executed</small><strong>LOCAL · Unknown</strong><code>Runtime observer unavailable</code><p>No accepted observer proves which exact code is executing locally.</p></div><div className="final-fusion__delta">→<span>Unknown</span></div><div className="final-fusion__version-card is-remote"><small>GitHub latest · remote exact</small><strong>REMOTE · Unknown</strong><code>Repository observer unavailable</code><p>The frontend does not infer remote identity or alignment.</p></div></section><section className="final-fusion__repo-card"><header><div><strong>Semantic delta & safe update</strong><span>Inspection before execution</span></div>{actionButton("Safe update")}</header><EmptyCopy>{description}</EmptyCopy></section><section className="final-fusion__runtime-services"><Panel title="Observed services" status="Unknown"><EmptyCopy>No runtime service observer.</EmptyCopy></Panel><Panel title="Safeguards" status="Unavailable"><EmptyCopy>Update and rollback evidence require a backend owner.</EmptyCopy></Panel></section><section className="final-fusion__terminal"><header><strong>Terminal · Logs</strong>{actionButton("Open terminal", "No PTY/process owner is authorized for the browser frontend.")}</header><code>No runtime log stream is available.</code></section></div>
      </Panel>
      <div className="final-fusion__rightstack"><JarvisPanel detail="Runtime commands remain proposals until a safe backend execution boundary exists." /><Panel title="Runtime status" className="final-fusion__facts"><EmptyCopy>Health, clean-state and alignment remain Unknown.</EmptyCopy></Panel></div>
    </div>
  );
}

function SurfaceBody({ kind, description, navigate }: Readonly<{ kind: FinalSurfaceKind; description: string; navigate: Navigate }>) {
  switch (kind) {
    case "project-basis": return <ProjectBasisSurface description={description} />;
    case "models": return <ModelsSurface description={description} />;
    case "literature": return <LiteratureSurface description={description} />;
    case "roadmap": return <RoadmapSurface description={description} navigate={navigate} />;
    case "calendar": return <CalendarSurface description={description} navigate={navigate} />;
    case "brainstorm": return <BrainstormSurface description={description} />;
    case "repository": return <RepositorySurface description={description} />;
    case "runtime": return <RuntimeSurface description={description} />;
  }
}

function FinalOperatorUnavailableSurface({ kind, title, description, navigate, links = [] }: FinalOperatorUnavailableSurfaceProps) {
  return (
    <section className={`final-fusion final-fusion--${kind}`} aria-labelledby={`final-fusion-${kind}-title`}>
      <header className="final-fusion__surface-head"><div><p className="eyebrow">Final operator surface · truthful staged state</p><h1 id={`final-fusion-${kind}-title`}>{title}</h1><p>{description}</p></div></header>
      <SurfaceBody kind={kind} description={description} navigate={navigate} />
      {links.length > 0 && <nav className="final-fusion__links" aria-label={`${title} compatibility routes`}>{links.map((link) => <AppLink key={link.href} href={link.href} navigate={navigate}>{link.label}</AppLink>)}</nav>}
    </section>
  );
}

export default FinalOperatorUnavailableSurface;
