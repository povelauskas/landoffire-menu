#!/usr/bin/env python3
"""Build the static Land of Fire menu site into dist/.

Inputs:  data/menu.json (sections + items, transcribed from the print menu)
         src/hi/p-NN.jpg (200 dpi page renders) for dish photo crops
Outputs: dist/index.html, dist/img/*.webp, icons, manifest, robots, sitemap
"""
import html, json, re, shutil, unicodedata
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
PAGES = ROOT / "src" / "hi"
SITE_URL = "https://landoffire-menu.vercel.app"
LANGS = ("lt", "en", "ru")
UI = {
    "lt": {"menu": "Meniu", "search": "Ieškoti patiekalo", "none": "Nieko nerasta",
           "top": "Į viršų", "lang": "Kalba", "prices": "Kainos nurodytos eurais su PVM."},
    "en": {"menu": "Menu", "search": "Search the menu", "none": "Nothing found",
           "top": "Back to top", "lang": "Language", "prices": "Prices in euros, VAT included."},
    "ru": {"menu": "Меню", "search": "Поиск блюда", "none": "Ничего не найдено",
           "top": "Наверх", "lang": "Язык", "prices": "Цены указаны в евро с НДС."},
}

e = lambda s: html.escape(s or "", quote=True)


def fold(s):
    """Lowercase, accent-free text for search: 'Şah Plov' matches 'sah plov'. Must match fold() in template.html."""
    s = s.lower().replace("ə", "e").replace("ı", "i")
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def slug(s):
    s = unicodedata.normalize("NFKD", s.replace("ə", "e").replace("ı", "i"))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.encode("ascii", "ignore").decode()).strip("-").lower()
    return s or "x"


def crop(page, box, name):
    """Crop a dish photo from a page render; write 480w and 960w WebP. Returns aspect ratio."""
    im = Image.open(PAGES / f"p-{page:02d}.jpg").convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = box
    im = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    for w in (480, 960):
        r = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(DIST / "img" / f"{name}-{w}.webp", "WEBP", quality=78, method=6)
    return im.width, im.height


def make_brand():
    """White logo with alpha cut from the cover, plus icons and a social share image."""
    cover = Image.open(PAGES / "p-01.jpg").convert("RGB")
    W, H = cover.size
    logo = cover.crop((int(.40 * W), int(.04 * H), int(.60 * W), int(.14 * H)))
    a = logo.convert("L").point(lambda v: max(0, min(255, (v - 120) * 2)))
    white = Image.new("RGBA", logo.size, (255, 255, 255, 0))
    white.putalpha(a)
    white.save(DIST / "img" / "logo.png", optimize=True)
    # Icon: flame mark on brand red
    mark = white.crop((int(.30 * white.width), 0, int(.70 * white.width), int(.62 * white.height)))
    for size, fname in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")):
        bg = Image.new("RGBA", (size, size), (163, 18, 28, 255))
        m = mark.copy()
        m.thumbnail((int(size * .72), int(size * .72)), Image.LANCZOS)
        bg.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
        bg.convert("RGB").save(DIST / fname, optimize=True)
    # Hero (table of dishes, bottom half of the cover)
    hero = cover.crop((0, int(.50 * H), W, H))
    for w in (800, 1600):
        hero.resize((w, round(hero.height * w / hero.width)), Image.LANCZOS).save(
            DIST / "img" / f"hero-{w}.webp", "WEBP", quality=75, method=6)
    # Open Graph 1200x630
    og = cover.crop((0, int(.30 * H), W, int(.30 * H) + round(W * 630 / 1200))).resize((1200, 630), Image.LANCZOS)
    og.save(DIST / "img" / "og.jpg", quality=82, optimize=True)


def t(obj, lang):
    """Render a per-language text as three spans; CSS shows the active one."""
    return "".join(f'<span lang="{l}" class="l-{l}">{e(obj.get(l, ""))}</span>' for l in LANGS if obj.get(l))


def money(p):
    return f'{e(str(p).replace(".", ","))}&nbsp;€'


def lbl(x):
    """A label is either plain text or a per-language dict."""
    return t(x, "lt") if isinstance(x, dict) else e(x)


