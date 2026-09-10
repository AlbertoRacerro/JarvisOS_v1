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
  const summary = details.locator(":scope > summary").filter({ hasText: /^Technical details$/ });
  if ((await summary.count()) !== 1) throw new Error("Technical details requires exactly one native summary control");
  await summary.waitFor({ state: "visible" });
  await summary.focus();
  if (!(await summary.evaluate((node) => node === document.activeElement))) {
    throw new Error("Technical details summary did not receive keyboard focus");
  }
  const initiallyOpen = await details.evaluate((node) => node.open);
  await summary.press("Enter");
  const afterEnter = await details.evaluate((node) => node.open);
  if (afterEnter === initiallyOpen) throw new Error("Technical details did not toggle with Enter");
  await summary.press("Space");
  const afterSpace = await details.evaluate((node) => node.open);
  if (afterSpace === afterEnter) throw new Error("Technical details did not toggle with Space");
  if (!afterSpace) {
    await summary.press("Enter");
    if (!(await details.evaluate((node) => node.open))) throw new Error("Technical details did not finish open");
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
  const providerSettingsResponsePromise = page.waitForResponse((candidate) => {
    const url = new URL(candidate.url());
    return candidate.request().method() === "GET"
      && url.origin === new URL(baseUrl).origin
      && url.pathname === "/ai/provider-settings";
  });
  const response = await page.goto(`${baseUrl}${route}`, { waitUntil: "networkidle", timeout: 30_000 });
  const providerSettingsResponse = await providerSettingsResponsePromise;
  record("124:http", Boolean(response) && response.status() < 500, `status=${response?.status() ?? "none"}`);
  record("124:provider-settings-http", providerSettingsResponse.ok(), `status=${providerSettingsResponse.status()}`);
  const providerSettings = await providerSettingsResponse.json();
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

  const serverScaleway = Array.isArray(providerSettings?.providers)
    ? providerSettings.providers.find((entry) => entry?.provider_id === "scaleway")
    : null;
  const serverCredential = serverScaleway?.credential;
  record(
    "124:credential-server-shape",
    Boolean(serverCredential)
      && typeof serverCredential.effective_source === "string"
      && typeof serverCredential.persisted_state === "string",
    `server-credential=${JSON.stringify(serverCredential ?? null)}`,
  );

  const credentialCard = page.locator('[data-provider-credential-owner="scaleway"]');
  await credentialCard.getByRole("heading", { name: "Scaleway credential", exact: true }).waitFor({ state: "visible" });
  const credentialSummary = credentialCard.locator(".settings-card__summary");
  await credentialSummary.waitFor({ state: "visible" });
  const credentialSummaryText = (await credentialSummary.innerText()).trim();
  const credentialDetails = credentialCard.locator("details").first();
  await openTechnicalDetails(credentialDetails);
  const effectiveSourceNode = credentialDetails.getByText(/^Effective source code · /);
  const persistedStateNode = credentialDetails.getByText(/^Persisted state code · /);
  await effectiveSourceNode.waitFor({ state: "visible" });
  await persistedStateNode.waitFor({ state: "visible" });
  const effectiveSourceText = await effectiveSourceNode.innerText();
  const persistedStateText = await persistedStateNode.innerText();
  const effectiveSource = effectiveSourceText.replace(/^Effective source code · /, "").trim();
  const persistedState = persistedStateText.replace(/^Persisted state code · /, "").trim();
  const validCredentialCombinations = new Set([
    "environment:absent",
    "environment:usable",
    "environment:corrupted",
    "environment:unavailable",
    "secure_persisted:usable",
    "absent:absent",
    "absent:corrupted",
    "invalid:absent",
    "invalid:usable",
    "invalid:corrupted",
    "invalid:unavailable",
    "unknown:unavailable",
  ]);
  const credentialCombination = `${effectiveSource}:${persistedState}`;
  record(
    "124:credential-canonical-codes",
    validCredentialCombinations.has(credentialCombination)
      && effectiveSource === serverCredential.effective_source
      && persistedState === serverCredential.persisted_state,
    `displayed=${credentialCombination} server=${serverCredential.effective_source}:${serverCredential.persisted_state}`,
  );
  const sourceMeanings = {
    not_required: "No credential required",
    environment: "Environment credential active",
    secure_persisted: "Securely stored credential active",
    invalid: "Environment credential invalid",
    absent: "No effective credential",
    unknown: "Credential availability unknown",
  };
  const persistedMeanings = {
    usable: "Stored credential ready",
    corrupted: "Stored credential damaged",
    unavailable: "Secure credential store unavailable",
    not_supported: "Stored credentials not supported",
    absent: "No stored credential",
  };
  const expectedSourceMeaning = sourceMeanings[effectiveSource] ?? "Credential availability unknown";
  const expectedPersistedMeaning = persistedMeanings[persistedState] ?? "Stored credential state unavailable";
  record(
    "124:credential-human-summary",
    credentialSummaryText.includes(expectedSourceMeaning)
      && credentialSummaryText.includes(expectedPersistedMeaning)
      && !credentialSummaryText.includes("_"),
    `summary=${JSON.stringify(credentialSummaryText)} expected_source=${JSON.stringify(expectedSourceMeaning)} expected_persisted=${JSON.stringify(expectedPersistedMeaning)}`,
  );
  record(
    "124:credential-technical-disclosure",
    true,
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
  const repositoryTruthResponsePromise = page.waitForResponse((candidate) => {
    const url = new URL(candidate.url());
    return candidate.request().method() === "GET"
      && url.origin === new URL(baseUrl).origin
      && url.pathname === "/api/coding/repository/ref"
      && url.searchParams.get("repository") === repository
      && url.searchParams.get("ref") === "master";
  });
  const repositoryResponse = await page.goto(`${baseUrl}${repositoryRoute}`, { waitUntil: "networkidle", timeout: 30_000 });
  const repositoryTruthResponse = await repositoryTruthResponsePromise;
  record("140:repository-http", Boolean(repositoryResponse) && repositoryResponse.status() < 500, `status=${repositoryResponse?.status() ?? "none"}`);
  record("140:repository-truth-http", repositoryTruthResponse.ok(), `status=${repositoryTruthResponse.status()}`);
  const repositoryTruth = await repositoryTruthResponse.json();
  record("140:repository-spa-path", new URL(page.url()).pathname === repositoryRoute, `url=${page.url()}`);
  const repositorySurface = page.getByTestId("coding-repository-surface");
  await repositorySurface.waitFor({ state: "visible" });
  await repositorySurface.getByText("Server-owned 118 repository truth", { exact: true }).waitFor({ state: "visible" });
  await repositorySurface.getByText("Repository browsing is context-neutral. These explicit actions are exact-base 111/123 operations; they do not commit, apply, execute, push, create a PR, merge, or mutate STATUS.", { exact: true }).waitFor({ state: "visible" });
  const repositoryDetails = repositorySurface.locator("details").first();
  await openTechnicalDetails(repositoryDetails);
  const resolvedCommitNode = repositoryDetails.getByText(/^Resolved commit · [0-9a-f]{40}$/);
  await resolvedCommitNode.waitFor({ state: "visible" });
  const resolvedCommitText = await resolvedCommitNode.innerText();
  const displayedResolvedSha = resolvedCommitText.replace(/^Resolved commit · /, "").trim();
  record(
    "140:repository-disclosure",
    typeof repositoryTruth.resolved_sha === "string"
      && /^[0-9a-f]{40}$/.test(repositoryTruth.resolved_sha)
      && displayedResolvedSha === repositoryTruth.resolved_sha,
    `displayed=${displayedResolvedSha} trusted=${repositoryTruth.resolved_sha}`,
  );
  record("140:repository-surface", true, "real Coding Repository workbench renders accepted server-owned 118 and explicit 111/123 authority boundary");
  await assertNoCodingMutationButtons("140:repository");
  await screenshot("repository");

  const runtimeRoute = "/coding/runtime";
  const runtimeTruthResponsePromise = page.waitForResponse((candidate) => {
    const url = new URL(candidate.url());
    return candidate.request().method() === "GET"
      && url.origin === new URL(baseUrl).origin
      && url.pathname === "/api/coding/runtime-truth"
      && url.searchParams.get("repository") === repository
      && url.searchParams.get("target_ref") === "master";
  });
  const runtimeResponse = await page.goto(`${baseUrl}${runtimeRoute}`, { waitUntil: "networkidle", timeout: 30_000 });
  const runtimeTruthResponse = await runtimeTruthResponsePromise;
  record("140:runtime-http", Boolean(runtimeResponse) && runtimeResponse.status() < 500, `status=${runtimeResponse?.status() ?? "none"}`);
  record("140:runtime-truth-http", runtimeTruthResponse.ok(), `status=${runtimeTruthResponse.status()}`);
  const runtimeTruth = await runtimeTruthResponse.json();
  record("140:runtime-spa-path", new URL(page.url()).pathname === runtimeRoute, `url=${page.url()}`);
  const runtimeSurface = page.getByTestId("coding-runtime-surface");
  await runtimeSurface.waitFor({ state: "visible" });
  const semanticSummary = runtimeSurface.locator(".final-fusion__summary-strip").first();
  await semanticSummary.waitFor({ state: "visible" });
  const semanticNodes = {
    Ahead: semanticSummary.getByText(/^Ahead · [0-9]+$/),
    Behind: semanticSummary.getByText(/^Behind · [0-9]+$/),
    "Changed files": semanticSummary.getByText(/^Changed files(?: shown)? · [0-9]+$/),
  };
  const semanticValues = {};
  const semanticTexts = {};
  for (const [label, locator] of Object.entries(semanticNodes)) {
    await locator.waitFor({ state: "visible" });
    const value = (await locator.innerText()).trim();
    semanticTexts[label] = value;
    const match = value.match(/^(?:Ahead|Behind|Changed files(?: shown)?) · ([0-9]+)$/);
    semanticValues[label] = match ? Number(match[1]) : null;
  }
  record(
    "140:runtime-semantic-summary",
    Number.isInteger(semanticValues.Ahead) && Number.isInteger(semanticValues.Behind) && Number.isInteger(semanticValues["Changed files"]),
    `summary=${JSON.stringify(semanticValues)}`,
  );
  const runtimeDetails = runtimeSurface.locator("details").first();
  await openTechnicalDetails(runtimeDetails);
  const localCommitNode = runtimeDetails.getByText(/^Local commit · [0-9a-f]{40}$/);
  await localCommitNode.waitFor({ state: "visible" });
  const localCommitText = await localCommitNode.innerText();
  const displayedLocalSha = localCommitText.replace(/^Local commit · /, "").trim();
  record("140:runtime-exact-local-commit", displayedLocalSha === expectedHead, `displayed=${displayedLocalSha} expected=${expectedHead}`);
  const remoteCommitNode = runtimeDetails.getByText(/^Remote commit · /);
  await remoteCommitNode.waitFor({ state: "visible" });
  const remoteCommitText = await remoteCommitNode.innerText();
  const displayedRemoteSha = remoteCommitText.replace(/^Remote commit · /, "").trim();
  const trustedRemoteSha = runtimeTruth.remote?.resolved_sha;
  record(
    "140:runtime-exact-remote-commit",
    typeof trustedRemoteSha === "string"
      && /^[0-9a-f]{40}$/.test(trustedRemoteSha)
      && displayedRemoteSha === trustedRemoteSha,
    `displayed=${displayedRemoteSha} trusted=${trustedRemoteSha ?? "missing"}`,
  );
  const rawDeltaNode = runtimeDetails.locator("pre").first();
  await rawDeltaNode.waitFor({ state: "visible" });
  const rawDeltaText = await rawDeltaNode.innerText();
  const disclosedDelta = JSON.parse(rawDeltaText);
  const trustedDelta = runtimeTruth.semantic_delta;
  const canonicalRelations = new Set(["ahead", "behind", "diverged", "identical"]);
  const validTrustedDelta = trustedDelta?.status === "available"
    && canonicalRelations.has(trustedDelta.relation)
    && Number.isInteger(trustedDelta.ahead_by)
    && trustedDelta.ahead_by >= 0
    && Number.isInteger(trustedDelta.behind_by)
    && trustedDelta.behind_by >= 0
    && Array.isArray(trustedDelta.files)
    && typeof trustedDelta.partial === "boolean"
    && (trustedDelta.relation !== "ahead" || (trustedDelta.ahead_by > 0 && trustedDelta.behind_by === 0))
    && (trustedDelta.relation !== "behind" || (trustedDelta.ahead_by === 0 && trustedDelta.behind_by > 0))
    && (trustedDelta.relation !== "diverged" || (trustedDelta.ahead_by > 0 && trustedDelta.behind_by > 0))
    && (trustedDelta.relation !== "identical" || (trustedDelta.ahead_by === 0 && trustedDelta.behind_by === 0));
  record("140:runtime-trusted-semantic-delta-schema", validTrustedDelta, `trusted=${JSON.stringify(trustedDelta)}`);
  const expectedChangedFilesLabel = trustedDelta.partial
    ? `Changed files shown · ${trustedDelta.files.length}`
    : `Changed files · ${trustedDelta.files.length}`;
  record(
    "140:runtime-changed-files-partial-label",
    semanticTexts["Changed files"] === expectedChangedFilesLabel,
    `rendered=${JSON.stringify(semanticTexts["Changed files"])} expected=${JSON.stringify(expectedChangedFilesLabel)}`,
  );
  const expectedRelation = trustedDelta.relation.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  const renderedRelationLocator = runtimeSurface.locator(".final-fusion__delta span").first();
  await renderedRelationLocator.waitFor({ state: "visible" });
  const renderedRelation = (await renderedRelationLocator.innerText()).trim();
  record(
    "140:runtime-server-semantic-delta",
    semanticValues.Ahead === trustedDelta.ahead_by
      && semanticValues.Behind === trustedDelta.behind_by
      && semanticValues["Changed files"] === trustedDelta.files.length
      && renderedRelation === expectedRelation
      && JSON.stringify(disclosedDelta) === JSON.stringify(trustedDelta)
      && runtimeTruth.live?.git_sha === displayedLocalSha
      && trustedRemoteSha === displayedRemoteSha,
    `rendered=${JSON.stringify({ relation: renderedRelation, ...semanticValues, remote_sha: displayedRemoteSha })} trusted=${JSON.stringify(trustedDelta)} trusted_remote=${trustedRemoteSha ?? "missing"} disclosed=${JSON.stringify(disclosedDelta)}`,
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
