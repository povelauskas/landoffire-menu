#!/usr/bin/env python3
"""Build the static Land of Fire menu site into dist/.

Inputs:  data/menu.json (sections + items, transcribed from the print menu)
         src/hi/p-NN.jpg (200 dpi page renders) for dish photo crops
Outputs: dist/index.html, dist/img/*.webp, icons, manifest, robots, sitemap
"""
import html, json, math, re, shutil, unicodedata
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


# Drink size icons: 24x24 line drawings, drawn at a height that grows with the volume.
ICONS = {
    "shot": "M7.5 4h9l-1.6 16H9.1z M8.3 11h7.4",
    "tumbler": "M5 6h14l-1.4 13.2a1 1 0 0 1-1 .8H7.4a1 1 0 0 1-1-.8z M5.8 13h12.4",
    "snifter": "M6.6 6h10.8c.4 1.2.6 2.3.6 3.5 0 3.6-2.7 6.5-6 6.5s-6-2.9-6-6.5c0-1.2.2-2.3.6-3.5z M6.2 11h11.6 M12 16v4.5 M8.5 20.5h7",
    "wine": "M7 3h10v4.5a5 5 0 0 1-10 0z M7.2 7h9.6 M12 12.5V20 M8.5 20.5h7",
    "flute": "M9.5 3h5l-.5 8.5a2 2 0 0 1-4 0z M9.8 7h4.4 M12 13.5v6.5 M9.5 20.5h5",
    "winebottle": "M10.4 2h3.2v5c0 1 3.4 2 3.4 5.2V21a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1v-8.8C7 9 10.4 8 10.4 7z M7 14h10",
    "bottle": "M10.6 2h2.8v3l2.6 2.2V21a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V7.2L10.6 5z M8 11h8v6H8",
    "soda": "M10.5 2h3v3c1.6 1 2.5 2.2 2.5 4.2V21a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V9.2C8 7.2 8.9 6 10.5 5z M8 12h8",
    "beer": "M5.5 5h10v15a1 1 0 0 1-1 1h-8a1 1 0 0 1-1-1z M15.5 9h2a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2 M5.5 8.5h10",
    "jug": "M7 3h9l-1.2 3.2C17 8.2 17 10.5 17 13v7a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1v-7c0-2.5 0-4.8 2.2-6.8z M17 9h1.5a1.5 1.5 0 0 1 1.5 1.5v4a1.5 1.5 0 0 1-1.5 1.5H17 M7 12h10",
    "armudu": "M8 3h8c0 3.2-2.2 4.5-2.2 8.5S16 17 16 20H8c0-3 2.2-4.5 2.2-8.5S8 6.2 8 3z M7 21h10",
    "espresso": "M5 9h11v4.5a4.5 4.5 0 0 1-4.5 4.5h-2A4.5 4.5 0 0 1 5 13.5z M16 10.5h1.5a2 2 0 0 1 0 4H16 M4 21h14",
    "cocktail": "M4 4h16l-8 9z M7 7.4h10 M12 13v7 M8 20.5h8",
}
SPRITE = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + "".join(
    f'<symbol id="i-{k}" viewBox="0 0 24 24"><path d="{d}" fill="none" stroke="currentColor" stroke-width="1.5" '
    f'stroke-linecap="round" stroke-linejoin="round"/></symbol>' for k, d in ICONS.items()) + "</svg>")
SERVES = {"wine": (150, {"lt": "taurės", "en": "glasses", "ru": "бокалов"}),
          "shot": (40, {"lt": "taurelių", "en": "shots", "ru": "рюмок"})}


def ml(label):
    m = re.match(r"([\d,]+)\s*(ml|l)$", str(label).strip().lower())
    return round(float(m.group(1).replace(",", ".")) * (1000 if m.group(2) == "l" else 1)) if m else None


