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
           "top": "Į viršų", "lang": "Kalba", "prices": "Kainos nurodytos eurais su PVM.",
           "add": "Pridėti", "mine": "Mano pasirinkimas", "total": "Iš viso", "show": "Rodyti padavėjui",
           "back": "Atgal", "clear": "Išvalyti", "clearq": "Išvalyti visą pasirinkimą?", "close": "Uždaryti",
           "note": "Tai ne užsakymas – parodykite šį sąrašą padavėjui.",
           "nosel": "Dar nieko nepasirinkote. Spauskite „Pridėti“ prie patiekalo.",
           "more": "Vienu daugiau", "less": "Vienu mažiau", "visit": "Apsilankykite", "addr": "Adresas", "phone": "Telefonas", "hours": "Darbo laikas", "hoursmap": "Žiūrėti Google Maps", "route": "Maršrutas", "call": "Skambinti", "seemenu": "Žiūrėti meniu", "legend": "Legenda", "rating": "Google įvertinimas", "pick": "Pasirinkite legendą"},
    "en": {"menu": "Menu", "search": "Search the menu", "none": "Nothing found",
           "top": "Back to top", "lang": "Language", "prices": "Prices in euros, VAT included.",
           "add": "Add", "mine": "My selection", "total": "Total", "show": "Show to waiter",
           "back": "Back", "clear": "Clear", "clearq": "Clear the whole selection?", "close": "Close",
           "note": "This is not an order – show this list to your waiter.",
           "nosel": "Nothing selected yet. Tap “Add” on a dish.",
           "more": "One more", "less": "One less", "visit": "Visit us", "addr": "Address", "phone": "Phone", "hours": "Opening hours", "hoursmap": "See Google Maps", "route": "Directions", "call": "Call", "seemenu": "See the menu", "legend": "The legend", "rating": "Google rating", "pick": "Choose a legend"},
    "ru": {"menu": "Меню", "search": "Поиск блюда", "none": "Ничего не найдено",
           "top": "Наверх", "lang": "Язык", "prices": "Цены указаны в евро с НДС.",
           "add": "Добавить", "mine": "Мой выбор", "total": "Итого", "show": "Показать официанту",
           "back": "Назад", "clear": "Очистить", "clearq": "Очистить весь выбор?", "close": "Закрыть",
           "note": "Это не заказ – покажите этот список официанту.",
           "nosel": "Вы ещё ничего не выбрали. Нажмите «Добавить» у блюда.",
           "more": "Ещё один", "less": "На один меньше", "visit": "Приходите", "addr": "Адрес", "phone": "Телефон", "hours": "Часы работы", "hoursmap": "Смотреть в Google Maps", "route": "Маршрут", "call": "Позвонить", "seemenu": "Смотреть меню", "legend": "Легенда", "rating": "Оценка Google", "pick": "Выберите легенду"},
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
    if it.get("sizes"):  # sizes are listed with their own add buttons in picks_html
        return ""
    if not it.get("price"):
        return ""
    unit = f' / {lbl(it["unit"])}' if it.get("unit") else ""
    vol = f'<small>{e(it["volume"])}</small> ' if it.get("volume") else ""
    return f'<span class="price">{vol}{money(it["price"])}{unit}</span>'


def picks_html(it, iid):
    """One pick control per orderable offer (each size is its own offer).
    data-k = stable key in the guest's saved selection, data-p = price in cents,
    data-z = size label (per-language dict or plain text) shown in the selection list."""
    offers = it.get("sizes") or ([{"price": it["price"]}] if it.get("price") else [])
    rows = []
    for k, o in enumerate(offers):
        key = iid if len(offers) == 1 else f"{iid}~{k}"
        z = o.get("label") or it.get("volume") or ""
        label = f'<span class="pl"><small>{lbl(z)}</small> {money(o["price"])}</span>' if it.get("sizes") else ""
        rows.append(f'<div class="pk">{label}<span class="ctl" data-k="{e(key)}" data-n="{e(it["name"])}" '
                    f'data-p="{round(float(o["price"]) * 100)}" data-z="{e(json.dumps(z, ensure_ascii=False))}"></span></div>')
    return f'<div class="picks">{"".join(rows)}</div>' if rows else ""


EARLY = ('try{var s=localStorage.getItem("lof-lang"),n=(navigator.language||"lt").slice(0,2);'
         'document.documentElement.dataset.lang=s||(n=="lt"||n=="ru"?n:n=="en"?"en":"lt")}'
         'catch(e){document.documentElement.dataset.lang="lt"}')


