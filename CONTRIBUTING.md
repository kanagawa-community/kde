# Contributing to Kanagawa for KDE Plasma

Thanks for helping. This port follows the
[Kanagawa community contributing guide](https://github.com/kanagawa-community/.github/blob/main/.github/CONTRIBUTING.md),
which explains conventional commits, the checks every pull request runs, and how
changes are reviewed. This page covers only what is specific to this port.

## Where to report what

- Problems with the theme in KDE Plasma, such as wrong colors, poor
  contrast, or a missing variant, belong in this repository's
  [issue tracker](https://github.com/kanagawa-community/kde/issues).
- Problems in KDE Plasma itself belong with its maintainers, not here. Start
  from the [application's page](https://kde.org/plasma-desktop/).
- Changes to the colors themselves belong in the
  [shared palette](https://github.com/kanagawa-community/.github/blob/main/docs/PALETTE.md),
  not in this port. Open an issue in the
  [.github repository](https://github.com/kanagawa-community/.github/issues)
  so every port stays in step.

## Colors

Take colors from the shared [palette](https://github.com/kanagawa-community/.github/blob/main/docs/PALETTE.md)
and follow the [style guide](https://github.com/kanagawa-community/.github/blob/main/docs/STYLE-GUIDE.md).
Do not sample colors from screenshots or add new ones. Every change must work in
Wave, Dragon, and Lotus.

To read the colors from a script, use the machine-readable
[palette.json](https://raw.githubusercontent.com/kanagawa-community/.github/main/palette.json).

## Working on this port

`color-schemes/`, `desktoptheme/`, `aurorae/` and `look-and-feel/` are generated
(`aurorae/` with the help of `scripts/aurorae.py`). Do not edit them by hand. `scripts/generate.py` reads the shared `palette.json` from a sibling
checkout of the [.github repository](https://github.com/kanagawa-community/.github)
(or from a path given as its first argument) and maps each KDE color to a palette
role. The README lists the mapping. After changing the mapping, regenerate and
commit the result:

```sh
python3 scripts/generate.py
```

A pull request also runs the **Generated** check (`.github/workflows/generated.yml`). It
regenerates the files from the current shared palette and fails if anything differs, so
commit the regenerated files with your change. When the palette itself changes, the check
fails until someone regenerates.

`wallpapers/` is written by `scripts/wallpapers.py`, which downloads the prints
from The Met and Wikimedia Commons and needs ImageMagick 7. Run it after changing a crop or the
palette colors; it replaces the whole folder. The Generated check leaves it out because it
needs the network.

The crops and the OLED mask (flood-fill seeds, erased areas, speck limits) are pixel
positions in each source image. `PIXELS` in the script holds each image's ImageMagick
pixel signature (`magick identify -format %#`), and the script stops if a download no
longer matches. If a museum really changes an image, recheck its crop and, for the
restored Great Wave, the mask, then update its signature.

Two KDE details the generator relies on:

- KWin lists Aurorae themes in System Settings only when they have a `metadata.desktop`,
  and lists SVG themes under the `org.kde.kwin.aurorae.v2` plugin. The global theme sets
  that plugin; with the older `org.kde.kwin.aurorae` the decoration still draws, but
  System Settings does not show it as selected.

To try a change, run `./install.sh` and apply the result with `plasma-apply-colorscheme`, `plasma-apply-desktoptheme` or
`plasma-apply-lookandfeel`. Check Dolphin, System Settings, the panel, a popup and
a tooltip.

Screenshots in `assets/` are real desktop captures. Take one per variant with
comparable content, then build the showcase and social preview with
`scripts/finish-previews.sh` from the .github repository. See the
[preview standard](https://github.com/kanagawa-community/.github/blob/main/docs/PREVIEWS.md).

## Pull requests

- Keep each pull request to one change, and include a screenshot of each variant
  it affects.
- Update the README when installation or usage changes.
