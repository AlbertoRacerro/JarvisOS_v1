import { useEffect, useState } from "react";

import { getSystemInfo, type SystemInfoResponse } from "../api/client";

function SystemStatus() {
  const [system, setSystem] = useState<SystemInfoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSystemInfo()
      .then(setSystem)
      .catch((caught: Error) => setError(caught.message));
  }, []);

  return (
    <section className="page">
      <div className="page-header">
        <p className="eyebrow">Local System</p>
        <h2>System Status</h2>
      </div>

      {error && <div className="error-banner">Backend unavailable: {error}</div>}

      <section className="panel">
        <h3>Backend</h3>
        <dl className="details">
          <div>
            <dt>Status</dt>
            <dd>{system?.status ?? "checking"}</dd>
          </div>
          <div>
            <dt>App</dt>
            <dd>{system?.app_name ?? "JarvisOS"}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{system?.environment ?? "local"}</dd>
          </div>
        </dl>
      </section>

      <section className="panel">
        <h3>Storage</h3>
        <dl className="details">
          <div>
            <dt>Data root</dt>
            <dd>{system?.data_root ?? "C:\\JarvisOS"}</dd>
          </div>
          <div>
            <dt>Data root exists</dt>
            <dd>{system ? String(system.data_root_exists) : "checking"}</dd>
          </div>
          <div>
            <dt>Database file</dt>
            <dd>{system?.database.database_file ?? "pending backend response"}</dd>
          </div>
          <div>
            <dt>Database ready</dt>
            <dd>{system ? String(system.database.ready) : "checking"}</dd>
          </div>
          <div>
            <dt>Database initialized</dt>
            <dd>{system ? String(system.database.initialized) : "checking"}</dd>
          </div>
        </dl>
      </section>

      <section className="panel">
        <h3>AI Gateway</h3>
        <dl className="details">
          <div>
            <dt>Provider</dt>
            <dd>{system?.ai.provider ?? "none"}</dd>
          </div>
          <div>
            <dt>Gateway boundary</dt>
            <dd>{system ? String(system.ai.gateway_configured) : "checking"}</dd>
          </div>
          <div>
            <dt>Provider configured</dt>
            <dd>{system ? String(system.ai.provider_configured) : "checking"}</dd>
          </div>
          <div>
            <dt>Provider calls</dt>
            <dd>{system ? String(system.ai.provider_calls_enabled) : "checking"}</dd>
          </div>
          <div>
            <dt>Provider mode</dt>
            <dd>{system?.ai.provider_mode ?? "checking"}</dd>
          </div>
          <div>
            <dt>Scaleway enabled</dt>
            <dd>{system ? String(system.ai.scaleway_enabled) : "checking"}</dd>
          </div>
          <div>
            <dt>Scaleway key</dt>
            <dd>{system ? String(system.ai.scaleway_api_key_configured) : "checking"}</dd>
          </div>
          <div>
            <dt>Scaleway implementation</dt>
            <dd>{system?.ai.scaleway_provider_implementation ?? "stub_no_external_calls"}</dd>
          </div>
          <div>
            <dt>Monthly budget</dt>
            <dd>${system?.ai.monthly_budget_usd ?? 0}</dd>
          </div>
          <div>
            <dt>Spend this month</dt>
            <dd>${system?.ai.spend_month_to_date_usd ?? 0}</dd>
          </div>
          <div>
            <dt>Scaleway smoke tests</dt>
            <dd>{system ? String(system.ai.scaleway_smoke_test_enabled) : "checking"}</dd>
          </div>
          <div>
            <dt>Live smoke tests</dt>
            <dd>{system ? String(system.ai.scaleway_live_smoke_test_enabled) : "checking"}</dd>
          </div>
          <div>
            <dt>Scaleway token cap</dt>
            <dd>{system?.ai.scaleway_monthly_token_cap ?? 0}</dd>
          </div>
          <div>
            <dt>Hard stop cap</dt>
            <dd>{system?.ai.scaleway_hard_stop_token_cap ?? 0}</dd>
          </div>
          <div>
            <dt>Free-tier reference</dt>
            <dd>{system?.ai.scaleway_free_tier_reference_tokens ?? 0}</dd>
          </div>
          <div>
            <dt>Token usage MTD</dt>
            <dd>
              {(system?.ai.scaleway_input_tokens_month_to_date ?? 0) + (system?.ai.scaleway_output_tokens_month_to_date ?? 0)}
            </dd>
          </div>
          <div>
            <dt>Blocking reason</dt>
            <dd>{system?.ai.blocking_reason ?? "none"}</dd>
          </div>
        </dl>
      </section>
    </section>
  );
}

export default SystemStatus;
