import { useEffect, useMemo, useState } from "react";

import { listWorkspaces, type Workspace } from "../api/client";
import {
  createCalendarAllocation,
  createRoadmapItem,
  listCalendarAllocations,
  listRoadmapItems,
  updateRoadmapItem,
  type CalendarAllocation,
  type RoadmapItem
} from "../api/development";

type Props = {
  mode: "timeline" | "calendar";
  workspaceId: string | null;
  onWorkspaceChange(next: string | null): void;
};

export default function DevelopmentRoadmap({ mode, workspaceId, onWorkspaceChange }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [items, setItems] = useState<RoadmapItem[]>([]);
  const [allocations, setAllocations] = useState<CalendarAllocation[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [eventTitle, setEventTitle] = useState("");
  const [eventItemId, setEventItemId] = useState("");
  const [eventStart, setEventStart] = useState("");
  const [eventEnd, setEventEnd] = useState("");
  const [eventTimezone, setEventTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC");

  useEffect(() => {
    let alive = true;
    listWorkspaces().then((rows) => {
      if (!alive) return;
      setWorkspaces(rows);
      if (!workspaceId && rows[0]) onWorkspaceChange(rows[0].id);
      else if (workspaceId && !rows.some((row) => row.id === workspaceId)) onWorkspaceChange(rows[0]?.id ?? null);
    }).catch((exc: unknown) => alive && setError(exc instanceof Error ? exc.message : "Workspace discovery failed."));
    return () => { alive = false; };
  }, [workspaceId, onWorkspaceChange]);

  async function refresh(selectedWorkspaceId: string) {
    const [nextItems, nextAllocations] = await Promise.all([
      listRoadmapItems(selectedWorkspaceId),
      listCalendarAllocations(selectedWorkspaceId)
    ]);
    setItems(nextItems);
    setAllocations(nextAllocations);
  }

  useEffect(() => {
    if (!workspaceId) {
      setItems([]);
      setAllocations([]);
      return;
    }
    let alive = true;
    setError(null);
    Promise.all([listRoadmapItems(workspaceId), listCalendarAllocations(workspaceId)])
      .then(([nextItems, nextAllocations]) => {
        if (!alive) return;
        setItems(nextItems);
        setAllocations(nextAllocations);
      })
      .catch((exc: unknown) => alive && setError(exc instanceof Error ? exc.message : "Development data failed to load."));
    return () => { alive = false; };
  }, [workspaceId]);

  const allocationsByItem = useMemo(() => {
    const map = new Map<string, number>();
    for (const allocation of allocations) {
      if (allocation.roadmap_item_id) map.set(allocation.roadmap_item_id, (map.get(allocation.roadmap_item_id) ?? 0) + 1);
    }
    return map;
  }, [allocations]);

  async function run(action: () => Promise<void>) {
    if (!workspaceId || busy) return;
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh(workspaceId);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Development mutation failed.");
    } finally {
      setBusy(false);
    }
  }

  const workspaceSelector = (
    <label>
      Workspace
      <select value={workspaceId ?? ""} onChange={(event) => onWorkspaceChange(event.target.value || null)}>
        <option value="">Select workspace</option>
        {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
      </select>
    </label>
  );

  return (
    <section className="operator-page" data-testid={`development-roadmap-${mode}`}>
      <header className="operator-page__header">
        <div>
          <p className="eyebrow">Development · Roadmap</p>
          <h1>{mode === "timeline" ? "Timeline" : "Calendar"}</h1>
          <p>{mode === "timeline" ? "Project windows and execution status remain Roadmap-owned state." : "Scheduled work blocks remain Calendar-owned state and never rewrite Roadmap windows."}</p>
        </div>
        {workspaceSelector}
      </header>

      {error ? <div role="alert" className="inline-notice inline-notice--error">{error}</div> : null}
      {!workspaceId ? <p>Select a workspace to load server-owned Development state.</p> : null}

      {workspaceId && mode === "timeline" ? <>
        <form onSubmit={(event) => {
          event.preventDefault();
          const title = newTitle.trim();
          if (!title) return;
          void run(async () => { await createRoadmapItem(workspaceId, title); setNewTitle(""); });
        }}>
          <label>New work item <input value={newTitle} onChange={(event) => setNewTitle(event.target.value)} /></label>
          <button type="submit" disabled={busy || !newTitle.trim()}>+ Add work item</button>
        </form>
        <div className="operator-card-grid">
          {items.map((item) => <article key={item.id} className="operator-card" data-testid="roadmap-item">
            <div><strong>{item.title}</strong><p>{item.item_type} · {item.priority}</p></div>
            <p>Status: <strong>{item.status}</strong></p>
            <p>Project window: {item.window_start_date ?? "unset"} → {item.window_end_date ?? "unset"}</p>
            <p>Scheduled blocks: {allocationsByItem.get(item.id) ?? 0}</p>
            {item.done_when ? <p>Done when: {item.done_when} · {item.done_when_satisfied ? "satisfied" : "not satisfied"}</p> : null}
            <div>
              {item.status !== "Done" && item.status !== "Cancelled" ? <button disabled={busy} onClick={() => void run(async () => { await updateRoadmapItem(item, { status: "Done" }); })}>Mark Done</button> : null}
            </div>
          </article>)}
          {items.length === 0 ? <p>No Roadmap items yet.</p> : null}
        </div>
      </> : null}

      {workspaceId && mode === "calendar" ? <>
        <form onSubmit={(event) => {
          event.preventDefault();
          if (!eventTitle.trim() || !eventStart || !eventEnd || !eventTimezone.trim()) return;
          void run(async () => {
            await createCalendarAllocation(workspaceId, eventItemId || null, eventTitle.trim(), eventStart, eventEnd, eventTimezone.trim());
            setEventTitle("");
            setEventStart("");
            setEventEnd("");
          });
        }}>
          <label>Title <input value={eventTitle} onChange={(event) => setEventTitle(event.target.value)} /></label>
          <label>Roadmap item <select value={eventItemId} onChange={(event) => setEventItemId(event.target.value)}><option value="">None</option>{items.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
          <label>Start <input type="datetime-local" value={eventStart} onChange={(event) => setEventStart(event.target.value)} /></label>
          <label>End <input type="datetime-local" value={eventEnd} onChange={(event) => setEventEnd(event.target.value)} /></label>
          <label>Time zone <input value={eventTimezone} onChange={(event) => setEventTimezone(event.target.value)} /></label>
          <button type="submit" disabled={busy}>+ Add event</button>
        </form>
        <div className="operator-card-grid">
          {allocations.map((allocation) => <article key={allocation.id} className="operator-card" data-testid="calendar-allocation">
            <strong>{allocation.title}</strong>
            <p>{allocation.start_instant} → {allocation.end_instant}</p>
            <p>Time zone: {allocation.timezone}</p>
            <p>Roadmap item: {items.find((item) => item.id === allocation.roadmap_item_id)?.title ?? "None"}</p>
          </article>)}
          {allocations.length === 0 ? <p>No Calendar allocations yet.</p> : null}
        </div>
      </> : null}
    </section>
  );
}