def drink_icon(it, label=""):
    """Pick a glass/bottle for a drink (and size) and scale it by volume. Returns (svg, serves-hint)."""
    g = (it.get("group") or {}).get("en", "")
    v = ml(label) if label else ml(it.get("volume", ""))
    if not g:
        return "", ""
    big = v and v >= 500
    if g in ("Wine", "Sparkling wine"):
        kind, unit = ("winebottle", "wine") if big else ("flute" if g.startswith("Sparkling") else "wine", None)
    elif g in ("Vodka", "Gin", "Rum", "Whisky", "Cognac", "Liqueurs & infusions"):
        small = {"Whisky": "tumbler", "Cognac": "snifter"}.get(g, "shot")
        kind, unit = ("bottle", "shot") if big else (small, None)
    elif g == "Beer":
        kind, unit = "beer", None
    elif g == "Compotes":
        kind, unit = ("jug" if v and v >= 1000 else "soda"), None
    elif g == "Non-alcoholic drinks":
        kind, unit = "soda", None
    elif g == "Cocktails":
        kind, unit = "cocktail", None
    elif g == "Hot drinks":
        kind, unit = ("armudu" if it["name"] == "Çay" else "espresso"), None
    else:
        return "", ""
    h = 22 if not v else round(18 + 14 * min(1, max(0, math.log(v / 40) / math.log(25))))
    svg = f'<svg class="ic" width="{h}" height="{h}" aria-hidden="true"><use href="#i-{kind}"/></svg>'
    hint = ""
    if unit and v:
        per, words = SERVES[unit]
        n = int(v / per)
        hint = f'<em class="serves">≈&nbsp;{n}&nbsp;{t(words, "lt")}</em>'
    return svg, hint


NBSP = "\u00a0"


LOGOS = json.loads((ROOT / "data" / "logos.json").read_text())


def logo(it):
    """Brand mark from Wikimedia Commons (public-domain files only, see data/logos.json); decorative."""
    lg = LOGOS.get(it["name"])
    return f'<img class="logo" src="{e(lg["file"])}" alt="" height="22" loading="lazy" decoding="async">' if lg else ""


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
    ic, _ = drink_icon(it)
    vol = f'<small class="vol">{ic}{e(it["volume"].replace(" ", NBSP))}</small> ' if it.get("volume") else (
        f'<small class="vol">{ic}</small> ' if ic else "")
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
        ic, hint = drink_icon(it, z if isinstance(z, str) else "")
        zt = e(z.replace(" ", NBSP)) if isinstance(z, str) else lbl(z)
        label = f'<span class="pl"><small class="vol">{ic}{zt}</small> {money(o["price"])}{hint}</span>' if it.get("sizes") else ""
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


LEGEND_TITLE = {"lt": "Legenda", "en": "The legend", "ru": "Легенда"}


def legend_html(g, cls):
    return (f'<article class="{cls}"><h3>{t(g["title"], "lt")}</h3><p>{t(g["body"], "lt")}</p>'
            f'<p class="more"><a href="apie">{t(ABOUT_LINK, "lt")}</a></p></article>')


