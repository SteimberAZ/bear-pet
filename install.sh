#!/usr/bin/env bash
# Installs Bear Pet for the current user and enables it on login.
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
AUTOSTART_DIR="$HOME/.config/autostart"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing dependencies (python3-pyqt6, wmctrl)..."
sudo apt install -y python3-pyqt6 wmctrl

mkdir -p "$BIN_DIR" "$AUTOSTART_DIR"
install -m 755 "$SCRIPT_DIR/bear_pet.py" "$BIN_DIR/bear_pet.py"

cat > "$AUTOSTART_DIR/bear-pet.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Bear Pet
Comment=A pixel-art bear that wanders around your desktop
Exec=sh -c "sleep 6; python3 $BIN_DIR/bear_pet.py"
X-GNOME-Autostart-enabled=true
EOF

echo "Done. Starting Bear Pet..."
nohup python3 "$BIN_DIR/bear_pet.py" > /dev/null 2>&1 &
echo "Bear Pet will also start automatically on your next login."
