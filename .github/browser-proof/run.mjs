import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { chromium } from "playwright";

const scenario = process.env.PROOF_SCENARIO;
const baseUrl = process.env.PROOF_BASE_URL ?? "http://127.0.0.1:8000";
const artifactDir = process.env.PROOF_ARTIFACT_DIR;
const expectedHead = process.env.PROOF_EXPECTED_HEAD_SHA;
const resolvedHead = process.env.PROOF_RESOLVED_HEAD_SHA;
const checkedOutHead = process.env.PROOF_CHECKED_OUT_HEAD_SHA;
const controllerSha = process.env.PROOF_CONTROLLER_SHA;
const prBaseSha = process.env.PROOF_PR_BASE_SHA;
const repository = process.env.PROOF_REPOSITORY;
const prNumber = process.env.PROOF_PR_NUMBER;
const runId = process.env.GITHUB_RUN_ID ?? "unknown";
const seedScript = process.env.PROOF_SEED_SCRIPT;
const proofPython = process.env.PROOF_PYTHON;
const candidateUser = process.env.PROOF_CANDIDATE_USER;

if (!scenario || !artifactDir || !expectedHead || !resolvedHead || !checkedOutHead || !controllerSha || !prBaseSha || !repository) {
  throw new Error("missing required proof identity environment");
}
if (expectedHead !== resolvedHead || expectedHead !== checkedOutHead) {
  throw new Error("exact-head identity mismatch before browser execution");
}

await mkdir(artifactDir, { recursive: true });
const startedAt = new Date().toISOString();
const assertions = [];
const artifacts = [];
const record = (name, pass, detail) => {
  assertions.push({ name, pass, detail });
  if (!pass) throw new Error(`${name}: ${detail}`);
};

const routes = {
  "113-memory-models": ["/memory/models"],
  "124-settings-ai": ["/settings/ai"],
  "140-coding": ["/coding/repository", "/coding/runtime"],
};
if (!(scenario in routes)) throw new Error(`unsupported proof scenario: ${scenario}`);

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
const page = await context.newPage();
page.on("pageerror", (error) => assertions.push({ name: "pageerror", pass: false, detail: String(error) }));
page.on("console", (message) => {
  if (message.type() === "error") assertions.push({ name: "console-error", pass: false, detail: message.text() });
});

const screenshot = async (name) => {
  const path = join(artifactDir, `${scenario}-${name}.png`);
  await page.screenshot({ path, fullPage: true });
  artifacts.push(path);
};

const openTechnicalDetails = async (details) => {
  if (!(await details.evaluate((node) => node.open))) {
    await details.getByText("Technical details", { exact: true }).click();
  }
};

const assertNoCodingMutationButtons = async (prefix) => {
  const forbidden = /^(commit|apply|execute|push|merge|create pr|create pull request|update|restart)(\b|\s)/i;
  const labels = await page.getByRole("button").allTextContents();
  record(
    `${prefix}:no-direct-mutation-buttons`,
    labels.every((label) => !forbidden.test(label.trim())),
    `button-labels=${JSON.stringify(labels)}`,
  );
};

