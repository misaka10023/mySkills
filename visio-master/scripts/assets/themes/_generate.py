"""Generator for the six bundled theme XMLs. Run once and discard.

This is a build-time helper; the produced .xml files are what apply_theme.py
ships and reads. Each theme follows ECMA-376 Part 1 §20.1.6 (theme part) with
the canonical 12-slot color scheme, a major/minor Latin font scheme, and the
standard 3-entry fillStyleLst / lnStyleLst / effectStyleLst / bgFillStyleLst.

Palettes are sourced from Microsoft Office gallery defaults documented across
PowerPoint 2013+ and Visio 2013+ theme builds.
"""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent

THEMES = {
    "office.xml": {
        "name": "Office",
        "scheme": "Office",
        "major": "Calibri Light",
        "minor": "Calibri",
        "dk1": ("sysClr", "windowText", "000000"),
        "lt1": ("sysClr", "window",     "FFFFFF"),
        "dk2": ("srgb", "44546A"),
        "lt2": ("srgb", "E7E6E6"),
        "accent1": "5B9BD5", "accent2": "ED7D31",
        "accent3": "A5A5A5", "accent4": "FFC000",
        "accent5": "4472C4", "accent6": "70AD47",
        "hlink": "0563C1", "folHlink": "954F72",
    },
    "facet.xml": {
        "name": "Facet",
        "scheme": "Facet",
        "major": "Trebuchet MS",
        "minor": "Trebuchet MS",
        "dk1": ("sysClr", "windowText", "000000"),
        "lt1": ("sysClr", "window",     "FFFFFF"),
        "dk2": ("srgb", "2C3E4C"),
        "lt2": ("srgb", "DBDBDB"),
        "accent1": "90C226", "accent2": "54A021",
        "accent3": "E6B91E", "accent4": "E76618",
        "accent5": "C42F1A", "accent6": "918655",
        "hlink": "99CA3C", "folHlink": "B9D272",
    },
    "ion.xml": {
        "name": "Ion",
        "scheme": "Ion",
        "major": "Century Gothic",
        "minor": "Century Gothic",
        "dk1": ("sysClr", "windowText", "000000"),
        "lt1": ("sysClr", "window",     "FFFFFF"),
        "dk2": ("srgb", "1E5155"),
        "lt2": ("srgb", "EBEBEB"),
        "accent1": "B01513", "accent2": "EA6312",
        "accent3": "E6B729", "accent4": "6BA53A",
        "accent5": "568E14", "accent6": "004F59",
        "hlink": "5DCEAF", "folHlink": "F2A287",
    },
    "slice.xml": {
        "name": "Slice",
        "scheme": "Slice",
        "major": "Century Gothic",
        "minor": "Century Gothic",
        "dk1": ("sysClr", "windowText", "000000"),
        "lt1": ("sysClr", "window",     "FFFFFF"),
        "dk2": ("srgb", "052F61"),
        "lt2": ("srgb", "A6B5C0"),
        "accent1": "052F61", "accent2": "A50E82",
        "accent3": "14967C", "accent4": "6A5E9C",
        "accent5": "F08100", "accent6": "C24F1D",
        "hlink": "9BBA60", "folHlink": "B0C5DC",
    },
    "wisp.xml": {
        "name": "Whisp",
        "scheme": "Whisp",
        "major": "Century Gothic",
        "minor": "Century Gothic",
        "dk1": ("sysClr", "windowText", "000000"),
        "lt1": ("sysClr", "window",     "FFFFFF"),
        "dk2": ("srgb", "766F66"),
        "lt2": ("srgb", "F1EADD"),
        "accent1": "73A950", "accent2": "D17C3F",
        "accent3": "8AAEBD", "accent4": "BB7359",
        "accent5": "B6A269", "accent6": "91A266",
        "hlink": "A3CC91", "folHlink": "C9C19F",
    },
    "berlin.xml": {
        "name": "Berlin",
        "scheme": "Berlin",
        "major": "Trebuchet MS",
        "minor": "Trebuchet MS",
        "dk1": ("sysClr", "windowText", "000000"),
        "lt1": ("sysClr", "window",     "FFFFFF"),
        "dk2": ("srgb", "9E3A26"),
        "lt2": ("srgb", "F2F2F2"),
        "accent1": "A6B727", "accent2": "DF5327",
        "accent3": "FE9E00", "accent4": "418AB3",
        "accent5": "D7D447", "accent6": "818183",
        "hlink": "9E5E9B", "folHlink": "7F6FA9",
    },
}


def _slot(spec):
    if spec[0] == "sysClr":
        return f'<a:sysClr val="{spec[1]}" lastClr="{spec[2]}"/>'
    return f'<a:srgbClr val="{spec[1]}"/>'


