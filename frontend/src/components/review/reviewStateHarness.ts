import type { MemoryRecord } from "../../api/memory";
import {
  acceptsReviewMutation,
  acceptsReviewRequest,
  isActionable,
  nextAfterRemoval,
  orderedRecords,
  promotionRoute,
  recordLabel,
  retainedSelection
} from "./reviewState";

const base = (overrides: Partial<MemoryRecord> = {}): MemoryRecord => ({
  id: "id-a",
  record_kind: "parameter",
  workspace_id: "ws-a",
  status: "proposed",
  origin: "ai_proposed",
  source_ai_job_id: null,
  promoted_at: null,
  created_at: "2026-08-15T10:00:00Z",
  updated_at: "2026-08-15T10:00:00Z",
  title: null,
  statement: null,
  decision_text: null,
  name: "Pressure",
  source_ref: null,
  notes: null,
  supersedes_parameter_id: null,
  scope: null,
  confidence: null,
  symbol: "P",
  value: "1",
  unit: "bar",
  value_status: "candidate",
  value_min: null,
  value_max: null,
  rationale: null,
  linked_run_id: null,
  ...overrides
});

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const ordered = orderedRecords([
  base({ id: "z", created_at: "2026-08-15T09:00:00Z" }),
  base({ id: "b", record_kind: "parameter", created_at: "2026-08-15T11:00:00Z" }),
  base({ id: "a", record_kind: "assumption", created_at: "2026-08-15T11:00:00Z" })
]);
assert(ordered.map((record) => record.id).join(",") === "a,b,z", "deterministic newest-first ordering failed");
assert(recordLabel(base({ name: "  " , id: "abcdef123456789" })).startsWith("parameter abcdef123456"), "label fallback failed");

const firstA = { generation: 1, workspaceId: "a", statusFilter: "proposed" as const };
const secondA = { generation: 3, workspaceId: "a", statusFilter: "proposed" as const };
assert(!acceptsReviewRequest(secondA, firstA), "A→B→A stale request accepted");
const firstProposed = { generation: 4, workspaceId: "a", statusFilter: "proposed" as const };
const secondProposed = { generation: 6, workspaceId: "a", statusFilter: "proposed" as const };
assert(!acceptsReviewRequest(secondProposed, firstProposed), "proposed→accepted→proposed stale request accepted");

const firstX = { generation: 1, workspaceId: "a", recordKind: "parameter" as const, recordId: "x" };
const secondX = { generation: 3, workspaceId: "a", recordKind: "parameter" as const, recordId: "x" };
assert(!acceptsReviewMutation(secondX, firstX), "X→Y→X stale mutation accepted");

const records = [base({ id: "a" }), base({ id: "b" }), base({ id: "c" })];
assert(retainedSelection(records, "b") === "b", "selection retention failed");
assert(retainedSelection(records, "missing") === "a", "selection fallback failed");
assert(nextAfterRemoval(records, "b") === "c", "next removal target failed");
assert(nextAfterRemoval(records, "c") === "b", "previous removal fallback failed");
assert(nextAfterRemoval([base({ id: "x" })], "x") === null, "empty removal fallback failed");

assert(promotionRoute(base({ supersedes_parameter_id: "old" })) === "replacement", "replacement route failed");
assert(promotionRoute(base({ record_kind: "assumption", name: null, statement: "Assume X" })) === "generic", "assumption route failed");
assert(promotionRoute(base({ record_kind: "decision", name: null, title: "Choose X" })) === "generic", "decision route failed");
assert(isActionable(base()), "proposed must be actionable");
assert(!isActionable(base({ status: "accepted" })), "accepted must not be actionable");

const unknownContent = base({ notes: "<script>ignored</script>", confidence: "future-value" });
assert(recordLabel(unknownContent) === "Pressure", "unknown additive content affected identity");

console.log("proposal-review-state: OK");
