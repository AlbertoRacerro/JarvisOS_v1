import { useState } from "react";

import { unitLabel, type BalanceRow, type Kpi, type ResultsView, type RunOutcome, type ViewQuantity } from "../../api/processDraft";
import "./RunResults.css";

/** Spec 181 toolbar state. Only `converged` uses a success colour; `ready` is an editor state, not a result. */
export type RunState = "blocked" | "ready" | "running" | "validated" | "converged" | "non_converged" | "failed" | "cancelled";

const RUN_STATE_TEXT: Record<RunState, string> = {
  blocked: "Blocked", ready: "Ready to run", running: "Running…", validated: "Validated (not solved)",
  converged: "Converged", non_converged: "Not converged", failed: "Failed", cancelled: "Cancelled",
};

export function runState(busy: "validate" | "run" | null, blockerCount: number, outcome: RunOutcome | null | undefined,
  outcomeIsForThisRevision: boolean): RunState {
  if (busy) return "running";
  if (outcome && outcomeIsForThisRevision) return outcome.state;
  return blockerCount ? "blocked" : "ready";
}

export function RunStateIndicator({ state, blockerCount, reason }: Readonly<{ state: RunState; blockerCount: number; reason?: string | null }>) {
  const text = state === "blocked" ? `${blockerCount} blocker${blockerCount === 1 ? "" : "s"}` : RUN_STATE_TEXT[state];
  return (
    <span className={`run-state run-state--${state}`} data-testid="run-state" data-state={state} role="status"
      title={reason ? `${RUN_STATE_TEXT[state]} · ${reason}` : RUN_STATE_TEXT[state]}>
      <span className="run-state__dot" aria-hidden="true" />{text}{reason && state !== "converged" ? <small> · {reason}</small> : null}
    </span>
  );
}

const number = (value: number) => (Math.abs(value) >= 1e5 || (value !== 0 && Math.abs(value) < 1e-3) ? value.toExponential(3) : String(Number(value.toPrecision(5))));

/** A value, or why there is none; the three null kinds and a real zero never look alike. */
export function QuantityText({ q }: Readonly<{ q: ViewQuantity | undefined | null }>) {
  if (!q) return <span className="view-q view-q--absent">—</span>;
  if (q.value === null)
    return <span className={`view-q view-q--${q.status}`} title={q.reason}>{q.status === "not_computed" ? "not computed" : q.status}</span>;
  return <span className={`view-q${q.label ? " view-q--last-iterate" : ""}`} title={q.label}>{number(q.value)} {unitLabel(q.unit)}</span>;
}

export function OutcomeDetails({ outcome }: Readonly<{ outcome: RunOutcome }>) {
  return (
    <dl className={`run-outcome run-outcome--${outcome.state}`} data-testid="run-outcome">
      <div><dt>Outcome</dt><dd>{outcome.label}</dd></div>
      {outcome.reason && <div><dt>Reason</dt><dd>{outcome.reason}</dd></div>}
      {outcome.message && <div><dt>Message</dt><dd>{outcome.message}</dd></div>}
      {outcome.iterations !== null && <div><dt>Iterations</dt><dd>{outcome.iterations}</dd></div>}
      {outcome.residual !== null && <div><dt>Last max normalized residual</dt><dd>{number(outcome.residual)}</dd></div>}
      {outcome.worst_tear && <div><dt>Worst tear</dt><dd>{outcome.worst_tear}</dd></div>}
      {outcome.failing.length > 0 && <div><dt>Failing</dt><dd><ul>{outcome.failing.map((item, index) => (
        <li key={index}><strong>{item.tag ?? "Flowsheet"}</strong>{item.stage ? ` (${item.stage})` : ""}{item.error ? `: ${item.error}` : ""}</li>
      ))}</ul></dd></div>}
      <div><dt>Results</dt><dd>{outcome.results_available === "converged" ? "converged results"
        : outcome.results_available === "last_iterate" ? "last iterate only — not a solution" : "none"}</dd></div>
      {outcome.artifact && <div><dt>Solved case</dt><dd><code>{outcome.artifact}</code></dd></div>}
    </dl>
  );
}

function Banner({ view, stale }: Readonly<{ view: ResultsView; stale: boolean }>) {
  const revision = view.draft_revision.split(":")[0];
  const text = view.label === "current"
    ? `${stale ? "Stale" : "Current"} · converged run ${view.run_id.slice(0, 8)} on revision ${revision}${stale ? ". Values describe that revision, not the current draft." : ""}`
    : view.label === "last_iterate"
      ? `${view.value_label} · run ${view.run_id.slice(0, 8)} on revision ${revision}. These values are not a solution.`
      : `No results · run ${view.run_id.slice(0, 8)} was not solved (${view.outcome.label}).`;
  return <p className={`results-banner results-banner--${view.label}${stale ? " is-stale" : ""}`} role="status" data-testid="results-banner">{text}</p>;
}

