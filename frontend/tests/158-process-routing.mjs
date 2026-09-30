import assert from "node:assert/strict";
import { addBend, isOrthogonal, offsetSegment, routeStream } from "../src/stages/processRouting.ts";

const start = { at: { x: 0, y: 0 }, side: "right" };
const end = { at: { x: 200, y: 100 }, side: "left" };
const base = routeStream(start, end);
assert.equal(isOrthogonal(base), true);
assert.deepEqual(base[0], start.at);
assert.deepEqual(base.at(-1), end.at);

const moved = offsetSegment(base, 2, 20);
assert.ok(moved?.length);
const edited = routeStream(start, end, moved);
assert.equal(isOrthogonal(edited), true);
assert.notDeepEqual(edited, base);
assert.deepEqual(edited[0], start.at);
assert.deepEqual(edited.at(-1), end.at);

const bend = addBend(base, 2, { x: 100, y: 50 });
assert.ok(bend?.length);
assert.equal(isOrthogonal(routeStream(start, end, bend)), true);
assert.equal(offsetSegment(base, 0, 20), null);

console.log("158 orthogonal route edit acceptance: PASS");
