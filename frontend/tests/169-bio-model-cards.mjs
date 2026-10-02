import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const editor = read("src/stages/ProcessDraftEditor.tsx");
const panel = read("src/components/process/BiologyModelLibrary.tsx");
const api = read("src/api/bioModels.ts");
const css = read("src/components/process/BiologyModelLibrary.css");
const fail = (message) => { throw new Error(`169 biology model card acceptance failed: ${message}`); };
const has = (text, fragment, message) => { if (!text.includes(fragment)) fail(message); };

has(editor, "Biology models…", "Biology model library must open from the Process draft toolbar");
has(panel, "data-testid=\"biology-model-library\"", "library panel must be testable in the operator UI");
has(panel, "allowedMathTags", "equations must use a typed allowlisted MathML tree");
if (/dangerouslySetInnerHTML|innerHTML\s*=/.test(panel)) fail("MathML must never use raw HTML insertion");
has(panel, "operator assumption", "values without basis refs must be labelled as operator assumptions");
has(panel, "source_changed_since_verification", "stale source verification state must be visible");
has(panel, "Verify", "parameter rows must expose explicit verification");
has(panel, "Review", "parameter rows must expose explicit expert review");
has(panel, "Duplicate set", "parameter sets must be duplicable");
has(panel, "Revision history", "parameter set history must be visible");
has(panel, "Evaluation preview", "model evaluation must show the factor breakdown");
has(api, "expected_revision: set.revision", "writes must send the CAS revision");
has(api, "expected_digest: set.digest", "writes must send the canonical digest");
has(panel, "error.status === 409", "a CAS conflict must reload current data");
has(css, "@media (max-width: 900px)", "library must adapt for narrow layouts");
has(css, ":focus-visible", "interactive controls must have a visible keyboard focus state");

console.log("169 biology model cards deterministic acceptance: PASS");
