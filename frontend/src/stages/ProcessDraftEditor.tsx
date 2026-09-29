import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import ProcessProposals from "../components/process/ProcessProposals";
import {
  createDraft,
  DRAFT_CHANGED_EVENT,
  DraftApiError,
  executeDraft,
  formatQuantity,
  getDraft,
  getDraftRegistry,
  getDraftRun,
  listDraftRevisions,
  listDrafts,
  patchDraft,
  restoreDraftRevision,
  unitLabel,
  type DraftObject,
  type DraftOp,
  type DraftProjection,
  type DraftQuantity,
  type DraftRegistry,
  type DraftRun,
  type DraftSummary,
  type Proposal,
  type RegistryUnit,
  type RevisionSummary,
  type StoredQuantity,
} from "../api/processDraft";
import "./ProcessDraftEditor.css";

type Point = { x: number; y: number };
type Drag = { id: string; pointer: Point; origin: Point; moved: boolean };
type Notice = { tone: "info" | "danger" | "success"; text: string } | null;

const UNIT_W = 76;
const UNIT_H = 44;
const STREAM_R = 7;

const errorText = (cause: unknown) =>
  cause instanceof DraftApiError
    ? `${cause.message}${cause.detail.field ? ` (${String(cause.detail.field)})` : ""} · ${cause.code}`
    : "The request failed.";

const portY = (count: number, port: number) => (port - (count - 1) / 2) * 14;

function nextTag(objects: DraftObject[], prefix: string) {
  const used = new Set(objects.map((item) => item.tag));
  let index = 1;
  while (used.has(`${prefix}${index}`)) index += 1;
  return `${prefix}${index}`;
}

function nextId(objects: DraftObject[], prefix: string) {
  const used = new Set(objects.map((item) => item.id));
  let index = 1;
  while (used.has(`${prefix}${index}`)) index += 1;
  return `${prefix}${index}`;
}

/** Unit-bearing input: the operator's value and unit travel to the server, which converts. */
function QuantityInput({
  label,
  kind,
  stored,
  units,
  value,
  onChange,
}: {
  label: string;
  kind: string;
  stored?: StoredQuantity;
  units: string[];
  value: { text: string; unit: string } | undefined;
  onChange(next: { text: string; unit: string }): void;
}) {
  const current = value ?? { text: stored ? String(stored.value) : "", unit: stored?.unit ?? units[0] };
  return (
    <label className="draft-quantity">
      <span>{label}</span>
      <span className="draft-quantity__row">
        <input
          inputMode="decimal"
          aria-label={label}
          value={current.text}
          onChange={(event) => onChange({ ...current, text: event.target.value })}
        />
        <select
          aria-label={`${label} unit`}
          value={current.unit}
          onChange={(event) => onChange({ ...current, unit: event.target.value })}
          disabled={units.length < 2}
        >
          {units.map((unit) => (
            <option key={unit} value={unit}>
              {unitLabel(unit)}
            </option>
          ))}
        </select>
      </span>
      <small data-kind={kind}>{stored ? `stored ${formatQuantity(stored)}` : "not set"}</small>
    </label>
  );
}

type FormState = Record<string, { text: string; unit: string }>;

function quantitiesFrom(form: FormState): Record<string, DraftQuantity> | null {
  const result: Record<string, DraftQuantity> = {};
  for (const [key, entry] of Object.entries(form)) {
    if (!entry.text.trim()) continue;
    const value = Number(entry.text);
    if (!Number.isFinite(value)) return null;
    result[key] = { value, unit: entry.unit };
  }
  return result;
}

