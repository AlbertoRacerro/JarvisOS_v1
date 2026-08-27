import type { ReactNode } from "react";

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

const actionButton = (label: string, reason: string) => (
  <button className="final-fusion__action" type="button" disabled title={reason} aria-label={`${label} unavailable: ${reason}`}>
    {label}
  </button>
);

function EmptyRegion({ title, children }: Readonly<{ title: string; children?: ReactNode }>) {
  return (
    <section className="final-fusion__region" aria-label={title}>
      <header><span>{title}</span><span className="final-fusion__status">Unavailable</span></header>
      <div className="final-fusion__empty">{children ?? "No truthful runtime data is available for this region."}</div>
    </section>
  );
}

function SurfaceBody({ kind, description }: Readonly<{ kind: FinalSurfaceKind; description: string }>) {
  switch (kind) {
    case "project-basis":
      return <div className="final-fusion__three-column"><EmptyRegion title="Project search" /><EmptyRegion title="Project Basis">{description}</EmptyRegion><EmptyRegion title="Jarvis context" /></div>;
    case "models":
      return <div className="final-fusion__dossier"><EmptyRegion title="Model identity" /><EmptyRegion title="Version dossier" /><EmptyRegion title="Results · Runs · Lineage" /></div>;
    case "literature":
      return <div className="final-fusion__split"><EmptyRegion title="Literature list" /><EmptyRegion title="Inline preview">{description}</EmptyRegion></div>;
    case "roadmap":
      return <div className="final-fusion__roadmap"><EmptyRegion title="Timeline">{description}</EmptyRegion><div className="final-fusion__execution"><EmptyRegion title="Ready" /><EmptyRegion title="In progress" /><EmptyRegion title="Blocked" /></div></div>;
    case "calendar":
      return <div className="final-fusion__calendar"><div className="final-fusion__view-switch" aria-label="Calendar views"><button disabled>Day</button><button className="is-current" disabled>Week</button><button disabled>Month</button><button disabled>Agenda</button></div><EmptyRegion title="Week schedule">{description}</EmptyRegion></div>;
    case "brainstorm":
      return <div className="final-fusion__three-column"><EmptyRegion title="RAW" /><EmptyRegion title="Discussion · Reconciliation">{description}</EmptyRegion><EmptyRegion title="RECONCILED · Jarvis context" /></div>;
    case "repository":
      return <div className="final-fusion__split final-fusion__split--repository"><EmptyRegion title="Repository Inspector">{description}</EmptyRegion><EmptyRegion title="Preview · Architecture" /></div>;
    case "runtime":
      return <div className="final-fusion__runtime"><EmptyRegion title="Local executed identity">Unknown</EmptyRegion><EmptyRegion title="Remote exact identity">Unknown</EmptyRegion><EmptyRegion title="Terminal · Logs">Unavailable — no browser shell/process authority.</EmptyRegion></div>;
  }
}

function FinalOperatorUnavailableSurface({ kind, title, description, navigate, links = [] }: FinalOperatorUnavailableSurfaceProps) {
  const unavailableReason = "This action has no accepted backend owner in the current 100f frontend-only boundary.";
  return (
    <section className={`final-fusion final-fusion--${kind}`} aria-labelledby={`final-fusion-${kind}-title`}>
      <header className="final-fusion__header">
        <div><p className="eyebrow">Final operator surface · truthful empty state</p><h1 id={`final-fusion-${kind}-title`}>{title}</h1><p>{description}</p></div>
        <div className="final-fusion__actions" aria-label={`${title} unavailable actions`}>
          {kind === "project-basis" && <>{actionButton("Revalidate", unavailableReason)}{actionButton("Approve all", unavailableReason)}</>}
          {kind === "roadmap" && <>{actionButton("Add workstream", unavailableReason)}{actionButton("Edit", unavailableReason)}</>}
          {kind === "calendar" && actionButton("Add event", unavailableReason)}
          {kind === "brainstorm" && <>{actionButton("Reconcile", unavailableReason)}{actionButton("Promote", unavailableReason)}</>}
          {kind === "repository" && actionButton("Suggest modification", "Proposal owner unavailable; the frontend cannot save repository files directly.")}
          {kind === "runtime" && <>{actionButton("Safe update", unavailableReason)}{actionButton("Open terminal", "No PTY/process owner is authorized for the browser frontend.")}</>}
        </div>
      </header>
      <SurfaceBody kind={kind} description={description} />
      {links.length > 0 && <nav className="final-fusion__links" aria-label={`${title} compatibility routes`}>{links.map((link) => <AppLink key={link.href} href={link.href} navigate={navigate}>{link.label}</AppLink>)}</nav>}
    </section>
  );
}

export default FinalOperatorUnavailableSurface;
