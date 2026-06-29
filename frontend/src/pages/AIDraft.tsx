import { type FormEvent, useEffect, useState } from "react";

import {
  createModelingDraft,
  deleteScalewayApiKey,
  getAISettings,
  getAIStatus,
  getScalewaySecretStatus,
  runAITask,
  runAISmokeConsole,
  runAISmokeTests,
  setScalewayApiKey,
  updateAISettings,
  type AISettings,
  type AIStatus,
  type AITaskRunResponse,
  type ModelingDraftResponse,
  type ScalewaySecretStatus,
  type SmokeConsoleResponse,
  type SmokeTestResponse
} from "../api/client";

function AIDraft() {
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [draft, setDraft] = useState<ModelingDraftResponse | null>(null);
  const [smokeResults, setSmokeResults] = useState<SmokeTestResponse | null>(null);
  const [scalewaySecretStatus, setScalewaySecretStatus] = useState<ScalewaySecretStatus | null>(null);
  const [smokeRunning, setSmokeRunning] = useState(false);
  const [smokeConsolePrompt, setSmokeConsolePrompt] = useState("ciao");
  const [smokeConsoleResult, setSmokeConsoleResult] = useState<SmokeConsoleResponse | null>(null);
  const [smokeConsoleRunning, setSmokeConsoleRunning] = useState(false);
  const [taskPrompt, setTaskPrompt] = useState("");
  const [taskRouteClass, setTaskRouteClass] = useState("local:fake");
  const [taskMaxTokens, setTaskMaxTokens] = useState("64");
  const [taskResult, setTaskResult] = useState<AITaskRunResponse | null>(null);
  const [taskRunning, setTaskRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = () =>
    Promise.all([
      getAISettings().then(setSettings),
      getAIStatus().then(setStatus),
      getScalewaySecretStatus().then(setScalewaySecretStatus)
    ]);

  useEffect(() => {
    refresh().catch((error: Error) => setMessage(error.message));
  }, []);

  const onSettingsSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    updateAISettings({
      monthly_api_budget_usd: Number(form.get("monthly_api_budget_usd") ?? 0),
      paid_ai_enabled: form.get("paid_ai_enabled") === "on",
      provider_mode: String(form.get("provider_mode") ?? "fake"),
      scaleway_enabled: form.get("scaleway_enabled") === "on",
      scaleway_smoke_test_enabled: form.get("scaleway_smoke_test_enabled") === "on",
      scaleway_live_smoke_test_enabled: form.get("scaleway_live_smoke_test_enabled") === "on",
      scaleway_monthly_token_cap: Number(form.get("scaleway_monthly_token_cap") ?? 500000),
      scaleway_hard_stop_token_cap: Number(form.get("scaleway_hard_stop_token_cap") ?? 800000),
      use_fake_provider_when_budget_zero: form.get("use_fake_provider_when_budget_zero") === "on"
    })
      .then(() => refresh())
      .catch((error: Error) => setMessage(error.message));
  };

  const onSmokeTestRun = (smokeMode: "synthetic" | "live") => {
    setSmokeRunning(true);
    setSmokeResults(null);
    runAISmokeTests({
      provider_mode: smokeMode === "live" ? "scaleway" : settings?.provider_mode ?? "fake",
      smoke_mode: smokeMode
    })
      .then(setSmokeResults)
      .then(() => refresh())
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setSmokeRunning(false));
  };

  const onScalewayKeySave = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const apiKey = String(formData.get("api_key") ?? "");
    setScalewayApiKey(apiKey)
      .then(setScalewaySecretStatus)
      .then(() => {
        form.reset();
        setMessage("Scaleway API key saved for this backend session.");
      })
      .then(() => refresh())
      .catch((error: Error) => setMessage(error.message));
  };

  const onScalewayKeyDelete = () => {
    deleteScalewayApiKey()
      .then(setScalewaySecretStatus)
      .then(() => {
        setMessage("App-entered Scaleway API key deleted.");
      })
      .then(() => refresh())
      .catch((error: Error) => setMessage(error.message));
  };

  const onScalewayKeyRefresh = () => {
    getScalewaySecretStatus()
      .then(setScalewaySecretStatus)
      .then(() => refresh())
      .catch((error: Error) => setMessage(error.message));
  };

  const onSmokeConsoleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSmokeConsoleRunning(true);
    setSmokeConsoleResult(null);
    runAISmokeConsole({
      prompt: smokeConsolePrompt,
      max_output_tokens: 80
    })
      .then(setSmokeConsoleResult)
      .then(() => refresh())
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setSmokeConsoleRunning(false));
  };

  const onSmokeConsoleClear = () => {
    setSmokeConsolePrompt("");
    setSmokeConsoleResult(null);
  };

  const onTaskSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const prompt = taskPrompt.trim();
    const parsedMaxTokens = Number(taskMaxTokens);
    const usesExternalRoute = taskRouteClass === "external:cheap";

    if (!prompt || taskRunning) return;
    if (usesExternalRoute && (!Number.isFinite(parsedMaxTokens) || parsedMaxTokens < 1)) {
      setTaskResult(null);
      setMessage("max_tokens must be at least 1 for external:cheap.");
      return;
    }

    setMessage(null);
    setTaskRunning(true);
    setTaskResult(null);
    runAITask({
      prompt,
      route_class: taskRouteClass,
      task_kind: "general",
      max_tokens: Number.isFinite(parsedMaxTokens) && parsedMaxTokens >= 1 ? parsedMaxTokens : undefined
    })
      .then(setTaskResult)
      .then(() => refresh())
      .catch((error: Error) => setMessage(error.message))
      .finally(() => setTaskRunning(false));
  };

  const onDraftSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setDraft(null);
    createModelingDraft({
      workspace_id: String(form.get("workspace_id") ?? "bluerev"),
      informal_model_idea: String(form.get("informal_model_idea") ?? ""),
      model_context: String(form.get("model_context") ?? ""),
      quality_level: String(form.get("quality_level") ?? "draft"),
      provider_mode: String(form.get("provider_mode") ?? settings?.provider_mode ?? "fake")
    })
      .then(setDraft)
      .catch((error: Error) => setMessage(error.message));
  };

  const tokenThreshold = smokeConsoleResult?.token_threshold ?? 500000;
  const currentInputTokens = smokeConsoleResult?.current_month_input_tokens ?? status?.scaleway_input_tokens_month_to_date ?? 0;
  const currentOutputTokens = smokeConsoleResult?.current_month_output_tokens ?? status?.scaleway_output_tokens_month_to_date ?? 0;
  const currentTotalTokens = smokeConsoleResult?.current_month_total_tokens ?? currentInputTokens + currentOutputTokens;
  const tokenThresholdPercent =
    smokeConsoleResult?.token_threshold_percent ?? Number(((currentTotalTokens / tokenThreshold) * 100).toFixed(2));
  const remainingTokens = smokeConsoleResult?.remaining_tokens_to_threshold ?? Math.max(tokenThreshold - currentTotalTokens, 0);
  const configuredMonthlyCap = smokeConsoleResult?.configured_monthly_token_cap ?? status?.scaleway_monthly_token_cap ?? 500000;
  const tokenMeterState =
    currentTotalTokens >= tokenThreshold
      ? "blocked"
      : tokenThresholdPercent >= 80
        ? "danger"
        : tokenThresholdPercent >= 50
          ? "warning"
          : "ok";

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">AI Co-Engineering</p>
        <h2>Modeling Draft</h2>
      </div>

      {message && <div className="error-banner">{message}</div>}

      <section className="panel">
        <h3>AI Cost Guard</h3>
        <dl className="details">
          <div>
            <dt>Provider mode</dt>
            <dd>{status?.active_provider_mode ?? "checking"}</dd>
          </div>
          <div>
            <dt>Policy mode</dt>
            <dd>{status?.policy_mode ?? "FAST_DEV"}</dd>
          </div>
          <div>
            <dt>Provider id</dt>
            <dd>{status?.provider_id ?? "checking"}</dd>
          </div>
          <div>
            <dt>Budget status</dt>
            <dd>{status?.budget_status ?? "checking"}</dd>
          </div>
          <div>
            <dt>Credential status</dt>
            <dd>{status?.credential_status ?? "checking"}</dd>
          </div>
          <div>
            <dt>Monthly budget</dt>
            <dd>${status?.monthly_api_budget_usd ?? 0}</dd>
          </div>
          <div>
            <dt>Spend this month</dt>
            <dd>${status?.spend_month_to_date_usd ?? 0}</dd>
          </div>
          <div>
            <dt>External calls</dt>
            <dd>{status ? String(status.external_calls_allowed) : "checking"}</dd>
          </div>
          <div>
            <dt>Scaleway key</dt>
            <dd>{status ? String(status.scaleway_api_key_configured) : "checking"}</dd>
          </div>
          <div>
            <dt>Scaleway implementation</dt>
            <dd>{status?.scaleway_provider_implementation ?? "stub_no_external_calls"}</dd>
          </div>
          <div>
            <dt>Scaleway enabled</dt>
            <dd>{status ? String(status.scaleway_enabled) : "checking"}</dd>
          </div>
          <div>
            <dt>Smoke test mode</dt>
            <dd>{status ? String(status.scaleway_smoke_test_enabled) : "checking"}</dd>
          </div>
          <div>
            <dt>Live smoke mode</dt>
            <dd>{status ? String(status.scaleway_live_smoke_test_enabled) : "checking"}</dd>
          </div>
          <div>
            <dt>Token cap</dt>
            <dd>{status?.scaleway_monthly_token_cap ?? 500000}</dd>
          </div>
          <div>
            <dt>Hard stop cap</dt>
            <dd>{status?.scaleway_hard_stop_token_cap ?? 800000}</dd>
          </div>
          <div>
            <dt>Free-tier reference</dt>
            <dd>{status?.scaleway_free_tier_reference_tokens ?? 1000000}</dd>
          </div>
          <div>
            <dt>Input tokens MTD</dt>
            <dd>{status?.scaleway_input_tokens_month_to_date ?? 0}</dd>
          </div>
          <div>
            <dt>Output tokens MTD</dt>
            <dd>{status?.scaleway_output_tokens_month_to_date ?? 0}</dd>
          </div>
          <div>
            <dt>Total tokens MTD</dt>
            <dd>{status?.usage_total_tokens ?? 0}</dd>
          </div>
          <div>
            <dt>Blocking reason</dt>
            <dd>{status?.blocking_reason ?? "none"}</dd>
          </div>
        </dl>
      </section>

      <section className="panel">
        <h3>Scaleway API Key</h3>
        <p className="panel-subtitle">
          Paste the key only here. JarvisOS never shows it again, never stores it in AI settings, and this runtime-memory key is forgotten when the backend restarts.
        </p>
        <div className="warning-banner">
          Do not paste API keys into chat, logs, docs, smoke prompts, or model fields. Live Scaleway calls may spend tokens and still require all AI Cost Guard settings.
        </div>
        <dl className="details">
          <div>
            <dt>Key present</dt>
            <dd>{scalewaySecretStatus ? String(scalewaySecretStatus.key_present) : "checking"}</dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>{scalewaySecretStatus?.source ?? "checking"}</dd>
          </div>
          <div>
            <dt>Preview</dt>
            <dd>{scalewaySecretStatus?.masked_preview ?? "none"}</dd>
          </div>
          <div>
            <dt>Storage</dt>
            <dd>{scalewaySecretStatus?.storage_mode ?? "runtime_memory"}</dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>{scalewaySecretStatus?.last_updated_at ?? "not stored by app"}</dd>
          </div>
        </dl>
        <form className="secret-key-form" onSubmit={onScalewayKeySave}>
          <label>
            Scaleway API key
            <input name="api_key" type="password" autoComplete="off" placeholder="Paste key for this backend session" required />
          </label>
          <div className="button-row">
            <button type="submit">Save Key</button>
            <button className="secondary-button" type="button" onClick={onScalewayKeyDelete}>
              Delete Saved Key
            </button>
            <button className="secondary-button" type="button" onClick={onScalewayKeyRefresh}>
              Refresh Status
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <h3>AI Settings</h3>
        <div className="warning-banner">
          Scaleway live mode is only for fixed synthetic smoke tests and the AI Smoke Console. It is disabled by default and requires paid AI, Scaleway mode, live smoke mode, an API key, privacy approval, and token-cap approval.
        </div>
        <form className="settings-form" onSubmit={onSettingsSubmit}>
          <label>
            Monthly budget USD
            <input name="monthly_api_budget_usd" type="number" min="0" step="1" defaultValue={settings?.monthly_api_budget_usd ?? 0} />
          </label>
          <label>
            Provider mode
            <select name="provider_mode" defaultValue={settings?.provider_mode ?? "fake"}>
              <option value="fake">fake</option>
              <option value="scaleway">scaleway</option>
            </select>
          </label>
          <label>
            Scaleway monthly token cap
            <input name="scaleway_monthly_token_cap" type="number" min="0" defaultValue={settings?.scaleway_monthly_token_cap ?? 500000} />
          </label>
          <label>
            Scaleway hard stop cap
            <input name="scaleway_hard_stop_token_cap" type="number" min="0" defaultValue={settings?.scaleway_hard_stop_token_cap ?? 800000} />
          </label>
          <label className="checkbox-line">
            <input name="paid_ai_enabled" type="checkbox" defaultChecked={settings?.paid_ai_enabled ?? false} />
            Enable paid AI
          </label>
          <label className="checkbox-line">
            <input name="scaleway_enabled" type="checkbox" defaultChecked={settings?.scaleway_enabled ?? false} />
            Enable Scaleway mode
          </label>
          <label className="checkbox-line">
            <input name="scaleway_smoke_test_enabled" type="checkbox" defaultChecked={settings?.scaleway_smoke_test_enabled ?? false} />
            Enable Scaleway smoke tests
          </label>
          <label className="checkbox-line">
            <input name="scaleway_live_smoke_test_enabled" type="checkbox" defaultChecked={settings?.scaleway_live_smoke_test_enabled ?? false} />
            Enable live Scaleway smoke call
          </label>
          <label className="checkbox-line">
            <input name="use_fake_provider_when_budget_zero" type="checkbox" defaultChecked={settings?.use_fake_provider_when_budget_zero ?? true} />
            Use fake provider when budget blocks real mode
          </label>
          <button type="submit">Update Settings</button>
        </form>
      </section>

      <section className="panel">
        <h3>Synthetic Smoke Tests</h3>
        <div className="warning-banner">
          Synthetic mode never calls Scaleway. Live mode calls Scaleway only when paid AI, Scaleway mode, live smoke mode, API key, privacy policy, and token cap all pass.
        </div>
        <div className="button-row">
          <button className="secondary-button" type="button" onClick={() => onSmokeTestRun("synthetic")} disabled={smokeRunning}>
            {smokeRunning ? "Running Smoke Tests" : "Run Synthetic Smoke Tests"}
          </button>
          <button className="secondary-button" type="button" onClick={() => onSmokeTestRun("live")} disabled={smokeRunning}>
            Run Live Scaleway Smoke Test
          </button>
        </div>
        {smokeResults && (
          <div className="table-wrap">
            <table className="smoke-table">
              <thead>
                <tr>
                  <th>Case</th>
                  <th>Expected</th>
                  <th>Local</th>
                  <th>Provider</th>
                  <th>Attempted</th>
                  <th>Succeeded</th>
                  <th>Pass</th>
                  <th>Block</th>
                  <th>Tokens</th>
                </tr>
              </thead>
              <tbody>
                {smokeResults.results.map((result) => (
                  <tr key={result.case_id}>
                    <td>{result.case_id}</td>
                    <td>{result.expected_class}</td>
                    <td>{result.local_privacy_class}</td>
                    <td>{result.provider_reported_class ?? result.fake_classification ?? "none"}</td>
                    <td>{String(result.external_call_attempted)}</td>
                    <td>{String(result.external_call_succeeded)}</td>
                    <td>{String(result.passed)}</td>
                    <td>{result.blocking_reason ?? "none"}</td>
                    <td>
                      {result.token_metadata.estimated_input_tokens} in / {result.token_metadata.estimated_output_tokens} out / {result.token_metadata.usage_source}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <pre className="metadata-block">
              {JSON.stringify(
                {
                  provider_mode: smokeResults.provider_mode,
                  smoke_mode: smokeResults.smoke_mode,
                  external_call_attempted: smokeResults.external_call_attempted,
                  external_call_succeeded: smokeResults.external_call_succeeded
                },
                null,
                2
              )}
            </pre>
          </div>
        )}
      </section>

      <section className="panel">
        <h3>AI Smoke Console</h3>
        <p className="panel-subtitle">
          For short public/internal provider checks in FAST_DEV. Do not paste API keys, Authorization headers, .env content, private keys, proprietary IP, or private strategy.
        </p>
        <div className="warning-banner">
          This is not general chat. Live calls may spend tokens, all calls go through policy/token/budget gates, and no conversation history is stored.
        </div>
        <form className="smoke-console-form" onSubmit={onSmokeConsoleSubmit}>
          <label>
            Short harmless prompt
            <textarea
              maxLength={500}
              rows={3}
              value={smokeConsolePrompt}
              placeholder="summarize this public batch-growth equation in one sentence"
              onChange={(event) => setSmokeConsolePrompt(event.target.value)}
            />
          </label>
          <div className="button-row">
            <button type="submit" disabled={smokeConsoleRunning || smokeConsolePrompt.trim().length === 0}>
              {smokeConsoleRunning ? "Sending" : "Send"}
            </button>
            <button className="secondary-button" type="button" onClick={onSmokeConsoleClear}>
              Clear
            </button>
          </div>
          <div className="character-count">{smokeConsolePrompt.length}/500 characters - max output 80 tokens</div>
        </form>

        <div className={`token-meter token-meter-${tokenMeterState}`}>
          <div className="token-meter-header">
            <strong>Smoke token counter</strong>
            <span>{tokenThresholdPercent.toFixed(2)}%</span>
          </div>
          <div className="token-meter-track" aria-label="Smoke token threshold usage">
            <div className="token-meter-fill" style={{ width: `${Math.min(tokenThresholdPercent, 100)}%` }} />
          </div>
          <dl className="details token-details">
            <div>
              <dt>Input tokens this month</dt>
              <dd>{currentInputTokens}</dd>
            </div>
            <div>
              <dt>Output tokens this month</dt>
              <dd>{currentOutputTokens}</dd>
            </div>
            <div>
              <dt>Total tokens this month</dt>
              <dd>{currentTotalTokens}</dd>
            </div>
            <div>
              <dt>Smoke threshold</dt>
              <dd>{tokenThreshold}</dd>
            </div>
            <div>
              <dt>Remaining to threshold</dt>
              <dd>{remainingTokens}</dd>
            </div>
            <div>
              <dt>Configured Scaleway cap</dt>
              <dd>{configuredMonthlyCap}</dd>
            </div>
          </dl>
          {tokenMeterState === "warning" && <div className="warning-banner token-banner">Smoke usage is over 50% of the display threshold.</div>}
          {tokenMeterState === "danger" && <div className="warning-banner token-banner">Smoke usage is over 80% of the display threshold.</div>}
          {tokenMeterState === "blocked" && <div className="error-banner token-banner">Smoke usage is at or above the 500,000 token display threshold.</div>}
        </div>

        {smokeConsoleResult && (
          <div className="smoke-console-result">
            {smokeConsoleResult.response_text ? (
              <div className="response-box">{smokeConsoleResult.response_text}</div>
            ) : (
              <div className="error-banner">{smokeConsoleResult.blocked_reason ?? "Smoke console request blocked."}</div>
            )}
            <pre className="metadata-block">
              {JSON.stringify(
                {
                  provider: smokeConsoleResult.provider,
                  model: smokeConsoleResult.model,
                  mode: smokeConsoleResult.mode,
                  privacy_class: smokeConsoleResult.privacy_class,
                  blocked_reason: smokeConsoleResult.blocked_reason,
                  external_call_attempted: smokeConsoleResult.external_call_attempted,
                  external_call_succeeded: smokeConsoleResult.external_call_succeeded,
                  estimated_input_tokens: smokeConsoleResult.estimated_input_tokens,
                  estimated_output_tokens: smokeConsoleResult.estimated_output_tokens,
                  actual_input_tokens: smokeConsoleResult.actual_input_tokens,
                  actual_output_tokens: smokeConsoleResult.actual_output_tokens,
                  usage_source: smokeConsoleResult.usage_source
                },
                null,
                2
              )}
            </pre>
          </div>
        )}
      </section>

      <section className="panel">
        <h3>AI Task</h3>
        <form className="smoke-console-form" onSubmit={onTaskSubmit}>
          <label>
            Prompt
            <textarea
              rows={3}
              value={taskPrompt}
              placeholder="Ask a short public/internal task"
              onChange={(event) => setTaskPrompt(event.target.value)}
            />
          </label>
          <label>
            Route
            <select value={taskRouteClass} onChange={(event) => setTaskRouteClass(event.target.value)}>
              <option value="local:fake">local:fake</option>
              <option value="external:cheap">external:cheap</option>
            </select>
          </label>
          <label>
            Max tokens
            <input
              type="number"
              min="1"
              value={taskMaxTokens}
              required={taskRouteClass === "external:cheap"}
              onChange={(event) => setTaskMaxTokens(event.target.value)}
            />
          </label>
          <div className="button-row">
            <button type="submit" disabled={taskRunning || taskPrompt.trim().length === 0}>
              {taskRunning ? "Running" : "Run Task"}
            </button>
          </div>
        </form>

        {taskResult && (
          <div className="smoke-console-result">
            {taskResult.status === "success" && taskResult.response_text ? (
              <div className="response-box">{taskResult.response_text}</div>
            ) : (
              <div className="error-banner">
                {taskResult.blocked_reason ?? taskResult.error_type ?? taskResult.status}
              </div>
            )}
            <pre className="metadata-block">
              {JSON.stringify(
                {
                  ledger_id: taskResult.ledger_id,
                  status: taskResult.status,
                  selected_route_class: taskResult.selected_route_class,
                  provider_id: taskResult.provider_id,
                  model_id: taskResult.model_id,
                  error_type: taskResult.error_type,
                  blocked_reason: taskResult.blocked_reason,
                  decision_reason: taskResult.decision_reason,
                  usage: taskResult.usage
                },
                null,
                2
              )}
            </pre>
          </div>
        )}
      </section>

      <section className="panel">
        <h3>Draft Request</h3>
        <form className="draft-form" onSubmit={onDraftSubmit}>
          <input name="workspace_id" defaultValue="bluerev" placeholder="Workspace ID" required />
          <select name="provider_mode" defaultValue={settings?.provider_mode ?? "fake"}>
            <option value="fake">fake</option>
            <option value="scaleway">scaleway</option>
          </select>
          <input name="quality_level" defaultValue="draft" placeholder="Quality level" />
          <textarea name="informal_model_idea" placeholder="Informal engineering model idea" rows={4} required />
          <textarea name="model_context" placeholder="Optional model context" rows={3} />
          <button type="submit">Create Structured Draft</button>
        </form>
      </section>

      {draft && (
        <section className="panel">
          <h3>Structured Draft</h3>
          {draft.draft ? (
            <div className="draft-result">
              <h4>{draft.draft.model_title_suggestion}</h4>
              <p>{draft.draft.engineering_question}</p>
              <p>{draft.draft.model_scope}</p>
              <DraftList title="Assumptions" items={draft.draft.proposed_assumptions} />
              <DraftList title="Parameters" items={draft.draft.proposed_parameters} />
              <DraftList title="Inputs" items={draft.draft.expected_inputs} />
              <DraftList title="Outputs" items={draft.draft.expected_outputs} />
              <DraftList title="Missing Information" items={draft.draft.missing_information} />
              <DraftList title="Weaknesses" items={draft.draft.model_weaknesses} />
              <p>{draft.draft.suggested_next_step}</p>
            </div>
          ) : (
            <div className="error-banner">{draft.ai_metadata.blocked_reason ?? "AI request blocked."}</div>
          )}
          <pre className="metadata-block">{JSON.stringify(draft.ai_metadata, null, 2)}</pre>
        </section>
      )}
    </section>
  );
}

function DraftList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h4>{title}</h4>
      <ul className="record-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default AIDraft;
