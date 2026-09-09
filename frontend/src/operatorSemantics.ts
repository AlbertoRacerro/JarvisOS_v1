type UnknownRecord = Record<string, unknown>;

function record(value: unknown): UnknownRecord {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value as UnknownRecord : {};
}

function records(value: unknown): UnknownRecord[] {
  return Array.isArray(value) ? value.filter((item): item is UnknownRecord => item !== null && typeof item === "object" && !Array.isArray(item)) : [];
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function runtimeDeltaSummary(value: UnknownRecord) {
  const files = records(value.files).map((file) => ({
    name: String(file.filename ?? file.path ?? "Unnamed file"),
    status: typeof file.status === "string" ? file.status : null
  }));
  return {
    relation: typeof value.relation === "string" ? value.relation : "unknown",
    aheadBy: finiteNumber(value.ahead_by),
    behindBy: finiteNumber(value.behind_by),
    files,
    status: typeof value.status === "string" ? value.status : "unavailable",
    partial: value.partial === true
  };
}

export function pullRequestEvidenceSummary(value: UnknownRecord) {
  const pr = record(value.pr);
  const checks = records(record(value.checks).check_runs);
  const reviews = records(record(value.reviews).reviews);
  const checkCount = (predicate: (item: UnknownRecord) => boolean) => checks.filter(predicate).length;
  const reviewCount = (predicate: (item: UnknownRecord) => boolean) => reviews.filter(predicate).length;
  return {
    title: typeof pr.title === "string" && pr.title.trim() ? pr.title : `Pull request ${String(pr.number ?? "")}`.trim(),
    state: pr.merged === true ? "merged" : typeof pr.state === "string" ? pr.state : "unknown",
    checks: {
      total: checks.length,
      passing: checkCount((item) => item.conclusion === "success" && item.stale !== true),
      failing: checkCount((item) => typeof item.conclusion === "string" && !["success", "neutral", "skipped"].includes(item.conclusion) && item.stale !== true),
      pending: checkCount((item) => item.status !== "completed" && item.stale !== true),
      stale: checkCount((item) => item.stale === true)
    },
    reviews: {
      total: reviews.length,
      approved: reviewCount((item) => String(item.state).toUpperCase() === "APPROVED" && item.stale !== true),
      blocking: reviewCount((item) => String(item.state).toUpperCase() === "CHANGES_REQUESTED" && item.stale !== true),
      stale: reviewCount((item) => item.stale === true)
    }
  };
}

export function providerLocation(requiresNetwork: boolean, executionClass: string): string {
  if (requiresNetwork || executionClass === "external_provider") return "Uses a network service";
  if (executionClass === "synthetic") return "Runs without an external service";
  return "Runs locally";
}

export function savedPaidAiSummary(paidAiEnabled: boolean, monthlyBudgetUsd: number): string {
  return paidAiEnabled
    ? `Paid AI is enabled within the saved $${monthlyBudgetUsd} monthly limit.`
    : "Paid AI is disabled in saved settings; no paid external request is permitted.";
}

export function credentialMeaning(effectiveSource: string, persistedState: string): string {
  if (effectiveSource === "not_required") return "No credential is required.";
  if (effectiveSource === "environment") return "An environment credential is active.";
  if (effectiveSource === "secure_persisted") return persistedState === "usable"
    ? "A securely stored credential is ready to use."
    : "A securely stored credential exists but is not usable.";
  if (effectiveSource === "invalid") return "The available environment credential is invalid.";
  if (persistedState === "corrupted") return "The stored credential is damaged and cannot be used.";
  if (persistedState === "unavailable") return "The secure credential store cannot currently be reached.";
  if (persistedState === "not_supported") return "This provider does not support stored credentials.";
  if (persistedState === "absent" || effectiveSource === "absent") return "No credential is configured.";
  return "Credential availability could not be determined.";
}
