---
name: browser-automation
description: Browser automation and screenshot capture using Chrome extension (claude-in-chrome) or Playwright scripting
---

# Browser Automation & Screenshot Capture

## When to Use

Trigger when: capturing screenshots of web UIs, automating browser interactions, creating visual documentation for README/docs, testing UI flows.

## Tool Selection

### Chrome Extension (claude-in-chrome MCP)

**Use for:** Interactive exploration, understanding UI flows, one-off screenshots, discovering element structure.

Available tools: `tabs_context_mcp`, `tabs_create_mcp`, `navigate`, `read_page`, `find`, `computer` (screenshot/click/type/scroll), `javascript_tool`, `get_page_text`.

Best when:
- You need to explore a UI to understand its flow before scripting
- One-off screenshots where reproducibility isn't needed
- The user wants to collaborate interactively ("I'll open the tab, you take screenshots")

### Playwright (npm package)

**Use for:** Reproducible screenshot batches, automated multi-step flows, capturing sequences with precise timing.

Install pattern (in the app's directory):
```bash
npm install --save-dev playwright --legacy-peer-deps
npx playwright install chromium
```

Best when:
- Capturing multiple screenshots in a single scripted run
- Flows with timed transitions (auto-advance, animations)
- Screenshots need to be re-capturable after UI changes

**Do NOT use:** html2canvas — it fails with Tailwind CSS v4's `color()` function.

### Two-Phase Approach (recommended for complex flows)

1. **Explore** with Chrome extension — click through, read_page, understand structure
2. **Script** with Playwright — write `.mjs` capture script for deterministic reproduction

---

## React SPA Patterns

### Scrolling

`window.scrollBy()` and `window.scrollTo()` do NOT work in React SPAs. React apps use `overflow-y-auto` on internal containers.

```javascript
// WRONG — does nothing in most React apps
await page.evaluate(() => window.scrollBy(0, 800));

// RIGHT — find the actual scrollable container
await page.evaluate(() => {
  const main = document.querySelector('main');  // or whatever has overflow-y-auto
  if (main) main.scrollTop = main.scrollHeight; // scroll to bottom
});

// Scroll to specific position (e.g., bottom minus offset)
await page.evaluate(() => {
  const el = document.querySelector('main');
  if (el) el.scrollTop = Math.max(0, el.scrollHeight - 400);
});
```

How to find the scroll container: look for `overflow-y-auto`, `overflow-auto`, or `overflow-y-scroll` in the component hierarchy. Common patterns: `<main>`, `<div className="flex-1 overflow-y-auto">`.

### Page Load

Always use `waitUntil: 'networkidle'` for React apps to ensure hydration:
```javascript
await page.goto('http://localhost:5173/route', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000); // extra buffer for animations
```

### Component Timers (auto-advance flows)

React components with `useEffect` + `setTimeout` auto-advance need matching waits:
```javascript
// If component has: setTimeout(() => setStep(1), 800)
// Your script needs:  waitForTimeout at least 800 + buffer
await page.waitForTimeout(1200);
```

Read the component source to find timer values before writing the script.

---

## Selector Patterns (Playwright)

### Buttons by text (preferred for visible text)
```javascript
// Regex — case insensitive, partial match
page.locator('button').filter({ hasText: /stabil/i })
page.locator('button', { hasText: /weiter/ })

// Exact match (fragile, avoid)
page.locator('text=Senden')
```

### Buttons by icon (Lucide icons)
```javascript
// Filter by child icon class
page.locator('button').filter({ has: page.locator('.lucide-mic') })
page.locator('button').filter({ has: page.locator('.lucide-send') })
```

### Avoiding ambiguous selectors
```javascript
// WRONG — matches any element with this text (headers, labels, etc.)
page.locator('text=Problem melden')

// RIGHT — constrain to button elements
page.locator('button').filter({ hasText: /Problem melden/ })
// or target by icon if text is ambiguous
page.locator('button').filter({ has: page.locator('.lucide-mic') })
```

### Safe click pattern
```javascript
const btn = page.locator('button').filter({ hasText: /pattern/i }).first();
if (await btn.isVisible({ timeout: 3000 })) {
  await btn.click();
}
await page.waitForTimeout(500);
```

---

## Playwright Script Template

```javascript
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, '../../docs/images'); // adjust path

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  await page.goto('http://localhost:5173/route', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // ... interactions ...

  await page.screenshot({ path: path.join(outDir, 'screenshot-name.png') });
  console.log('OK: screenshot-name.png');

  await page.close();
  await browser.close();
}

main().catch(console.error);
```

Run with: `node capture-script.mjs`

Requires dev server running: `npm run dev` in another terminal.

---

## Cleanup Checklist

After capturing screenshots:
1. Remove capture script(s) from the project
2. `npm uninstall playwright --legacy-peer-deps`
3. Verify package.json/lock are clean (no playwright residue)
4. If you'll need to recapture later, keep the script in a `scripts/` dir or commit it

Note: Uninstalling playwright removes chromium binaries. Reinstalling requires both `npm install` AND `npx playwright install chromium`.

---

## Known Pitfalls

| Pitfall | Fix |
|---------|-----|
| html2canvas + Tailwind v4 | Don't use html2canvas. Use Playwright. |
| `window.scrollBy` no-op | Find the real scroll container (`overflow-y-auto`) |
| Ambiguous `text=` selectors | Use `button.filter({ hasText: /regex/ })` |
| Auto-advance timers | Read component source for setTimeout values |
| Playwright chromium missing | Run `npx playwright install chromium` after npm install |
| Framer Motion not rendering | It works in headless — just add waitForTimeout for animations |
| React not hydrated | Use `waitUntil: 'networkidle'` + extra timeout |