const pretty = (key: string) => key.replace(/_/g, " ");

/** The selected stream's or unit's results (spec 181 results navigator). */
export function ObjectResults({ view, kind, tag, stale, onSelectTag }: Readonly<{ view: ResultsView; kind: "stream" | "unit"; tag: string;
  stale: boolean; onSelectTag: (tag: string) => void }>) {
  if (view.label === "not_solved") return <section className="object-results" data-testid="object-results"><Banner view={view} stale={stale} /></section>;
  if (kind === "stream") {
    const stream = view.streams[tag];
    if (!stream) return null;
    return (
      <section className="object-results" aria-label={`Results for ${tag}`} data-testid="object-results">
        <Banner view={view} stale={stale} />
        <p className="object-results__links">
          {stream.from ? <button type="button" onClick={() => onSelectTag(stream.from as string)}>from {stream.from}</button> : <span>feed</span>}
          {" → "}
          {stream.to ? <button type="button" onClick={() => onSelectTag(stream.to as string)}>to {stream.to}</button> : <span>product</span>}
          {stream.owner && <span className="object-results__owner"> · {stream.owner === "jarvis_bio" ? "Jarvis" : "DWSIM"}{stream.state_source ? ` (${pretty(stream.state_source)})` : ""}</span>}
        </p>
        <dl className="object-results__grid">
          {(["temperature", "pressure", "mass_flow", "molar_flow", "volumetric_flow", "vapor_fraction"] as const).map((key) => (
            <div key={key}><dt>{pretty(key)}</dt><dd><QuantityText q={stream[key]} /></dd></div>
          ))}
        </dl>
        <h4>Composition (mass fraction)</h4>
        <dl className="object-results__grid">
          {Object.entries(stream.mass_fractions).map(([name, q]) => <div key={name}><dt>{name}</dt><dd><QuantityText q={q} /></dd></div>)}
        </dl>
        {stream.culture && <>
          <h4>Culture</h4>
          {stream.culture_failure && <p className="draft-dwsim-error">{stream.culture_failure}</p>}
          <dl className="object-results__grid">
            {Object.entries(stream.culture).map(([name, q]) => <div key={name}><dt>{name}</dt><dd><QuantityText q={q} /></dd></div>)}
          </dl>
        </>}
      </section>
    );
  }
  const unit = view.units[tag];
  if (!unit) return null;
  return (
    <section className="object-results" aria-label={`Results for ${tag}`} data-testid="object-results">
      <Banner view={view} stale={stale} />
      <p className="object-results__links">
        {unit.inlets.map((name) => <button key={`in-${name}`} type="button" onClick={() => onSelectTag(name)}>in {name}</button>)}
        {unit.outlets.map((name) => <button key={`out-${name}`} type="button" onClick={() => onSelectTag(name)}>out {name}</button>)}
      </p>
      <p className="object-results__status">
        {unit.calculated === false ? <strong className="view-q--failed">Not calculated{unit.error ? `: ${unit.error}` : ""}</strong>
          : unit.calculated ? "Calculated" : "No calculation state reported"}
        {unit.fidelity ? ` · ${unit.fidelity}` : ""}
      </p>
      {Object.keys(unit.quantities).length > 0 ? (
        <dl className="object-results__grid">
          {Object.entries(unit.quantities).map(([key, q]) => (
            <div key={key}><dt>{q.label ?? pretty(key)}</dt><dd><QuantityText q={q} /></dd></div>
          ))}
        </dl>
      ) : <p className="draft-hint">This unit reported no quantities.</p>}
    </section>
  );
}

function KpiTable({ kpis }: Readonly<{ kpis: Kpi[] }>) {
  return (
    <table className="results-table" data-testid="kpi-table">
      <thead><tr><th>KPI</th><th>Value</th><th>Definition</th></tr></thead>
      <tbody>{kpis.map((kpi) => (
        <tr key={kpi.id} data-status={kpi.status} data-kpi={kpi.id}>
          <td>{kpi.label}</td>
          <td>{kpi.value !== null ? `${number(kpi.value)} ${kpi.unit === "1" ? "" : unitLabel(kpi.unit)}` : <span className={`view-q view-q--${kpi.status}`}>{kpi.status.replace(/_/g, " ")}: {kpi.reason}</span>}</td>
          <td className="results-table__definition">{kpi.definition}</td>
        </tr>
      ))}</tbody>
    </table>
  );
}

