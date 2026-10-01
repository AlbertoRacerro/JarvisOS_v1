import assert from "node:assert/strict";
import fs from "node:fs";
import { actionStatePresentation, buildSurfaceRef, isToolCallShaped } from "../src/components/ai/workspaceActionPresentation.ts";

const process = buildSurfaceRef("design-process", null, {
  draft_id: "draft-1",
  process_selection: [{ kind: "stream", id: "stream-1", tag: "feed" }]
});
assert.deepEqual(process, {
  route_id: "design-process", draft_id: "draft-1",
  process_selection: [{ kind: "stream", id: "stream-1", tag: "feed" }]
});

const bluecadPart = {
  kind: "bluecad-part", workspaceId: "ws", candidateId: "candidate-1", artifactId: "a",
  viewerSessionId: "v", ephemeralObjectId: "mesh", meshKey: "m", semanticKey: "s", partId: "part-1"
};
assert.deepEqual(buildSurfaceRef("design-bluecad", bluecadPart, { draft_id: null, process_selection: [] }), {
  route_id: "design-bluecad", candidate_id: "candidate-1", bluecad_part_ids: ["part-1"]
});
assert.deepEqual(buildSurfaceRef("design-bluecad", { kind: "geometry-hit", viewerSessionId: "v", ephemeralObjectId: "x" }, { draft_id: null, process_selection: [] }), {
  route_id: "design-bluecad", candidate_id: null, bluecad_part_ids: []
});
assert.deepEqual(buildSurfaceRef("dashboard", null, { draft_id: "draft-1", process_selection: [] }), { route_id: "dashboard" });

for (const text of ['{"tool_calls":[{"name":"jarvis_process_act"}]}', '<function=jarvis_process_act>{}', '<|tool_call|>jarvis_bluecad_act', '<|im_start|>tool_call', '<start_function_call>jarvis_bluecad_act', 'jarvis_process_act({"op":"set_value"})', 'mcp__jarvis__jarvis_process_act']) {
  assert.equal(isToolCallShaped(text), true, text);
}
for (const text of ["The selected stream is feed.", "{\"answer\":\"done\"}", null, ""]) assert.equal(isToolCallShaped(text), false, String(text));

assert.deepEqual(actionStatePresentation("applied"), { label: "Applied", tone: "success" });
assert.deepEqual(actionStatePresentation("proposed"), { label: "Proposed", tone: "pending" });
assert.deepEqual(actionStatePresentation("refused"), { label: "Refused", tone: "plain" });
assert.deepEqual(actionStatePresentation("stale"), { label: "Stale", tone: "plain" });
assert.deepEqual(actionStatePresentation("dismissed"), { label: "Dismissed", tone: "muted" });
assert.deepEqual(actionStatePresentation("undone"), { label: "Undone", tone: "muted" });

const sidecar = fs.readFileSync(new URL("../src/components/ai/useJarvisSidecar.tsx", import.meta.url), "utf8");
const threadApi = fs.readFileSync(new URL("../src/api/threads.ts", import.meta.url), "utf8");
const actionApi = fs.readFileSync(new URL("../src/api/workspaceActions.ts", import.meta.url), "utf8");
assert.match(threadApi, /surface_context: options\.surfaceContext/);
assert.match(threadApi, /surface_context: surfaceContext/);
assert.match(sidecar, /getSurfaceBrief\(workspaceId, surfaceContext\)/);
assert.match(sidecar, /<WorkspaceActionCards actions=\{interaction\.actions \?\? \[\]\}/);
assert.match(sidecar, /surfaceBrief\?\.summary/);
assert.match(sidecar, /technicalDetails=\{interaction\.technical_details\}/);
assert.match(actionApi, /`\$\{basePath\(workspaceId\)\}\/brief`/);
assert.match(actionApi, /\/\$\{encodeURIComponent\(actionId\)\}\/apply/);

console.log("166 surface context and action presentation checks passed");
