#!/usr/bin/env bash
# Install the Kanagawa themes for KDE Plasma: every variant, or only the ones named.
# ./uninstall.sh takes the same arguments and removes them again.
#
# Usage: ./install.sh [all|wave|dragon|lotus ...]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
cap() { case "$1" in wave) echo Wave ;; dragon) echo Dragon ;; lotus) echo Lotus ;; esac; }
# The SilentSDDM login preset needs root and stays a manual step (see the README).
# Print "<file in this repository>\t<folder it goes in>" for one variant.
items() {
  if [[ "$1" == shared ]]; then
    for w in wallpapers/hokusai-*; do printf "%s\t%s\n" "$w" "$data/wallpapers"; done
    return
  fi
  printf "color-schemes/Kanagawa%s.colors\t%s\n" "$(cap "$1")" "$data/color-schemes"
  printf "desktoptheme/kanagawa-%s\t%s\n" "$1" "$data/plasma/desktoptheme"
  printf "look-and-feel/org.kanagawa-community.%s\t%s\n" "$1" "$data/plasma/look-and-feel"
  printf "aurorae/kanagawa-%s\t%s\n" "$1" "$data/aurorae/themes"
  for w in wallpapers/kanagawa-"$1"-*; do printf "%s\t%s\n" "$w" "$data/wallpapers"; done
}
after() {
  [[ "$uninstall" == false ]] || return 0
  echo "Apply a variant with: plasma-apply-lookandfeel -a org.kanagawa-community.wave"
}

uninstall=false
if [[ "${1:-}" == --uninstall ]]; then
  uninstall=true
  shift
fi
selected=""
add() { case " $selected " in *" $1 "*) ;; *) selected="$selected $1" ;; esac; }
for arg in "${@:-all}"; do
  case "$arg" in
    all) add wave; add dragon; add lotus ;;
    wave | dragon | lotus) add "$arg" ;;
    *) echo "usage: $0 [all|wave|dragon|lotus ...]" >&2; exit 2 ;;
  esac
done
# The Hokusai prints belong to no variant: install them with any, remove them only with all three.
count() { echo $#; }
# shellcheck disable=SC2086 # word-split the variant list on purpose
if [[ "$uninstall" == false || $(count $selected) -eq 3 ]]; then selected="$selected shared"; fi
for v in $selected; do
  # Remove first, so a reinstall drops files the repository no longer has.
  while IFS=$'\t' read -r src dir; do
    rm -rf "${dir:?}/$(basename "$src")"
    if [[ "$uninstall" == false ]]; then
      mkdir -p "$dir"
      cp -R "$src" "$dir/"
    fi
  done < <(items "$v")
  [[ "$v" == shared ]] && continue
  if [[ "$uninstall" == true ]]; then echo "Removed kanagawa-$v"; else echo "Installed kanagawa-$v"; fi
done
after