def render_mag(data, dims, place, legend):
    """Magazine edition: same data and pick controls, editorial layout. Section 00 is the legend."""
    alt0 = " · ".join(LEGEND_TITLE[l] for l in LANGS)
    nav = [f'<a href="#legenda" data-sec="legenda"><i>00</i>{t(LEGEND_TITLE, "lt")}</a>']
    toc = [f'<li><a href="#legenda"><span class="n">00</span><span class="t">{t(LEGEND_TITLE, "lt")}</span>'
           f'<span class="c caps">{t(legend["title"], "lt")}</span></a></li>']
    body = [f'<section id="legenda" class="sec" aria-labelledby="mh-legenda"><div class="opener"><span class="num">00</span>'
            f'<h2 id="mh-legenda">{t(LEGEND_TITLE, "lt")}</h2><span class="alt caps">{e(alt0)}</span></div>'
            f'{legend_html(legend, "legend")}</section>']
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
                    f'<article class="li" data-s="{e(search)}">{logo(it)}<div class="row"><span class="nm">{e(it["name"])}</span>'
                    f'<span class="dots"></span><span class="pr">{price_html(it)}</span></div>{extra}{p}{picks_html(it, iid)}</article>')
        inner = (f'<div class="feats">{"".join(feats)}</div>' if feats else "") + (f'<div class="list">{"".join(rows)}</div>' if rows else "")
        body.append(f'<section id="{sid}" class="sec" aria-labelledby="mh-{sid}"><div class="opener"><span class="num">{num}</span>'
                    f'<h2 id="mh-{sid}">{t(sec["title"], "lt")}</h2><span class="alt caps">{e(alt)}</span></div>{inner}'
                    f'{"<p class=sec-note>" + t(sec["note"], "lt") + "</p>" if sec.get("note") else ""}</section>')
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
    legends = "".join(f'<article class="legend" data-lg="{g["key"]}"{"" if i == 0 else " hidden"}>'
                      f'<h3>{t(g["title"], "lt")}</h3><p>{t(g["body"], "lt")}</p></article>'
                      for i, g in enumerate(about["legends"]))
    return {"{{KICKER}}": t(it["kicker"], "lt"), "{{TITLE}}": t(it["title"], "lt"), "{{LEAD}}": t(it["lead"], "lt"),
            "{{POINTS}}": "".join(f"<li>{t(p, 'lt')}</li>" for p in it["points"]),
            "{{LEGENDS}}": legends,
            "{{ADDR}}": e(pl["address"]), "{{MAPS}}": e(pl["maps"]), "{{PHONE}}": e(pl["phone"]), "{{TEL}}": tel,
            "{{RATING}}": e(pl["rating"]), "{{IG}}": e(pl["instagram"]), "{{FOOTER}}": footer_html(pl)}


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "img").mkdir(parents=True)
    data = json.loads((ROOT / "data" / "menu.json").read_text())
    make_brand()

    about = json.loads((ROOT / "data" / "about.json").read_text())
    legend = about["legends"][0]
    nav = [f'<a href="#legenda" data-sec="legenda">{t(LEGEND_TITLE, "lt")}</a>']
    body = [f'<section id="legenda" class="sec" aria-labelledby="h-legenda"><h2 id="h-legenda">{t(LEGEND_TITLE, "lt")}</h2>'
            f'{legend_html(legend, "legend card")}</section>']
    ld_sections, seen, dims = [], set(), {}
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
                f'<div class="txt"><h3 class="it"><span class="name">{logo(it)}{e(it["name"])}</span>{price_html(it)}</h3>'
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
              .replace("{{SITE}}", SITE_URL).replace("{{EARLY}}", EARLY).replace("{{ICONS}}", SPRITE))
    (DIST / "index.html").write_text(out)
    common = {"{{ICONS}}": SPRITE, "{{UI}}": json.dumps(UI, ensure_ascii=False), "{{SITE}}": SITE_URL, "{{EARLY}}": EARLY}
    fill = lambda tpl, extra: _fill((ROOT / tpl).read_text(), {**common, **extra})
    (DIST / "magazine.html").write_text(fill("template-mag.html", render_mag(data, dims, place, about["legends"][0])))
    (DIST / "apie.html").write_text(fill("template-about.html", render_about(about)))
    shutil.copytree(ROOT / "static" / "logos", DIST / "logos")
    for f in ("manifest.webmanifest", "robots.txt", "qr.html", "qr.svg", "qr.png", "qr-korteles.pdf", "app.js", "type.css"):
        shutil.copy(ROOT / "static" / f, DIST / f)
    shutil.copytree(ROOT / "static" / "fonts", DIST / "fonts")
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE_URL}/</loc></url><url><loc>{SITE_URL}/apie</loc></url></urlset>\n')
    n = sum(len(s["items"]) for s in data["sections"])
    print(f"built {len(data['sections'])} sections, {n} items")


if __name__ == "__main__":
    build()
