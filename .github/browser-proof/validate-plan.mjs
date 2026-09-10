import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { loadTrustedPlan } from "./plan-lib.mjs";

const planId = process.argv[2];
if (!planId) throw new Error("usage: node validate-plan.mjs <plan-id>");
const root = dirname(fileURLToPath(import.meta.url));
const plan = await loadTrustedPlan(planId, join(root, "plans"));
process.stdout.write(`${plan.id}\n`);
