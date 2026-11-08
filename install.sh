#!/usr/bin/env bash
# Install the Kanagawa themes for KDE Plasma: every variant, or only the ones named.
# ./uninstall.sh takes the same arguments and removes them again.
#
# Usage: ./install.sh [all|wave|dragon|lotus ...]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
cap() { case "$1" in wave) echo Wave ;; dragon) echo Dragon ;; lotus) echo Lotus ;; esac; }
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
# The global theme selects the Kanagawa cursors and icons, so their ports come along, with
# Konsole and Kate. Each runs its own install.sh with the same variants.
PORTS="cursors icons konsole kate"
port() {
  local p="$1"
  shift
  # A sibling checkout of the port, as in the organization's workspace, wins over a clone.
  if [[ -x "../$p/install.sh" ]] && git -C "../$p" remote get-url origin 2>/dev/null | grep -q "kanagawa-community/$p"; then
    "../$p/install.sh" "$@"
    return
  fi
  # Only the themes are needed, and uninstalling needs none: skip the port's sources.
  git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/kanagawa-community/$p" "$tmp/$p"
  [[ "${1:-}" == --uninstall ]] || git -C "$tmp/$p" sparse-checkout set themes
  "$tmp/$p/install.sh" "$@"
}
after() {
  local p variants="${selected/ shared/}"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  for p in $PORTS; do
    echo "$p:"
    # shellcheck disable=SC2086 # word-split the variant list on purpose
    if [[ "$uninstall" == true ]]; then port "$p" --uninstall $variants; else port "$p" $variants; fi
  done
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
