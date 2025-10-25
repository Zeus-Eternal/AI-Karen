const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const artifacts = './e2e-artifacts';
  try { fs.rmSync(artifacts, { recursive: true }); } catch {};
  fs.mkdirSync(artifacts, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    recordHar: { path: `${artifacts}/session.har` },
  });

  const page = await context.newPage();
  const logs = [];
  page.on('console', (msg) => logs.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', (err) => logs.push({ type: 'pageerror', text: String(err) }));

  // Navigate to the app to ensure cookies are same-origin
  await page.goto('http://localhost:8010/', { waitUntil: 'networkidle' });

  // Perform login via fetch in browser context so cookie is set by browser
  const payload = { email: 'admin@example.com', password: 'adminadmin' };
  const loginResult = await page.evaluate(async (p) => {
    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(p),
      credentials: 'include'
    });
    const text = await resp.text();
    return { status: resp.status, headers: Array.from(resp.headers.entries()), body: text };
  }, payload);

  // Call validate-session to see whether cookie was sent
  const validate = await page.evaluate(async () => {
    const resp = await fetch('/api/auth/validate-session', { credentials: 'include' });
    const text = await resp.text();
    return { status: resp.status, headers: Array.from(resp.headers.entries()), body: text };
  });

  // Export cookies and logs
  const cookies = await context.cookies();
  fs.writeFileSync(`${artifacts}/cookies.json`, JSON.stringify(cookies, null, 2));
  fs.writeFileSync(`${artifacts}/console.json`, JSON.stringify(logs, null, 2));
  fs.writeFileSync(`${artifacts}/login.json`, JSON.stringify(loginResult, null, 2));
  fs.writeFileSync(`${artifacts}/validate.json`, JSON.stringify(validate, null, 2));

  console.log('Artifacts written to', artifacts);

  await browser.close();
  process.exit(0);
})();
