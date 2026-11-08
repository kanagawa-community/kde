#!/usr/bin/env bash
# Remove what install.sh installed.
exec "$(dirname "${BASH_SOURCE[0]}")/install.sh" --uninstall
