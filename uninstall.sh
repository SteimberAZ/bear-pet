#!/usr/bin/env bash
# Removes Bear Pet and its autostart entry. Dependencies are left installed.
set -euo pipefail

pkill -f bear_pet.py || true
rm -f "$HOME/.local/bin/bear_pet.py" "$HOME/.config/autostart/bear-pet.desktop"
echo "Bear Pet removed."
