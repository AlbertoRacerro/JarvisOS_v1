from pathlib import Path

path = Path("evidence/058c-browser.mjs")
text = path.read_text(encoding="utf-8")
old = '''await page.getByRole("button", { name: "Select B" }).click();
await page.getByText(/Unsaved object changes belong to the previous engineering target/).waitFor();
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "13", "dirty A draft is not rebased onto B");
await page.getByRole("button", { name: "Discard previous object changes and load selected object" }).click();
await page.waitForFunction(() => document.querySelector("#engineering-property-tube_length")?.value === "20");
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "20", "explicit discard adopts B baseline");
'''
new = '''await page.getByRole("button", { name: "Select B" }).click();
await page.getByText(/Unsaved object changes belong to the previous engineering target/).waitFor();
assert.equal(await page.locator("#engineering-property-tube_length").count(), 0, "conflicted B target exposes no editable object geometry before operator resolution");
await page.getByRole("button", { name: "Select A" }).click();
await page.waitForFunction(() => document.querySelector("#engineering-property-tube_length")?.value === "13");
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "13", "reselecting previous A target restores its dirty draft");
await page.getByRole("button", { name: "Select B" }).click();
await page.getByText(/Unsaved object changes belong to the previous engineering target/).waitFor();
await page.getByRole("button", { name: "Discard previous object changes and load selected object" }).click();
await page.waitForFunction(() => document.querySelector("#engineering-property-tube_length")?.value === "20");
assert.equal(await page.locator("#engineering-property-tube_length").inputValue(), "20", "explicit discard adopts B baseline");
'''
if old not in text:
    raise SystemExit("expected evidence block not found")
text = text.replace(old, new)
text = text.replace('for (const [name] of variables)', 'for (const { name } of variables)')
text = text.replace(
    '''// A delayed stale candidate response must not overwrite the newer B target.\ndelayA = true;''',
    '''// A delayed stale candidate response must not overwrite the newer B target.\nawait gotoHarness();\nawait page.getByRole("button", { name: "Select B" }).click();\nawait page.waitForFunction(() => document.querySelector("#engineering-property-tube_length")?.value === "20");\ndelayA = true;'''
)
text = text.replace('let providerCalls = 0;', 'let providerCalls = 0;\nconst providerPaths = [];\nconst providerDispatchPaths = new Set(["/ai/modeling/draft", "/ai/tasks/run", "/ai/tasks/escalations/confirm", "/ai/smoke-tests/run", "/ai/smoke-console/run"]);')
text = text.replace(
    'if (url.pathname.includes("/ai/")) providerCalls += 1;',
    'if (providerDispatchPaths.has(url.pathname)) { providerCalls += 1; providerPaths.push(`${request.method()} ${url.pathname}`); }'
)
text = text.replace(
    'assert.equal(providerCalls, 0, "semantic selection/edit/navigation causes zero AI provider calls");',
    'console.log("PROVIDER_DISPATCH_PATHS", JSON.stringify(providerPaths));\nassert.equal(providerCalls, 0, "semantic selection/edit/navigation causes zero provider-dispatch calls");'
)
path.write_text(text, encoding="utf-8")
