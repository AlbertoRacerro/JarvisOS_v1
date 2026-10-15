import { useCallback, useEffect, useState } from "react";
import { patchDraft, type DraftProjection, type DraftOp } from "../../api/processDraft";
import { contentOf, type LinkInfo } from "./dynamicLogic";
import { failureText, listDraftLinks, listEnvProfiles, listRunLinks, type EnvProfile } from "./dynamicApi";
import { type OnPatch } from "./fields";
import { Refusal, SimulationNotice } from "./SimulationNotice";
import ScenarioEditor from "./ScenarioEditor";
import ScheduleEditor from "./ScheduleEditor";
import ControllerEditor from "./ControllerEditor";
import RunsPanel, { useDynamicRuns } from "./RunsPanel";
import Comparison from "./Comparison";
import "./DynamicPanel.css";

export default function DynamicPanel({ workspaceId, draft, onUpdated }: { workspaceId: string; draft: DraftProjection; onUpdated(next: DraftProjection): void }) {
  const [profiles, setProfiles] = useState<EnvProfile[]>([]);
  const [links, setLinks] = useState<LinkInfo[]>([]);
  const [runLinks, setRunLinks] = useState<Record<string, LinkInfo>>({});
  const [problem, setProblem] = useState<{ code: string | null; message: string } | null>(null);
  const [tab, setTab] = useState<"scenario" | "schedule" | "controller" | "runs" | "compare">("scenario");
  const { runs, refresh, problem: runProblem } = useDynamicRuns(workspaceId, draft.draft_id, draft.revision);
  const reloadLinks = useCallback(() => { void Promise.all([listDraftLinks(workspaceId, draft.draft_id), listRunLinks(workspaceId, draft.draft_id)])
    .then(([nextLinks, nextRuns]) => { setLinks(nextLinks); setRunLinks(nextRuns); }).catch((cause) => setProblem(failureText(cause))); }, [workspaceId, draft.draft_id]);
  useEffect(() => { void listEnvProfiles(workspaceId).then(setProfiles).catch((cause) => setProblem(failureText(cause))); reloadLinks(); }, [workspaceId, reloadLinks, draft.revision]);
  const onPatch: OnPatch = async (ops) => {
    try {
      const next = await patchDraft(workspaceId, draft.draft_id, draft.revision, ops as DraftOp[]);
      onUpdated(next); reloadLinks(); return { ok: true, seq: next.seq };
    } catch (cause) { return { ok: false, ...failureText(cause) }; }
  };
  const content = contentOf(draft.dynamic as Parameters<typeof contentOf>[0]);
  const tabs = [["scenario", "Scenarios"], ["schedule", "Schedules"], ["controller", "Controllers"], ["runs", "Runs and results"], ["compare", "Compare"]] as const;
  return <section className="dyn-panel" aria-label="Dynamic Studio"><header><h3>Dynamic Studio</h3><SimulationNotice />
      <p>Create a saved scenario, schedule and controller for the Tier 1 process model. Changes create a draft revision. Start and re-run are explicit.</p></header>
    <div className="dyn-tabs" role="tablist" aria-label="Dynamic Studio sections">{tabs.map(([key, label]) => <button key={key} type="button" role="tab" aria-selected={tab === key} onClick={() => setTab(key)}>{label}</button>)}</div>
    {problem && <Refusal {...problem} />}
    {tab === "scenario" && <ScenarioEditor key={draft.draft_id} draft={draft} content={content} profiles={profiles} onPatch={onPatch} />}
    {tab === "schedule" && <ScheduleEditor key={draft.draft_id} draft={draft} content={content} links={links} onPatch={onPatch} />}
    {tab === "controller" && <ControllerEditor key={draft.draft_id} draft={draft} content={content} onPatch={onPatch} />}
    {tab === "runs" && <RunsPanel workspaceId={workspaceId} draftId={draft.draft_id} headSeq={draft.seq} scenarios={Object.keys(content.scenarios)} runs={runs} refresh={refresh} runLinks={runLinks} problem={runProblem} />}
    {tab === "compare" && <Comparison workspaceId={workspaceId} draftId={draft.draft_id} headSeq={draft.seq} runs={runs} />}
  </section>;
}
