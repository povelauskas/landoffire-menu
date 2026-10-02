#!/usr/bin/env python3
"""Merge the per-page transcriptions (src/pages-*.json) into data/menu.json.

Run once; afterwards data/menu.json is the source of truth and can be edited by hand.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).parent
pages = []
for f in sorted((ROOT / "src").glob("pages-*.json")):
    pages += json.loads(f.read_text())
pages.sort(key=lambda p: p["page"])

SECTION_IDS = {"Šašlykai": "kebabai", "Pagrindiniai Patiekalai": "karsti", "Sriubos": "sriubos",
               "Garnyrai": "garnyrai", "Salotos": "salotos", "Desertai": "desertai", "Gėrimai": "gerimai",
               "Meniu gimtadieniui ar banketui": "banketai"}
GROUPS = {  # drink sub-headings as printed
    "Non-Alcoholic": {"lt": "Nealkoholiniai gėrimai", "ru": "Безалкогольные напитки", "en": "Non-alcoholic drinks"},
    "Compotes": {"lt": "Kompotai", "ru": "Компоты", "en": "Compotes"},
    "Wine": {"lt": "Vynas", "ru": "Вино", "en": "Wine"},
    "Sparkling": {"lt": "Putojantis vynas", "ru": "Игристое вино", "en": "Sparkling wine"},
    "Vodka": {"lt": "Degtinė", "ru": "Водка", "en": "Vodka"},
    "Gin": {"lt": "Džinas", "ru": "Джин", "en": "Gin"},
    "Rum": {"lt": "Romas", "ru": "Ром", "en": "Rum"},
    "Whisky": {"lt": "Viskis", "ru": "Виски", "en": "Whisky"},
    "Cognac": {"lt": "Konjakas", "ru": "Коньяк", "en": "Cognac"},
    "Liqueurs": {"lt": "Likeriai ir trauktinės", "ru": "Ликёры и настойки", "en": "Liqueurs & infusions"},
    "Beer": {"lt": "Alus", "ru": "Пиво", "en": "Beer"},
    "Cocktails": {"lt": "Kokteiliai", "ru": "Коктейли", "en": "Cocktails"},
    "Hot Drinks": {"lt": "Karšti gėrimai", "ru": "Горячие напитки", "en": "Hot drinks"},
    "Snacks": {"lt": "Užkandžiai", "ru": "Закуски", "en": "Snacks"},
}
SIZE_LBL = {"Small": {"lt": "Maža", "ru": "Маленькая", "en": "Small"},
            "Large": {"lt": "Didelė", "ru": "Большая", "en": "Large"}}
FIXES = {  # obvious print typos, corrected (listed in the README)
    ("Düyü", "ru"): "Рис басмати",
}

sections = []
cur_group = None
for p in pages:
    lt = p["section"].get("lt")
    if not lt:
        continue
    if lt == "Alkoholiniai gėrimai":  # continuation pages of the drinks list
        lt = "Gėrimai"
    if not sections or sections[-1]["title"]["lt"] != lt:
        title = dict(p["section"])
        if lt == "Gėrimai":
            title = {"lt": "Gėrimai", "ru": "Напитки", "en": "Drinks"}
        if lt == "Desertai":
            title["en"] = title.get("en") or "Desserts"
        sections.append({"id": SECTION_IDS[lt], "title": title, "items": []})
    sec = sections[-1]
    for it in p["items"]:
        extra = it.get("extra") or ""
        item = {"name": it["name"], "page": p["page"]}
        for l in ("lt", "ru", "en"):
            v = FIXES.get((it["name"], l), it.get(l))
            if v and v.strip().lower() != it["name"].strip().lower():
                item[l] = re.sub(r"\s*–\s*\d+\.\d\d\s*€\s*\.", "", v)  # Şah Plov EN repeats its price
        if it.get("photo"):
            item["photo"] = it["photo"]
        sizes = re.findall(r"(\d+(?:,\d+)?\s*(?:ML|L))\s+(\d+\.\d\d)\s*€", extra)
        if sizes:
            item["sizes"] = [{"label": s.lower().replace(" ml", " ml"), "price": pr} for s, pr in sizes]
        elif m := re.match(r"(\d+(?:,\d+)?\s*(?:ML|L))\b", extra):
            item["volume"] = m.group(1).lower()
            item["price"] = it["price"]
        elif "Small" in extra:
            prs = re.findall(r"(\d+\.\d\d) € (Small|Large)", extra)
            item["sizes"] = [{"label": SIZE_LBL[k], "price": v} for v, k in prs]
        else:
            item["price"] = it["price"]
        if sec["id"] == "gerimai":
            for key, g in GROUPS.items():
                if key in extra or g["lt"] in extra:
                    cur_group = g
            if it["name"] == "Sirab":
                cur_group = GROUPS["Non-Alcoholic"]
            if "Martini" in it["name"]:
                cur_group = GROUPS["Sparkling"]
            item["group"] = cur_group
        if sec["id"] == "banketai":
            if it["name"].startswith("SET"):
                ppl = re.search(r"(\d+–\d+)", extra).group(1)
                item["people"] = {"lt": f"{ppl} žmonėms", "ru": f"на {ppl} человек", "en": f"for {ppl} people"}
                for l in ("lt", "ru", "en"):
                    item[l] = item[l].replace("; ", "\n")
            elif "Napoleon" in it["name"]:
                item["unit"] = "kg"
            elif "musiqi" in it["name"]:
                item["unit"] = {"lt": "val.", "ru": "час", "en": "hour"}
        sec["items"].append(item)

info = {
    "instagram": "landoffire.vilnius",
    "footer_html": '<p><a href="https://www.instagram.com/landoffire.vilnius/" rel="noopener">Instagram @landoffire.vilnius</a></p>',
}
out = ROOT / "data" / "menu.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"info": info, "sections": sections}, ensure_ascii=False, indent=1) + "\n")
print({s["id"]: len(s["items"]) for s in sections})
