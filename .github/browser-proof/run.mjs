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

const prove113 = async () => {
  const route = "/memory/models";
  const response = await page.goto(`${baseUrl}${route}`, { waitUntil: "networkidle", timeout: 30_000 });
  record("113:http", Boolean(response) && response.status() < 500, `status=${response?.status() ?? "none"}`);
  record("113:spa-path", new URL(page.url()).pathname === route, `url=${page.url()}`);
  await page.getByText("No exact model versions", { exact: true }).waitFor({ state: "visible" });
  record("113:empty-state", true, "workspace-only seed renders explicit no-exact-version state");
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
  record("113:two-exact-versions", (await versionA.count()) === 1 && (await versionB.count()) === 1, "two exact version choices are distinguishable");

  await versionA.click();
  await page.getByText("proof-version-a", { exact: true }).waitFor({ state: "visible" });
  record("113:select-a-exact-identity", await versionA.getAttribute("aria-pressed") === "true", "Version A selection owns exact proof-version-a dossier identity");

  await versionB.click();
  await page.getByText("proof-version-b", { exact: true }).waitFor({ state: "visible" });
  record("113:select-b-exact-identity", await versionB.getAttribute("aria-pressed") === "true", "Version B selection owns exact proof-version-b dossier identity");
  record("113:a-deselected", await versionA.getAttribute("aria-pressed") === "false", "Version A is no longer the selected dossier");

  const body = (await page.locator("body").innerText()).toLowerCase();
  const forbidden = ["edit model", "save model", "approve model", "run model", "provider key", "git push", "filesystem"];
  record("113:no-mutation-affordance", forbidden.every((label) => !body.includes(label)), "dossier surface exposes no accepted forbidden mutation/provider/filesystem/GitHub affordance");
  await screenshot("exact-version-b");
};

let verdict = "PASS";
let failure = null;
try {
  if (scenario === "113-memory-models") {
    await prove113();
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
  seed_version: scenario === "113-memory-models" ? "113-workspace-then-two-exact-versions-v1" : "not-run-refused-v1",
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
