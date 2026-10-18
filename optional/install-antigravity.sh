#!/usr/bin/env bash
# Optional: install Antigravity on Fedora.
#
# Heads-up, read before saying yes:
#  - Google has no signed Fedora repo that I could verify. The community-documented RPM repo
#    below is served with gpgcheck=0 (no signature check) and lags behind (it was at 1.23.2
#    when I checked; the 2.x desktop app ships as a tarball instead).
#  - Check https://antigravity.google/download for the current official Linux instructions first.
set -euo pipefail

echo "This adds an UNSIGNED dnf repo (gpgcheck=0) for Antigravity. Continue? [y/N]"
read -r ans
[ "$ans" = "y" ] || { echo "Cancelled."; exit 0; }

sudo tee /etc/yum.repos.d/antigravity.repo >/dev/null <<'EOF'
[antigravity-rpm]
name=Antigravity RPM Repository
baseurl=https://us-central1-yum.pkg.dev/projects/antigravity-auto-updater-dev/antigravity-rpm
enabled=1
gpgcheck=0
EOF
sudo dnf install -y antigravity
echo "Installed. Launch with: antigravity   (or the Antigravity button in the bar)"
