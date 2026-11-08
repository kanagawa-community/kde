#!/usr/bin/env python3
"""Write the Plasma wallpaper packages in wallpapers/.

Downloads public-domain Hokusai prints (The Met's Open Access collection, CC0, and one
restored scan from Wikimedia Commons), crops each to its printed area and to 16:9, and
writes 3840x2160 JPEGs. It also writes palette versions of The Great Wave per variant:
monochrome ones, and an "OLED" one with the wave on a near-black background.
Needs ImageMagick 7 and network access.

Usage: scripts/wallpapers.py [path/to/palette.json]   (default: ../.github/palette.json)
"""
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True
from aurorae import hexify  # noqa: E402
from generate import ROOT, VARIANTS, metadata, roles, write  # noqa: E402

SIZE = "3840x2160"
MET = "https://www.metmuseum.org/art/collection/search/"
MET_IMAGE = "https://images.metmuseum.org/CRDImages/as/original/"
COMMONS = "https://commons.wikimedia.org/wiki/File:Great_Wave_off_Kanagawa2.jpg"
CC0 = "CC0-1.0"

# id -> (title, image URL, source page, license, 16:9 crop "WxH+X+Y" inside the printed area)
# Crops and the OLED mask are pixel positions, so each download must have exactly these
# pixels: PIXELS holds ImageMagick's pixel signature (%#), which ignores metadata the
# museums rewrite.
PIXELS = {
    "hokusai-great-wave": "a568a526da8a28587314f1d7008bac5b156bfdfa42a4936f4534d7b4a627a5e3",
    "hokusai-great-wave-restored": "921e79c3abcd7002d5dfc7f77e83459ef8d19ab5972effbc20284964fd9c6267",
    "hokusai-red-fuji": "870d9107ed0c9c9b9779da9f744681b817bdf5aecce5d1a763e28248b4535852",
    "hokusai-kajikazawa": "2f807a7466524dabc7ee795868c6edbb4a13b50f42d5c119f4548e2632f6c248",
    "hokusai-misaka": "79afede8b72622f9fe6b1343fb5b72c30a4e02a076863c0b1b8b57867b29d6ef",
    "hokusai-umezawa": "97c876fd7cd6c3a6c243cc0a3d68a06ca113b7e5f7fc1b0bdedbcf2b0e8419cb",
    "hokusai-kazusa": "5128fd8bafbec46dcada87b5d7b47c4cea901a0c91ab54796d5e8355199a6667",
    "hokusai-tsukudajima": "31a2782405c6f6b541590fbdf30b5b287953e8228c4565b23c4ead67a192050c",
    "hokusai-suwa": "5eb9ff0f472358a2cb4fa47169ab0210208fbb4c14904cad40656bd3c2fe5e3a",
}
PRINTS = {
    "hokusai-great-wave": (
        "The Great Wave off Kanagawa", f"{MET_IMAGE}DP141042.jpg", f"{MET}39799", CC0, "3720x2093+70+150",
    ),
    # The Met's JP1847 impression, cleaned up on Wikimedia Commons; twice the Met API's resolution.
    "hokusai-great-wave-restored": (
        "The Great Wave off Kanagawa, restored",
        "https://upload.wikimedia.org/wikipedia/commons/0/0d/Great_Wave_off_Kanagawa2.jpg",
        COMMONS,
        "Public domain",
        "8120x4568+60+160",
    ),
    "hokusai-red-fuji": ("Red Fuji", f"{MET_IMAGE}DP141062.jpg", f"{MET}36490", CC0, "3570x2008+160+250"),
    "hokusai-kajikazawa": (
        "Kajikazawa in Kai Province", f"{MET_IMAGE}DP141085.jpg", f"{MET}39800", CC0, "3700x2081+75+60",
    ),
    "hokusai-misaka": (
        "Reflection in Lake at Misaka", f"{MET_IMAGE}DP140993.jpg", f"{MET}36495", CC0, "3689x2075+70+120",
    ),
    "hokusai-umezawa": (
        "Umezawa Manor in Sagami Province", f"{MET_IMAGE}DP140983.jpg", f"{MET}36501", CC0, "3720x2093+130+200",
    ),
    "hokusai-kazusa": ("At Sea off Kazusa", f"{MET_IMAGE}DP140984.jpg", f"{MET}36502", CC0, "3690x2076+140+230"),
    "hokusai-tsukudajima": (
        "Tsukudajima in Musashi Province", f"{MET_IMAGE}DP140986.jpg", f"{MET}36504", CC0, "3660x2059+170+220",
    ),
    "hokusai-suwa": (
        "Lake Suwa in Shinano Province", f"{MET_IMAGE}DP140970.jpg", f"{MET}39798", CC0, "3610x2031+125+200",
    ),
}
# The palette versions are made from this print.
BASE = "hokusai-great-wave-restored"
# Monochrome Great Wave: suffix -> (dark role, light role, negate). Negated prints put
# the paper in the dark color, so the wave stands out of a dark desktop.
MONO = {
    "ink": ("ui.bg", "ui.fg", False),
    "blue": ("ui.bg", "syn.fun", True),
    "paper": ("ui.bg", "ui.fg_dim", True),
}
# OLED version: the sky is flood-filled on a 1200 px copy of BASE, where Hokusai's
# outlines are solid, from these seed pixels (checked to sit on sky, off Fuji and the
# spray). A 5% fuzz stops at the paper of the crest; 9% leaks into it.
OLED_WIDTH = 1200
OLED_SEEDS = [
    (120, 24), (360, 24), (600, 24), (840, 24), (1080, 24), (1176, 24), (720, 120), (840, 120),
    (960, 120), (1080, 120), (1176, 120), (780, 240), (960, 240), (1140, 240), (540, 360), (660, 360),
    (840, 360), (1020, 360), (600, 480), (720, 480), (840, 480), (960, 480), (1092, 72),
    # left of the wave, around the cartouche and signature
    (24, 36), (36, 72), (36, 144), (132, 48), (132, 144), (24, 228), (60, 216), (168, 180), (240, 108),
    (12, 96), (18, 120), (18, 180), (54, 168), (54, 240), (12, 240), (36, 204),
    # the darker band of sky at the horizon, either side of Fuji
    *[(x, y) for x in (600, 618, 636, 654, 672, 690) for y in (498, 510, 522, 534, 546, 558)
      if (x, y) not in {(618, 558)}],
    *[(x, y) for x in (888, 906, 924, 942, 960, 978) for y in (498, 510, 522, 534, 546, 558)
      if not (x >= 924 and y == 558) and not (x == 978 and y > 510)],
]
# Rectangles (x0, y0, x1, y1) at OLED_WIDTH painted as sky: the cartouche and the
# signature, which float on the black otherwise.
OLED_ERASE = [(68, 42, 124, 229), (0, 118, 70, 250)]
# The cut-out's alpha is built at half the print's resolution. Specks of paper grain
# left in the sky are dropped there: blobs smaller than SPECK px, or than SPECK_OUTSIDE
# px outside SPRAY (x0, y0, x1, y1), where Hokusai's spray dots are.
SPECK, SPECK_OUTSIDE, SPRAY = 60, 750, (1560, 450, 3420, 1880)
# Circle wallpapers: the wave, as printed and mirrored, cut into a circle ("WxH+X+Y" of the print),
# centered on each ANSI color and on true black for OLED screens. #000000 is not a
# palette color; it is there because OLED pixels only switch off at true black.
CIRCLE_CROP, CIRCLE_SIZE = "5440x5440+511+195", 800
# "Side" wallpaper: a large circle left of center,
# leaving the right of the screen empty for widgets or the SilentSDDM login form.
SIDE_SIZE, SIDE_CENTER = 1500, (1150, 1080)
# "Dim" wallpaper, also the login screen background: the restored print under ui.bg at
# DIM percent, so light text reads over its sky.
DIM = 70
ANSI = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
# Pixels on the sky's edge stay only if they look like the print: light paper (foam),
# blue (wave) or warm yellow (boats). Lab channels scaled to 0..1; sampled from the print.
KEEP = "max(max(clamp((u.r-0.80)*25),clamp((0.525-u.b)*25)),clamp((u.b-0.60)*25))"


