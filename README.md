# Land of Fire — menu website

Phone-first online menu for **Land of Fire** (Azerbaijani cuisine, Vilnius), built from the
print menu `menu final print exp.pdf` (26 pages, Sep 2026).

Live: https://landoffire-menu.vercel.app

- Static HTML, no framework, no trackers, no external fonts — one ~100 KB page plus lazy WebP photos.
- Lithuanian / English / Russian switch (remembers the choice, defaults to the phone's language).
- "My selection": guests tap Add (per size where there are sizes), see count and total in a bottom bar,
  and open a large-text "show to waiter" view (keeps the screen awake). Not an order; stored only on
  the guest's phone for 6 hours.
- Sticky section chips that follow the scroll, instant search, back-to-top button.
- schema.org `Restaurant` + `Menu` JSON-LD, Open Graph image, web-app manifest and icons.

## Change a price or dish

Edit `data/menu.json`, then run `python3 build.py` and deploy (`vercel deploy --prod`).
Rebuilding needs the page renders in `src/hi/` (not committed; made from the PDF with
`pdftoppm -jpeg -r 200 menu.pdf src/hi/p`). The built site in `dist/` is committed.

## Corrected print typos

- Düyü, Russian text printed as "Бasmati düyüsü" → shown as "Рис басмати".
- Şah Plov, English text repeated the price inline → removed.
- Lithuanian "Pateikiama su duona" (7 dishes) → "Patiekiama su duona" (patiekti = to serve), as the menu already says elsewhere.
- Tava Kotleti, Russian "Жареный мясной котлет" → "Жареная мясная котлета" (котлета is feminine).
- Russian "Подается" → "Подаётся" so all dishes use the same spelling.
- Russian banquet tab "Банкет" → "Банкеты", plural like the other tabs.
