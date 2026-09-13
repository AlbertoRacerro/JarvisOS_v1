import { useEffect, useMemo, useState } from "react";

import { listWorkspaces, type Workspace } from "../api/client";
import {
  createCalendarAllocation,
  createRoadmapItem,
  deleteCalendarAllocation,
  deleteRoadmapItem,
  listCalendarAllocations,
  listRoadmapItems,
  updateCalendarAllocation,
  updateRoadmapItem,
  type CalendarAllocation,
  type RoadmapItem
} from "../api/development";

type Props = {
  mode: "timeline" | "calendar";
  workspaceId: string | null;
  onWorkspaceChange(next: string | null): void;
};

type CalendarView = "Day" | "Week" | "Month" | "Agenda";
const ROADMAP_STATUSES = ["Planned", "Ready", "In progress", "Blocked", "Done", "Cancelled"] as const;
const DAY_MS = 24 * 60 * 60 * 1000;

function formatAllocationInstant(instant: string, timeZone: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone
  }).format(new Date(instant));
}

function zonedParts(instant: string | Date, timeZone: string): Record<string, string> {
  return Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23"
    }).formatToParts(typeof instant === "string" ? new Date(instant) : instant).filter((part) => part.type !== "literal").map((part) => [part.type, part.value])
  );
}