function BalanceTable({ rows }: Readonly<{ rows: Record<string, BalanceRow> }>) {
  return (
    <table className="results-table">
      <thead><tr><th>Quantity</th><th>In</th><th>Out</th><th>Residual</th><th>Tolerance</th><th>Passed</th></tr></thead>
      <tbody>{Object.entries(rows).map(([name, row]) => (
        <tr key={name}><td>{pretty(name)}</td><td>{row.in == null ? "—" : number(row.in)}</td><td>{row.out == null ? "—" : number(row.out)}</td>
          <td>{row.residual == null ? "—" : number(row.residual)} {row.unit ?? ""}</td><td>{row.tolerance == null ? "—" : number(row.tolerance)}</td>
          <td>{row.passed == null ? "—" : row.passed ? "yes" : "no"}</td></tr>
      ))}</tbody>
    </table>
  );
}

const TABS = ["Summary", "Boundary", "Streams", "Balances & findings"] as const;

/** The Results tab: KPIs, boundary in/out, full stream table with composition, balances and findings. */
export function ResultsWorkspace({ view, stale, compounds, onSelectTag }: Readonly<{ view: ResultsView; stale: boolean; compounds: string[];
  onSelectTag: (tag: string) => void }>) {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Summary");
  const streamRow = (tag: string) => {
    const stream = view.streams[tag];
    return stream && (
      <tr key={tag}>
        <td><button type="button" className="results-link" onClick={() => onSelectTag(tag)}>{tag}</button></td>
        <td>{stream.role}</td>
        {(["temperature", "pressure", "mass_flow", "volumetric_flow"] as const).map((key) => <td key={key}><QuantityText q={stream[key]} /></td>)}
        {compounds.map((name) => <td key={name}><QuantityText q={stream.mass_fractions[name]} /></td>)}
        <td><QuantityText q={stream.culture?.biomass} /></td>
      </tr>
    );
  };
  const mass = view.balances.mass;
  return (
    <section className={`results-workspace results-workspace--${view.label}`} aria-label="Run results" data-testid="results-workspace">
      <Banner view={view} stale={stale} />
      <div className="results-tabs" role="tablist" aria-label="Results sections">
        {TABS.map((name) => (
          <button key={name} type="button" role="tab" aria-selected={tab === name} className={tab === name ? "is-active" : ""} onClick={() => setTab(name)}>{name}</button>
        ))}
      </div>
      {tab === "Summary" && <KpiTable kpis={view.kpis} />}
      {tab === "Boundary" && (
        <table className="results-table" data-testid="boundary-table">
          <thead><tr><th>Direction</th><th>Streams</th><th>Total mass flow</th>{compounds.map((name) => <th key={name}>{name}</th>)}</tr></thead>
          <tbody>
            <tr><td>Inputs</td><td>{view.boundary.inputs.join(", ") || "—"}</td><td><QuantityText q={view.boundary.totals.mass_flow_in} /></td>
              {compounds.map((name) => <td key={name}><QuantityText q={view.boundary.totals.by_compound_in[name]} /></td>)}</tr>
            <tr><td>Outputs</td><td>{view.boundary.outputs.join(", ") || "—"}</td><td><QuantityText q={view.boundary.totals.mass_flow_out} /></td>
              {compounds.map((name) => <td key={name}><QuantityText q={view.boundary.totals.by_compound_out[name]} /></td>)}</tr>
          </tbody>
        </table>
      )}
      {tab === "Streams" && (view.label === "not_solved" ? <p className="draft-hint">No stream values: the run was not solved.</p> : (
        <div className="results-scroll">
          <table className="results-table" data-testid="stream-table">
            <thead><tr><th>Stream</th><th>Role</th><th>T</th><th>P</th><th>Mass flow</th><th>Volumetric flow</th>
              {compounds.map((name) => <th key={name}>w {name}</th>)}<th>Biomass</th></tr></thead>
            <tbody>{Object.keys(view.streams).map(streamRow)}</tbody>
          </table>
        </div>
      ))}
      {tab === "Balances & findings" && (
        <div className="results-balances">
          <h4>Mass balance</h4>
          {mass.status && mass.status !== "calculated" && mass.in === undefined
            ? <p className="view-q view-q--unavailable">{mass.reason ?? mass.error ?? mass.status}</p>
            : mass.residual_kg_s !== undefined ? <p>Residual {number(mass.residual_kg_s)} kg/s</p> : <BalanceTable rows={{ carrier_mass: mass }} />}
          {view.balances.culture && <><h4>Culture balances (whole flowsheet)</h4><BalanceTable rows={view.balances.culture} /></>}
          {view.balances.unit_balances && Object.entries(view.balances.unit_balances).map(([tag, rows]) => (
            <details key={tag}><summary>Unit balance · {tag}</summary><BalanceTable rows={rows} /></details>
          ))}
          <h4>Findings</h4>
          {view.findings.length ? (
            <ul className="draft-findings">{view.findings.map((finding, index) => (
              <li key={index} data-severity={finding.severity}><strong>{finding.object || "Flowsheet"}</strong> {finding.message}</li>
            ))}</ul>
          ) : <p className="draft-hint">No result findings.</p>}
        </div>
      )}
    </section>
  );
}