def _fill(tpl, subs):
    for k, v in subs.items():
        tpl = tpl.replace(k, v)
    assert "{{" not in tpl, re.findall(r"{{\w+}}", tpl)
    return tpl


def footer_html(place):
    tel = re.sub(r"[^+0-9]", "", place["phone"])
    return (f'<p class="word">Land <b>of</b> Fire</p>'
            f'<p><a href="{e(place["maps"])}" rel="noopener">{e(place["address"])}</a><br>'
            f'<a href="tel:{tel}">{e(place["phone"])}</a><br>'
            f'<a href="https://www.instagram.com/{e(place["instagram"])}/" rel="noopener">Instagram @{e(place["instagram"])}</a></p>'
            f'<p><a href="apie">{t(ABOUT_LINK, "lt")}</a></p>')


ABOUT_LINK = {"lt": "Apie mus ir legenda →", "en": "About us & our legend →", "ru": "О нас и легенда →"}
QUOTES = {1: {"lt": "Ugnis – pirmasis prieskonis.", "en": "Fire is the first spice.", "ru": "Огонь – первая специя."},
          4: {"lt": "Prie azerbaidžanietiško stalo niekas neišeina alkanas.",
              "en": "Nobody leaves an Azerbaijani table hungry.",
              "ru": "Из-за азербайджанского стола никто не уходит голодным."}}


def render_mag(data, dims, place):
    """Magazine edition: same data and pick controls, editorial layout."""
    nav, toc, body = [], [], []
    for n, sec in enumerate(data["sections"], 1):
        sid, num = sec["id"], f"{n:02d}"
        title = sec.get("nav", sec["title"])
        nav.append(f'<a href="#{sid}" data-sec="{sid}"><i>{num}</i>{t(title, "lt")}</a>')
        toc.append(f'<li><a href="#{sid}"><span class="n">{num}</span><span class="t">{t(sec["title"], "lt")}</span>'
                   f'<span class="c caps">{len(sec["items"])}</span></a></li>')
        alt = " · ".join(sec["title"][l] for l in LANGS if sec["title"].get(l))
        feats, rows, group = [], [], None
        for i, it in enumerate(sec["items"]):
            iid = it["_iid"]  # same keys as the classic page, so a selection carries over
            search = fold(" ".join([it["name"]] + [it.get(l, "") for l in LANGS]))
            desc = {l: it.get(l, "") for l in LANGS}
            p = f'<p>{t(desc, "lt")}</p>' if any(desc.values()) else ""
            extra = f'<p class="extra">{t(it["people"], "lt")}</p>' if it.get("people") else ""
            ref = f'{n}.{i + 1}'
            if it.get("photo"):
                w, h = dims[iid]
                feats.append(
                    f'<article class="feat" data-s="{e(search)}"><figure><img src="img/{iid}-960.webp" '
                    f'srcset="img/{iid}-480.webp 480w, img/{iid}-960.webp 960w" sizes="(min-width: 860px) 50vw, 100vw" '
                    f'width="{w}" height="{h}" alt="{e(it["name"])}" loading="lazy" decoding="async">'
                    f'<figcaption class="caps"><span>{ref}</span><span>{t(sec["title"], "lt")}</span></figcaption></figure>'
                    f'<div><h3>{e(it["name"])}</h3><span class="pr">{price_html(it)}</span>{extra}{p}{picks_html(it, iid)}</div></article>')
            else:
                if it.get("group") and it["group"] != group:
                    group = it["group"]
                    rows.append(f'<h3 class="grp">{t(group, "lt")}</h3>')
                rows.append(
                    f'<article class="li" data-s="{e(search)}"><div class="row"><span class="nm">{e(it["name"])}</span>'
                    f'<span class="dots"></span><span class="pr">{price_html(it)}</span></div>{extra}{p}{picks_html(it, iid)}</article>')
        inner = (f'<div class="feats">{"".join(feats)}</div>' if feats else "") + (f'<div class="list">{"".join(rows)}</div>' if rows else "")
        body.append(f'<section id="{sid}" class="sec" aria-labelledby="mh-{sid}"><div class="opener"><span class="num">{num}</span>'
                    f'<h2 id="mh-{sid}">{t(sec["title"], "lt")}</h2><span class="alt caps">{e(alt)}</span></div>{inner}</section>')
        if n in QUOTES:
            body.append(f'<blockquote class="quote"><q>{t(QUOTES[n], "lt")}</q></blockquote>')
    return {"{{NAV}}": "".join(nav), "{{TOC}}": "".join(toc), "{{BODY}}": "".join(body),
            "{{FOOTER}}": footer_html(place) + f'<p data-ui="prices">Kainos nurodytos eurais su PVM.</p>',
            "{{SEASON}}": t({"lt": "Ruduo 2026", "en": "Autumn 2026", "ru": "Осень 2026"}, "lt"),
            "{{TOCTITLE}}": t({"lt": "Turinys", "en": "Contents", "ru": "Содержание"}, "lt"),
            "{{COVERLINE}}": t({"lt": "Mėsa ant žarijų, šafranas ir dolma – Azerbaidžano virtuvė Vilniuje.",
                                "en": "Charcoal, saffron and dolma – Azerbaijani cuisine in Vilnius.",
                                "ru": "Угли, шафран и долма – азербайджанская кухня в Вильнюсе."}, "lt")}


