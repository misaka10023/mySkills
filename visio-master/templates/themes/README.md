# Theme Catalog

This directory ships the six **`theme1.xml`** payloads that the visio-master
builder injects into a generated `.vsdx` package. Each payload is a complete
DrawingML theme part conformant with ECMA-376 Part 1 §20.1.6.9
(`CT_OfficeStyleSheet`) and is round-trip safe through Visio desktop, Visio
for the Web, and any OOXML-aware consumer that honours
`application/vnd.openxmlformats-officedocument.theme+xml`.

Three things live here:

| Artifact | Role |
|----------|------|
| `*.xml` (six files) | Theme payloads; each one is dropped into a package at `visio/theme/theme1.xml` to seed colour, font, and format schemes. |
| `themes_index.json` | Machine-readable catalogue: filename, gallery name, all twelve `clrScheme` slots in 6-char hex, major/minor Latin font, recommended variant, recommended embellishment level. The Stylist role consumes this index to resolve a theme name to a payload + metadata. |
| `README.md` | This file. Describes the six payloads, the index schema, and the three programmatic selection paths. |

The reference for **how** themes interact with shapes, variants, and overrides
is `references/theme-and-data-graphics.md` §1-§3 and `research/20-themes-styles.md`
§1-§6. This document is operational only: which file to pick, when, and how to
hand it to the builder.

---

## 1. The Six Bundled Themes

| File | Theme name (`<a:theme name="...">`) | Intent | Default variant | Embellishment | Notes |
|------|-------------------------------------|--------|-----------------|----------------|-------|
| `office.xml` | `Office` | Faithful reproduction of the Office baseline so a generated document looks identical to a `Document.SetTheme("Office")` call against shipping Visio. Use as the safe default. | 1 | 1 (subtle) | Matches the ECMA-376 default palette verbatim. Use when round-tripping with Word/Excel/PowerPoint matters. |
| `facet.xml` | `Facet` | Crisp angled aesthetic, blue-green-orange accent triad. Suitable for product overview decks and architecture diagrams that want a non-default but still neutral look. | 2 | 2 (moderate) | Custom payload; not bit-identical to Microsoft's gallery `Facet`. The name field is set so `Document.SetTheme("Facet")` resolves to this payload after injection. |
| `slice.xml` | `Slice` | Warm/cold dual-accent palette tuned for high-contrast data dashboards. Pairs well with Color-by-Value DGs. | 1 | 2 (moderate) | Custom payload; cool primary + warm secondary, designed for diverging numeric scales. |
| `integral.xml` | `Integral` | Banded background variant; muted earth tones. Use for swimlane / cross-functional diagrams where the page benefits from a slight tint. | 3 | 3 (intense) | Custom payload; `lt2` is set to a warm cream to surface the banded fill matrix at intense embellishment. |
| `brand-corporate.xml` | `Brand Corporate` | Red / navy / green / gold corporate brand. Mirrors the recipe in `references/theme-and-data-graphics.md` §3.4 — used as the canonical "swap built-in look for brand" smoke test. | 1 | 1 (subtle) | `accent1..accent4` follow the recipe exactly; `accent5` and `accent6` extend with a cool/warm auxiliary pair. Apply via `SetTheme("Brand Corporate")` then no variant swap. |
| `mono-print.xml` | `Mono Print` | Pure greyscale, print-safe at 300 dpi monochrome. Use for archival exports, regulatory submissions, and wire-frame mockups. | 1 | 0 (none) | All accents are tints of black; `hlink` and `folHlink` collapse to mid-grey so links survive monochrome printing. |

### 1.1 Per-theme palette (6-char hex)

The values below mirror what `themes_index.json` carries; the README is the
human-readable view, the JSON is the machine-readable source of truth.

| Slot | `office.xml` | `facet.xml` | `slice.xml` | `integral.xml` | `brand-corporate.xml` | `mono-print.xml` |
|------|--------------|-------------|--------------|----------------|------------------------|--------------------|
| `dk1` | `000000` | `000000` | `000000` | `000000` | `000000` | `000000` |
| `lt1` | `FFFFFF` | `FFFFFF` | `FFFFFF` | `FFFFFF` | `FFFFFF` | `FFFFFF` |
| `dk2` | `44546A` | `2C3E50` | `1F3864` | `8B4513` | `1F2A37` | `262626` |
| `lt2` | `E7E6E6` | `DBDBDB` | `EAEAEA` | `F5EFE0` | `F2F2F2` | `F2F2F2` |
| `accent1` | `5B9BD5` | `90C226` | `052F61` | `330D00` | `C00000` | `000000` |
| `accent2` | `ED7D31` | `54A021` | `A50E82` | `A23A00` | `203864` | `404040` |
| `accent3` | `A5A5A5` | `E6B91E` | `14967C` | `B17F00` | `548235` | `808080` |
| `accent4` | `FFC000` | `E76618` | `6E9B3A` | `7E6240` | `BF9000` | `B0B0B0` |
| `accent5` | `4472C4` | `C42F1A` | `A01B1B` | `B07000` | `2E75B6` | `D9D9D9` |
| `accent6` | `70AD47` | `8C0F45` | `D87E13` | `5C7E1F` | `C55A11` | `595959` |
| `hlink` | `0563C1` | `0563C1` | `0563C1` | `8B4513` | `2E75B6` | `404040` |
| `folHlink` | `954F72` | `954F72` | `954F72` | `5C4033` | `7030A0` | `595959` |

