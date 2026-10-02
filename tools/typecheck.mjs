// Measures rendered typography on a phone viewport and flags rule breaks.
// Usage: node tools/typecheck.mjs <base-url>   (e.g. https://landoffire-menu.vercel.app)
import { chromium, devices } from '/home/mpovas/dev/app-factory/app-template/node_modules/playwright/index.mjs';

const base = process.argv[2] || 'https://landoffire-menu.vercel.app';
const pages = base.startsWith('file:') ? ['/index.html', '/magazine.html', '/apie.html'] : ['/', '/magazine', '/apie'];
const b = await chromium.launch();
let fails = 0;
for (const dev of ['iPhone SE', 'iPhone 13']) for (const lang of ['lt', 'ru']) for (const path of pages) {
  const ctx = await b.newContext({ ...devices[dev], locale: lang });  // 375px: the narrow case
  const p = await ctx.newPage();
  await p.addInitScript(l => localStorage.setItem('lof-lang', l), lang);
  await p.goto(base + path, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const r = await p.evaluate(() => {
    const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const [R, G, B] = m.slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return { L: .2126 * R + .7152 * G + .0722 * B, a: m[3] ?? 1 }; };
    const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e).backgroundColor; if (lum(c).a > .9) return c; } return 'rgb(255,255,255)'; };
    const out = { small: [], tight: [], contrast: [], overflow: [], targets: [], sizes: {} };
    const seen = new Set();
    for (const el of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || !el.offsetParent && cs.position !== 'fixed') continue;
      const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (!own) continue;
      const fs = parseFloat(cs.fontSize), lh = cs.lineHeight === 'normal' ? fs * 1.2 : parseFloat(cs.lineHeight);
      const txt = el.textContent.trim().slice(0, 30);
      out.sizes[fs.toFixed(1)] = (out.sizes[fs.toFixed(1)] || 0) + 1;
      if (fs < 12.5 && !seen.has('s' + txt)) { seen.add('s' + txt); out.small.push(`${fs}px "${txt}"`); }
      const rg = document.createRange(); rg.selectNodeContents(el); const lines = new Set([...rg.getClientRects()].map(q => Math.round(q.top))).size;
      if (lines > 1 && lh / fs < 1.08 && !seen.has('t' + txt)) { seen.add('t' + txt); out.tight.push(`${(lh / fs).toFixed(2)} "${txt}"`); }
      const a = lum(cs.color).L, bb = lum(bgOf(el)).L, ratio = (Math.max(a, bb) + .05) / (Math.min(a, bb) + .05);
      const large = fs >= 24 || (fs >= 18.66 && +cs.fontWeight >= 700);
      if (ratio < (large ? 3 : 4.5) && !seen.has('c' + txt)) { seen.add('c' + txt); out.contrast.push(`${ratio.toFixed(2)} "${txt}"`); }
      if (el.scrollWidth > el.clientWidth + 1 && cs.overflowX === 'visible' && !el.closest('nav') && !seen.has('o' + txt)) { seen.add('o' + txt); out.overflow.push(`"${txt}"`); }
    }
    for (const el of document.querySelectorAll('button, a')) {
      const r = el.getBoundingClientRect(); if (!r.width || getComputedStyle(el).visibility === 'hidden' || el.closest('.skip,p,dd,footer')) continue;
      if (r.height < 24 || r.width < 24) out.targets.push(`${Math.round(r.width)}x${Math.round(r.height)} "${el.textContent.trim().slice(0, 20)}"`);
    }
    out.hscroll = document.documentElement.scrollWidth > innerWidth;
    return out;
  });
  const bad = r.small.length + r.tight.length + r.contrast.length + r.overflow.length + r.targets.length + (r.hscroll ? 1 : 0);
  fails += bad;
  console.log(`\n${dev} ${lang} ${path}  issues=${bad}  sizes(px:count)=${Object.entries(r.sizes).sort((x, y) => x[0] - y[0]).map(([k, v]) => k + ':' + v).join(' ')}`);
  for (const k of ['small', 'tight', 'contrast', 'overflow', 'targets']) if (r[k].length) console.log(`  ${k}: ${r[k].slice(0, 8).join(' | ')}${r[k].length > 8 ? ` …+${r[k].length - 8}` : ''}`);
  if (r.hscroll) console.log('  horizontal scroll!');
  await ctx.close();
}
await b.close();
console.log(`\nTOTAL ISSUES ${fails}`);
