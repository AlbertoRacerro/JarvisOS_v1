import { useEffect, useState } from "react";
import { readProviderQuotas, type ProviderQuota, type ProviderQuotas, type ProviderQuotaWindow } from "../../api/coding";

// Read-only provider usage rings (spec 217). The server reads agent-relay and agy /quota at most once per TTL; this panel only
// re-asks the server once a minute and never calls a provider or CLI itself.
const POLL_MS = 60_000;
const ROWS: readonly { kind: ProviderQuotaWindow["kind"]; label: string }[] = [
  { kind: "five_hour", label: "5-hour" },
  { kind: "weekly", label: "Weekly" },
];
const FRONTIER_MODELS = ["Opus", "Argon"];
const RADIUS = 22;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const REASONS: Record<string, string> = {
  agy_quota_unreadable: "agy /quota unreadable",
  relay_limits_unreadable: "agent-relay limits unreadable",
  no_reading: "No reading",
  no_usage_windows: "No usage windows reported",
  not_authenticated: "Not signed in",
};

function until(iso: string | null, now: Date): string | null {
  if (!iso) return null;
  const minutes = Math.round((new Date(iso).getTime() - now.getTime()) / 60_000);
  if (!Number.isFinite(minutes) || minutes <= 0) return null;
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours}h ${minutes % 60}m` : `${Math.floor(hours / 24)}d ${hours % 24}h`;
}

function age(iso: string | null | undefined, now: Date): string | null {
  if (!iso) return null;
  const minutes = Math.round((now.getTime() - new Date(iso).getTime()) / 60_000);
  return Number.isFinite(minutes) ? (minutes < 1 ? "read just now" : `read ${minutes} min ago`) : null;
}

export function QuotaRing({ window, now, model }: Readonly<{ window: ProviderQuotaWindow; now: Date; model?: string | null }>) {
  const left = Math.max(0, Math.min(100, window.remaining_percent));
  const state = window.exhausted ? "exhausted" : window.stale ? "stale" : left <= 15 ? "low" : "ok";
  const reset = until(window.resets_at, now);
  return <div className="coding-quota-cell" data-state={state}>
    <svg viewBox="0 0 56 56" role="img" aria-label={`${left}% left${window.exhausted ? ", exhausted" : ""}${window.stale ? ", out of date" : ""}`}>
      <circle className="coding-quota-track" cx="28" cy="28" r={RADIUS} />
      {left > 0 ? <circle className="coding-quota-value" cx="28" cy="28" r={RADIUS}
        strokeDasharray={`${(left / 100) * CIRCUMFERENCE} ${CIRCUMFERENCE}`} transform="rotate(-90 28 28)" /> : null}
      <text x="28" y="28" dominantBaseline="central" textAnchor="middle">{`${Math.round(left)}%`}</text>
    </svg>
    <span className="coding-quota-caption">
      {model ? <span className="coding-quota-model">{model}</span> : null}
      <strong>{window.exhausted ? "Exhausted" : "left"}</strong>
      {window.stale ? <em>out of date</em> : null}
      {reset ? <span title={`Resets in ${reset}`}>↻ {reset}</span> : null}
    </span>
  </div>;
}

function Missing({ text }: Readonly<{ text: string }>) {
  return <div className="coding-quota-cell" data-state="missing"><span className="coding-quota-na">N/A</span><span className="coding-quota-caption"><span>{text}</span></span></div>;
}

function cell(provider: ProviderQuota, window: ProviderQuotaWindow | undefined, now: Date) {
  if (provider.status !== "ok") return <Missing text={REASONS[provider.reason ?? ""] ?? "Not available"} />;
  return window ? <QuotaRing window={window} now={now} /> : <Missing text="Not reported" />;
}

export function ProviderQuotaView({ data, error, now = new Date() }: Readonly<{ data: ProviderQuotas | null; error: string | null; now?: Date }>) {
  const providers = data?.providers ?? [];
  const pools = providers.flatMap((p) => p.windows.filter((w) => w.kind === "pool").map((w) => ({ provider: p.provider, window: w })));
  const frontier = providers.some((p) => p.windows.some((w) => w.kind === "frontier"));
  // One shared row for each provider's top model pool (Claude Opus, Antigravity Argon); its name sits under the ring.
  const modelName = (w: ProviderQuotaWindow) => {
    const text = `${w.label ?? ""} ${w.id}`.toLowerCase();
    const known = FRONTIER_MODELS.find((name) => text.includes(name.toLowerCase()));
    return known ?? (w.label ?? w.id).split(/[ ·_-]/)[0];
  };
  return <section className="coding-control-section coding-quota" aria-label="Provider usage">
    <header><h3>Provider usage</h3><span>{data ? age(data.read_at, now) : error ? "unavailable" : "reading…"}</span></header>
    {error ? <p className="coding-control-empty" role="status">Provider usage unavailable: {error}</p> : null}
    {data ? <div className="coding-quota-grid" style={{ gridTemplateColumns: `max-content repeat(${providers.length}, minmax(0, 1fr))` }}>
      <span />
      {providers.map((p) => <strong key={p.provider} className="coding-quota-provider">{p.label}</strong>)}
      {ROWS.map((row) => <div key={row.kind} className="coding-quota-row" role="group" aria-label={row.label}>
        <span className="coding-quota-rowlabel">{row.label}</span>
        {providers.map((p) => <div key={p.provider}>{cell(p, p.windows.find((w) => w.kind === row.kind), now)}</div>)}
      </div>)}
      {frontier ? <div className="coding-quota-row" role="group" aria-label="Frontier model">
        <span className="coding-quota-rowlabel">Frontier model</span>
        {providers.map((p) => { const w = p.windows.find((item) => item.kind === "frontier");
          return <div key={p.provider}>{w ? <QuotaRing window={w} now={now} model={modelName(w)} /> : null}</div>; })}
      </div> : null}
      {pools.map(({ provider, window }) => <div key={`${provider}/${window.id}`} className="coding-quota-row" role="group" aria-label={window.label ?? window.id}>
        <span className="coding-quota-rowlabel">{window.label ?? window.id.replace(/_/g, " ")}</span>
        {providers.map((p) => <div key={p.provider}>{p.provider === provider ? <QuotaRing window={window} now={now} /> : null}</div>)}
      </div>)}
    </div> : null}
  </section>;
}

export default function ProviderQuotaPanel() {
  const [data, setData] = useState<ProviderQuotas | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const tick = async () => {
      try {
        const next = await readProviderQuotas();
        if (active) { setData(next); setError(null); }
      } catch {
        if (active) setError("server unreachable");
      }
      if (active) timer = setTimeout(() => void tick(), POLL_MS);
    };
    void tick();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, []);
  return <ProviderQuotaView data={data} error={error} />;
}
