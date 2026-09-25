import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import type {
  EditorCommand,
  EditorObjectRead,
  EditorProjectionRead,
  RevisionRead,
} from "../api/generated/dwsimEditor";
import {
  createDwsimCase,
  DwsimEditorError,
  dwsimRevisionDownloadUrl,
  getDwsimProjection,
  importDwsimCase,
  listDwsimCases,
  listDwsimRevisions,
  restoreDwsimRevision,
  runDwsimCommand,
} from "../api/dwsimEditor";
import type { EditorCaseRead } from "../api/generated/dwsimEditor";
import type { PrimaryStageProps } from "./registry";
import "./ProcessStage.css";

const unitTypes = [
  "Mixer",
  "Splitter",
  "Heater",
  "Cooler",
  "Pump",
  "Valve",
  "Tank",
  "HeatExchanger",
];
type Point = { x: number; y: number };
type Drag = { id: string; origin: Point; pointer: Point };
type PanGesture = { clientX: number; clientY: number; origin: Point };
const unavailableText = (error: DwsimEditorError) =>
  error.status === 503
    ? `DWSIM unavailable · ${error.message} (${error.code})`
    : `${error.message} (${error.code})`;
const record = (value: unknown): Record<string, unknown> =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
const display = (value: unknown) =>
  typeof value === "string" || typeof value === "number"
    ? String(value)
    : value == null
      ? "—"
      : JSON.stringify(value);
function readProjectKnowledgeHandoff() {
  const params = new URLSearchParams(window.location.search);
  const revisionId = params.get("project_knowledge_revision_id")?.trim();
  const basisDigest = params.get("project_knowledge_basis_digest")?.trim();
  const validationSetDigest = params
    .get("project_knowledge_validation_set_digest")
    ?.trim();
  const requirementIds = params
    .getAll("project_knowledge_requirement_id")
    .map((value) => value.trim())
    .filter(Boolean);
  const present = Array.from(params.keys()).some((key) =>
    key.startsWith("project_knowledge_"),
  );
  return present
    ? {
        revisionId,
        basisDigest,
        validationSetDigest,
        requirementIds,
        valid: Boolean(
          revisionId &&
          basisDigest &&
          validationSetDigest &&
          requirementIds.length,
        ),
      }
    : null;
}