const prove113 = async () => {
  const route = "/memory/models";
  const response = await page.goto(`${baseUrl}${route}`, { waitUntil: "networkidle", timeout: 30_000 });
  record("113:http", Boolean(response) && response.status() < 500, `status=${response?.status() ?? "none"}`);
  record("113:spa-path", new URL(page.url()).pathname === route, `url=${page.url()}`);
  await page.getByText("No model versions", { exact: true }).waitFor({ state: "visible" });
  record("113:empty-state", true, "workspace-only seed renders explicit no-model-version state");
  await screenshot("empty");

  if (!seedScript || !proofPython || !candidateUser) throw new Error("113 proof requires bounded unprivileged seed identity");
  const seedEnv = [
    "GITHUB_TOKEN=",
    "GH_TOKEN=",
    `JARVISOS_DATA_ROOT=${process.env.JARVISOS_DATA_ROOT ?? ""}`,
    `PYTHONPATH=${process.env.PYTHONPATH ?? ""}`,
  ];
  const seeded = spawnSync("sudo", ["-u", candidateUser, "-H", "env", ...seedEnv, proofPython, seedScript, "versions"], {
    encoding: "utf8",
  });
  record("113:trusted-version-seed", seeded.status === 0, seeded.stderr || seeded.stdout || `status=${seeded.status}`);

  await page.reload({ waitUntil: "networkidle", timeout: 30_000 });
  const versionA = page.getByRole("button", { name: /Version A exact/ });
  const versionB = page.getByRole("button", { name: /Version B exact/ });
  await versionA.waitFor({ state: "visible" });
  await versionB.waitFor({ state: "visible" });
  record("113:two-exact-versions", (await versionA.count()) === 1 && (await versionB.count()) === 1, "two human-labelled exact version choices are distinguishable");

  const dossier = page.getByRole("region", { name: "Version dossier" });
  await versionA.click();
  record("113:select-a", await versionA.getAttribute("aria-pressed") === "true", "Version A remains the selected exact dossier");
  await openTechnicalDetails(dossier.locator("details").first());
  await dossier.getByText("proof-version-a", { exact: true }).waitFor({ state: "visible" });
  record("113:select-a-exact-identity", true, "Version A exact identity is available through the real Technical details disclosure");

  await versionB.click();
  record("113:select-b", await versionB.getAttribute("aria-pressed") === "true", "Version B remains the selected exact dossier");
  record("113:a-deselected", await versionA.getAttribute("aria-pressed") === "false", "Version A is no longer the selected dossier");
  await openTechnicalDetails(dossier.locator("details").first());
  await dossier.getByText("proof-version-b", { exact: true }).waitFor({ state: "visible" });
  record("113:select-b-exact-identity", true, "Version B exact identity is available through the real Technical details disclosure");

  const body = (await page.locator("body").innerText()).toLowerCase();
  const forbidden = ["edit model", "save model", "approve model", "run model", "provider key", "git push", "filesystem"];
  record("113:no-mutation-affordance", forbidden.every((label) => !body.includes(label)), "dossier surface exposes no accepted forbidden mutation/provider/filesystem/GitHub affordance");
  await screenshot("exact-version-b");
};

const prove124 = async () => {
  const route = "/settings/ai";
  const response = await page.goto(`${baseUrl}${route}`, { waitUntil: "networkidle", timeout: 30_000 });
  record("124:http", Boolean(response) && response.status() < 500, `status=${response?.status() ?? "none"}`);
  record("124:spa-path", new URL(page.url()).pathname === route, `url=${page.url()}`);
  await page.getByRole("heading", { name: "Settings", exact: true }).waitFor({ state: "visible" });
  await page.getByRole("heading", { name: "Provider catalogue", exact: true }).waitFor({ state: "visible" });
  await page.locator("[data-provider-settings-list]").waitFor({ state: "visible" });

  const providerIds = ["fake", "local_ollama", "scaleway", "deepseek", "glm", "kimi"];
  for (const providerId of providerIds) {
    const row = page.locator(`[data-provider-id="${providerId}"]`);
    await row.waitFor({ state: "visible" });
    record(`124:provider:${providerId}`, (await row.count()) === 1, `canonical provider row ${providerId} is rendered once`);
  }

  const credentialCard = page.locator('[data-provider-credential-owner="scaleway"]');
  await credentialCard.getByRole("heading", { name: "Scaleway credential", exact: true }).waitFor({ state: "visible" });
  const credentialSummary = credentialCard.locator(".settings-card__summary");
  await credentialSummary.waitFor({ state: "visible" });
  const credentialSummaryText = (await credentialSummary.innerText()).trim();
  const credentialDetails = credentialCard.locator("details").first();
  await openTechnicalDetails(credentialDetails);
  const effectiveSourceText = await credentialDetails.getByText(/^Effective source code · /).innerText();
  const persistedStateText = await credentialDetails.getByText(/^Persisted state code · /).innerText();
  const effectiveSource = effectiveSourceText.replace(/^Effective source code · /, "").trim();
  const persistedState = persistedStateText.replace(/^Persisted state code · /, "").trim();
  const sourcePrefixes = {
    not_required: "Credential not required",
    environment: "Environment active",
    invalid: "Environment credential invalid",
    unknown: "Credential state unavailable",
    secure_persisted: "Secure persisted",
  };
  const expectedPrefix = sourcePrefixes[effectiveSource]
    ?? (persistedState === "not_supported" ? "Environment credential unavailable" : "No effective credential");
  const canonicalCredentialCodes = [effectiveSource, persistedState].filter(Boolean);
  const primaryContainsRawCode = canonicalCredentialCodes.some((code) =>
    credentialSummaryText.toLowerCase().split(/[^a-z0-9_]+/).includes(code.toLowerCase())
  );
  record(
    "124:credential-human-summary",
    credentialSummaryText.startsWith(expectedPrefix) && !credentialSummaryText.includes("_") && !primaryContainsRawCode,
    `summary=${JSON.stringify(credentialSummaryText)} source=${effectiveSource} persisted=${persistedState}`,
  );
  record(
    "124:credential-technical-disclosure",
    effectiveSource.length > 0 && persistedState.length > 0,
    `effective_source=${effectiveSource} persisted_state=${persistedState}`,
  );
  await page.getByRole("heading", { name: "Current usage", exact: true }).waitFor({ state: "visible" });

  const passwordInput = page.getByLabel("Replace API key");
  record("124:credential-input-empty", (await passwordInput.inputValue()) === "", "credential value is never projected into the browser input");

  const body = await page.locator("body").innerText();
  const secretVocabulary = ["SCALEWAY_API_KEY", "DEEPSEEK_API_KEY", "GLM_API_KEY", "KIMI_API_KEY", "api_key_ref", "base_url"];
  record("124:no-secret-reference-leak", secretVocabulary.every((value) => !body.includes(value)), "provider secret refs/base URLs are absent from rendered settings text");

  const buttons = (await page.getByRole("button").allTextContents()).map((label) => label.trim().toLowerCase());
  const providerExecution = /provider.*(test|smoke|run)|(test|smoke|run).*provider/;
  record("124:no-provider-execution-affordance", buttons.every((label) => !providerExecution.test(label)), `button-labels=${JSON.stringify(buttons)}`);

  const egressStates = await page.locator("[data-provider-egress-state]").evaluateAll((nodes) => nodes.map((node) => node.getAttribute("data-provider-egress-state")));
  record("124:provider-egress-state", egressStates.length === providerIds.length && egressStates.every((value) => value === "allowed" || value === "blocked"), `states=${JSON.stringify(egressStates)}`);
  await screenshot("settings-ai");
};

