import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";

import type { AISettings, AIStatus, SystemInfoResponse } from "../api/client";
import {
  SettingsApiError,
  loadAISettings,
  loadAIStatus,
  loadSecretStatus,
  loadSystemInfo,
  removeScalewayCredential,
  replaceScalewayCredential,
  saveAISetting,
  type SettingsSecretStatus
} from "../api/settings";
import InlineNotice from "../components/ui/InlineNotice";
import Surface from "../components/ui/Surface";

type NumericKey =
  | "monthly_api_budget_usd"
  | "scaleway_monthly_token_cap"
  | "scaleway_hard_stop_token_cap"
  | "max_direct_continuations";
type BooleanKey = "paid_ai_enabled" | "scaleway_enabled";
type EditableKey = NumericKey | BooleanKey;
type Draft = Record<NumericKey, string> & Record<BooleanKey, boolean>;

type CanonicalSnapshot = {
  settings: AISettings;
  status: AIStatus;
  secret: SettingsSecretStatus;
  system: SystemInfoResponse;
};

const numericKeys: NumericKey[] = [
  "monthly_api_budget_usd",
  "scaleway_monthly_token_cap",
  "scaleway_hard_stop_token_cap",
  "max_direct_continuations"
];

function draftFrom(settings: AISettings): Draft {
  return {
    monthly_api_budget_usd: String(settings.monthly_api_budget_usd),
    scaleway_monthly_token_cap: String(settings.scaleway_monthly_token_cap),
    scaleway_hard_stop_token_cap: String(settings.scaleway_hard_stop_token_cap),
    max_direct_continuations: String(settings.max_direct_continuations),
    paid_ai_enabled: settings.paid_ai_enabled,
    scaleway_enabled: settings.scaleway_enabled
  };
}

function displayError(caught: unknown, fallback: string): string {
  if (caught instanceof SettingsApiError) {
    return caught.code ? `${caught.message} (${caught.code})` : caught.message;
  }
  return caught instanceof Error ? caught.message : fallback;
}

