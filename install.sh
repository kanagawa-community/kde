#!/usr/bin/env bash
# Install the Kanagawa color schemes, Plasma styles, window decorations, global themes
# and wallpapers for the current user. `--uninstall` removes exactly what this installs.
# The SilentSDDM login preset needs root and stays a manual step (see the README).
#
# Usage: ./install.sh [--uninstall]
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
# repository folder -> folder under $data
parts=(
  "color-schemes:color-schemes"
  "desktoptheme:plasma/desktoptheme"
  "look-and-feel:plasma/look-and-feel"
  "aurorae:aurorae/themes"
  "wallpapers:wallpapers"
)

case "${1:-}" in
  "") uninstall=false ;;
  --uninstall) uninstall=true ;;
  *) echo "usage: $0 [--uninstall]" >&2; exit 2 ;;
esac

for part in "${parts[@]}"; do
  src="${part%%:*}" dest="$data/${part#*:}"
  mkdir -p "$dest"
  for item in "$src"/*; do
    name="$(basename "$item")"
    # Remove first, so files dropped from the repository do not linger.
    rm -rf "${dest:?}/$name"
    if [[ "$uninstall" == false ]]; then
      cp -r "$item" "$dest/"
    fi
  done
  echo "$([[ "$uninstall" == true ]] && echo removed || echo installed) $src in $dest"
done

if [[ "$uninstall" == false ]]; then
  echo "Apply a variant with: plasma-apply-lookandfeel -a org.kanagawa-community.wave"
else
  echo "If a Kanagawa theme was active, pick another one in System Settings."
fi