const prove140 = async () => {
  const repositoryRoute = "/coding/repository";
  const repositoryResponse = await page.goto(`${baseUrl}${repositoryRoute}`, { waitUntil: "networkidle", timeout: 30_000 });
  record("140:repository-http", Boolean(repositoryResponse) && repositoryResponse.status() < 500, `status=${repositoryResponse?.status() ?? "none"}`);
  record("140:repository-spa-path", new URL(page.url()).pathname === repositoryRoute, `url=${page.url()}`);
  const repositorySurface = page.getByTestId("coding-repository-surface");
  await repositorySurface.waitFor({ state: "visible" });
  await repositorySurface.getByText("Server-owned 118 repository truth", { exact: true }).waitFor({ state: "visible" });
  await repositorySurface.getByText("Repository browsing is context-neutral. These explicit actions are exact-base 111/123 operations; they do not commit, apply, execute, push, create a PR, merge, or mutate STATUS.", { exact: true }).waitFor({ state: "visible" });
  const repositoryDetails = repositorySurface.locator("details").first();
  await openTechnicalDetails(repositoryDetails);
  await repositoryDetails.getByText(/^Resolved commit · [0-9a-f]{40}$/).waitFor({ state: "visible" });
  record("140:repository-disclosure", true, "repository machine identity is available through a real Technical details interaction");
  record("140:repository-surface", true, "real Coding Repository workbench renders accepted server-owned 118 and explicit 111/123 authority boundary");
  await assertNoCodingMutationButtons("140:repository");
  await screenshot("repository");

  const runtimeRoute = "/coding/runtime";
  const runtimeResponse = await page.goto(`${baseUrl}${runtimeRoute}`, { waitUntil: "networkidle", timeout: 30_000 });
  record("140:runtime-http", Boolean(runtimeResponse) && runtimeResponse.status() < 500, `status=${runtimeResponse?.status() ?? "none"}`);
  record("140:runtime-spa-path", new URL(page.url()).pathname === runtimeRoute, `url=${page.url()}`);
  const runtimeSurface = page.getByTestId("coding-runtime-surface");
  await runtimeSurface.waitFor({ state: "visible" });
  const semanticSummary = runtimeSurface.locator(".final-fusion__summary-strip").first();
  await semanticSummary.waitFor({ state: "visible" });
  const semanticSpans = await semanticSummary.locator("span").allTextContents();
  const semanticValues = Object.fromEntries(semanticSpans.map((value) => {
    const match = value.trim().match(/^(Ahead|Behind|Changed files) · ([0-9]+)$/);
    return match ? [match[1], Number(match[2])] : [value.trim(), null];
  }));
  record(
    "140:runtime-semantic-summary",
    Number.isInteger(semanticValues.Ahead) && Number.isInteger(semanticValues.Behind) && Number.isInteger(semanticValues["Changed files"]),
    `summary=${JSON.stringify(semanticSpans)}`,
  );
  const runtimeDetails = runtimeSurface.locator("details").first();
  await openTechnicalDetails(runtimeDetails);
  const localCommitText = await runtimeDetails.getByText(/^Local commit · /).innerText();
  const displayedLocalSha = localCommitText.replace(/^Local commit · /, "").trim();
  record("140:runtime-exact-local-commit", displayedLocalSha === expectedHead, `displayed=${displayedLocalSha} expected=${expectedHead}`);
  const rawDeltaText = await runtimeDetails.locator("pre").first().innerText();
  const rawDelta = JSON.parse(rawDeltaText);
  const expectedAhead = Number(rawDelta.ahead_by);
  const expectedBehind = Number(rawDelta.behind_by);
  const expectedChanged = Array.isArray(rawDelta.files) ? rawDelta.files.length : Number.NaN;
  const rawRelation = String(rawDelta.relation ?? "");
  const renderedRelation = (await runtimeSurface.locator(".final-fusion__delta span").first().innerText()).trim();
  const expectedRelation = rawRelation.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  record(
    "140:runtime-server-semantic-delta",
    Number.isInteger(expectedAhead)
      && Number.isInteger(expectedBehind)
      && Number.isInteger(expectedChanged)
      && semanticValues.Ahead === expectedAhead
      && semanticValues.Behind === expectedBehind
      && semanticValues["Changed files"] === expectedChanged
      && rawRelation.length > 0
      && renderedRelation === expectedRelation,
    `rendered=${JSON.stringify({ relation: renderedRelation, ...semanticValues })} raw=${JSON.stringify(rawDelta)}`,
  );
  record("140:runtime-disclosure", true, "runtime exact identity and canonical server-owned semantic delta are verified through a real Technical details interaction");
  await runtimeSurface.getByRole("heading", { name: "Development pipeline", exact: true }).waitFor({ state: "visible" });
  record("140:runtime-surface", true, "real Coding Runtime workbench renders server-owned 119 semantic delta and 120 pipeline projection surface");
  await assertNoCodingMutationButtons("140:runtime");
  await screenshot("runtime");
};

