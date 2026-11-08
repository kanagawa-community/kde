#!/usr/bin/env python3
"""Write the color scheme, Plasma desktop theme, window decoration and look-and-feel package per variant.

Usage: scripts/generate.py [path/to/palette.json]   (default: ../.github/palette.json)
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep scripts/__pycache__ out of the repo
import aurorae  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = ["wave", "dragon", "lotus"]
# KDE color set -> (BackgroundNormal, BackgroundAlternate, ForegroundNormal, ForegroundInactive)
SETS = {
    "Button": ("ui.bg_p1", "ui.bg_p2", "ui.fg", "ui.fg_dim"),
    "Complementary": ("ui.bg_m3", "ui.bg_dim", "ui.fg", "ui.fg_dim"),
    "Header": ("ui.bg", "ui.bg_m1", "ui.fg", "ui.fg_dim"),
    "Header][Inactive": ("ui.bg_m3", "ui.bg_dim", "ui.fg", "ui.fg_dim"),
    # ui.bg_search, not ui.bg_visual: Plasma also uses Selection as the accent on
    # checkboxes and sliders, where waveBlue1 is barely visible. ui.pmenu.fg, the text on
    # a selected menu item: ui.fg on ui.bg_search is below 4.5:1 in Lotus.
    "Selection": ("ui.bg_search", "ui.bg_visual", "ui.pmenu.fg", "ui.fg_dim"),
    "Tooltip": ("ui.float.bg", "ui.bg_m1", "ui.float.fg", "syn.comment"),
    "View": ("ui.bg_m1", "ui.bg", "ui.fg", "syn.comment"),
    "Window": ("ui.bg", "ui.bg_m1", "ui.fg", "ui.fg_dim"),
}
# Inactive text in light variants: syn.comment is 2.6:1 on Lotus's view, and the only role
# reaching 4.5:1 is darker than normal text. This is the most readable one still dimmer.
LIGHT_INACTIVE = {"syn.comment": "ui.float.fg_border"}
# Same in every set.
SHARED = {
    "DecorationFocus": "syn.fun",
    "DecorationHover": "syn.fun",
    "ForegroundActive": "syn.fun",
    "ForegroundLink": "syn.special1",
    "ForegroundNegative": "diag.error",
    "ForegroundNeutral": "diag.warning",
    "ForegroundPositive": "diag.ok",
    "ForegroundVisited": "syn.statement",
}
# Copied from BreezeDark.colors.
EFFECTS = """[ColorEffects:Disabled]
Color=56,56,56
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color=112,111,110
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0
"""


def roles(variant):
    """Map each role to "r,g,b"; a role missing from the palette raises KeyError later."""
    return {
        role: ",".join(map(str, color["rgb"]))
        for color in variant["colors"].values()
        for role in color["usage"]
    }


def colors(name, scheme, r, light):
    out = [EFFECTS]
    for kde_set, (bg, bg_alt, fg, fg_inactive) in SETS.items():
        if light:
            fg_inactive = LIGHT_INACTIVE.get(fg_inactive, fg_inactive)
        keys = {
            "BackgroundAlternate": bg_alt,
            "BackgroundNormal": bg,
            "ForegroundInactive": fg_inactive,
            "ForegroundNormal": fg,
            **SHARED,
        }
        out.append(f"[Colors:{kde_set}]\n" + "".join(f"{k}={r[v]}\n" for k, v in sorted(keys.items())))
    out.append(f"[General]\nColorScheme={scheme}\nName=Kanagawa {name}\nshadeSortColumn=true\n")
    out.append("[KDE]\ncontrast=4\n")
    out.append(
        # Matches Header, which Breeze and the Aurorae decoration use for titlebars.
        f"[WM]\nactiveBackground={r['ui.bg']}\nactiveBlend={r['ui.fg']}\n"
        f"activeForeground={r['ui.fg']}\ninactiveBackground={r['ui.bg_m3']}\n"
        f"inactiveBlend={r['ui.fg_dim']}\ninactiveForeground={r['ui.fg_dim']}\n"
    )
    return "\n".join(out)


def metadata(plugin_id, name, description, **extra):
    return json.dumps(
        {
            "KPlugin": {
                "Authors": [{"Name": "Kanagawa Community contributors"}],
                "Description": description,
                "Id": plugin_id,
                "License": "MIT",
                "Name": name,
                "Website": "https://github.com/kanagawa-community/kde",
            },
            **extra,
        },
        indent=2,
    ) + "\n"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(path.relative_to(ROOT))


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / ".github" / "palette.json"
    variants = json.loads(path.read_text())["variants"]
    for v in VARIANTS:
        name, scheme, plasma_id = f"Kanagawa {v.capitalize()}", f"Kanagawa{v.capitalize()}", f"kanagawa-{v}"
        lnf_id = f"org.kanagawa-community.{v}"
        r = roles(variants[v])
        text = colors(v.capitalize(), scheme, r, variants[v]["appearance"] == "light")

        write(ROOT / "color-schemes" / f"{scheme}.colors", text)

        # Like Breeze Dark: only metadata and colors, SVGs fall back to the default theme.
        theme = ROOT / "desktoptheme" / plasma_id
        write(theme / "colors", text)
        write(theme / "metadata.json", metadata(plasma_id, name, f"{name} Plasma style", **{"X-Plasma-API": "5.0"}))
        write(theme / "plasmarc", "[AdaptiveTransparency]\nenabled=true\n")

        lnf = ROOT / "look-and-feel" / lnf_id
        write(lnf / "metadata.json", metadata(lnf_id, name, f"{name} global theme", **{"KPackageStructure": "Plasma/LookAndFeel"}))
        write(
            lnf / "contents" / "defaults",
            "[kdeglobals][KDE]\nwidgetStyle=Breeze\n\n"
            f"[kdeglobals][General]\nColorScheme={scheme}\n\n"
            # From the icons port; Plasma falls back to Breeze without it.
            f"[kdeglobals][Icons]\nTheme=Kanagawa-Kora-{v.capitalize()}\n\n"
            f"[plasmarc][Theme]\nname={plasma_id}\n\n"
            # From the cursors port; Plasma falls back to its default cursors without it.
            f"[kcminputrc][Mouse]\ncursorTheme=Kanagawa-{v.capitalize()}\n\n"
            # Package written by scripts/wallpapers.py.
            f"[Wallpaper]\nImage=kanagawa-{v}-great-wave-blue\n\n"
            # SVG Aurorae themes are listed under the v2 plugin; with plain aurorae the theme
            # renders but System Settings does not show it as selected.
            f"[kwinrc][org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae.v2\ntheme=__aurorae__svg__{plasma_id}\n",
        )

        deco = ROOT / "aurorae" / plasma_id
        write(deco / "metadata.json", metadata(plasma_id, name, f"{name} window decoration", **{"KPackageStructure": "KWin/Aurorae"}))
        # KWin lists Aurorae themes in System Settings only by metadata.desktop.
        write(
            deco / "metadata.desktop",
            f"[Desktop Entry]\nName={name}\nX-KDE-PluginInfo-Author=Kanagawa Community contributors\n"
            f"X-KDE-PluginInfo-EnabledByDefault=true\nX-KDE-PluginInfo-License=MIT\nX-KDE-PluginInfo-Name={plasma_id}\n",
        )
        for file, content in aurorae.files(plasma_id, r).items():
            write(deco / file, content)


if __name__ == "__main__":
    main()
