import {
  MAX_OUTPUT_KEYS,
  MAX_SELECTED_RUNS,
  acceptsWorkspaceResponse,
  compareAnalyticsRuns,
  projectAnalyticsRun,
  retainExistingSelection,
  toggleRunSelection,
  type AnalyticsRun,
} from "./analyticsState";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const envelope = (outputs: Record<string, unknown>) => JSON.stringify({ schema_version: 1, status: "succeeded", outputs, diagnostics: [] });
const run = (id: string, outputs: Record<string, unknown>, patch: Partial<AnalyticsRun> = {}): AnalyticsRun => ({ id, model_version_id: "model-v1", run_label: id, status: "succeeded", output_payload: envelope(outputs), ...patch });
const metric = (value: unknown, unit: unknown) => ({ value, unit });

const valid = projectAnalyticsRun(run("a", { pressure: metric(10, "Pa") }));
assert(valid.state === "ok" && valid.observations.pressure.value === 10, "valid schema-v1 observation was not extracted");
for (const [name, value] of Object.entries({ text: "10", bool: true, nil: null, object: {}, array: [] })) {
  const projected = projectAnalyticsRun(run(name, { pressure: metric(value, "Pa") }));
  assert(projected.state === "ok" && projected.rejectedKeys.pressure, `${name} value was not rejected`);
}
assert(projectAnalyticsRun(run("bad-status", { p: metric(1, "Pa") }, { status: "failed" })).state === "rejected", "non-succeeded run was accepted");
assert(projectAnalyticsRun(run("bad-json", {}, { output_payload: "{" })).state === "rejected", "malformed payload was accepted");
assert(projectAnalyticsRun(run("bad-array", {}, { output_payload: "[]" })).state === "rejected", "array payload was accepted");
assert(projectAnalyticsRun(run("wrong-schema", {}, { output_payload: JSON.stringify({ schema_version: 2, status: "succeeded", outputs: {} }) })).state === "rejected", "wrong schema was accepted");
assert(projectAnalyticsRun(run("blank-unit", { p: metric(1, " ") })).rejectedKeys.p, "blank unit was accepted");
assert(projectAnalyticsRun(run("oversized-key", { ["x".repeat(161)]: metric(1, "Pa") })).state === "rejected", "oversized key did not fail closed");
const tooMany = Object.fromEntries(Array.from({ length: MAX_OUTPUT_KEYS + 1 }, (_, index) => [`k${index}`, metric(index, "Pa")]));
assert(projectAnalyticsRun(run("many", tooMany)).state === "rejected", "output-key cap was not enforced");

const same = compareAnalyticsRuns([run("a", { p: metric(10, "Pa") }), run("b", { p: metric(14, "Pa") })]);
const sameGroup = same.groups[0];
assert(same.state === "ready" && sameGroup?.state === "valid" && sameGroup.min === 10 && sameGroup.max === 14 && sameGroup.range === 4, "same metric/unit comparison failed");
assert(compareAnalyticsRuns([run("a", { p: metric(10, "Pa") }), run("b", { p: metric(14, "Pa") }, { model_version_id: "model-v2" })]).state === "rejected", "mixed model versions were accepted");
const unitMismatch = compareAnalyticsRuns([run("a", { p: metric(10, "Pa") }), run("b", { p: metric(0.014, "kPa") })]);
assert(unitMismatch.groups[0]?.state === "rejected", "Pa/kPa mismatch was converted or accepted");
const differentKeys = compareAnalyticsRuns([run("a", { p: metric(10, "Pa") }), run("b", { q: metric(10, "Pa") })]);
assert(differentKeys.groups.every((group) => group.state === "rejected"), "same-unit different metrics were grouped");
const missingMetric = compareAnalyticsRuns([run("a", { p: metric(10, "Pa") }), run("b", { p: metric("bad", "Pa") })]);
assert(missingMetric.groups[0]?.state === "rejected", "invalid/missing selected metric was silently dropped");

let selected: string[] = [];
for (let index = 0; index < MAX_SELECTED_RUNS; index += 1) selected = toggleRunSelection(selected, `r${index}`);
assert(toggleRunSelection(selected, "overflow").length === MAX_SELECTED_RUNS, "six-run cap was not enforced");
assert(toggleRunSelection(selected, "r0").length === MAX_SELECTED_RUNS - 1, "selected run could not be removed");
assert(retainExistingSelection(["a", "gone", "b"], [run("a", {}), run("b", {})]).join(",") === "a,b", "disappeared run was not removed");
assert(!acceptsWorkspaceResponse({ generation: 1, identity: "A" }, 3, "A"), "stale A-B-A response accepted");
assert(acceptsWorkspaceResponse({ generation: 3, identity: "A" }, 3, "A"), "current workspace response rejected");

console.log("analytics state harness passed");