let verdict = "PASS";
let failure = null;
try {
  if (scenario === "113-memory-models") {
    await prove113();
  } else if (scenario === "124-settings-ai") {
    await prove124();
  } else if (scenario === "140-coding") {
    await prove140();
  } else {
    verdict = "REFUSED";
    failure = `${scenario} trusted candidate-specific browser assertions are not ready; no PASS emitted`;
    assertions.push({
      name: `${scenario}:refused-not-ready`,
      pass: true,
      detail: "trusted candidate-specific assertions must exist before this scenario can produce browser-proof PASS",
    });
  }
} catch (error) {
  verdict = "FAIL";
  failure = String(error?.stack ?? error);
} finally {
  const trace = join(artifactDir, `${scenario}-trace.zip`);
  await context.tracing.stop({ path: trace });
  artifacts.push(trace);
  await browser.close();
}

const failedAssertions = assertions.filter((item) => item.pass === false);
if (verdict === "PASS" && failedAssertions.length > 0) {
  verdict = "FAIL";
  failure = failure ?? `browser emitted ${failedAssertions.length} failed asynchronous assertion(s)`;
}

const backendLog = join(artifactDir, "backend.log");
try {
  await readFile(backendLog);
  artifacts.push(backendLog);
} catch (error) {
  if (error?.code !== "ENOENT") throw error;
}

const digests = {};
for (const path of artifacts) {
  const bytes = await readFile(path);
  digests[path.split("/").at(-1)] = createHash("sha256").update(bytes).digest("hex");
}

const seedVersion = scenario === "113-memory-models"
  ? "113-workspace-then-two-exact-versions-v2"
  : scenario === "124-settings-ai"
    ? "124-production-settings-owner-projection-v2"
    : scenario === "140-coding"
      ? "140-production-routes-semantic-disclosures-v2"
      : "not-run-refused-v1";

const manifest = {
  schema: "jarvisos.exact-head-browser-proof.v1",
  repository,
  pr_number: prNumber ? Number(prNumber) : null,
  pr_base_sha: prBaseSha,
  expected_head_sha: expectedHead,
  resolved_pr_head_sha: resolvedHead,
  checked_out_head_sha: checkedOutHead,
  controller_sha: controllerSha,
  workflow_run_id: runId,
  scenario,
  seed_version: seedVersion,
  browser: "chromium",
  playwright_version: "1.55.0",
  started_at: startedAt,
  ended_at: new Date().toISOString(),
  assertions,
  artifacts: digests,
  verdict,
  failure,
};
await writeFile(join(artifactDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

if (verdict !== "PASS" || failedAssertions.length > 0) process.exitCode = 1;