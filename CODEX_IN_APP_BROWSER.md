# Codex App In-App Browser Invocation

This note records the repository-local procedure for driving the Codex App in-app browser from this Windows workstation. Use this path when a task explicitly asks for the in-app browser, and do not substitute `mcp__playwright__` browser tools for that request.

## Fixed Browser Client

Use the bundled browser client at this exact versioned path:

```powershell
$browserClient = "$env:USERPROFILE\.codex\plugins\cache\openai-bundled\browser\26.519.22136\scripts\browser-client.mjs"
```

Verify it exists before trying browser work:

```powershell
Test-Path "$env:USERPROFILE\.codex\plugins\cache\openai-bundled\browser\26.519.22136\scripts\browser-client.mjs"
```

## Runtime Setup

Run the browser setup through the Node REPL JavaScript tool, not a shell process and not `mcp__playwright__`.

```js
if (!globalThis.agent) {
  const { setupBrowserRuntime } = await import(
    "C:/Users/keepoux/.codex/plugins/cache/openai-bundled/browser/26.519.22136/scripts/browser-client.mjs"
  );
  await setupBrowserRuntime({ globals: globalThis });
}

if (!globalThis.browser) {
  globalThis.browser = await agent.browsers.get("iab");
}

await browser.nameSession("🔎 ScienceClaw local app");
```

`iab` selects the Codex App in-app browser. If the user wants to see the browser, make it visible:

```js
await (await browser.capabilities.get("visibility")).set(true);
```

## Open ScienceClaw

Create or reuse a tab, then navigate to the local frontend:

```js
if (typeof tab === "undefined") {
  globalThis.tab = await browser.tabs.new();
}

await tab.goto("http://localhost:5173/");
await tab.playwright.waitForLoadState({ state: "load", timeoutMs: 15000 });

console.log(JSON.stringify({
  url: await tab.url(),
  title: await tab.title(),
}));
```

Expected result for the local frontend:

```json
{"url":"http://localhost:5173/","title":"ScienceClaw"}
```

## Important Distinctions

- This workflow uses the Codex App in-app browser through the fixed `browser-client.mjs` path above.
- `tab.playwright` is the in-app browser runtime API after `browser-client.mjs` setup; it is not the external `mcp__playwright__` browser tool.
- Do not claim an in-app browser smoke has passed if the evidence came only from `mcp__playwright__`.
- Keep the browser visible only when the user asks to watch or interact with the page.