def magick(*args):
    subprocess.run(["magick", *map(str, args)], check=True)


def package(pid, name, description, authors, website, license_, image_args):
    out = ROOT / "wallpapers" / pid
    image = out / "contents" / "images" / f"{SIZE}.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    magick(*image_args, "-strip", "-quality", "90", image)
    print(image.relative_to(ROOT))
    meta = json.loads(metadata(pid, name, description, KPackageStructure="Wallpaper/Images"))
    meta["KPlugin"].update(Authors=[{"Name": a} for a in authors], License=license_, Website=website)
    write(out / "metadata.json", json.dumps(meta, indent=2) + "\n")


def oled_alpha(tmp, src):
    """Alpha of the print at half its size: 0 on the sky, 1 inside the print's shapes."""
    full = subprocess.run(["magick", "identify", "-format", "%wx%h", src], capture_output=True, text=True,
                          check=True).stdout
    w, h = (int(n) // 2 for n in full.split("x"))
    fill = []
    for x, y in OLED_SEEDS:
        fill += ["-draw", f"color {x},{y} floodfill"]
    magick(src, "-resize", f"{OLED_WIDTH}x", "-alpha", "set", "-fuzz", "5%", "-fill", "none", *fill,
           "-alpha", "extract", "-negate", "-morphology", "Close", "Disk:1.5",
           "-fill", "white", *[a for r in OLED_ERASE for a in ("-draw", "rectangle %d,%d %d,%d" % r)],
           tmp / "sky.png")
    magick(tmp / "sky.png", "-morphology", "Dilate", "Disk:2", tmp / "edge.png")
    for name in ("sky", "edge"):
        magick(tmp / f"{name}.png", "-resize", f"{w}x{h}!", tmp / f"{name}-half.png")
    magick(src, "-resize", f"{w}x{h}!", "-colorspace", "Lab", "-fx", KEEP, "-channel", "R", "-separate",
           "+channel", tmp / "keep.png")
    # sky -> 0; the ring the dilation added -> colour test; everything else -> 1
    alpha = tmp / "alpha.png"
    magick(tmp / "sky-half.png", tmp / "edge-half.png", tmp / "keep.png", "-fx", "u>0.5?0:(v>0.5?u[2]:1)",
           "-blur", "0x0.6", alpha)
    blobs = subprocess.run(
        ["magick", alpha, "-threshold", "50%", "-define", "connected-components:verbose=true",
         "-define", "connected-components:exclude-header=true", "-connected-components", "8", "null:"],
        capture_output=True, text=True, check=True).stdout
    erase = []
    for line in blobs.splitlines():
        # "  id: WxH+X+Y cx,cy area color"
        _, geometry, _, area, color = line.split()[:5]
        bw, bh, x, y = map(int, geometry.replace("x", "+").split("+"))
        area = float(area)
        in_spray = SPRAY[0] <= x and x + bw <= SPRAY[2] and SPRAY[1] <= y and y + bh <= SPRAY[3]
        if "255" in color and (area < SPECK or (area < SPECK_OUTSIDE and not in_spray)):
            erase += ["-draw", f"rectangle {x - 1},{y - 1} {x + bw},{y + bh}"]
    magick(alpha, "-fill", "black", *erase, "-resize", f"{full}!", alpha)
    return alpha


def cutout(src, alpha, view):
    """magick args for the print, colours cleaned up, cut along `alpha`, both through `view`."""
    return [src, "-level", "0%,90%", "-modulate", "100,110", *view,
            "(", alpha, *view, ")", "-alpha", "off", "-compose", "CopyOpacity", "-composite"]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / ".github" / "palette.json"
    variants = json.loads(path.read_text())["variants"]
    with tempfile.TemporaryDirectory() as tmp:
        sources = {}
        for pid, (_, url, *_) in PRINTS.items():
            req = urllib.request.Request(url, headers={"User-Agent": "kanagawa-community-kde-wallpapers"})
            sources[pid] = Path(tmp) / f"{pid}.jpg"
            sources[pid].write_bytes(urllib.request.urlopen(req, timeout=120).read())
            signature = subprocess.run(["magick", "identify", "-format", "%#", sources[pid]], capture_output=True,
                                       text=True, check=True).stdout
            if signature != PIXELS[pid]:
                sys.exit(f"{url} changed upstream; re-check its crop (and the OLED mask) before updating PIXELS")

        # Everything in wallpapers/ is written below; start clean so dropped packages go away.
        # Only after every download checked out, so a failed run leaves the old files.
        shutil.rmtree(ROOT / "wallpapers", ignore_errors=True)
        crops = {}
        for pid, (title, _, page, license_, crop) in PRINTS.items():
            crops[pid] = [sources[pid], "-crop", crop, "+repage", "-resize", f"{SIZE}!"]
            package(
                pid,
                f"{title} (Hokusai)",
                f"Katsushika Hokusai, {title}, from Thirty-six Views of Mount Fuji. {license_}.",
                ["Katsushika Hokusai"],
                page,
                license_,
                crops[pid],
            )

        wave, page, license_ = crops[BASE], PRINTS[BASE][2], PRINTS[BASE][3]
        src, crop = sources[BASE], PRINTS[BASE][4]
        alpha = oled_alpha(Path(tmp), src)
        def disc(d, mirror):
            """magick args for the wave cut into a circle `d` px across."""
            mask = Path(tmp) / f"circle-{d}.png"
            magick("-size", f"{d}x{d}", "xc:none", "-fill", "white", "-draw",
                   f"circle {d / 2},{d / 2} {d / 2},0.5", mask)
            view = ["-crop", CIRCLE_CROP, "+repage", "-resize", f"{d}x{d}!", *(["-flop"] if mirror else [])]
            return [*cutout(src, alpha, view), "(", mask, ")", "-compose", "DstIn", "-composite"]

        discs = {mirror: disc(CIRCLE_SIZE, mirror) for mirror in ("", "-mirrored")}
        side = disc(SIDE_SIZE, "")
        authors = ["Katsushika Hokusai", "Kanagawa Community contributors"]
        for v in VARIANTS:
            r, cap = roles(variants[v]), v.capitalize()
            for suffix, (dark, light, negate) in MONO.items():
                package(
                    f"kanagawa-{v}-great-wave-{suffix}",
                    f"Kanagawa {cap} Great Wave ({suffix})",
                    f"The Great Wave by Katsushika Hokusai in Kanagawa {cap} {light}.",
                    authors,
                    page,
                    license_,
                    [*wave, "-colorspace", "gray", "-auto-level", *(["-negate"] if negate else []),
                     "+level-colors", f"{hexify(r[dark])},{hexify(r[light])}"],
                )
            package(
                f"kanagawa-{v}-great-wave-oled",
                f"Kanagawa {cap} Great Wave (OLED)",
                f"The Great Wave by Katsushika Hokusai, its sky replaced with Kanagawa {cap} ui.bg_m3.",
                authors,
                page,
                license_,
                [*cutout(src, alpha, ["-crop", crop, "+repage", "-resize", f"{SIZE}!"]),
                 "-background", hexify(r["ui.bg_m3"]), "-alpha", "remove", "-alpha", "off"],
            )
            package(
                f"kanagawa-{v}-great-wave-dim",
                f"Kanagawa {cap} Great Wave dim",
                f"The Great Wave by Katsushika Hokusai under Kanagawa {cap} ui.bg.",
                authors,
                page,
                license_,
                [*wave, "(", "+clone", "-fill", hexify(r["ui.bg"]), "-colorize", "100", ")", "-compose", "blend",
                 "-define", f"compose:args={DIM}", "-composite"],
            )
            package(
                f"kanagawa-{v}-great-wave-side",
                f"Kanagawa {cap} Great Wave side",
                f"The Great Wave by Katsushika Hokusai in a large circle on the left, on Kanagawa {cap} ui.bg_m3.",
                authors,
                page,
                license_,
                ["-size", SIZE, f"xc:{hexify(r['ui.bg_m3'])}", "(", *side, ")", "-geometry",
                 f"+{SIDE_CENTER[0] - SIDE_SIZE // 2}+{SIDE_CENTER[1] - SIDE_SIZE // 2}", "-compose", "Over",
                 "-composite"],
            )
            for mirror, art in discs.items():
                for name, bg in [*((c, hexify(r[f"term.{c}"])) for c in ANSI), ("oled", "#000000")]:
                    package(
                        f"kanagawa-{v}-great-wave-circle{mirror}-{name}",
                        f"Kanagawa {cap} Great Wave circle{mirror.replace('-', ', ')} ({name})",
                        f"The Great Wave by Katsushika Hokusai{mirror.replace('-', ', ')} in a circle on "
                        f"Kanagawa {cap} " + ("true black." if name == "oled" else f"term.{name}."),
                        authors,
                        page,
                        license_,
                        ["-size", SIZE, f"xc:{bg}", "(", *art, ")", "-gravity", "center", "-compose", "Over",
                         "-composite"],
                    )

if __name__ == "__main__":
    main()
