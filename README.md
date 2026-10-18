# Dragon: Fedora + niri + Noctalia

A glass-look desktop in the style of the Nava OS videos: frosted floating bar and dock, a purple and red palette with light and dark modes, a command bar, a pull-down control center, and an AI section in the top bar.

## Install

```
tar xzf dragon.tar.gz && cd dragon
./install.sh            # add --no-cosmic / --no-claude / --no-dm to skip parts; --grub for the boot menu
reboot                  # choose "Niri" at the login screen
```

Existing `~/.config/{niri,noctalia,kitty}` are moved to `*.bak-<timestamp>` first.
Your old configs can be merged back in afterwards; start with the `.bak` folders.

## Keys

| Key | Action |
|---|---|
| Super+L | Lock (swaylock over a frosted screenshot) |
| Super+Space | Command bar |
| Super+S | Control center |
| Super+Shift+T | Toggle light/dark |
| Super+Shift+C | Claude Code (floating terminal) |
| Super+Shift+A | Antigravity |
| Super+N / Super+E | Notepad (COSMIC Edit) / Files (COSMIC Files) |
| Print / Super+Shift+S | Noctalia region screenshot / COSMIC Screenshot |
| Super+Shift+/ | Full key list |

In the bar, the AI section is `[ Claude ][ Antigravity ]`. Left click opens it; right click on Claude continues the last session, and right click on Antigravity opens its terminal agent (`agy`).

## How light/dark works

`~/.config/noctalia/palettes/Dragon.json` holds both palettes (purple primary, red secondary). Switching mode (Super+Shift+T, the bar button, or `noctalia msg theme-mode-set auto`) re-renders:
- the swaylock colours, kitty colours and niri focus-ring colours (templates in `noctalia/templates/`);
- the wallpaper (`dragon-light.jpg` / `-dark.jpg`);
- GTK and COSMIC dark mode (`dragon-sync-theme`).

Change the accents by editing `mPrimary` (purple) and `mSecondary` (red) in the palette file. It hot-reloads.

## Things I could not test (no Fedora/niri/Noctalia in my sandbox)

Run these on first boot and send me any errors:
1. `niri validate` and `noctalia config validate`. The install script runs both.
2. Bar widget names and the custom buttons come from the Noctalia v5 docs, but I could not run them. If the AI buttons are missing, `noctalia msg settings-open bar` will show valid names.
3. `custom_button` colours (`color = "secondary"`) are my guess at the value format. A warning there is harmless.
4. COSMIC apps follow dark mode only on a best-effort basis (`is_dark` file plus the GTK setting).
5. `cosmic-screenshot` may show another portal's UI under niri. Print (Noctalia's own screenshot) is the reliable one.
6. Noctalia's own lock screen is still reachable from the session menu as a fallback. Super+L, idle and sleep all use swaylock.

## GRUB theme + Windows 11 (optional, off by default)

A frosted dark boot menu in the same purple and red, with Windows 11 in the list. It is dark-only, because a bootloader can't follow the desktop light/dark switch.

```
./install.sh --grub-dry-run     # shows exactly what would change, touches nothing
./install.sh --grub             # or:  sudo ./grub/install-grub.sh
sudo ./grub/install-grub.sh --uninstall   # removes the theme and its settings
```

What it does, and why it is safe to try:
- **Refuses to run** if Fedora booted in legacy/BIOS mode (GRUB can't boot Windows 11 from there), if `/boot/efi` isn't mounted, or if it isn't Fedora.
- **Backs up** `/etc/default/grub`, `grub.cfg` and your UEFI boot entries to `/root/dragon-grub-backup-<time>/`.
- **Edits one marked block** in `/etc/default/grub`, which `--uninstall` removes exactly.
- **Builds the new `grub.cfg` to a temporary file**, checks it with GRUB's own syntax checker, and only then replaces the real one.
- **Finds Windows** with os-prober. If that misses it, it finds the Windows EFI partition by UUID and adds a direct entry instead.
- **Prints the command** to put Fedora first in the UEFI boot order (it does not change the order itself).

Known problems it warns about:
- **Secure Boot on Fedora 44:** Windows failed to start from GRUB until `shim` reached 16.1-7. Run `sudo dnf upgrade --refresh` first. The script checks.
- **BitLocker:** Windows 11 may be encrypted without you having turned it on. Have your recovery key ready (account.microsoft.com/devices/recoverykey) before the first reboot.
- **Windows Update** can put itself first in the boot order again. Re-run the `efibootmgr -o ...` line the script prints.
- **Fast Startup** must be off in Windows, and the clocks disagree (`sudo timedatectl set-local-rtc 1 --adjust-system-clock` fixes it).

Tested here: the theme rendered in a UEFI emulator, the config edits, the generated Windows entry, and the shell code. **Not tested:** the script against a real Fedora + Windows disk. Keep a Fedora live USB nearby the first time.

To change the design: edit `tools/gen-grub-theme.py` and run it (needs Pillow, numpy, `grub-mkfont` and the Inter font). The theme font is Inter (SIL OFL).

## Antigravity

`optional/install-antigravity.sh` uses the only Fedora route I found: a community-documented RPM repo with **no signature check** that lags behind the current 2.x app. Check Google's download page first.