### 1.2 Per-theme font scheme

| File | Major Latin (`<a:majorFont><a:latin typeface>`) | Minor Latin (`<a:minorFont><a:latin typeface>`) | Rationale |
|------|---------------------------------------------------|----------------------------------------------------|-----------|
| `office.xml` | `Calibri Light` | `Calibri` | ECMA default; no surprises. |
| `facet.xml` | `Trebuchet MS` | `Trebuchet MS` | Matches the visual register of Microsoft's gallery `Facet`. |
| `slice.xml` | `Century Gothic` | `Century Gothic` | Geometric sans pairs with the dual-accent palette. |
| `integral.xml` | `Tw Cen MT` | `Tw Cen MT` | Slightly condensed humanist — fits banded backgrounds. |
| `brand-corporate.xml` | `Segoe UI Semibold` | `Segoe UI` | Microsoft brand-friendly, ships with Windows 7+. |
| `mono-print.xml` | `Arial` | `Arial` | Universal; survives every fallback step in `references/theme-and-data-graphics.md` §8.2. |

If a target machine lacks a font, Visio walks the fallback chain documented
in `research/20-themes-styles.md` §8.2 — theme major/minor → document default
→ Calibri → system substitution table. The bundled payloads do not embed
fonts; embedded subsets are the caller's responsibility per `Save -> Embed
fonts in the file` or via post-build `<FaceName Flags='...325'/>` patching.

---

## 2. Directory Layout

```
templates/themes/
├── README.md                    # this file
├── themes_index.json            # canonical metadata index (consumed by Stylist)
├── office.xml                   # theme1.xml payload — Office baseline
├── facet.xml                    # theme1.xml payload — Facet
├── slice.xml                    # theme1.xml payload — Slice
├── integral.xml                 # theme1.xml payload — Integral
├── brand-corporate.xml          # theme1.xml payload — Brand Corporate
└── mono-print.xml               # theme1.xml payload — Mono Print
```

Every `*.xml` is a self-contained DrawingML theme part. The builder copies it
**as-is** into the generated package at `visio/theme/theme1.xml`. No template
substitution, no XSLT, no string replacement happens at build time — what you
see in the file is what ships. To customise, copy a payload to a new filename,
edit, then add an entry to `themes_index.json`.

---

## 3. `themes_index.json` Schema

The index is a single JSON document with a top-level `themes` array. Each
entry exposes the metadata needed to (a) resolve a theme name to a file and
(b) drive the builder's downstream stages (variant, override, font fallback)
without re-parsing the XML.

```json
{
  "schema_version": 1,
  "themes": [
    {
      "id": "office",
      "name": "Office",
      "file": "office.xml",
      "intent": "default",
      "default_variant": 1,
      "default_embellishment": 1,
      "palette": {
        "dk1": "000000", "lt1": "FFFFFF",
        "dk2": "44546A", "lt2": "E7E6E6",
        "accent1": "5B9BD5", "accent2": "ED7D31",
        "accent3": "A5A5A5", "accent4": "FFC000",
        "accent5": "4472C4", "accent6": "70AD47",
        "hlink":   "0563C1", "folHlink": "954F72"
      },
      "fonts": { "major": "Calibri Light", "minor": "Calibri" },
      "tags": ["baseline", "round-trip-safe", "neutral"]
    }
    /* … five more entries, one per bundled file … */
  ]
}
```

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `schema_version` | integer | yes | Current version is `1`. Bump on breaking changes. |
| `themes[].id` | string | yes | Stable identifier; lower-kebab-case; matches the file basename without extension. Used as the lookup key in code. |
| `themes[].name` | string | yes | Human-visible name; matches `<a:theme name="...">` in the XML payload. Pass to `Document.SetTheme(name)` after injection. |
| `themes[].file` | string | yes | Filename relative to this directory. |
| `themes[].intent` | enum | yes | One of `default`, `gallery-match`, `brand`, `print`. |
| `themes[].default_variant` | integer 1..4 | yes | Recommended initial `VariantThemeIndex`. Pass to `SetThemeVariant`. |
| `themes[].default_embellishment` | integer 0..3 | yes | Recommended initial `VariantEmbellishmentIdx` (`0=none, 1=subtle, 2=moderate, 3=intense`). |
| `themes[].palette` | object | yes | All twelve `clrScheme` slots, 6-char uppercase hex (no leading `#`). |
| `themes[].fonts` | object | yes | `{major, minor}` Latin typefaces. |
| `themes[].tags` | string[] | optional | Free-form tags; the Stylist may filter by tag (`brand`, `print`, `dashboard`, …). |

