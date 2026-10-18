#!/usr/bin/env bash
# Dragon installer for Fedora Everything (44 or newer).
# Run as your normal user (it calls sudo where needed):  ./install.sh
# Options: --no-cosmic  skip COSMIC apps   --no-claude  skip Claude Code   --no-dm  skip SDDM
#          --grub       also install the GRUB theme + Windows 11 detection (see grub/install-grub.sh)
#          --grub-dry-run  only show what --grub would change
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
WP="$HOME/.local/share/wallpapers/dragon"
STAMP="$(date +%Y%m%d-%H%M%S)"
COSMIC=1; CLAUDE=1; DM=1; GRUB=0; GRUB_DRY=0

for a in "$@"; do
    case "$a" in
        --no-cosmic) COSMIC=0 ;;
        --no-claude) CLAUDE=0 ;;
        --no-dm)     DM=0 ;;
        --grub)      GRUB=1 ;;
        --grub-dry-run) GRUB=1; GRUB_DRY=1 ;;
        -h|--help)   sed -n '2,7p' "$0"; exit 0 ;;
        *) echo "Unknown option: $a" >&2; exit 2 ;;
    esac
done

[ "$(id -u)" -ne 0 ] || { echo "Run as your normal user, not root." >&2; exit 1; }

. /etc/os-release
if [ "${ID:-}" != "fedora" ] || [ "${VERSION_ID:-0}" -lt 44 ]; then
    echo "This is written for Fedora 44+ (Noctalia v5 is in the default repos from 44)." >&2
    echo "Detected: ${PRETTY_NAME:-unknown}. Continue anyway? [y/N]" >&2
    read -r ans; [ "$ans" = "y" ] || exit 1
fi

say() { printf '\n\033[1;35m==> %s\033[0m\n' "$*"; }

# ───────────────────────── 1. Packages ─────────────────────────
say "Installing the desktop (niri + Noctalia) and tools"
sudo dnf install -y --skip-unavailable \
    niri noctalia kitty \
    swaylock swayidle grim jq ImageMagick libnotify \
    xdg-desktop-portal-gnome xdg-desktop-portal-gtk gnome-keyring polkit \
    NetworkManager bluez upower power-profiles-daemon \
    pipewire pipewire-pulseaudio wireplumber \
    rsms-inter-fonts jetbrains-mono-fonts google-noto-emoji-fonts \
    firefox git curl

if [ "$DM" -eq 1 ]; then
    say "Installing SDDM login screen"
    sudo dnf install -y sddm
    sudo systemctl enable sddm
    sudo systemctl set-default graphical.target
fi
sudo systemctl enable --now NetworkManager bluetooth power-profiles-daemon 2>/dev/null || true

if [ "$COSMIC" -eq 1 ]; then
    say "Installing COSMIC apps (Edit = notepad, Files, Player, Store, Terminal, Monitor, Screenshot)"
    sudo dnf install -y --skip-unavailable \
        cosmic-edit cosmic-files cosmic-player cosmic-store \
        cosmic-term cosmic-monitor cosmic-screenshot
fi

# ───────────────────────── 2. Claude Code (signed Anthropic repo) ─────────────────────────
if [ "$CLAUDE" -eq 1 ]; then
    say "Installing Claude Code from Anthropic's signed dnf repo"
    want="31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE"
    tmp="$(mktemp -d)"
    curl -fsSL https://downloads.claude.ai/keys/claude-code.asc -o "$tmp/claude-code.asc"
    got="$(gpg --show-keys --with-colons "$tmp/claude-code.asc" | awk -F: '$1=="fpr"{print $10; exit}')"
    if [ "$got" != "$want" ]; then
        echo "Claude Code signing key fingerprint mismatch ($got). Aborting this step." >&2
        rm -rf "$tmp"
    else
        sudo rpm --import "$tmp/claude-code.asc"
        rm -rf "$tmp"
        sudo tee /etc/yum.repos.d/claude-code.repo >/dev/null <<'EOF'
[claude-code]
name=Claude Code
baseurl=https://downloads.claude.ai/claude-code/rpm/stable
enabled=1
gpgcheck=1
gpgkey=https://downloads.claude.ai/keys/claude-code.asc
EOF
        sudo dnf install -y claude-code
    fi
fi

# ───────────────────────── 3. Scripts ─────────────────────────
say "Installing helper scripts to /usr/local/bin"
sudo install -m 0755 "$HERE"/bin/glass-lock "$HERE"/bin/ai-claude "$HERE"/bin/ai-antigravity \
    "$HERE"/bin/dragon-sync-theme /usr/local/bin/

# ───────────────────────── 4. Config (with backup) ─────────────────────────
say "Installing config (existing niri/noctalia/kitty configs are backed up first)"
for d in niri noctalia kitty; do
    if [ -e "$CFG/$d" ]; then
        mv "$CFG/$d" "$CFG/$d.bak-$STAMP"
        echo "  backed up $CFG/$d -> $CFG/$d.bak-$STAMP"
    fi
done
mkdir -p "$CFG" "$CFG/swaylock" "$WP" "$HOME/Pictures/Screenshots"
cp -r "$HERE"/dotfiles/niri "$HERE"/dotfiles/noctalia "$HERE"/dotfiles/kitty "$CFG"/
sed -i "s#@HOME@#$HOME#g" "$CFG/noctalia/config.toml"
cp "$HERE"/wallpapers/*.jpg "$WP"/

# ───────────────────────── 5. GRUB (optional; boot-critical, so only on request) ─────────────────────────
if [ "$GRUB" -eq 1 ]; then
    say "GRUB theme + Windows 11 detection"
    if [ "$GRUB_DRY" -eq 1 ]; then
        sudo "$HERE/grub/install-grub.sh" --dry-run
    else
        sudo "$HERE/grub/install-grub.sh"
    fi
fi

# ───────────────────────── 6. Check ─────────────────────────
say "Checking the configs"
command -v niri >/dev/null && { niri validate && echo "niri config OK"; } || true
command -v noctalia >/dev/null && { noctalia config validate && echo "noctalia config OK"; } || true

cat <<EOF

Done. Next:
  1. Reboot (or log out), pick "Niri" at the login screen.
  2. First login: it applies the theme and wallpaper by itself. If swaylock or kitty look unthemed,
     run once:  noctalia msg templates-apply
  3. Sign in to Claude Code:  claude        (or click the Claude button in the bar)
  4. Antigravity is optional:  ./optional/install-antigravity.sh
Keys: Super+L lock, Super+Space command bar, Super+S control center, Super+Shift+T light/dark,
      Super+Shift+C Claude Code, Super+Shift+A Antigravity, Super+N notepad, Super+E files.
EOF
