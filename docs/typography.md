# Typography and alignment rules

One shared scale lives in `static/type.css`; every page uses it. Sources were checked on 2026-10-02.

| Role | Phone → desktop | Line height | Notes |
|---|---|---|---|
| Labels, chips, caps | 13px | 1.3 | caps tracked +8–10% (Butterick: 5–12%) |
| Secondary text | 15px | 1.5 | |
| Body / descriptions | 17px | 1.5 | iOS body size (Apple HIG) |
| Prices | 17px | — | `lining-nums tabular-nums`, no-break space before € |
| List item names | 20 → 24px | 1.2 | |
| Classic dish names | 22 → 24px | 1.25 | Material 3 title-large |
| Magazine dish names | 26 → 36px | 1.2 | |
| Section titles | 30 → 44px | 1.1–1.2 | |
| Page titles | 36 → 56px | 1.1 | M3 display-small on phones |
| Cover word | 72 → 152px | 0.9 | one short word only |

Rules followed:
- Sizes in `rem`, so the guest's own text size still applies (MDN font-size). Fluid steps use `clamp()` with a rem term (WCAG F94).
- Body line height 1.5 and lines ≤ 65ch (WCAG 1.4.8; Butterick 45–90 characters).
- Touch targets are 44–48px (Apple 44pt, Material 48dp, WCAG 2.5.8 needs at least 24px).
- Text contrast is at least 4.5:1, or 3:1 for large text (WCAG 1.4.3). This is checked by `tools/typecheck.mjs`.
- Headings use `text-wrap: balance`; paragraphs use `pretty` and `hyphens: auto` with `lang` per language. Safari has no Lithuanian hyphenation, so long words break with `overflow-wrap` instead.
- Name and price rows align on the first baseline. Prices wrap below long names instead of overflowing.
- Currency follows VLKK/CLDR: `7,00 €`, with a no-break space before €.

Check: `node tools/typecheck.mjs <url or file://…/dist>`. It runs on iPhone SE and iPhone 13 widths, in LT and RU. It flags text under 12.5px, tight multi-line leading, low contrast, overflow, small targets and horizontal scroll.

# Drink logos

Only files that Wikimedia Commons marks as **public domain** (mostly `{{PD-textlogo}}`) are used, with no CC-BY-SA and no files taken from brand sites.
Public domain covers copyright only. The marks are still trademarks of their owners and are shown only to identify the drinks sold; the site says this under Drinks.
Brands without a public-domain file on Commons have no logo.

| Drink | File | Licence | Source |
|---|---|---|---|
| Coca-Cola | `logos/coca-cola.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Coca-Cola_logo.svg |
| Sprite | `logos/sprite.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Sprite_2026.svg |
| Fanta | `logos/fanta.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Fanta_2023.svg |
| Schweppes | `logos/schweppes.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Schweppes_wordmark.svg |
| Red Bull | `logos/red-bull.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Logo_of_Red_bull.svg |
| Martini Asti | `logos/martini.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Martini_Logo.svg |
| Absolut | `logos/absolut.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Logo-absolut.svg |
| Nemiroff | `logos/nemiroff.png` | Public domain | https://commons.wikimedia.org/wiki/File:NemiroffLogo.jpg |
| Ballantine's Finest | `logos/ballantines.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Ballantines_logo.svg |
| Corona Extra | `logos/corona-extra.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Corona_Extra_text_logo.svg |
| Aperol Spritz | `logos/aperol.svg` | Public domain | https://commons.wikimedia.org/wiki/File:Aperol_Logo.svg |

# Drink size icons

These are line icons drawn for this site (no third-party artwork). The icon type comes from the drink group and its size: a shot glass, whisky tumbler or cognac snifter for 40 ml; a wine glass or flute for 150 ml; bottles for 500 ml and over; a beer mug, soda bottle, compote jug, armudu tea glass, espresso cup or cocktail glass. Icon height grows with the volume, from 18px at 40 ml to 32px at 1 l.
Bottle hints: wine 750 ml ≈ 5 × 150 ml glasses; spirits 500/700 ml ≈ 12/17 × 40 ml shots.