function dateKeyForInstant(instant: string | Date, timeZone: string): string {
  const parts = zonedParts(instant, timeZone);
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function allocationDateKey(allocation: CalendarAllocation): string {
  return dateKeyForInstant(allocation.start_instant, allocation.timezone);
}

function allocationEndDateKey(allocation: CalendarAllocation): string {
  const exclusiveEnd = new Date(Math.max(
    new Date(allocation.start_instant).getTime(),
    new Date(allocation.end_instant).getTime() - 1
  ));
  return dateKeyForInstant(exclusiveEnd, allocation.timezone);
}

function allocationOverlapsDateRange(allocation: CalendarAllocation, firstDay: string, lastDay: string): boolean {
  return allocationDateKey(allocation) <= lastDay && allocationEndDateKey(allocation) >= firstDay;
}

function allocationLocalInput(instant: string, timeZone: string): string {
  const parts = zonedParts(instant, timeZone);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

function shiftDate(dateKey: string, days: number): string {
  const date = new Date(`${dateKey}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function weekStart(dateKey: string): string {
  const date = new Date(`${dateKey}T00:00:00Z`);
  const mondayOffset = (date.getUTCDay() + 6) % 7;
  return shiftDate(dateKey, -mondayOffset);
}

function monthRange(dateKey: string): [string, string] {
  const [year, month] = dateKey.split("-").map(Number);
  const first = `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-01`;
  const nextMonth = new Date(Date.UTC(year, month, 1));
  nextMonth.setUTCDate(nextMonth.getUTCDate() - 1);
  return [first, nextMonth.toISOString().slice(0, 10)];
}

function dayOffset(dateKey: string, origin: string): number {
  return Math.round((new Date(`${dateKey}T00:00:00Z`).getTime() - new Date(`${origin}T00:00:00Z`).getTime()) / DAY_MS);
}

export default function DevelopmentRoadmap({ mode, workspaceId, onWorkspaceChange }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [items, setItems] = useState<RoadmapItem[]>([]);
  const [allocations, setAllocations] = useState<CalendarAllocation[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editWindowStart, setEditWindowStart] = useState("");
  const [editWindowEnd, setEditWindowEnd] = useState("");
  const [editDoneWhen, setEditDoneWhen] = useState("");
  const [calendarView, setCalendarView] = useState<CalendarView>("Week");
  const [calendarAnchor, setCalendarAnchor] = useState(() => new Date().toISOString().slice(0, 10));
  const [calendarAnchorTouched, setCalendarAnchorTouched] = useState(false);
  const [eventTitle, setEventTitle] = useState("");
  const [eventItemId, setEventItemId] = useState("");
  const [eventStart, setEventStart] = useState("");
  const [eventEnd, setEventEnd] = useState("");
  const [eventTimezone, setEventTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC");
  const [editingAllocationId, setEditingAllocationId] = useState<string | null>(null);
  const [editEventTitle, setEditEventTitle] = useState("");
  const [editEventItemId, setEditEventItemId] = useState("");
  const [editEventStart, setEditEventStart] = useState("");
  const [editEventEnd, setEditEventEnd] = useState("");
  const [editEventTimezone, setEditEventTimezone] = useState("");
  const requestedRoadmapItemId = new URLSearchParams(window.location.search).get("roadmap_item_id");

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

  useEffect(() => {
    if (mode !== "calendar" || eventItemId || items.length === 0) return;
    if (requestedRoadmapItemId && items.some((item) => item.id === requestedRoadmapItemId)) setEventItemId(requestedRoadmapItemId);
  }, [mode, eventItemId, items, requestedRoadmapItemId]);

  useEffect(() => {
    if (mode !== "calendar" || calendarAnchorTouched || allocations.length === 0) return;
    setCalendarAnchor(allocationDateKey(allocations[0]));
  }, [mode, allocations, calendarAnchorTouched]);

  useEffect(() => {
    if (mode !== "timeline" || !requestedRoadmapItemId || items.length === 0) return;
    document.getElementById(`roadmap-item-${requestedRoadmapItemId}`)?.scrollIntoView({ block: "center" });
  }, [mode, requestedRoadmapItemId, items]);

  const allocationsByItem = useMemo(() => {
    const map = new Map<string, number>();
    for (const allocation of allocations) {
      if (allocation.roadmap_item_id) map.set(allocation.roadmap_item_id, (map.get(allocation.roadmap_item_id) ?? 0) + 1);
    }
    return map;
  }, [allocations]);

  const timelineRange = useMemo(() => {
    const starts = items.map((item) => item.window_start_date).filter((value): value is string => Boolean(value));
    const ends = items.map((item) => item.window_end_date).filter((value): value is string => Boolean(value));
    if (starts.length === 0 && ends.length === 0) return null;
    const first = [...starts, ...ends].sort()[0];
    const last = [...starts, ...ends].sort().at(-1) ?? first;
    return { first, last, days: Math.max(1, dayOffset(last, first) + 1) };
  }, [items]);

  const projectedAllocations = useMemo(() => {
    const sorted = [...allocations].sort((left, right) => left.start_instant.localeCompare(right.start_instant));
    if (calendarView === "Agenda") return sorted;
    if (calendarView === "Day") return sorted.filter((allocation) => allocationOverlapsDateRange(allocation, calendarAnchor, calendarAnchor));
    if (calendarView === "Month") {
      const [firstDay, lastDay] = monthRange(calendarAnchor);
      return sorted.filter((allocation) => allocationOverlapsDateRange(allocation, firstDay, lastDay));
    }
    const firstDay = weekStart(calendarAnchor);
    const lastDay = shiftDate(firstDay, 6);
    return sorted.filter((allocation) => allocationOverlapsDateRange(allocation, firstDay, lastDay));
  }, [allocations, calendarView, calendarAnchor]);

  const openedRoadmapItem = mode === "timeline" && requestedRoadmapItemId
    ? items.find((item) => item.id === requestedRoadmapItemId) ?? null
    : null;

  async function run(action: () => Promise<void>) {
    if (!workspaceId || busy) return;
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh(workspaceId);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Development mutation failed.");
      try {
        await refresh(workspaceId);
      } catch {
        // Keep the original mutation error visible; the next explicit refresh remains available through navigation.
      }
    } finally {
      setBusy(false);
    }
  }

  function beginRoadmapEdit(item: RoadmapItem) {
    setEditingItemId(item.id);
    setEditTitle(item.title);
    setEditWindowStart(item.window_start_date ?? "");
    setEditWindowEnd(item.window_end_date ?? "");
    setEditDoneWhen(item.done_when ?? "");
  }

  function beginAllocationEdit(allocation: CalendarAllocation) {
    setEditingAllocationId(allocation.id);
    setEditEventTitle(allocation.title);
    setEditEventItemId(allocation.roadmap_item_id ?? "");
    setEditEventStart(allocationLocalInput(allocation.start_instant, allocation.timezone));
    setEditEventEnd(allocationLocalInput(allocation.end_instant, allocation.timezone));
    setEditEventTimezone(allocation.timezone);
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
        {requestedRoadmapItemId ? <p aria-live="polite">Opened roadmap item: {openedRoadmapItem?.title ?? "not found in this workspace"}</p> : null}
        <form onSubmit={(event) => {
          event.preventDefault();
          const title = newTitle.trim();
          if (!title) return;
          void run(async () => { await createRoadmapItem(workspaceId, title); setNewTitle(""); });
        }}>
          <label>New work item <input value={newTitle} onChange={(event) => setNewTitle(event.target.value)} /></label>
          <button type="submit" disabled={busy || !newTitle.trim()}>+ Add work item</button>
        </form>

        <section aria-label="Roadmap project-window timeline" data-testid="roadmap-timeline-projection">
          <h2>Project windows</h2>
          {timelineRange ? <>
            <p>{timelineRange.first} → {timelineRange.last}</p>
            {items.filter((item) => item.window_start_date || item.window_end_date).map((item) => {
              const start = item.window_start_date ?? item.window_end_date ?? timelineRange.first;
              const end = item.window_end_date ?? item.window_start_date ?? start;
              const left = Math.max(0, dayOffset(start, timelineRange.first));
              const width = Math.max(1, dayOffset(end, start) + 1);
              return <div key={item.id} data-testid="roadmap-timeline-window">
                <span>{item.title}</span>
                <div
                  role="img"
                  aria-label={`${item.title}: ${start} to ${end}`}
                  style={{ marginLeft: `${(left / timelineRange.days) * 100}%`, width: `${Math.min(100 - (left / timelineRange.days) * 100, (width / timelineRange.days) * 100)}%` }}
                >{start} → {end}</div>
              </div>;
            })}
          </> : <p>No project windows set.</p>}
        </section>

        <details data-testid="roadmap-execution-status">
          <summary>Execution status</summary>
          {ROADMAP_STATUSES.map((status) => {
            const matching = items.filter((item) => item.status === status);
            return <div key={status}><strong>{status} · {matching.length}</strong>{matching.length ? <ul>{matching.map((item) => <li key={item.id}><a href={`#roadmap-item-${item.id}`}>{item.title}</a></li>)}</ul> : null}</div>;
          })}
        </details>

        <div className="operator-card-grid">
          {items.map((item) => <article key={item.id} id={`roadmap-item-${item.id}`} className="operator-card" data-testid="roadmap-item" data-opened={requestedRoadmapItemId === item.id ? "true" : undefined}>
            {editingItemId === item.id ? <form onSubmit={(event) => {
              event.preventDefault();
              void run(async () => {
                await updateRoadmapItem(item, {
                  title: editTitle.trim(),
                  window_start_date: editWindowStart || null,
                  window_end_date: editWindowEnd || null,
                  done_when: editDoneWhen.trim() || null
                });
                setEditingItemId(null);
              });
            }}>
              <label>Edit title <input value={editTitle} onChange={(event) => setEditTitle(event.target.value)} /></label>
              <label>Window start <input type="date" value={editWindowStart} onChange={(event) => setEditWindowStart(event.target.value)} /></label>
              <label>Window end <input type="date" value={editWindowEnd} onChange={(event) => setEditWindowEnd(event.target.value)} /></label>
              <label>Done when <input value={editDoneWhen} onChange={(event) => setEditDoneWhen(event.target.value)} /></label>
              <button type="submit" disabled={busy || !editTitle.trim()}>Save work item</button>
              <button type="button" disabled={busy} onClick={() => setEditingItemId(null)}>Cancel</button>
            </form> : <>
              <div><strong>{item.title}</strong><p>{item.item_type} · {item.priority}</p></div>
              <p>Status: <strong>{item.status}</strong></p>
              <p>Project window: {item.window_start_date ?? "unset"} → {item.window_end_date ?? "unset"}</p>
              <p>Scheduled blocks: {allocationsByItem.get(item.id) ?? 0}</p>
              {item.done_when ? <p>Done when: {item.done_when} · {item.done_when_satisfied ? "satisfied" : "not satisfied"}</p> : null}
              <label>Lifecycle status <select value={item.status} disabled={busy} onChange={(event) => void run(async () => { await updateRoadmapItem(item, { status: event.target.value }); })}>{ROADMAP_STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}</select></label>
              <div>
                <button type="button" disabled={busy} onClick={() => beginRoadmapEdit(item)}>Edit work item</button>
                {item.status !== "Done" && item.status !== "Cancelled" ? <button type="button" disabled={busy} onClick={() => void run(async () => { await updateRoadmapItem(item, { status: "Done" }); })}>Mark Done</button> : null}
                <button type="button" disabled={busy} onClick={() => void run(async () => { await deleteRoadmapItem(item); })}>Delete work item</button>
                <a href={`/development/roadmap/calendar?roadmap_item_id=${encodeURIComponent(item.id)}`}>Schedule in Calendar</a>
              </div>
            </>}
          </article>)}
          {items.length === 0 ? <p>No Roadmap items yet.</p> : null}
        </div>
      </> : null}

      {workspaceId && mode === "calendar" ? <>
        <div role="region" aria-label="Calendar projection">
          {(["Day", "Week", "Month", "Agenda"] as CalendarView[]).map((view) => (
            <button key={view} type="button" aria-pressed={calendarView === view} onClick={() => setCalendarView(view)}>{view}</button>
          ))}
          <label>View date <input type="date" value={calendarAnchor} onChange={(event) => { setCalendarAnchor(event.target.value); setCalendarAnchorTouched(true); }} /></label>
          <p>Calendar projection: <strong>{calendarView}</strong>{calendarView === "Agenda" ? " · all allocations" : ` · ${calendarAnchor}`}</p>
        </div>
        <form onSubmit={(event) => {
          event.preventDefault();
          if (!eventTitle.trim() || !eventStart || !eventEnd || !eventTimezone.trim()) return;
          void run(async () => {
            await createCalendarAllocation(workspaceId, eventItemId || null, eventTitle.trim(), eventStart, eventEnd, eventTimezone.trim());
            setCalendarAnchor(eventStart.slice(0, 10));
            setCalendarAnchorTouched(true);
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
        <div className="operator-card-grid" data-calendar-view={calendarView.toLowerCase()}>
          {projectedAllocations.map((allocation) => <article key={allocation.id} className="operator-card" data-testid="calendar-allocation">
            {editingAllocationId === allocation.id ? <form onSubmit={(event) => {
              event.preventDefault();
              void run(async () => {
                await updateCalendarAllocation(allocation, {
                  title: editEventTitle.trim(),
                  roadmap_item_id: editEventItemId || null,
                  start_local: editEventStart,
                  end_local: editEventEnd,
                  timezone: editEventTimezone.trim()
                });
                setCalendarAnchor(editEventStart.slice(0, 10));
                setCalendarAnchorTouched(true);
                setEditingAllocationId(null);
              });
            }}>
              <label>Edit event title <input value={editEventTitle} onChange={(event) => setEditEventTitle(event.target.value)} /></label>
              <label>Edit Roadmap item <select value={editEventItemId} onChange={(event) => setEditEventItemId(event.target.value)}><option value="">None</option>{items.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
              <label>Edit start <input type="datetime-local" value={editEventStart} onChange={(event) => setEditEventStart(event.target.value)} /></label>
              <label>Edit end <input type="datetime-local" value={editEventEnd} onChange={(event) => setEditEventEnd(event.target.value)} /></label>
              <label>Edit time zone <input value={editEventTimezone} onChange={(event) => setEditEventTimezone(event.target.value)} /></label>
              <button type="submit" disabled={busy || !editEventTitle.trim() || !editEventStart || !editEventEnd || !editEventTimezone.trim()}>Save event</button>
              <button type="button" disabled={busy} onClick={() => setEditingAllocationId(null)}>Cancel</button>
            </form> : <>
              <strong>{allocation.title}</strong>
              <p>{formatAllocationInstant(allocation.start_instant, allocation.timezone)} → {formatAllocationInstant(allocation.end_instant, allocation.timezone)}</p>
              <p>Time zone: {allocation.timezone}</p>
              <p>Roadmap item: {items.find((item) => item.id === allocation.roadmap_item_id)?.title ?? "None"}</p>
              <div>
                <button type="button" disabled={busy} onClick={() => beginAllocationEdit(allocation)}>Edit event</button>
                <button type="button" disabled={busy} onClick={() => void run(async () => { await deleteCalendarAllocation(allocation); })}>Delete event</button>
                {allocation.roadmap_item_id ? <a href={`/development/roadmap/timeline?roadmap_item_id=${encodeURIComponent(allocation.roadmap_item_id)}`}>Open roadmap item</a> : null}
              </div>
            </>}
          </article>)}
          {projectedAllocations.length === 0 ? <p>No Calendar allocations in this {calendarView.toLowerCase()} projection.</p> : null}
        </div>
      </> : null}
    </section>
  );
}