def price_html(it):
    if it.get("sizes"):
        return '<span class="sizes">' + "".join(
            f'<span class="sz"><small>{lbl(s["label"])}</small> {money(s["price"])}</span>' for s in it["sizes"]) + "</span>"
    if not it.get("price"):
        return ""
    unit = f' / {lbl(it["unit"])}' if it.get("unit") else ""
    vol = f'<small>{e(it["volume"])}</small> ' if it.get("volume") else ""
    return f'<span class="price">{vol}{money(it["price"])}{unit}</span>'


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "img").mkdir(parents=True)
    data = json.loads((ROOT / "data" / "menu.json").read_text())
    make_brand()

    nav, body, ld_sections, seen = [], [], [], set()
    for sec in data["sections"]:
        sid = sec["id"]
        nav.append(f'<a href="#{sid}" data-sec="{sid}">{t(sec.get("nav", sec["title"]), "lt")}</a>')
        cards, ld_items, group = [], [], None
        for i, it in enumerate(sec["items"]):
            iid = f"{sid}-{slug(it['name'])}"
            iid += f"-{i}" if iid in seen else ""
            seen.add(iid)
            search = fold(" ".join([it["name"]] + [it.get(l, "") for l in LANGS]))
            desc = {l: it.get(l, "") for l in LANGS}
            img = ""
            if it.get("photo"):
                w, h = crop(it["page"], it["photo"], iid)
                eager = 'fetchpriority="high"' if not body and i == 0 else 'loading="lazy"'
                img = (f'<img src="img/{iid}-480.webp" srcset="img/{iid}-480.webp 480w, img/{iid}-960.webp 960w" '
                       f'sizes="(min-width: 900px) 420px, (min-width: 600px) 45vw, 92vw" width="{w}" height="{h}" '
                       f'alt="{e(it["name"])}" decoding="async" {eager}>')
            if it.get("group") and it["group"] != group:
                group = it["group"]
                cards.append(f'<h3 class="grp">{t(group, "lt")}</h3>')
            extra = f'<p class="extra">{t(it["people"], "lt")}</p>' if it.get("people") else ""
            cls = "card" if img else "row"
            cards.append(
                f'<article class="{cls}" id="{iid}" data-s="{e(search)}">{img}'
                f'<div class="txt"><h3 class="it"><span class="name">{e(it["name"])}</span>{price_html(it)}</h3>'
                f'{extra}{"<p>" + t(desc, "lt") + "</p>" if any(desc.values()) else ""}</div></article>')
            ld = {"@type": "MenuItem", "name": it["name"], "description": it.get("en") or it.get("lt", "")}
            if it.get("sizes"):
                ld["offers"] = [{"@type": "Offer", "price": z["price"], "priceCurrency": "EUR"} for z in it["sizes"]]
            elif it.get("price"):
                ld["offers"] = {"@type": "Offer", "price": str(it["price"]), "priceCurrency": "EUR"}
            ld_items.append(ld)
        note = f'<p class="sec-note">{t(sec["note"], "lt")}</p>' if sec.get("note") else ""
        body.append(
            f'<section id="{sid}" class="sec" aria-labelledby="h-{sid}">'
            f'<h2 id="h-{sid}">{t(sec["title"], "lt")}</h2>{note}<div class="grid">{"".join(cards)}</div></section>')
        ld_sections.append({"@type": "MenuSection", "name": sec["title"]["en"], "hasMenuItem": ld_items})

    info = data["info"]
    ld = {
        "@context": "https://schema.org", "@type": "Restaurant", "name": "Land of Fire",
        "servesCuisine": "Azerbaijani", "url": SITE_URL, "image": f"{SITE_URL}/img/og.jpg",
        "hasMenu": {"@type": "Menu", "name": "Land of Fire menu", "hasMenuSection": ld_sections},
    }
    for k in ("telephone", "address"):
        if info.get(k):
            ld[k] = info[k]
    tpl = (ROOT / "template.html").read_text()
    out = (tpl.replace("{{NAV}}", "".join(nav)).replace("{{BODY}}", "".join(body))
              .replace("{{FOOTER}}", info.get("footer_html", ""))
              .replace("{{UI}}", json.dumps(UI, ensure_ascii=False))
              .replace("{{LD}}", json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"))
              .replace("{{SITE}}", SITE_URL))
    (DIST / "index.html").write_text(out)
    for f in ("manifest.webmanifest", "robots.txt", "qr.html", "qr.svg", "qr.png", "qr-korteles.pdf"):
        shutil.copy(ROOT / "static" / f, DIST / f)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE_URL}/</loc></url></urlset>\n')
    n = sum(len(s["items"]) for s in data["sections"])
    print(f"built {len(data['sections'])} sections, {n} items")


if __name__ == "__main__":
    build()