function ProcessStage({
  workspaceId,
  navigate,
  onShellRegionsChange,
}: PrimaryStageProps) {
  const [cases, setCases] = useState<EditorCaseRead[]>([]);
  const [caseId, setCaseId] = useState("");
  const [projection, setProjection] = useState<EditorProjectionRead | null>(
    null,
  );
  const [revisions, setRevisions] = useState<RevisionRead[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [runtimeUnavailable, setRuntimeUnavailable] = useState<{
    code: string;
    message: string;
  } | null>(null);
  const [tag, setTag] = useState("");
  const [unitType, setUnitType] = useState(unitTypes[0]);
  const [rename, setRename] = useState("");
  const [temperature, setTemperature] = useState("");
  const [pressure, setPressure] = useState("");
  const [massFlow, setMassFlow] = useState("");
  const [molarFlow, setMolarFlow] = useState("");
  const [composition, setComposition] = useState("");
  const [unitProperties, setUnitProperties] = useState("{}");
  const [compoundText, setCompoundText] = useState("Water");
  const [packageName, setPackageName] = useState("Steam Tables");
  const [connectUnit, setConnectUnit] = useState("");
  const [connectStream, setConnectStream] = useState("");
  const [connectRole, setConnectRole] = useState<
    "feed" | "product" | "energy_feed" | "energy_product"
  >("feed");
  const [connectPort, setConnectPort] = useState("0");
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Point>({ x: 0, y: 0 });
  const [placeX, setPlaceX] = useState("40");
  const [placeY, setPlaceY] = useState("40");
  const [drag, setDrag] = useState<Drag | null>(null);
  const [panGesture, setPanGesture] = useState<PanGesture | null>(null);
  const [ghost, setGhost] = useState<Point | null>(null);
  const [waitCancelled, setWaitCancelled] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const flight = useRef(false);
  const selected = useMemo(
    () =>
      projection?.objects.find((item) => item.native_id === selectedId) ?? null,
    [projection, selectedId],
  );
  useEffect(() => {
    onShellRegionsChange({
      sidecar: selected ? (
        <div className="dwsim-sidecar-inspector">
          <strong>
            {selected.tag ?? selected.type ?? "Unnamed DWSIM object"}
          </strong>
          <dl>
            <div>
              <dt>Type</dt>
              <dd>{selected.type ?? "—"}</dd>
            </div>
            <div>
              <dt>Native ID</dt>
              <dd>{selected.native_id ?? "—"} · case-local</dd>
            </div>
            <div>
              <dt>Category</dt>
              <dd>{selected.category}</dd>
            </div>
            <div>
              <dt>Calculation state</dt>
              <dd>
                {selected.calculated == null
                  ? "Unknown"
                  : selected.calculated
                    ? "Calculated"
                    : "Not calculated"}
              </dd>
            </div>
            {selected.errors && (
              <div>
                <dt>Errors</dt>
                <dd>{selected.errors}</dd>
              </div>
            )}
          </dl>
          <p>
            Engineering graph and results are read from DWSIM revision{" "}
            {projection?.revision.slice(0, 18)}.
          </p>
        </div>
      ) : undefined,
    });
  }, [onShellRegionsChange, projection?.revision, selected]);
  const safeObjects = useMemo(
    () =>
      Array.isArray(projection?.objects)
        ? projection.objects.filter((item) => item && typeof item === "object")
        : [],
    [projection],
  );
  const geometryIds = useMemo(
    () =>
      new Set(
        safeObjects
          .map((item) => item.native_id)
          .filter(
            (id): id is string => typeof id === "string" && id.length > 0,
          ),
      ),
    [safeObjects],
  );
  const connections = useMemo(() => {
    const all = Array.isArray(projection?.connections)
      ? projection.connections
      : [];
    const valid = all.filter(
      (edge) =>
        edge &&
        typeof edge === "object" &&
        typeof edge.source_native_id === "string" &&
        typeof edge.target_native_id === "string" &&
        geometryIds.has(edge.source_native_id) &&
        geometryIds.has(edge.target_native_id),
    );
    return { valid, invalidCount: all.length - valid.length };
  }, [geometryIds, projection]);
  const missingCoordinateCount = safeObjects.filter(
    (item) =>
      typeof item.x !== "number" ||
      !Number.isFinite(item.x) ||
      typeof item.y !== "number" ||
      !Number.isFinite(item.y),
  ).length;
  const unknownCategoryCount = safeObjects.filter(
    (item) =>
      !["unit", "material_stream", "energy_stream", "other"].includes(
        item.category,
      ),
  ).length;

  const loadCase = useCallback(
    async (id: string) => {
      if (!workspaceId || !id) return;
      setCaseId(id);
      setLoading(true);
      try {
        const [view, history] = await Promise.all([
          getDwsimProjection(workspaceId, id),
          listDwsimRevisions(workspaceId, id),
        ]);
        setProjection(view);
        setRevisions(history);
        setRuntimeUnavailable(null);
        setCaseId(id);
        setSelectedId(null);
        setMessage("");
      } catch (cause) {
        if (cause instanceof DwsimEditorError) {
          if (cause.status === 503)
            setRuntimeUnavailable({ code: cause.code, message: cause.message });
          setProjection(null);
          setMessage(unavailableText(cause));
        } else
          setMessage(
            cause instanceof Error
              ? cause.message
              : "Could not load DWSIM projection.",
          );
      } finally {
        setLoading(false);
      }
    },
    [workspaceId],
  );

  const refreshCases = useCallback(async () => {
    if (!workspaceId) return;
    try {
      const rows = await listDwsimCases(workspaceId);
      setCases(rows);
      if (
        rows.length &&
        (!caseId || !rows.some((item) => item.case_id === caseId))
      )
        await loadCase(rows[0].case_id);
      if (!rows.length) {
        setCaseId("");
        setProjection(null);
        setRevisions([]);
      }
    } catch (cause) {
      if (cause instanceof DwsimEditorError && cause.status === 503)
        setRuntimeUnavailable({ code: cause.code, message: cause.message });
      setMessage(
        cause instanceof Error
          ? unavailableText(
              cause instanceof DwsimEditorError
                ? cause
                : new DwsimEditorError(500, "request_failed", cause.message),
            )
          : "Could not list DWSIM cases.",
      );
    }
  }, [caseId, loadCase, workspaceId]);
  useEffect(() => {
    void refreshCases();
  }, [refreshCases]);

  type CommandPayload = EditorCommand extends infer Command
    ? Command extends EditorCommand
      ? Omit<Command, "expected_revision">
      : never
    : never;
  const command = useCallback(
    async (payload: CommandPayload) => {
      if (
        !workspaceId ||
        !caseId ||
        !projection ||
        !Array.isArray(projection.editable_commands) ||
        !projection.editable_commands.includes(payload.kind)
      )
        return;
      if (flight.current) return;
      flight.current = true;
      setLoading(true);
      setWaitCancelled(false);
      setMessage(`Applying ${payload.kind}…`);
      try {
        const result = await runDwsimCommand(workspaceId, caseId, {
          ...payload,
          expected_revision: projection.revision,
        } as EditorCommand);
        setProjection(result.projection);
        setRuntimeUnavailable(null);
        setMessage(
          `${payload.kind} read back as revision ${result.projection.revision.slice(0, 12)}.`,
        );
        try {
          setRevisions(await listDwsimRevisions(workspaceId, caseId));
        } catch (cause) {
          setMessage(
            `${payload.kind} read back as revision ${result.projection.revision.slice(0, 12)}. Revision history refresh failed: ${cause instanceof Error ? cause.message : "unknown error"}`,
          );
        }
      } catch (cause) {
        if (cause instanceof DwsimEditorError && cause.status === 409) {
          await loadCase(caseId);
          setMessage(
            "Changed elsewhere. The stale edit was discarded; review the refreshed server projection before editing again.",
          );
        } else if (cause instanceof DwsimEditorError) {
          if (cause.status === 503)
            setRuntimeUnavailable({ code: cause.code, message: cause.message });
          setMessage(unavailableText(cause));
        } else
          setMessage(
            cause instanceof Error ? cause.message : "DWSIM command failed.",
          );
      } finally {
        flight.current = false;
        setLoading(false);
      }
    },
    [caseId, loadCase, projection, workspaceId],
  );

  const createCase = async () => {
    if (!workspaceId || loading || flight.current || runtimeUnavailable) return;
    flight.current = true;
    setLoading(true);
    try {
      const created = await createDwsimCase(
        workspaceId,
        tag.trim() || "DWSIM case",
      );
      setCases((all) => [created, ...all]);
      setTag("");
      await loadCase(created.case_id);
    } catch (cause) {
      if (cause instanceof DwsimEditorError && cause.status === 503)
        setRuntimeUnavailable({ code: cause.code, message: cause.message });
      setMessage(
        cause instanceof DwsimEditorError
          ? unavailableText(cause)
          : "Could not create DWSIM case.",
      );
    } finally {
      flight.current = false;
      setLoading(false);
    }
  };
  const can = (kind: string) =>
    Boolean(
      Array.isArray(projection?.editable_commands) &&
      projection.editable_commands.includes(kind) &&
      !loading &&
      !flight.current &&
      !runtimeUnavailable,
    );
  const unsupported = (kind: string) =>
    (projection?.unsupported_commands &&
    typeof projection.unsupported_commands === "object"
      ? projection.unsupported_commands[kind]
      : undefined) ??
    (runtimeUnavailable
      ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
      : "Command is not available in this projection.");
  const pointAt = (event: ReactPointerEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    return {
      x: Math.round(
        (((event.clientX - bounds.left) * 1000) / bounds.width - pan.x) / zoom,
      ),
      y: Math.round(
        (((event.clientY - bounds.top) * 700) / bounds.height - pan.y) / zoom,
      ),
    };
  };
  const paletteCreate = (
    kind: "create_unit" | "create_material_stream" | "create_energy_stream",
    selectedType?: string,
  ) => {
    const p = { x: Number(placeX) || 0, y: Number(placeY) || 0 };
    const nextTag =
      tag.trim() ||
      `${selectedType ?? (kind === "create_unit" ? "Unit" : kind === "create_energy_stream" ? "Energy" : "Stream")}${safeObjects.length + 1}`;
    if (kind === "create_unit")
      void command({
        kind,
        unit_type: selectedType ?? unitType,
        tag: nextTag,
        ...p,
      });
    else if (kind === "create_material_stream")
      void command({
        kind,
        tag: nextTag,
        ...p,
        temperature: null,
        pressure: null,
        mass_flow: null,
        composition: null,
      });
    else void command({ kind, tag: nextTag, ...p });
    setTag("");
  };
  const submitInspector = () => {
    if (!projection || !selected?.tag) return;
    if (rename.trim() && rename.trim() !== selected.tag) {
      void command({
        kind: "rename",
        object: selected.tag,
        new_tag: rename.trim(),
      });
      return;
    }
    if (selected.category === "material_stream") {
      const parseQuantity = (value: string, unit: string) =>
        value.trim() ? { value: Number(value), unit } : null;
      let fractions: Record<string, number> | null = null;
      if (composition.trim()) {
        try {
          fractions = JSON.parse(composition) as Record<string, number>;
        } catch {
          setMessage(
            "Composition must be a JSON object of compound mass fractions.",
          );
          return;
        }
      }
      void command({
        kind: "set_stream_conditions",
        stream: selected.tag,
        temperature: parseQuantity(temperature, "K"),
        pressure: parseQuantity(pressure, "Pa"),
        mass_flow: parseQuantity(massFlow, "kg/s"),
        molar_flow: parseQuantity(molarFlow, "mol/s"),
        composition: fractions,
      });
    } else if (selected.category === "unit") {
      try {
        void command({
          kind: "set_unit_properties",
          unit: selected.tag,
          properties: JSON.parse(unitProperties) as Record<string, unknown>,
        });
      } catch {
        setMessage("Unit properties must be valid JSON.");
      }
    }
  };
  const restoreRevision = async (revision: string) => {
    if (!workspaceId || !caseId || !projection || loading || runtimeUnavailable)
      return;
    if (flight.current) return;
    flight.current = true;
    setLoading(true);
    setMessage("Restoring revision…");
    try {
      const result = await restoreDwsimRevision(
        workspaceId,
        caseId,
        projection.revision,
        revision,
      );
      setProjection(result.projection);
      setRevisions(await listDwsimRevisions(workspaceId, caseId));
      setMessage(
        `Restored as revision ${result.projection.revision.slice(0, 12)}.`,
      );
    } catch (cause) {
      if (cause instanceof DwsimEditorError && cause.status === 409) {
        await loadCase(caseId);
        setMessage(
          "Changed elsewhere. Restore was discarded; the current case was refreshed.",
        );
      } else
        setMessage(
          cause instanceof DwsimEditorError
            ? unavailableText(cause)
            : "Restore failed.",
        );
    } finally {
      flight.current = false;
      setLoading(false);
    }
  };
  const selectedIdText = selected?.native_id
    ? `${selected.native_id} · case-local`
    : "—";
  const solve = record(projection?.last_solve);
  const solveObjects = Array.isArray(solve.object_calculation)
    ? solve.object_calculation
        .filter((item) => item && typeof item === "object")
        .map(record)
    : [];
  const selectedResults = record(selected?.results);
  const handoff = readProjectKnowledgeHandoff();

  return (
    <section
      className="process-stage design-stage"
      aria-labelledby="process-stage-title"
      data-testid="process-editor-surface"
    >
      <header className="design-stage__header process-stage__header">
        <div className="design-stage__title-row">
          <div>
            <p className="eyebrow">Design · DWSIM</p>
            <h1 id="process-stage-title">Process workspace</h1>
            <p className="panel-subtitle">
              Interactive editor backed by the current immutable DWSIM case
              revision.
            </p>
          </div>
          <span
            className={`design-stage__truth-state ${runtimeUnavailable ? "is-unavailable" : ""}`}
          >
            {runtimeUnavailable
              ? "DWSIM unavailable"
              : projection
                ? "DWSIM available"
                : "DWSIM status unknown"}
          </span>
        </div>
        <nav className="design-stage__tabs" aria-label="Design workspaces">
          <button type="button" className="is-active" aria-current="page">
            Process
          </button>
          <button type="button" onClick={() => navigate("/design/bluecad")}>
            BLUECAD
          </button>
        </nav>
        <div className="dwsim-truth">
          <label>
            Case
            <select
              aria-label="DWSIM case"
              value={caseId}
              disabled={loading}
              onChange={(e) => void loadCase(e.target.value)}
            >
              <option value="">Select a case…</option>
              {cases.map((item) => (
                <option key={item.case_id} value={item.case_id}>
                  {item.case_id.slice(0, 8)} · rev{" "}
                  {
                    item.revision.split(":")[
                      item.revision.split(":").length - 1
                    ]
                  }
                </option>
              ))}
            </select>
          </label>
          <label>
            New case name
            <input
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              aria-label="New case name"
              disabled={loading || Boolean(runtimeUnavailable)}
              title={
                runtimeUnavailable
                  ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                  : undefined
              }
            />
          </label>
          <button
            type="button"
            disabled={loading || Boolean(runtimeUnavailable)}
            title={
              runtimeUnavailable
                ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                : "Create an empty native DWSIM case"
            }
            onClick={() => void createCase()}
          >
            New blank case
          </button>
          <button
            type="button"
            disabled={loading || Boolean(runtimeUnavailable)}
            title={
              runtimeUnavailable
                ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                : "Import a native DWSIM case"
            }
            onClick={() => fileRef.current?.click()}
          >
            Import .dwxmz / .dwxml
          </button>
          <button
            type="button"
            disabled={loading || !caseId}
            onClick={() => void loadCase(caseId)}
          >
            Refresh projection
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".dwxmz,.dwxml"
            hidden
            onChange={(e) => {
              const file = e.currentTarget.files?.[0];
              if (
                !file ||
                !workspaceId ||
                loading ||
                flight.current ||
                runtimeUnavailable
              )
                return;
              flight.current = true;
              setLoading(true);
              void importDwsimCase(workspaceId, file)
                .then(async (created) => {
                  setCases((all) => [created, ...all]);
                  await loadCase(created.case_id);
                })
                .catch((cause: unknown) => {
                  if (cause instanceof DwsimEditorError && cause.status === 503)
                    setRuntimeUnavailable({
                      code: cause.code,
                      message: cause.message,
                    });
                  setMessage(
                    cause instanceof DwsimEditorError
                      ? unavailableText(cause)
                      : "Import failed.",
                  );
                })
                .finally(() => {
                  flight.current = false;
                  setLoading(false);
                  e.currentTarget.value = "";
                });
            }}
          />
        </div>
        <div className="dwsim-truth__meta">
          <span>
            Revision · <code>{projection?.revision.slice(0, 18) ?? "—"}</code>
          </span>
          <span>DWSIM · {projection?.dwsim_version ?? "—"}</span>
          <span>Last solve · {display(solve.solve_status ?? "not run")}</span>
          {solve.mass_balance_residual_kg_s !== undefined && (
            <span>
              Residual · {display(solve.mass_balance_residual_kg_s)} kg/s ·
              source: last_solve.mass_balance_residual_kg_s
            </span>
          )}
        </div>
      </header>
      {projection?.last_solve && (
        <details className="dwsim-solve-results">
          <summary>
            Solve read-back · per-object calculation ({solveObjects.length})
          </summary>
          <ul>
            {solveObjects.map((item, index) => (
              <li key={`${display(item.tag)}:${index}`}>
                <strong>{display(item.tag)}</strong> ·{" "}
                {item.calculated === true
                  ? "calculated"
                  : item.calculated === false
                    ? "not calculated"
                    : "calculation state unknown"}
                {item.errors ? ` · ${display(item.errors)}` : ""}
              </li>
            ))}
          </ul>
          {typeof solve.mass_balance_status === "string" && (
            <p>
              Mass balance status · {display(solve.mass_balance_status)}
              {solve.mass_balance_error
                ? ` · ${display(solve.mass_balance_error)}`
                : ""}
            </p>
          )}
        </details>
      )}
      {handoff && (
        <div
          className="final-fusion__context-strip"
          role="status"
          aria-label="Project Knowledge recomputation handoff"
        >
          {handoff.valid ? (
            <>
              Project Knowledge recomputation request context · revision{" "}
              {handoff.revisionId} · basis {handoff.basisDigest} · validation
              set {handoff.validationSetDigest} · requirements{" "}
              {handoff.requirementIds.join(", ")}. Context is inspectable only;
              This editor cannot launch recomputation from the handoff.
            </>
          ) : (
            <>
              Incomplete Project Knowledge recomputation handoff ignored. No
              Process action is authorized from partial local URL context.
            </>
          )}
        </div>
      )}
      {runtimeUnavailable && (
        <div className="dwsim-error" role="alert">
          <strong>DWSIM unavailable · {runtimeUnavailable.code}</strong>
          <span>
            {runtimeUnavailable.message}. Editing controls are disabled until
            the runtime is available.
          </span>
        </div>
      )}
      {message && (
        <div className="dwsim-message" role="status" aria-live="polite">
          {message}
          {loading && flight.current && (
            <button
              type="button"
              onClick={() => {
                setWaitCancelled(true);
                setMessage(
                  "UI wait canceled; DWSIM command continues on the server.",
                );
              }}
            >
              Cancel UI wait
            </button>
          )}
          {waitCancelled && (
            <span>
              Server command remains in flight; its projection will still be
              applied when it returns.
            </span>
          )}
        </div>
      )}
      <div className="dwsim-workbench">
        <aside className="dwsim-palette" aria-label="DWSIM palette">
          <h2>Palette</h2>
          <label>
            Tag
            <input
              value={tag}
              onChange={(e) => setTag(e.target.value)}
              aria-label="Object tag"
              disabled={Boolean(runtimeUnavailable) || loading}
            />
          </label>
          <label>
            Unit type
            <select
              value={unitType}
              onChange={(e) => setUnitType(e.target.value)}
              disabled={Boolean(runtimeUnavailable) || loading}
            >
              {unitTypes.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            Canvas X
            <input
              type="number"
              aria-label="Canvas X"
              value={placeX}
              onChange={(e) => setPlaceX(e.target.value)}
              disabled={Boolean(runtimeUnavailable) || loading}
            />
          </label>
          <label>
            Canvas Y
            <input
              type="number"
              aria-label="Canvas Y"
              value={placeY}
              onChange={(e) => setPlaceY(e.target.value)}
              disabled={Boolean(runtimeUnavailable) || loading}
            />
          </label>
          <button
            disabled={!can("create_unit")}
            title={
              !can("create_unit")
                ? unsupported("create_unit")
                : "Add selected unit at the canvas coordinates"
            }
            onClick={() => paletteCreate("create_unit")}
          >
            Add unit
          </button>
          <button
            disabled={!can("create_material_stream")}
            title={
              !can("create_material_stream")
                ? unsupported("create_material_stream")
                : "Add a material stream at the canvas coordinates"
            }
            onClick={() => paletteCreate("create_material_stream")}
          >
            Material stream
          </button>
          <button
            disabled={!can("create_energy_stream")}
            title={
              !can("create_energy_stream")
                ? unsupported("create_energy_stream")
                : "Add an energy stream at the canvas coordinates"
            }
            onClick={() => paletteCreate("create_energy_stream")}
          >
            Energy stream
          </button>
          <h3>Available unit types</h3>
          <div className="dwsim-palette__types">
            {unitTypes.map((item) => (
              <button
                key={item}
                disabled={!can("create_unit")}
                title={
                  !can("create_unit")
                    ? unsupported("create_unit")
                    : `Add ${item}`
                }
                onClick={() => paletteCreate("create_unit", item)}
              >
                {item}
              </button>
            ))}
          </div>
          <h3>Command availability</h3>
          <div className="dwsim-command-catalogue">
            {(projection?.editable_commands ?? []).map((kind) => (
              <span key={kind} title="Available in current server projection">
                {kind} · available
              </span>
            ))}
            {Object.entries(projection?.unsupported_commands ?? {}).map(
              ([kind, reason]) => (
                <span key={kind} title={reason}>
                  {kind} · unsupported: {reason}
                </span>
              ),
            )}
          </div>
        </aside>
        <main className="dwsim-canvas-wrap">
          <div className="dwsim-canvas-toolbar">
            <button
              type="button"
              onClick={() => {
                setZoom(1);
                setPan({ x: 0, y: 0 });
              }}
            >
              Fit view
            </button>
            <button
              type="button"
              aria-label="Zoom out"
              onClick={() => setZoom((z) => Math.max(0.4, z - 0.1))}
            >
              −
            </button>
            <span>{Math.round(zoom * 100)}%</span>
            <button
              type="button"
              aria-label="Zoom in"
              onClick={() => setZoom((z) => Math.min(2, z + 0.1))}
            >
              +
            </button>
            <button
              disabled={!can("solve")}
              title={!can("solve") ? unsupported("solve") : "Run DWSIM solve"}
              onClick={() => void command({ kind: "solve" })}
            >
              Solve
            </button>
          </div>
          {projection ? (
            <svg
              className="dwsim-canvas"
              role="group"
              aria-label="DWSIM process canvas. Select an object to inspect; drag an object to move it or drag the empty canvas to pan."
              viewBox="0 0 1000 700"
              onPointerDown={(event) => {
                if (event.target === event.currentTarget) {
                  setPanGesture({
                    clientX: event.clientX,
                    clientY: event.clientY,
                    origin: pan,
                  });
                  event.currentTarget.setPointerCapture(event.pointerId);
                }
              }}
              onPointerMove={(event) => {
                if (panGesture) {
                  const bounds = event.currentTarget.getBoundingClientRect();
                  setPan({
                    x:
                      panGesture.origin.x +
                      ((event.clientX - panGesture.clientX) * 1000) /
                        bounds.width,
                    y:
                      panGesture.origin.y +
                      ((event.clientY - panGesture.clientY) * 700) /
                        bounds.height,
                  });
                } else if (drag) setGhost(pointAt(event));
              }}
              onPointerUp={(event) => {
                if (panGesture) {
                  setPanGesture(null);
                  event.currentTarget.releasePointerCapture?.(event.pointerId);
                  return;
                }
                if (!drag) return;
                const p = pointAt(event);
                setGhost(null);
                setDrag(null);
                event.currentTarget.releasePointerCapture?.(event.pointerId);
                if (
                  drag.id &&
                  (p.x !== drag.origin.x || p.y !== drag.origin.y)
                ) {
                  const object = safeObjects.find(
                    (item) => item.native_id === drag.id,
                  );
                  if (object?.tag)
                    void command({
                      kind: "move",
                      object: object.tag,
                      x: p.x,
                      y: p.y,
                    });
                }
              }}
            >
              <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
                {connections.valid.map((edge, index) => {
                  const a = safeObjects.find(
                    (item) => item.native_id === edge.source_native_id,
                  );
                  const b = safeObjects.find(
                    (item) => item.native_id === edge.target_native_id,
                  );
                  if (
                    !a ||
                    !b ||
                    a.x == null ||
                    a.y == null ||
                    b.x == null ||
                    b.y == null
                  )
                    return null;
                  return (
                    <path
                      key={`${edge.source_native_id}:${edge.source_port}:${edge.target_native_id}:${edge.target_port}:${index}`}
                      className={`dwsim-edge dwsim-edge--${edge.kind}`}
                      d={`M ${a.x + 55} ${a.y + 25} C ${a.x + 120} ${a.y + 25}, ${b.x - 50} ${b.y + 25}, ${b.x} ${b.y + 25}`}
                    />
                  );
                })}
                {safeObjects.map((object, index) => {
                  const id = object.native_id;
                  if (
                    !id ||
                    typeof object.x !== "number" ||
                    !Number.isFinite(object.x) ||
                    typeof object.y !== "number" ||
                    !Number.isFinite(object.y) ||
                    ![
                      "unit",
                      "material_stream",
                      "energy_stream",
                      "other",
                    ].includes(object.category)
                  )
                    return null;
                  const pos =
                    drag?.id === id && ghost
                      ? ghost
                      : { x: object.x, y: object.y };
                  const w =
                    object.width && object.width > 20
                      ? Math.min(150, object.width)
                      : object.category === "unit"
                        ? 96
                        : 92;
                  const h =
                    object.height && object.height > 20
                      ? Math.min(90, object.height)
                      : 48;
                  return (
                    <g
                      key={id}
                      className={`dwsim-node dwsim-node--${object.category}`}
                      transform={`translate(${pos.x},${pos.y})`}
                      role="button"
                      tabIndex={0}
                      aria-label={`${object.tag ?? object.type ?? "DWSIM object"}, ${object.category}`}
                      onClick={() => {
                        setSelectedId(id);
                        setRename(object.tag ?? "");
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setSelectedId(id);
                          setRename(object.tag ?? "");
                        }
                      }}
                      onPointerDown={(e) => {
                        if (e.button !== 0 || loading || runtimeUnavailable)
                          return;
                        e.stopPropagation();
                        const start = { x: object.x ?? 0, y: object.y ?? 0 };
                        setSelectedId(id);
                        setDrag({
                          id,
                          origin: start,
                          pointer: { x: e.clientX, y: e.clientY },
                        });
                        setGhost(start);
                        e.currentTarget.ownerSVGElement?.setPointerCapture(
                          e.pointerId,
                        );
                      }}
                    >
                      <rect
                        width={w}
                        height={h}
                        rx={object.category === "unit" ? 8 : 20}
                        className={selectedId === id ? "is-selected" : ""}
                      />
                      <text x={w / 2} y={h / 2 - 2} textAnchor="middle">
                        {object.tag ?? object.type ?? `Object ${index + 1}`}
                      </text>
                      <text
                        className="dwsim-node__type"
                        x={w / 2}
                        y={h / 2 + 13}
                        textAnchor="middle"
                      >
                        {object.type ?? object.category}
                      </text>
                      {object.errors && (
                        <text
                          className="dwsim-node__badge dwsim-node__badge--error"
                          x={w - 6}
                          y={9}
                        >
                          !
                        </text>
                      )}
                      {object.calculated === true && (
                        <text className="dwsim-node__badge" x={w - 8} y={h - 7}>
                          ✓
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </svg>
          ) : (
            <div className="dwsim-empty">
              <strong>
                {runtimeUnavailable
                  ? "No process topology is loaded."
                  : loading
                    ? "Loading DWSIM projection…"
                    : "Create or import a DWSIM case to begin."}
              </strong>
              <span>
                A graph appears only after the server returns a real DWSIM
                projection.
              </span>
            </div>
          )}
          {connections.invalidCount > 0 && (
            <div className="dwsim-warning" role="status">
              {connections.invalidCount} connection record(s) reference missing
              or invalid objects and were not drawn.
            </div>
          )}
          {missingCoordinateCount > 0 && (
            <div className="dwsim-warning" role="status">
              {missingCoordinateCount} projected object(s) have missing or
              invalid coordinates and were not drawn.
            </div>
          )}
          {(unknownCategoryCount > 0 ||
            safeObjects.some((item) => item.category === "other")) && (
            <div className="dwsim-warning" role="status">
              {unknownCategoryCount +
                safeObjects.filter((item) => item.category === "other")
                  .length}{" "}
              unrecognized object category object(s) are shown with neutral
              styling or omitted from the canvas.
            </div>
          )}
          <details className="dwsim-evidence">
            <summary>
              Read-back evidence · projection SHA-256 {projection?.case_sha256}
            </summary>
            <pre>{JSON.stringify(projection, null, 2)}</pre>
          </details>
        </main>
        <aside
          className="dwsim-inspector"
          aria-label="Selected DWSIM object properties"
        >
          <h2>Inspector</h2>
          {selected ? (
            <>
              <strong>
                {selected.tag ?? selected.type ?? "Unnamed object"}
              </strong>
              <dl>
                <dt>Type</dt>
                <dd>{selected.type ?? "—"}</dd>
                <dt>Native ID</dt>
                <dd>{selectedIdText}</dd>
                <dt>Calculation</dt>
                <dd>
                  {selected.calculated == null
                    ? "Unknown"
                    : selected.calculated
                      ? "Calculated"
                      : "Not calculated"}
                </dd>
                {selected.errors && (
                  <>
                    <dt>Errors</dt>
                    <dd className="dwsim-error-text">{selected.errors}</dd>
                  </>
                )}
              </dl>
              <label>
                Tag
                <input
                  aria-label="Rename selected object"
                  value={rename}
                  onChange={(e) => setRename(e.target.value)}
                  disabled={loading || Boolean(runtimeUnavailable)}
                  title={
                    runtimeUnavailable
                      ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                      : undefined
                  }
                />
              </label>
              <button
                disabled={!can("rename")}
                title={
                  !can("rename") ? unsupported("rename") : "Rename in DWSIM"
                }
                onClick={() =>
                  void command({
                    kind: "rename",
                    object: selected.tag ?? "",
                    new_tag: rename.trim(),
                  })
                }
              >
                Rename
              </button>
              {selected.category === "material_stream" && (
                <>
                  <h3>Stream conditions</h3>
                  <p>
                    Server results · T {display(selectedResults.temperature_K)}{" "}
                    K · P {display(selectedResults.pressure_Pa)} Pa · mass flow{" "}
                    {display(selectedResults.mass_flow_kg_s)} kg/s · molar flow{" "}
                    {display(selectedResults.molar_flow_mol_s)} mol/s ·
                    composition{" "}
                    {display(
                      selectedResults.composition ??
                        selectedResults.mass_fractions,
                    )}
                  </p>
                  <p>
                    Inputs · T K · pressure Pa · mass flow kg/s · molar flow
                    mol/s
                  </p>
                  <label>
                    Temperature (K)
                    <input
                      type="number"
                      value={temperature}
                      onChange={(e) => setTemperature(e.target.value)}
                      disabled={loading || Boolean(runtimeUnavailable)}
                      title={
                        runtimeUnavailable
                          ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                          : undefined
                      }
                    />
                  </label>
                  <label>
                    Pressure (Pa)
                    <input
                      type="number"
                      value={pressure}
                      onChange={(e) => setPressure(e.target.value)}
                      disabled={loading || Boolean(runtimeUnavailable)}
                      title={
                        runtimeUnavailable
                          ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                          : undefined
                      }
                    />
                  </label>
                  <label>
                    Mass flow (kg/s)
                    <input
                      type="number"
                      value={massFlow}
                      onChange={(e) => setMassFlow(e.target.value)}
                      disabled={loading || Boolean(runtimeUnavailable)}
                      title={
                        runtimeUnavailable
                          ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                          : undefined
                      }
                    />
                  </label>
                  <label>
                    Molar flow (mol/s)
                    <input
                      type="number"
                      value={molarFlow}
                      onChange={(e) => setMolarFlow(e.target.value)}
                      disabled={loading || Boolean(runtimeUnavailable)}
                      title={
                        runtimeUnavailable
                          ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                          : undefined
                      }
                    />
                  </label>
                  <label>
                    Mass fractions JSON
                    <input
                      value={composition}
                      onChange={(e) => setComposition(e.target.value)}
                      placeholder='{"Water":1}'
                      disabled={loading || Boolean(runtimeUnavailable)}
                      title={
                        runtimeUnavailable
                          ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                          : undefined
                      }
                    />
                  </label>
                  <button
                    disabled={!can("set_stream_conditions")}
                    title={
                      !can("set_stream_conditions")
                        ? unsupported("set_stream_conditions")
                        : "Apply stream conditions"
                    }
                    onClick={submitInspector}
                  >
                    Apply stream conditions
                  </button>
                </>
              )}
              {selected.category === "unit" && (
                <>
                  <h3>Unit properties</h3>
                  <label>
                    Property values JSON
                    <textarea
                      rows={4}
                      value={unitProperties}
                      onChange={(e) => setUnitProperties(e.target.value)}
                      disabled={loading || Boolean(runtimeUnavailable)}
                      title={
                        runtimeUnavailable
                          ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                          : undefined
                      }
                    />
                  </label>
                  <button
                    disabled={!can("set_unit_properties")}
                    title={
                      !can("set_unit_properties")
                        ? unsupported("set_unit_properties")
                        : "Apply DWSIM properties"
                    }
                    onClick={submitInspector}
                  >
                    Apply unit properties
                  </button>
                </>
              )}
              {selected.results && (
                <details>
                  <summary>Read-only results</summary>
                  <pre>{JSON.stringify(selected.results, null, 2)}</pre>
                </details>
              )}
              <button
                disabled={!can("delete_object")}
                title={
                  !can("delete_object")
                    ? unsupported("delete_object")
                    : "Delete object"
                }
                onClick={() =>
                  selected.tag &&
                  void command({ kind: "delete_object", object: selected.tag })
                }
              >
                Delete object
              </button>
            </>
          ) : (
            <p>Select an object in the server-backed canvas to inspect it.</p>
          )}
          <h3>Thermodynamics</h3>
          <p>Current package · {projection?.property_package ?? "not set"}</p>
          <label>
            Compounds (comma separated)
            <input
              value={compoundText}
              onChange={(e) => setCompoundText(e.target.value)}
              disabled={loading || Boolean(runtimeUnavailable)}
              title={
                runtimeUnavailable
                  ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                  : undefined
              }
            />
          </label>
          <button
            disabled={!can("add_compounds")}
            title={
              !can("add_compounds")
                ? unsupported("add_compounds")
                : "Add compounds"
            }
            onClick={() =>
              void command({
                kind: "add_compounds",
                compounds: compoundText
                  .split(",")
                  .map((v) => v.trim())
                  .filter(Boolean),
              })
            }
          >
            Add compounds
          </button>
          <label>
            Property package
            <input
              value={packageName}
              onChange={(e) => setPackageName(e.target.value)}
              disabled={loading || Boolean(runtimeUnavailable)}
              title={
                runtimeUnavailable
                  ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                  : undefined
              }
            />
          </label>
          <button
            disabled={!can("set_property_package")}
            title={
              !can("set_property_package")
                ? unsupported("set_property_package")
                : "Set property package"
            }
            onClick={() =>
              void command({ kind: "set_property_package", name: packageName })
            }
          >
            Set property package
          </button>
          <p>Compounds · {projection?.compounds.join(", ") || "none"}</p>
          <h3>Connect objects</h3>
          <label>
            Unit
            <select
              value={connectUnit}
              onChange={(e) => setConnectUnit(e.target.value)}
              disabled={loading || Boolean(runtimeUnavailable)}
              title={
                runtimeUnavailable
                  ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                  : undefined
              }
            >
              {safeObjects
                .filter((o) => o.category === "unit" && o.tag)
                .map((o) => (
                  <option key={o.native_id} value={o.tag!}>
                    {o.tag}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Stream
            <select
              value={connectStream}
              onChange={(e) => setConnectStream(e.target.value)}
              disabled={loading || Boolean(runtimeUnavailable)}
              title={
                runtimeUnavailable
                  ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                  : undefined
              }
            >
              {safeObjects
                .filter(
                  (o) =>
                    (o.category === "material_stream" ||
                      o.category === "energy_stream") &&
                    o.tag,
                )
                .map((o) => (
                  <option key={o.native_id} value={o.tag!}>
                    {o.tag}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Role
            <select
              value={connectRole}
              onChange={(e) =>
                setConnectRole(e.target.value as typeof connectRole)
              }
            >
              <option value="feed">feed</option>
              <option value="product">product</option>
              <option value="energy_feed">energy_feed</option>
              <option value="energy_product">energy_product</option>
            </select>
          </label>
          <label>
            Port
            <input
              type="number"
              min="0"
              value={connectPort}
              onChange={(e) => setConnectPort(e.target.value)}
              disabled={loading || Boolean(runtimeUnavailable)}
              title={
                runtimeUnavailable
                  ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                  : undefined
              }
            />
          </label>
          <button
            disabled={!can("connect") || !connectUnit || !connectStream}
            title={
              !can("connect")
                ? unsupported("connect")
                : "Connect selected unit and stream"
            }
            onClick={() =>
              void command({
                kind: "connect",
                unit: connectUnit,
                stream: connectStream,
                role: connectRole,
                port: Math.max(0, Number(connectPort) || 0),
              })
            }
          >
            Connect
          </button>
          <button
            disabled={!can("disconnect")}
            title={
              !can("disconnect")
                ? unsupported("disconnect")
                : "Disconnect objects"
            }
          >
            Disconnect
          </button>
        </aside>
      </div>
      <section className="dwsim-revisions">
        <h2>Revision history</h2>
        {[...revisions].reverse().map((revision) => (
          <div key={revision.revision}>
            <span>
              #{revision.seq} · {revision.command_kind} ·{" "}
              {revision.revision.slice(0, 16)}
            </span>
            <a
              href={
                caseId && workspaceId
                  ? dwsimRevisionDownloadUrl(
                      workspaceId,
                      caseId,
                      revision.revision,
                    )
                  : undefined
              }
              aria-disabled={!caseId || !workspaceId}
            >
              Download
            </a>
            <button
              disabled={
                loading ||
                runtimeUnavailable !== null ||
                !projection ||
                revision.revision === projection.revision
              }
              title={
                runtimeUnavailable
                  ? `${runtimeUnavailable.code}: ${runtimeUnavailable.message}`
                  : "Restore this revision with current revision CAS"
              }
              onClick={() => void restoreRevision(revision.revision)}
            >
              Restore
            </button>
          </div>
        ))}
      </section>
    </section>
  );
}

export default ProcessStage;