def render_about(about):
    pl = about["place"]
    tel = re.sub(r"[^+0-9]", "", pl["phone"])
    it = about["intro"]
    tabs = "".join(f'<button type="button" role="tab" data-lg="{g["key"]}" aria-selected="{str(i == 0).lower()}">'
                   f'<b>{g["key"]}</b> {t(g["title"], "lt")}</button>' for i, g in enumerate(about["legends"]))
    legends = "".join(f'<article class="legend" data-lg="{g["key"]}"{"" if i == 0 else " hidden"}>'
                      f'<h3>{t(g["title"], "lt")}</h3><p>{t(g["body"], "lt")}</p></article>'
                      for i, g in enumerate(about["legends"]))
    return {"{{KICKER}}": t(it["kicker"], "lt"), "{{TITLE}}": t(it["title"], "lt"), "{{LEAD}}": t(it["lead"], "lt"),
            "{{POINTS}}": "".join(f"<li>{t(p, 'lt')}</li>" for p in it["points"]),
            "{{TABS}}": tabs, "{{LEGENDS}}": legends,
            "{{ADDR}}": e(pl["address"]), "{{MAPS}}": e(pl["maps"]), "{{PHONE}}": e(pl["phone"]), "{{TEL}}": tel,
            "{{RATING}}": e(pl["rating"]), "{{IG}}": e(pl["instagram"]), "{{FOOTER}}": footer_html(pl)}


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "img").mkdir(parents=True)
    data = json.loads((ROOT / "data" / "menu.json").read_text())
    make_brand()

    nav, body, ld_sections, seen, dims = [], [], [], set(), {}
    for sec in data["sections"]:
        sid = sec["id"]
        nav.append(f'<a href="#{sid}" data-sec="{sid}">{t(sec.get("nav", sec["title"]), "lt")}</a>')
        cards, ld_items, group = [], [], None
        for i, it in enumerate(sec["items"]):
            iid = f"{sid}-{slug(it['name'])}"
            iid += f"-{i}" if iid in seen else ""
            seen.add(iid)
            it["_iid"] = iid
            search = fold(" ".join([it["name"]] + [it.get(l, "") for l in LANGS]))
            desc = {l: it.get(l, "") for l in LANGS}
            img = ""
            if it.get("photo"):
                w, h = dims[iid] = crop(it["page"], it["photo"], iid)
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
                f'{extra}{"<p>" + t(desc, "lt") + "</p>" if any(desc.values()) else ""}{picks_html(it, iid)}</div></article>')
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
    about = json.loads((ROOT / "data" / "about.json").read_text())
    place = about["place"]
    info["footer_html"] = footer_html(place)
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
              .replace("{{SITE}}", SITE_URL).replace("{{EARLY}}", EARLY))
    (DIST / "index.html").write_text(out)
    common = {"{{UI}}": json.dumps(UI, ensure_ascii=False), "{{SITE}}": SITE_URL, "{{EARLY}}": EARLY}
    fill = lambda tpl, extra: _fill((ROOT / tpl).read_text(), {**common, **extra})
    (DIST / "magazine.html").write_text(fill("template-mag.html", render_mag(data, dims, place)))
    (DIST / "apie.html").write_text(fill("template-about.html", render_about(about)))
    for f in ("manifest.webmanifest", "robots.txt", "qr.html", "qr.svg", "qr.png", "qr-korteles.pdf", "app.js"):
        shutil.copy(ROOT / "static" / f, DIST / f)
    shutil.copytree(ROOT / "static" / "fonts", DIST / "fonts")
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE_URL}/</loc></url><url><loc>{SITE_URL}/apie</loc></url></urlset>\n')
    n = sum(len(s["items"]) for s in data["sections"])
    print(f"built {len(data['sections'])} sections, {n} items")


if __name__ == "__main__":
    build()