export default function ProcessDraftEditor({ workspaceId }: Readonly<{ workspaceId: string }>) {
  const [registry, setRegistry] = useState<DraftRegistry | null>(null);
  const [drafts, setDrafts] = useState<DraftSummary[]>([]);
  const [draft, setDraft] = useState<DraftProjection | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState<"validate" | "run" | null>(null);
  const [lastRun, setLastRun] = useState<DraftRun | null>(null);
  const [solvedRun, setSolvedRun] = useState<DraftRun | null>(null);
  const [revisions, setRevisions] = useState<RevisionSummary[] | null>(null);
  const [drag, setDrag] = useState<Drag | null>(null);
  const [overrides, setOverrides] = useState<Record<string, Point>>({});
  const [form, setForm] = useState<FormState>({});
  const [composition, setComposition] = useState<Record<string, string>>({});
  const [mode, setMode] = useState<string>("");
  const [rename, setRename] = useState("");
  const revisionRef = useRef<string>("");
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const svgRef = useRef<SVGSVGElement>(null);

  const accept = useCallback((next: DraftProjection) => {
    revisionRef.current = next.revision;
    setDraft(next);
  }, []);

  const loadDraft = useCallback(
    async (draftId: string) => {
      accept(await getDraft(workspaceId, draftId));
    },
    [accept, workspaceId],
  );

  useEffect(() => {
    let live = true;
    setDraft(null);
    setLastRun(null);
    setSolvedRun(null);
    void (async () => {
      try {
        const [reg, rows] = await Promise.all([getDraftRegistry(workspaceId), listDrafts(workspaceId)]);
        if (!live) return;
        setRegistry(reg);
        setDrafts(rows);
        if (rows[0]) accept(await getDraft(workspaceId, rows[0].draft_id));
      } catch (cause) {
        if (live) setNotice({ tone: "danger", text: errorText(cause) });
      }
    })();
    return () => {
      live = false;
    };
  }, [accept, workspaceId]);

  // Hermes proposals and Sidecar approvals arrive out of band; keep the canvas current.
  useEffect(() => {
    if (!draft) return;
    const draftId = draft.draft_id;
    const refresh = () => {
      if (drag || busy) return;
      void getDraft(workspaceId, draftId)
        .then((next) => {
          setDraft((current) => {
            if (
              current &&
              current.revision === next.revision &&
              JSON.stringify(current.proposals.map((p) => [p.proposal_id, p.state])) ===
                JSON.stringify(next.proposals.map((p) => [p.proposal_id, p.state])) &&
              current.results.last_attempt?.run_id === next.results.last_attempt?.run_id
            )
              return current;
            revisionRef.current = next.revision;
            return next;
          });
        })
        .catch(() => undefined);
    };
    const timer = window.setInterval(refresh, 3000);
    window.addEventListener(DRAFT_CHANGED_EVENT, refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener(DRAFT_CHANGED_EVENT, refresh);
    };
  }, [busy, drag, draft, workspaceId]);

  // Results shown on the canvas always come from the recorded run bound to a revision.
  const solvedRunId = draft?.results.run_id;
  useEffect(() => {
    if (!draft || !solvedRunId) return setSolvedRun(null);
    if (solvedRun?.run_id === solvedRunId) return;
    void getDraftRun(workspaceId, draft.draft_id, solvedRunId).then(setSolvedRun).catch(() => undefined);
  }, [draft, solvedRun?.run_id, solvedRunId, workspaceId]);

  const apply = useCallback(
    (ops: DraftOp[]) => {
      if (!draft) return Promise.resolve();
      const draftId = draft.draft_id;
      queue.current = queue.current.then(async () => {
        try {
          accept(await patchDraft(workspaceId, draftId, revisionRef.current, ops));
          setNotice(null);
          return true;
        } catch (cause) {
          if (cause instanceof DraftApiError && cause.status === 409) {
            await loadDraft(draftId);
            setNotice({ tone: "danger", text: "The draft changed elsewhere. It was reloaded; re-apply your edit." });
          } else {
            setNotice({ tone: "danger", text: errorText(cause) });
          }
          return false;
        } finally {
          setOverrides({});
        }
      });
      return queue.current;
    },
    [accept, draft, loadDraft, workspaceId],
  );

  const objects = useMemo(() => draft?.objects ?? [], [draft]);
  const byId = useMemo(() => new Map(objects.map((item) => [item.id, item])), [objects]);
  const units = objects.filter((item) => item.kind === "unit");
  const selected = selectedId ? byId.get(selectedId) ?? null : null;
  const unitSpec = (type: string): RegistryUnit | undefined => registry?.units.find((item) => item.type === type);
  const blockers = (draft?.findings ?? []).filter((item) => item.severity === "blocker");
  const pending = (draft?.proposals ?? []).filter((item) => item.state === "pending");
  const proposalTargets = useMemo(() => {
    const map = new Map<string, Proposal["changes"]>();
    for (const proposal of pending) for (const change of proposal.changes) map.set(change.target_id, [...(map.get(change.target_id) ?? []), change]);
    return map;
  }, [pending]);

  // Inspector drafts reset whenever the selection or its revision changes.
  useEffect(() => {
    setForm({});
    setRename(selected?.tag ?? "");
    setMode(selected?.mode ?? "");
    setComposition(
      Object.fromEntries((draft?.compounds ?? []).map((name) => [name, String(selected?.spec?.composition?.[name] ?? "")])),
    );
  }, [selected?.id, draft?.revision]); // eslint-disable-line react-hooks/exhaustive-deps

  const position = (item: DraftObject): Point => overrides[item.id] ?? { x: item.x, y: item.y };
  const toSvg = (event: { clientX: number; clientY: number }): Point => {
    const svg = svgRef.current;
    const matrix = svg?.getScreenCTM();
    if (!svg || !matrix) return { x: event.clientX, y: event.clientY };
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    return { x: point.x, y: point.y };
  };

  const onPointerDown = (event: ReactPointerEvent, item: DraftObject) => {
    event.stopPropagation();
    (event.target as Element).setPointerCapture?.(event.pointerId);
    setSelectedId(item.id);
    setDrag({ id: item.id, pointer: toSvg(event), origin: position(item), moved: false });
  };
  const onPointerMove = (event: ReactPointerEvent) => {
    if (!drag) return;
    const point = toSvg(event);
    const dx = point.x - drag.pointer.x;
    const dy = point.y - drag.pointer.y;
    if (!drag.moved && Math.hypot(dx, dy) < 3) return;
    setDrag({ ...drag, moved: true });
    setOverrides({ [drag.id]: { x: Math.round(drag.origin.x + dx), y: Math.round(drag.origin.y + dy) } });
  };
  const onPointerUp = () => {
    if (!drag) return;
    const moved = overrides[drag.id];
    setDrag(null);
    if (drag.moved && moved) void apply([{ op: "move", id: drag.id, x: moved.x, y: moved.y }]);
  };

  const addUnit = (type: string) => {
    const spot = { x: 80 + (objects.length % 6) * 110, y: 80 + Math.floor(objects.length / 6) * 110 };
    const prefix = { Heater: "H", Cooler: "C", Pump: "P", Valve: "V", Mixer: "M", Flash: "F" }[type] ?? "U";
    const id = nextId(objects, "u");
    void apply([{ op: "add_unit", id, type, tag: nextTag(objects, `${prefix}-`), ...spot }]).then(() => setSelectedId(id));
  };
  const addStream = () => {
    const spot = { x: 80 + (objects.length % 6) * 110, y: 60 + Math.floor(objects.length / 6) * 110 };
    const id = nextId(objects, "s");
    void apply([{ op: "add_stream", id, tag: nextTag(objects, "S"), ...spot }]).then(() => setSelectedId(id));
  };

  const act = async (action: "validate" | "run", revision?: string) => {
    if (!draft) return;
    setBusy(action);
    setNotice(null);
    try {
      const result = await executeDraft(workspaceId, draft.draft_id, revision ?? draft.revision, action);
      setLastRun(result.run);
      if (result.run.status === "completed") setSolvedRun(result.run);
      accept(result.draft);
    } catch (cause) {
      setNotice({ tone: "danger", text: errorText(cause) });
    } finally {
      setBusy(null);
    }
  };

  if (!registry) return <div className="draft-editor draft-editor--loading">{notice?.text ?? "Loading process draft…"}</div>;
  if (!draft)
    return (
      <div className="draft-editor draft-editor--empty">
        <p>No process draft yet. A draft is the Jarvis-owned flowsheet: edits are instant and DWSIM runs only on Validate/Run.</p>
        <button
          type="button"
          onClick={() =>
            void createDraft(workspaceId, "Process draft").then((created) => {
              accept(created);
              setDrafts([{ draft_id: created.draft_id, name: created.name, revision: created.revision, updated_at: "" }]);
            })
          }
        >
          Create process draft
        </button>
        {notice && <p role="alert">{notice.text}</p>}
      </div>
    );

  const results = draft.results;
  const streamResult = (tag: string) => solvedRun?.streams?.[tag]?.display;
  const bounds = objects.reduce(
    (acc, item) => {
      const point = position(item);
      return { minX: Math.min(acc.minX, point.x - 90), minY: Math.min(acc.minY, point.y - 90), maxX: Math.max(acc.maxX, point.x + 120), maxY: Math.max(acc.maxY, point.y + 90) };
    },
    { minX: 0, minY: 0, maxX: 760, maxY: 360 },
  );

  const renderEdges = () =>
    objects
      .filter((item) => item.kind === "stream")
      .flatMap((stream) => {
        const at = position(stream);
        const lines = [];
        for (const end of ["source", "target"] as const) {
          const endpoint = stream[end];
          const unit = endpoint ? byId.get(endpoint.unit) : undefined;
          if (!endpoint || !unit) continue;
          const spec = unitSpec(unit.type);
          const u = position(unit);
          const count = end === "source" ? spec?.outlets.length ?? 1 : spec?.inlets.length ?? 1;
          const unitPoint = { x: u.x + (end === "source" ? UNIT_W / 2 : -UNIT_W / 2), y: u.y + portY(count, endpoint.port) };
          const [from, to] = end === "source" ? [unitPoint, { x: at.x - STREAM_R, y: at.y }] : [{ x: at.x + STREAM_R, y: at.y }, unitPoint];
          lines.push(
            <path
              key={`${stream.id}-${end}`}
              className="draft-edge"
              d={`M${from.x},${from.y} C${(from.x + to.x) / 2},${from.y} ${(from.x + to.x) / 2},${to.y} ${to.x},${to.y}`}
              markerEnd="url(#draft-arrow)"
            />,
          );
        }
        return lines;
      });

  const renderBadge = (item: DraftObject, point: Point) => {
    const changes = proposalTargets.get(item.id);
    if (!changes) return null;
    const text = changes.map((change) => `${change.property.replace(/_/g, " ")}: ${formatQuantity(change.current)} → ${formatQuantity(change.proposed)}`);
    const width = Math.max(...text.map((line) => line.length)) * 6.2 + 16;
    const top = point.y - (item.kind === "unit" ? UNIT_H / 2 : STREAM_R) - 14 - text.length * 14;
    return (
      <g className="draft-proposal-badge" data-testid={`proposal-badge-${item.tag}`}>
        <rect x={point.x - width / 2} y={top} width={width} height={text.length * 14 + 8} rx={4} />
        {text.map((line, index) => (
          <text key={line} x={point.x} y={top + 14 + index * 14} textAnchor="middle">
            {line}
          </text>
        ))}
      </g>
    );
  };

  const renderObject = (item: DraftObject) => {
    const point = position(item);
    const findings = draft.findings.filter((finding) => finding.object === item.tag && finding.severity === "blocker");
    const classes = [
      "draft-node",
      `draft-node--${item.kind}`,
      selectedId === item.id ? "is-selected" : "",
      findings.length ? "has-findings" : "",
      proposalTargets.has(item.id) ? "is-proposal-target" : "",
    ].join(" ");
    if (item.kind === "unit") {
      const spec = unitSpec(item.type);
      return (
        <g key={item.id} className={classes} onPointerDown={(event) => onPointerDown(event, item)} data-testid={`node-${item.tag}`}>
          <rect x={point.x - UNIT_W / 2} y={point.y - UNIT_H / 2} width={UNIT_W} height={UNIT_H} rx={6} />
          <text x={point.x} y={point.y - 3} textAnchor="middle" className="draft-node__tag">{item.tag}</text>
          <text x={point.x} y={point.y + 12} textAnchor="middle" className="draft-node__type">{spec?.label ?? item.type}</text>
          {renderBadge(item, point)}
        </g>
      );
    }
    const shown = streamResult(item.tag);
    const feed = !item.source;
    return (
      <g key={item.id} className={classes} onPointerDown={(event) => onPointerDown(event, item)} data-testid={`node-${item.tag}`}>
        <circle cx={point.x} cy={point.y} r={STREAM_R} className={feed ? "is-feed" : ""} />
        <text x={point.x} y={point.y + 20} textAnchor="middle" className="draft-node__tag">{item.tag}</text>
        {shown && (
          <text x={point.x} y={point.y + 33} textAnchor="middle" className={`draft-node__result${results.state === "stale" ? " is-stale" : ""}`}>
            {[shown.temperature, shown.pressure, shown.mass_flow].filter(Boolean).map((value) => formatQuantity(value)).join(" · ")}
          </text>
        )}
        {renderBadge(item, point)}
      </g>
    );
  };

  const streamOptions = (end: "source" | "target") =>
    units.flatMap((unit) => {
      const spec = unitSpec(unit.type);
      const ports = end === "source" ? spec?.outlets ?? [] : spec?.inlets ?? [];
      return ports.map((name, port) => ({ value: `${unit.id}:${port}`, label: `${unit.tag} · ${name}` }));
    });

  const renderStreamInspector = (stream: DraftObject) => {
    const units_ = registry.quantity_units;
    const feed = !stream.source;
    const sum = Object.values(composition).reduce((acc, text) => acc + (Number(text) || 0), 0);
    const shown = solvedRun?.streams?.[stream.tag];
    return (
      <>
        {(["source", "target"] as const).map((end) => (
          <label key={end} className="draft-field">
            <span>{end === "source" ? "From (unit outlet)" : "To (unit inlet)"}</span>
            <select
              aria-label={end === "source" ? "Stream source" : "Stream target"}
              value={stream[end] ? `${stream[end]!.unit}:${stream[end]!.port}` : ""}
              onChange={(event) => {
                const [unit, port] = event.target.value.split(":");
                void apply(
                  event.target.value
                    ? [{ op: "connect", stream: stream.id, end, unit, port: Number(port) }]
                    : [{ op: "disconnect", stream: stream.id, end }],
                );
              }}
            >
              <option value="">{end === "source" ? "— feed (no source)" : "— product (no target)"}</option>
              {streamOptions(end).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
        ))}
        {feed ? (
          <fieldset className="draft-fieldset">
            <legend>Feed specification</legend>
            {registry.stream_specs.map((spec) => (
              <QuantityInput
                key={spec.key}
                label={spec.label}
                kind={spec.kind}
                stored={stream.spec?.[spec.key as "temperature"]}
                units={units_[spec.kind].display}
                value={form[spec.key]}
                onChange={(next) => setForm((current) => ({ ...current, [spec.key]: next }))}
              />
            ))}
            <button
              type="button"
              disabled={!Object.keys(form).length}
              onClick={() => {
                const values = quantitiesFrom(form);
                if (!values) return setNotice({ tone: "danger", text: "Enter numbers only." });
                void apply([{ op: "set_stream_spec", stream: stream.id, ...values }]);
              }}
            >
              Apply conditions
            </button>
            <table className="draft-composition" aria-label="Composition (mass fractions)">
              <thead><tr><th>Compound</th><th>Mass fraction</th></tr></thead>
              <tbody>
                {draft.compounds.map((name) => (
                  <tr key={name}>
                    <td>{name}</td>
                    <td>
                      <input
                        inputMode="decimal"
                        aria-label={`${name} mass fraction`}
                        value={composition[name] ?? ""}
                        onChange={(event) => setComposition((current) => ({ ...current, [name]: event.target.value }))}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot><tr><td>Sum</td><td className={Math.abs(sum - 1) > 1e-6 ? "is-invalid" : ""}>{sum.toPrecision(6)}</td></tr></tfoot>
            </table>
            {!draft.compounds.length && <p className="draft-hint">Declare compounds in Thermo first.</p>}
            <button
              type="button"
              disabled={!draft.compounds.length}
              onClick={() => {
                const entries = Object.entries(composition).filter(([, text]) => text.trim() !== "");
                if (entries.some(([, text]) => !Number.isFinite(Number(text))))
                  return setNotice({ tone: "danger", text: "Mass fractions must be numbers." });
                void apply([{ op: "set_stream_spec", stream: stream.id, composition: Object.fromEntries(entries.map(([name, text]) => [name, Number(text)])) }]);
              }}
            >
              Apply composition
            </button>
          </fieldset>
        ) : (
          <p className="draft-hint">Computed by DWSIM from its upstream unit. Only feed streams take specifications.</p>
        )}
        {shown?.display && (
          <dl className={`draft-results-inline${results.state === "stale" ? " is-stale" : ""}`}>
            {Object.entries(shown.display).map(([key, value]) => (
              <div key={key}><dt>{key.replace("_", " ")}</dt><dd>{formatQuantity(value)}</dd></div>
            ))}
            {shown.vapor_fraction != null && <div><dt>vapor fraction</dt><dd>{shown.vapor_fraction.toPrecision(4)}</dd></div>}
          </dl>
        )}
      </>
    );
  };

  const renderUnitInspector = (unit: DraftObject) => {
    const spec = unitSpec(unit.type);
    if (!spec) return <p>Unsupported unit type.</p>;
    const activeMode = mode || unit.mode || "";
    const params = spec.params.filter((param) => param.modes.includes(activeMode));
    const connected = (end: "source" | "target", port: number) =>
      objects.find((item) => item.kind === "stream" && item[end]?.unit === unit.id && item[end]?.port === port)?.tag ?? "—";
    const reported = solvedRun?.units?.[unit.tag]?.reported;
    return (
      <>
        <dl className="draft-ports">
          {spec.inlets.map((name, port) => (<div key={`in${port}`}><dt>{name}</dt><dd>{connected("target", port)}</dd></div>))}
          {spec.outlets.map((name, port) => (<div key={`out${port}`}><dt>{name}</dt><dd>{connected("source", port)}</dd></div>))}
        </dl>
        {spec.modes.length > 0 && (
          <fieldset className="draft-fieldset">
            <legend>Specification</legend>
            <label className="draft-field">
              <span>Mode</span>
              <select aria-label="Unit mode" value={activeMode} onChange={(event) => { setMode(event.target.value); setForm({}); }}>
                {spec.modes.map((item) => (<option key={item} value={item}>{item.replace(/_/g, " ")}</option>))}
              </select>
            </label>
            {params.map((param) => (
              <QuantityInput
                key={param.key}
                label={param.label}
                kind={param.kind}
                stored={activeMode === unit.mode ? unit.params?.[param.key] : undefined}
                units={registry.quantity_units[param.kind].display}
                value={form[param.key]}
                onChange={(next) => setForm((current) => ({ ...current, [param.key]: next }))}
              />
            ))}
            <button
              type="button"
              disabled={!Object.keys(form).length && activeMode === unit.mode}
              onClick={() => {
                const values = quantitiesFrom(form);
                if (!values) return setNotice({ tone: "danger", text: "Enter numbers only." });
                void apply([{ op: "set_unit_params", unit: unit.id, ...(activeMode !== unit.mode ? { mode: activeMode } : {}), values }]);
              }}
            >
              Apply specification
            </button>
          </fieldset>
        )}
        {reported && Object.keys(reported).length > 0 && (
          <dl className={`draft-results-inline${results.state === "stale" ? " is-stale" : ""}`}>
            {Object.entries(reported).slice(0, 8).map(([key, value]) => (
              <div key={key}><dt>{key}</dt><dd>{value.value} {value.units}</dd></div>
            ))}
          </dl>
        )}
      </>
    );
  };

  const renderRun = (run: DraftRun) => (
    <section className={`draft-run draft-run--${run.status}`} aria-label="Last DWSIM attempt">
      <header>
        <strong>{run.action === "validate" ? "Validate" : "Run"}: {run.status.replace(/_/g, " ")}</strong>
        <span>revision {run.draft_revision.split(":")[0]} · {run.compile_seconds ?? "—"} s</span>
      </header>
      {run.status === "materialization_mismatch" && (
        <>
          <p>DWSIM did not reproduce the draft exactly, so nothing was solved. Differences:</p>
          <table className="draft-diffs">
            <thead><tr><th>Path</th><th>Draft expects</th><th>DWSIM holds</th></tr></thead>
            <tbody>
              {(run.materialization_diffs ?? []).map((diff) => (
                <tr key={diff.path}><td>{diff.path}</td><td>{String(diff.expected)}</td><td>{String(diff.actual)}</td></tr>
              ))}
            </tbody>
          </table>
          <button type="button" disabled={busy !== null} onClick={() => void act(run.action, run.draft_revision)}>Retry</button>
        </>
      )}
      {run.status === "materialization_failed" && (
        <p>DWSIM refused step {String(run.error_detail?.step ?? "?")}. {run.error}{" "}
          <button type="button" disabled={busy !== null} onClick={() => void act(run.action, run.draft_revision)}>Retry</button></p>
      )}
      {run.dwsim_check && run.dwsim_check.findings.length > 0 && (
        <ul className="draft-findings">
          {run.dwsim_check.findings.map((finding, index) => (
            <li key={index} data-severity={finding.severity}><strong>{finding.object || "Flowsheet"}</strong> {finding.message} {finding.fix && <em>{finding.fix}</em>}</li>
          ))}
        </ul>
      )}
      {run.status === "validated" && <p>DWSIM reproduced the draft exactly and its check found nothing blocking.</p>}
      {run.solve && run.status !== "completed" && <p>Solve failed: {run.solve.failed_objects.map((item) => `${item.tag} ${item.error}`).join("; ") || "DWSIM reported errors."}</p>}
    </section>
  );

  const renderResults = () => {
    if (!solvedRun || results.state === "none") return <p className="draft-hint">No results yet. Run compiles this exact revision into DWSIM.</p>;
    return (
      <section className={`draft-results draft-results--${results.state}`} aria-label="DWSIM results">
        <div className="draft-results__banner" role="status">
          {results.state === "current"
            ? `Current · run ${solvedRun.run_id.slice(0, 8)} on revision ${solvedRun.draft_revision.split(":")[0]}`
            : `Stale · ${results.edits_since} edit(s) since run ${solvedRun.run_id.slice(0, 8)} on revision ${solvedRun.draft_revision.split(":")[0]}. Values below describe that revision, not the current draft.`}
        </div>
        <table>
          <thead><tr><th>Stream</th><th>T</th><th>P</th><th>Mass flow</th><th>Vapor frac.</th></tr></thead>
          <tbody>
            {Object.entries(solvedRun.streams ?? {}).map(([tag, value]) => (
              <tr key={tag}>
                <td>{tag}</td>
                <td>{formatQuantity(value.display?.temperature)}</td>
                <td>{formatQuantity(value.display?.pressure)}</td>
                <td>{formatQuantity(value.display?.mass_flow)}</td>
                <td>{value.vapor_fraction == null ? "—" : value.vapor_fraction.toPrecision(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <dl className="draft-provenance">
          <div><dt>Mass balance residual</dt><dd>{solvedRun.mass_balance?.status === "calculated" ? `${solvedRun.mass_balance.residual_kg_s?.toExponential(2)} kg/s` : solvedRun.mass_balance?.error ?? "—"}</dd></div>
          <div><dt>Revision</dt><dd>{solvedRun.draft_revision}</dd></div>
          <div><dt>Materialization</dt><dd title={solvedRun.materialization_fingerprint}>{solvedRun.materialization_fingerprint?.slice(0, 19)}…</dd></div>
          <div><dt>Compiler / DWSIM</dt><dd>{solvedRun.compiler_version} / {solvedRun.dwsim_version} · MCP {solvedRun.mcp_sha256.slice(0, 8)}</dd></div>
        </dl>
      </section>
    );
  };

  return (
    <div className="draft-editor">
      <div className="draft-toolbar">
        <label className="draft-field draft-field--inline">
          <span>Draft</span>
          <select
            aria-label="Process draft"
            value={draft.draft_id}
            onChange={(event) => void loadDraft(event.target.value)}
          >
            {drafts.map((row) => (<option key={row.draft_id} value={row.draft_id}>{row.name}</option>))}
          </select>
        </label>
        <span className="draft-revision">revision {draft.seq}</span>
        <button type="button" disabled={busy !== null || blockers.length > 0} title={blockers.length ? "Resolve the findings first" : "Compile this revision into DWSIM, verify it, and run DWSIM's check"} onClick={() => void act("validate")}>
          {busy === "validate" ? "Validating…" : "Validate (DWSIM)"}
        </button>
        <button type="button" className="draft-run-button" disabled={busy !== null || blockers.length > 0} onClick={() => void act("run")}>
          {busy === "run" ? "Running…" : "Run (DWSIM)"}
        </button>
        <span className={`draft-state draft-state--${results.state}`} data-testid="results-state">
          {results.state === "none" ? "No results" : results.state === "current" ? "Results current" : `Results stale (${results.edits_since} edits)`}
        </span>
        <button type="button" className="draft-history-toggle" onClick={() => void (revisions ? setRevisions(null) : listDraftRevisions(workspaceId, draft.draft_id).then(setRevisions))}>
          {revisions ? "Hide history" : "History"}
        </button>
      </div>
      {notice && <p className={`draft-notice draft-notice--${notice.tone}`} role="alert">{notice.text}</p>}
      <div className="draft-body">
        <aside className="draft-palette" aria-label="Palette">
          <h3>Add</h3>
          <button type="button" onClick={addStream}>Material stream</button>
          {registry.units.map((unit) => (
            <button key={unit.type} type="button" onClick={() => addUnit(unit.type)}>{unit.label}</button>
          ))}
          <h3>Not yet supported</h3>
          <ul className="draft-unsupported">
            {Object.entries(registry.unsupported).map(([type, reason]) => (<li key={type} title={reason}>{type}</li>))}
          </ul>
        </aside>
        <div className="draft-canvas-wrap">
          <svg
            ref={svgRef}
            className="draft-canvas"
            role="img"
            aria-label="Process flowsheet draft"
            viewBox={`${bounds.minX} ${bounds.minY} ${bounds.maxX - bounds.minX} ${bounds.maxY - bounds.minY}`}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerDown={() => setSelectedId(null)}
          >
            <defs>
              <marker id="draft-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" />
              </marker>
            </defs>
            {renderEdges()}
            {objects.map(renderObject)}
          </svg>
          <section className="draft-findings-panel" aria-label="Draft findings">
            <h3>Before DWSIM: {blockers.length ? `${blockers.length} to resolve` : "draft complete"}</h3>
            <ul className="draft-findings">
              {draft.findings.map((finding, index) => (
                <li key={index} data-severity={finding.severity}>
                  <button type="button" onClick={() => setSelectedId(objects.find((item) => item.tag === finding.object)?.id ?? null)}>
                    <strong>{finding.object || "Draft"}</strong> {finding.message}
                  </button>
                </li>
              ))}
            </ul>
          </section>
          {lastRun && renderRun(lastRun)}
          {renderResults()}
          {revisions && (
            <section className="draft-history" aria-label="Revision history">
              <ol>
                {revisions.map((row) => (
                  <li key={row.revision}>
                    <span>#{row.seq} · {row.actor} · {row.ops.join(", ") || "created"}</span>
                    {row.revision !== draft.revision && (
                      <button type="button" onClick={() => void restoreDraftRevision(workspaceId, draft.draft_id, draft.revision, row.revision).then((next) => { accept(next); setRevisions(null); }).catch((cause) => setNotice({ tone: "danger", text: errorText(cause) }))}>
                        Restore
                      </button>
                    )}
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
        <aside className="draft-inspector" aria-label="Inspector">
          <ProcessProposals workspaceId={workspaceId} draftId={draft.draft_id} proposals={draft.proposals} onDecided={() => void loadDraft(draft.draft_id)} />
          {selected ? (
            <>
              <h3>{selected.kind === "unit" ? unitSpec(selected.type)?.label : "Material stream"} {selected.tag}</h3>
              <div className="draft-rename">
                <input aria-label="Tag" value={rename} onChange={(event) => setRename(event.target.value)} />
                <button type="button" disabled={!rename || rename === selected.tag} onClick={() => void apply([{ op: "rename", id: selected.id, tag: rename }])}>Rename</button>
                <button type="button" className="draft-delete" onClick={() => { void apply([{ op: "delete", id: selected.id }]); setSelectedId(null); }}>Delete</button>
              </div>
              {selected.kind === "stream" ? renderStreamInspector(selected) : renderUnitInspector(selected)}
            </>
          ) : (
            <fieldset className="draft-fieldset" aria-label="Thermo">
              <legend>Thermo</legend>
              <label className="draft-field">
                <span>Property package</span>
                <select
                  aria-label="Property package"
                  value={draft.property_package ?? ""}
                  onChange={(event) => void apply([{ op: "set_thermo", property_package: event.target.value }])}
                >
                  <option value="" disabled>Choose…</option>
                  {registry.property_packages.map((name) => (<option key={name} value={name}>{name}</option>))}
                </select>
              </label>
              <div className="draft-compounds" role="group" aria-label="Compounds">
                {registry.compounds.map((name) => (
                  <label key={name}>
                    <input
                      type="checkbox"
                      checked={draft.compounds.includes(name)}
                      onChange={(event) =>
                        void apply([{ op: "set_thermo", compounds: event.target.checked ? [...draft.compounds, name] : draft.compounds.filter((item) => item !== name) }])
                      }
                    />
                    {name}
                  </label>
                ))}
              </div>
              <p className="draft-hint">Select an object on the canvas to edit it.</p>
            </fieldset>
          )}
        </aside>
      </div>
    </div>
  );
}