FMT_SCHEME = """\
    <a:fmtScheme name="{scheme}">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:gradFill rotWithShape="1">
          <a:gsLst>
            <a:gs pos="0"><a:schemeClr val="phClr"><a:lumMod val="110000"/><a:satMod val="105000"/><a:tint val="67000"/></a:schemeClr></a:gs>
            <a:gs pos="50000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="103000"/><a:tint val="73000"/></a:schemeClr></a:gs>
            <a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="109000"/><a:tint val="81000"/></a:schemeClr></a:gs>
          </a:gsLst>
          <a:lin ang="5400000" scaled="0"/>
        </a:gradFill>
        <a:gradFill rotWithShape="1">
          <a:gsLst>
            <a:gs pos="0"><a:schemeClr val="phClr"><a:satMod val="103000"/><a:lumMod val="102000"/><a:tint val="94000"/></a:schemeClr></a:gs>
            <a:gs pos="50000"><a:schemeClr val="phClr"><a:satMod val="110000"/><a:lumMod val="100000"/><a:shade val="100000"/></a:schemeClr></a:gs>
            <a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="99000"/><a:satMod val="120000"/><a:shade val="78000"/></a:schemeClr></a:gs>
          </a:gsLst>
          <a:lin ang="5400000" scaled="0"/>
        </a:gradFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="6350"  cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
        <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
        <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst><a:outerShdw blurRad="57150" dist="19050" dir="5400000" algn="ctr" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="63000"/></a:srgbClr></a:outerShdw></a:effectLst></a:effectStyle>
        <a:effectStyle><a:effectLst><a:outerShdw blurRad="57150" dist="19050" dir="5400000" algn="ctr" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="63000"/></a:srgbClr></a:outerShdw></a:effectLst></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"><a:tint val="95000"/><a:satMod val="170000"/></a:schemeClr></a:solidFill>
        <a:gradFill rotWithShape="1">
          <a:gsLst>
            <a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="93000"/><a:satMod val="150000"/><a:shade val="98000"/><a:lumMod val="102000"/></a:schemeClr></a:gs>
            <a:gs pos="50000"><a:schemeClr val="phClr"><a:tint val="98000"/><a:satMod val="130000"/><a:shade val="90000"/><a:lumMod val="103000"/></a:schemeClr></a:gs>
            <a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="63000"/><a:satMod val="120000"/></a:schemeClr></a:gs>
          </a:gsLst>
          <a:lin ang="5400000" scaled="0"/>
        </a:gradFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
"""


def render(spec):
    body = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="{spec["name"]}">\n'
        '  <a:themeElements>\n'
        f'    <a:clrScheme name="{spec["scheme"]}">\n'
        f'      <a:dk1>{_slot(spec["dk1"])}</a:dk1>\n'
        f'      <a:lt1>{_slot(spec["lt1"])}</a:lt1>\n'
        f'      <a:dk2>{_slot(spec["dk2"])}</a:dk2>\n'
        f'      <a:lt2>{_slot(spec["lt2"])}</a:lt2>\n'
        f'      <a:accent1><a:srgbClr val="{spec["accent1"]}"/></a:accent1>\n'
        f'      <a:accent2><a:srgbClr val="{spec["accent2"]}"/></a:accent2>\n'
        f'      <a:accent3><a:srgbClr val="{spec["accent3"]}"/></a:accent3>\n'
        f'      <a:accent4><a:srgbClr val="{spec["accent4"]}"/></a:accent4>\n'
        f'      <a:accent5><a:srgbClr val="{spec["accent5"]}"/></a:accent5>\n'
        f'      <a:accent6><a:srgbClr val="{spec["accent6"]}"/></a:accent6>\n'
        f'      <a:hlink><a:srgbClr val="{spec["hlink"]}"/></a:hlink>\n'
        f'      <a:folHlink><a:srgbClr val="{spec["folHlink"]}"/></a:folHlink>\n'
        '    </a:clrScheme>\n'
        f'    <a:fontScheme name="{spec["scheme"]}">\n'
        '      <a:majorFont>\n'
        f'        <a:latin typeface="{spec["major"]}"/>\n'
        '        <a:ea typeface=""/>\n'
        '        <a:cs typeface=""/>\n'
        '      </a:majorFont>\n'
        '      <a:minorFont>\n'
        f'        <a:latin typeface="{spec["minor"]}"/>\n'
        '        <a:ea typeface=""/>\n'
        '        <a:cs typeface=""/>\n'
        '      </a:minorFont>\n'
        '    </a:fontScheme>\n'
        + FMT_SCHEME.format(scheme=spec["scheme"]) +
        '  </a:themeElements>\n'
        '  <a:objectDefaults/>\n'
        '  <a:extraClrSchemeLst/>\n'
        '</a:theme>\n'
    )
    return body


def main() -> int:
    for fname, spec in THEMES.items():
        (OUT / fname).write_text(render(spec), encoding="utf-8")
        print(f"wrote {fname}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