Validation: parse with any JSON 1.1 parser; reject duplicate `id`s; assert
that every `palette.{slot}` value matches `^[0-9A-F]{6}$`; assert
`default_variant ∈ {1,2,3,4}` and `default_embellishment ∈ {0,1,2,3}`.

---

## 4. How to Pick a Theme Programmatically

There are three paths, in order of increasing intrusiveness. Pick the
**least intrusive** path that achieves the desired result.

### 4.1 Path A — by name against the active gallery (post-injection)

Use this when the document was generated by visio-master (so the bundled
payload is already at `visio/theme/theme1.xml`) and you want to swap to a
different bundled theme **after** the document has been opened in Visio.
The injection step makes the new theme's name resolvable through
`Document.Themes`.

```python
"""Pick a bundled theme by its index name, against an already-open document."""
from __future__ import annotations
import json
from pathlib import Path

import pythoncom
import win32com.client as win32

THEMES_DIR = Path(__file__).parent  # templates/themes

def load_index() -> dict:
    with (THEMES_DIR / "themes_index.json").open("r", encoding="utf-8") as f:
        return json.load(f)

def pick_theme(doc, theme_id: str) -> None:
    index = load_index()
    entry = next((t for t in index["themes"] if t["id"] == theme_id), None)
    if entry is None:
        raise KeyError(f"unknown theme id '{theme_id}'")

    pythoncom.CoInitialize()
    doc.SetTheme(entry["name"])
    doc.SetThemeVariant(entry["default_variant"])
    doc.PageSheet.CellsU("VariantEmbellishmentIdx").FormulaU = str(
        entry["default_embellishment"]
    )

    applied = doc.PageSheet.CellsU("ThemeIndex").ResultIU
    if applied == 0:
        raise RuntimeError(
            f"SetTheme('{entry['name']}') no-op; payload likely not injected"
        )
```

### 4.2 Path B — by file injection (pre-build)

Use this during the build step when assembling a fresh `.vsdx`. Copy the
chosen payload over `visio/theme/theme1.xml`, leave the rest of the package
untouched.

```python
"""Inject a bundled theme payload into a .vsdx ZIP."""
from __future__ import annotations
import json
import shutil
import zipfile
from pathlib import Path

THEMES_DIR = Path(__file__).parent
THEME_PART = "visio/theme/theme1.xml"

def inject_theme(vsdx_path: Path, theme_id: str) -> None:
    index = json.loads((THEMES_DIR / "themes_index.json").read_text("utf-8"))
    entry = next((t for t in index["themes"] if t["id"] == theme_id), None)
    if entry is None:
        raise KeyError(f"unknown theme id '{theme_id}'")

    payload = (THEMES_DIR / entry["file"]).read_bytes()

    backup = vsdx_path.with_suffix(vsdx_path.suffix + ".bak")
    shutil.copy2(vsdx_path, backup)
    tmp = vsdx_path.with_suffix(vsdx_path.suffix + ".tmp")
    with zipfile.ZipFile(vsdx_path, "r") as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        seen = False
        for item in zin.infolist():
            data = payload if item.filename == THEME_PART else zin.read(item.filename)
            if item.filename == THEME_PART:
                seen = True
            zout.writestr(item, data)
        if not seen:
            raise RuntimeError(f"{THEME_PART} not present in {vsdx_path.name}")
    tmp.replace(vsdx_path)
```

After injection, **the document still needs `SetTheme(name)` to wire the
DocumentSheet cells (`ThemeIndex`, `VariantThemeIndex`)**. Path B alone
swaps the colour/font/format scheme but leaves the document's theme cells
pointing at whatever was there before — Visio will recompute on first open
and the visual result depends on shapes' Quick Style cells. The reliable
combination is `inject_theme(...)` followed by Path A on first open.

### 4.3 Path C — by name lookup with fallback to brand override

Use this when the desired result is "the bundled `Brand Corporate` look,
regardless of which theme is currently loaded". Apply the override step
documented in `references/theme-and-data-graphics.md` §2.5 row 2.