function Settings() {
  const mounted = useRef(true);
  const generation = useRef(0);
  const deleteTriggerRef = useRef<HTMLButtonElement | null>(null);
  const deleteConfirmRef = useRef<HTMLButtonElement | null>(null);
  const credentialInputRef = useRef<HTMLInputElement | null>(null);

  const [settings, setSettings] = useState<AISettings | null>(null);
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [secret, setSecret] = useState<SettingsSecretStatus | null>(null);
  const [system, setSystem] = useState<SystemInfoResponse | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [loading, setLoading] = useState(true);
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [credentialBusy, setCredentialBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const loadCanonical = useCallback(async (
    preserveDraft = false,
    savedKey?: EditableKey,
    projectFailure = true
  ): Promise<boolean> => {
    const owner = ++generation.current;
    setLoading(true);
    if (projectFailure) setError(null);

    try {
      const [nextSettings, nextStatus, nextSecret, nextSystem] = await Promise.all([
        loadAISettings(),
        loadAIStatus(),
        loadSecretStatus(),
        loadSystemInfo()
      ]);
      if (!mounted.current || owner !== generation.current) return false;

      const snapshot: CanonicalSnapshot = {
        settings: nextSettings,
        status: nextStatus,
        secret: nextSecret,
        system: nextSystem
      };
      setSettings(snapshot.settings);
      setStatus(snapshot.status);
      setSecret(snapshot.secret);
      setSystem(snapshot.system);
      setDraft((current) => {
        const canonicalDraft = draftFrom(snapshot.settings);
        if (!preserveDraft || !current) return canonicalDraft;
        if (!savedKey) return current;
        return { ...current, [savedKey]: canonicalDraft[savedKey] };
      });
      setUncertain(false);
      return true;
    } catch (caught) {
      if (mounted.current && owner === generation.current && projectFailure) {
        setError(displayError(caught, "Settings could not be loaded."));
      }
      return false;
    } finally {
      if (mounted.current && owner === generation.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void loadCanonical();
    return () => {
      mounted.current = false;
      generation.current += 1;
    };
  }, [loadCanonical]);

  useEffect(() => {
    if (confirmDelete) deleteConfirmRef.current?.focus();
  }, [confirmDelete]);

  const refreshAfterMutation = async (savedKey?: EditableKey): Promise<boolean> => {
    const refreshed = await loadCanonical(true, savedKey, false);
    if (!refreshed && mounted.current) {
      setUncertain(true);
      setError("State uncertain — canonical reread failed. Reload before another mutation.");
    }
    return refreshed;
  };

  const save = async (key: EditableKey) => {
    if (!draft || settingsBusy || uncertain) return;

    let value: number | boolean = draft[key];
    if (numericKeys.includes(key as NumericKey)) {
      const raw = draft[key as NumericKey].trim();
      const parsed = Number(raw);
      const valid = raw !== "" && Number.isFinite(parsed) && parsed >= 0
        && (key !== "max_direct_continuations" || (Number.isInteger(parsed) && parsed <= 16));
      if (!valid) {
        setError(key === "max_direct_continuations"
          ? "Direct continuations must be an integer from 0 to 16."
          : "Enter a finite value greater than or equal to zero.");
        return;
      }
      value = parsed;
    }

    setSettingsBusy(true);
    setError(null);
    setMessage(null);
    try {
      await saveAISetting({ [key]: value });
      if (await refreshAfterMutation(key)) {
        setMessage("Saved. Canonical settings reloaded.");
      }
    } catch (caught) {
      const failure = displayError(caught, "Settings write failed.");
      const refreshed = await refreshAfterMutation();
      if (refreshed && mounted.current) {
        setError(`${failure} Canonical state was reloaded; no retry was attempted.`);
      }
    } finally {
      if (mounted.current) setSettingsBusy(false);
    }
  };

  const replaceCredential = async (event: FormEvent) => {
    event.preventDefault();
    if (credentialBusy || uncertain || !apiKey.trim()) return;

    const submitted = apiKey;
    setCredentialBusy(true);
    setError(null);
    setMessage(null);
    try {
      await replaceScalewayCredential(submitted);
      setApiKey("");
      if (await refreshAfterMutation()) {
        setMessage("Credential mutation completed. Canonical secure status reloaded.");
      }
    } catch (caught) {
      setApiKey("");
      const failure = displayError(caught, "Credential write failed.");
      const refreshed = await refreshAfterMutation();
      if (refreshed && mounted.current) {
        setError(`${failure} Canonical credential state was reloaded; no retry was attempted.`);
      }
    } finally {
      submitted.replace(/./g, "");
      if (mounted.current) setCredentialBusy(false);
    }
  };

  const cancelDelete = () => {
    setConfirmDelete(false);
    requestAnimationFrame(() => deleteTriggerRef.current?.focus());
  };

  const removeCredential = async () => {
    if (credentialBusy || uncertain) return;

    setCredentialBusy(true);
    setError(null);
    setMessage(null);
    try {
      await removeScalewayCredential();
      setConfirmDelete(false);
      if (await refreshAfterMutation()) {
        setMessage("Credential deleted. Canonical secure status reloaded.");
        requestAnimationFrame(() => credentialInputRef.current?.focus());
      }
    } catch (caught) {
      const failure = displayError(caught, "Credential delete failed.");
      const refreshed = await refreshAfterMutation();
      if (refreshed && mounted.current) {
        setError(`${failure} Canonical credential state was reloaded; no retry was attempted.`);
      }
    } finally {
      if (mounted.current) setCredentialBusy(false);
    }
  };

  const manuallyReload = async () => {
    setMessage(null);
    if (await loadCanonical(true)) setMessage("Canonical state reloaded.");
  };

  const allMutationsBusy = settingsBusy || credentialBusy || uncertain;

  return (
    <section className="settings-page" aria-labelledby="settings-title">
      <header className="page-header">
        <p className="eyebrow">Operator controls</p>
        <h1 id="settings-title">Settings</h1>
        <p>Budget, provider permission and secure credential controls. Internal routing and diagnostics stay read-only.</p>
      </header>

      {loading && <InlineNotice tone="info">Loading canonical settings.</InlineNotice>}
      {uncertain && (
        <InlineNotice tone="danger">
          State uncertain. Reload canonical state before another mutation. <button onClick={() => void manuallyReload()}>Reload</button>
        </InlineNotice>
      )}
      {error && <InlineNotice tone="danger">{error}</InlineNotice>}
      {message && <InlineNotice tone="success">{message}</InlineNotice>}

      <div className="settings-grid">
        <Surface className="settings-card">
          <h2>AI permission & budget</h2>
          <p className="settings-card__summary">
            External calls: <strong>{status?.external_calls_allowed ? "Allowed" : "Blocked"}</strong>
            {status?.blocking_reason ? ` — ${status.blocking_reason}` : ""}
          </p>
          {draft && (
            <div className="settings-fields">
              <label>
                <span>Monthly API budget <small>USD</small></span>
                <span className="settings-field">
                  <input inputMode="decimal" value={draft.monthly_api_budget_usd} disabled={allMutationsBusy} onChange={(event) => setDraft({ ...draft, monthly_api_budget_usd: event.target.value })} />
                  <button disabled={allMutationsBusy} onClick={() => void save("monthly_api_budget_usd")}>Save</button>
                </span>
              </label>
              <label className="settings-toggle">
                <span>Paid AI enabled</span>
                <input type="checkbox" checked={draft.paid_ai_enabled} disabled={allMutationsBusy} onChange={(event) => setDraft({ ...draft, paid_ai_enabled: event.target.checked })} />
                <button disabled={allMutationsBusy} onClick={() => void save("paid_ai_enabled")}>Save</button>
              </label>
              <label className="settings-toggle">
                <span>Scaleway enabled</span>
                <input type="checkbox" checked={draft.scaleway_enabled} disabled={allMutationsBusy} onChange={(event) => setDraft({ ...draft, scaleway_enabled: event.target.checked })} />
                <button disabled={allMutationsBusy} onClick={() => void save("scaleway_enabled")}>Save</button>
              </label>
              <label>
                <span>Monthly token cap</span>
                <span className="settings-field">
                  <input inputMode="numeric" value={draft.scaleway_monthly_token_cap} disabled={allMutationsBusy} onChange={(event) => setDraft({ ...draft, scaleway_monthly_token_cap: event.target.value })} />
                  <button disabled={allMutationsBusy} onClick={() => void save("scaleway_monthly_token_cap")}>Save</button>
                </span>
              </label>
              <label>
                <span>Hard-stop token cap</span>
                <span className="settings-field">
                  <input inputMode="numeric" value={draft.scaleway_hard_stop_token_cap} disabled={allMutationsBusy} onChange={(event) => setDraft({ ...draft, scaleway_hard_stop_token_cap: event.target.value })} />
                  <button disabled={allMutationsBusy} onClick={() => void save("scaleway_hard_stop_token_cap")}>Save</button>
                </span>
              </label>
              <label>
                <span>Direct continuations <small>0–16</small></span>
                <span className="settings-field">
                  <input inputMode="numeric" value={draft.max_direct_continuations} disabled={allMutationsBusy} onChange={(event) => setDraft({ ...draft, max_direct_continuations: event.target.value })} />
                  <button disabled={allMutationsBusy} onClick={() => void save("max_direct_continuations")}>Save</button>
                </span>
              </label>
            </div>
          )}
        </Surface>

        <Surface className="settings-card">
          <h2>Scaleway credential</h2>
          <dl className="settings-facts">
            <div><dt>Effective source</dt><dd>{secret?.effective_source ?? "checking"}</dd></div>
            <div><dt>Persisted state</dt><dd>{secret?.persisted_state ?? "checking"}</dd></div>
            <div><dt>Storage mode</dt><dd>{secret?.storage_mode ?? "checking"}</dd></div>
          </dl>
          <form className="settings-secret" onSubmit={replaceCredential}>
            <label>
              Replace API key
              <input ref={credentialInputRef} type="password" autoComplete="new-password" value={apiKey} disabled={allMutationsBusy || secret?.effective_source === "environment"} onChange={(event) => setApiKey(event.target.value)} />
            </label>
            <button disabled={allMutationsBusy || !apiKey.trim() || secret?.effective_source === "environment"}>Store securely</button>
          </form>
          {secret?.effective_source === "environment" && (
            <p className="settings-muted">Environment credentials override persisted credentials and cannot be replaced here.</p>
          )}
          {!confirmDelete ? (
            <button ref={deleteTriggerRef} className="button-secondary" disabled={allMutationsBusy || !secret?.key_present} onClick={() => setConfirmDelete(true)}>
              Delete persisted credential
            </button>
          ) : (
            <div className="settings-confirm" role="group" aria-label="Confirm credential deletion" onKeyDown={(event) => { if (event.key === "Escape") cancelDelete(); }}>
              <span>Delete the persisted credential?</span>
              <button ref={deleteConfirmRef} disabled={allMutationsBusy} onClick={() => void removeCredential()}>Delete</button>
              <button className="button-secondary" disabled={credentialBusy} onClick={cancelDelete}>Cancel</button>
            </div>
          )}
        </Surface>

        <Surface className="settings-card">
          <h2>Current usage</h2>
          <dl className="settings-facts">
            <div><dt>Spend this month</dt><dd>${status?.spend_month_to_date_usd ?? 0}</dd></div>
            <div><dt>Token usage</dt><dd>{status?.usage_total_tokens ?? 0}</dd></div>
            <div><dt>Budget status</dt><dd>{status?.budget_status ?? "checking"}</dd></div>
            <div><dt>Provider</dt><dd>{status?.provider_id ?? "checking"}</dd></div>
          </dl>
        </Surface>

        <Surface className="settings-card">
          <h2>System</h2>
          <dl className="settings-facts">
            <div><dt>Environment</dt><dd>{system?.environment ?? "checking"}</dd></div>
            <div><dt>Data root</dt><dd>{system ? (system.data_root_exists ? "Available" : "Missing") : "checking"}</dd></div>
            <div><dt>Database</dt><dd>{system ? (system.database.ready ? "Ready" : "Not ready") : "checking"}</dd></div>
            <div><dt>Provider configured</dt><dd>{system ? (system.ai.provider_configured ? "Yes" : "No") : "checking"}</dd></div>
          </dl>
          <details>
            <summary>Advanced diagnostics</summary>
            <p>Policy: {settings?.policy_mode ?? "checking"}</p>
            <p>Provider mode: {status?.provider_mode ?? "checking"}</p>
            <p>Credential reason: {secret?.reason_code ?? "none"}</p>
          </details>
        </Surface>
      </div>

      <nav className="settings-legacy" aria-label="Legacy diagnostics">
        <a href="/legacy/system-status">Legacy System Status</a>
        <a href="/legacy/ai-draft">Legacy AI Draft</a>
      </nav>
    </section>
  );
}

export default Settings;
