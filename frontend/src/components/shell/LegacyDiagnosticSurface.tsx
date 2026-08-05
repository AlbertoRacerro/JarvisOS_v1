import type { ReactNode } from "react";

import StatusBadge from "../ui/StatusBadge";

type LegacyDiagnosticSurfaceProps = Readonly<{
  title: string;
  children: ReactNode;
}>;

function LegacyDiagnosticSurface({ title, children }: LegacyDiagnosticSurfaceProps) {
  return (
    <section className="shell-legacy" aria-labelledby="legacy-diagnostic-title">
      <header className="shell-legacy__header">
        <div>
          <p className="eyebrow">Transition route</p>
          <h1 id="legacy-diagnostic-title">{title}</h1>
        </div>
        <StatusBadge state="stale">Legacy diagnostic surface</StatusBadge>
      </header>
      <div className="shell-legacy__content">{children}</div>
    </section>
  );
}

export default LegacyDiagnosticSurface;