```python
def apply_brand_override(doc, theme_id: str = "brand-corporate") -> None:
    index = json.loads((THEMES_DIR / "themes_index.json").read_text("utf-8"))
    entry = next(t for t in index["themes"] if t["id"] == theme_id)

    # 1. Theme + variant first (mandatory order)
    doc.SetTheme(entry["name"])
    doc.SetThemeVariant(entry["default_variant"])

    # 2. Force accent1..accent4 to the index palette, regardless of variant
    palette = entry["palette"]
    for slot, key in enumerate(("accent1", "accent2", "accent3", "accent4"), start=1):
        rgb = palette[key]
        c = doc.Colors.Item(slot)
        c.Red   = int(rgb[0:2], 16)
        c.Green = int(rgb[2:4], 16)
        c.Blue  = int(rgb[4:6], 16)
```

This path is the one to use when the underlying document was generated
externally (e.g., from a stencil drag-drop session in Visio) and the goal is
to brand it without rewriting the theme part.

---

## 5. Picking the Right Theme

| Scenario | Recommended `id` | Why |
|----------|------------------|------|
| Default for a new diagram with no brand requirement | `office` | Round-trip safe; matches the gallery default; requires zero downstream tweaks. |
| Architecture / system diagrams that want non-default but still neutral | `facet` | Crisp accent triad reads well on white; muted enough for technical diagrams. |
| Data dashboards using Color-by-Value or Data Bar DGs | `slice` | Diverging warm/cold accents map cleanly onto numeric scales. |
| Swimlane / cross-functional / process charts | `integral` | Banded background surfaces lane separators without extra fill shapes. |
| Internal corporate decks where brand colours are required | `brand-corporate` | Ships the canonical red/navy/green/gold; pair with Path C if seed doc has a different theme. |
| Print, archive, regulatory submission, wire-frame | `mono-print` | Pure greyscale; survives monochrome printing and accessibility colour-blindness audits unchanged. |

When in doubt, default to `office` and let the user opt into a richer theme.

---

## 6. Variant + Override Interaction Reminder

The **mandatory order** documented in `references/theme-and-data-graphics.md`
§2.1 — `SetTheme → SetThemeVariant → Colors(1..4) override` — applies to
every selection path here. The bundled payload only seeds the colour scheme;
the variant rotation and 4-colour override are runtime decisions.

Quick reference (full table in the same reference, §2.5):

| Goal | Use `SetTheme` | Use `SetThemeVariant` | Use `Colors(1..4)` override |
|------|----------------|------------------------|------------------------------|
| Apply built-in look | yes | optional (default 1) | no |
| Brand palette over built-in shape | yes | yes (closest variant) | yes (4 accents) |
| Colour-only swap, keep current shapes | no | no | yes (touches only `<ColorEntry>` rows) |
| Reset to Office default | `office` | `1` | clear `<ColorEntry/>` rows |

Calling the override before the variant blows the override away on the next
variant call. Verify with
`PageSheet.CellsU("ThemeIndex").ResultIU` and
`PageSheet.CellsU("VariantThemeIndex").ResultIU` after each step.

---

## 7. Verification

After injecting and applying a theme, run the smoke check in
`references/theme-and-data-graphics.md` §2.4 — read back `ThemeIndex` and
`VariantThemeIndex` from the DocumentSheet, assert non-zero. A second tier of
verification opens the saved package and asserts against the XML:

```python
import zipfile
from xml.etree import ElementTree as ET

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

def assert_theme_name(vsdx_path: str, expected_name: str) -> None:
    with zipfile.ZipFile(vsdx_path, "r") as zf:
        with zf.open("visio/theme/theme1.xml") as f:
            root = ET.parse(f).getroot()
    actual = root.get("name")
    if actual != expected_name:
        raise AssertionError(f"theme name {actual!r} != {expected_name!r}")
```

---

## 8. Cross-references

- `references/theme-and-data-graphics.md` — operational sequence for theme
  application, variant rotation, 4-colour override, and the
  theme + data-graphic intersection (Color-by-Value).
- `references/shared-standards.md` — OPC content types, namespace prefixes,
  package layout that govern the `theme/theme1.xml` part this directory
  ships.
- `references/com-quick-ref.md` — `Document.SetTheme`,
  `Document.SetThemeVariant`, `Document.Colors`, `Page.SetTheme`
  signatures and HRESULT semantics.
- `references/shapesheet-quick-ref.md` — `THEMEVAL`, `MSO_THEME_COLOR`,
  `THEMEGUARD`, `Quick Style*` cell mechanics.
- `research/20-themes-styles.md` — DrawingML schema, gallery enumeration,
  Quick Style matrix indices, font fallback chain, custom theme construction
  paths.
- `templates/stencils/README.md` — sibling catalog covering the bundled
  master stencils that consume these themes via `THEMEVAL()` formulas.
