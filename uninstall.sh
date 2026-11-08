#!/usr/bin/env bash
# Remove what install.sh installs. Takes the same arguments: all (default), wave, dragon, lotus.
exec "$(dirname "${BASH_SOURCE[0]}")/install.sh" --uninstall "$@"
