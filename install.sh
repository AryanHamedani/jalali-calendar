#!/bin/bash

# Install or update Jalali Calendar.
#
#   curl -fsSL https://raw.githubusercontent.com/AryanHamedani/jalali-calendar/main/install.sh | bash
#   … | bash -s -- --replace-clock   on Omarchy, take the stock clock's place
#   … | bash -s -- --waybar          use the Waybar front end even on Omarchy
#
# On Omarchy it installs the shell widget; anywhere else, the jalali-calendar
# command and a Waybar module. Safe to run again: it updates and fixes
# whatever is missing.

set -euo pipefail

# Everything runs from main, called on the last line: under `curl | bash` a
# download cut short runs nothing, and no child can read the script as input.
main() {

REPO=https://github.com/AryanHamedani/jalali-calendar
OMARCHY_ID=io.github.aryanhamedani.jalali-calendar

step() { printf '\033[1m==>\033[0m %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

front=auto
replace_clock=0
for arg in "$@"; do
  case $arg in
  --replace-clock) replace_clock=1 ;;
  --waybar) front=waybar ;;
  *) die "unknown option: $arg" ;;
  esac
done
if [[ $front == auto ]]; then
  if command -v omarchy >/dev/null && [[ -d $HOME/.config/omarchy ]]; then front=omarchy; else front=waybar; fi
fi

apt_ready=0
pkg_install() {
  if command -v pacman >/dev/null; then sudo pacman -S --needed --noconfirm "$@"
  elif command -v apt-get >/dev/null; then { ((apt_ready)) || sudo apt-get update; } && apt_ready=1 && sudo apt-get install -y "$@"
  elif command -v dnf >/dev/null; then sudo dnf install -y "$@"
  elif command -v zypper >/dev/null; then sudo zypper -n install "$@"
  else return 1; fi
}

needs=(git)
[[ $front == omarchy ]] && needs+=(jq)
for cmd in "${needs[@]}"; do
  command -v "$cmd" >/dev/null || pkg_install "$cmd" || die "install $cmd, then run this again"
done

checkout() {
  if [[ -d $1/.git ]]; then
    step "Updating $1"
    git -C "$1" pull --ff-only --quiet
  elif [[ -e $1 ]]; then
    die "$1 exists but is not a git checkout; move it away and run this again"
  else
    step "Cloning into $1"
    git clone --quiet "$REPO" "$1"
  fi
}

# Persian mode needs a face with the script. Best effort: the calendar works
# without it, and English mode never needs it.
if ! fc-list : family | grep -i vazirmatn >/dev/null; then
  step "Installing the Vazirmatn font, for Persian mode"
  if command -v omarchy >/dev/null; then omarchy pkg aur add vazirmatn-fonts || true
  elif command -v pacman >/dev/null; then
    if command -v yay >/dev/null; then yay -S --needed --noconfirm vazirmatn-fonts || true
    elif command -v paru >/dev/null; then paru -S --needed --noconfirm vazirmatn-fonts || true
    else note "Install vazirmatn-fonts from the AUR for Persian mode"; fi
  elif command -v apt-get >/dev/null; then pkg_install fonts-vazirmatn || true
  elif command -v dnf >/dev/null; then sudo dnf install -y vazirmatn-fonts || true
  else note "Install the Vazirmatn font for Persian mode"; fi
fi

in_bar() { jq -e --arg id "$1" '[.bar.layout[]?[]? | .id] | index($id)' "$HOME/.config/omarchy/shell.json" >/dev/null 2>&1; }

if [[ $front == omarchy ]]; then
  dir="$HOME/.config/omarchy/plugins/$OMARCHY_ID"
  if [[ -d $dir/.git ]]; then
    checkout "$dir"
  else
    [[ ! -e $dir ]] || die "$dir exists but is not a git checkout; move it away and run this again"
    step "Adding the Omarchy shell widget"
    omarchy plugin add "$REPO" --enable --yes
  fi
  omarchy plugin enable "$OMARCHY_ID" >/dev/null 2>&1 || true

  shell_json="$HOME/.config/omarchy/shell.json"
  if ((replace_clock)) && in_bar omarchy.clock; then
    step "Replacing the stock clock"
    cp "$shell_json" "$shell_json.bak-$(date +%s)"
    # The clock's slot, its settings and the center anchor pass to the
    # calendar; its formats are Qt's, which this widget reads the same way.
    jq --arg id "$OMARCHY_ID" '
      def swap: if .id == "omarchy.clock" then .id = $id else . end;
      .bar.layout |= with_entries(.value |= (map(select(.id != $id)) | map(swap)))
      | if .bar.centerAnchor == "omarchy.clock" then .bar.centerAnchor = $id else . end
    ' "$shell_json" >"$shell_json.tmp" && mv "$shell_json.tmp" "$shell_json"
  elif ! in_bar "$OMARCHY_ID"; then
    step "Placing it in the bar, after the clock"
    omarchy bar put "$OMARCHY_ID" --after omarchy.clock 2>/dev/null || omarchy bar put "$OMARCHY_ID" --section center
  fi
  step "Done"
  if in_bar omarchy.clock; then
    note "To take the stock clock's place, run this again with --replace-clock"
  fi
  note "Persian, right to left:  omarchy bar set $OMARCHY_ID language fa"
  exit 0
fi

command -v python3 >/dev/null || pkg_install python3 || pkg_install python || die "install python3, then run this again"
dir="${XDG_DATA_HOME:-$HOME/.local/share}/jalali-calendar"
checkout "$dir"
step "Linking the jalali-calendar command into ~/.local/bin"
mkdir -p "$HOME/.local/bin"
ln -sfn "$dir/bin/jalali-calendar" "$HOME/.local/bin/jalali-calendar"

waybar="${XDG_CONFIG_HOME:-$HOME/.config}/waybar"
step "Adding the Waybar module to $waybar"
mkdir -p "$waybar"
# A bar started by the compositor may not have ~/.local/bin on its PATH.
sed "s#\"jalali-calendar #\"$HOME/.local/bin/jalali-calendar #g" "$dir/waybar/module.jsonc" >"$waybar/jalali-calendar.jsonc"
cp "$dir/waybar/style.css" "$waybar/jalali-calendar.css"

step "Done: $("$dir/bin/jalali-calendar")"
cat <<EOF

To show it, add two lines to your Waybar config (~/.config/waybar/config.jsonc),
with "custom/jalali" where your clock was:

    "include": ["~/.config/waybar/jalali-calendar.jsonc"],
    "modules-center": ["custom/jalali"],

and one to the top of ~/.config/waybar/style.css:

    @import "jalali-calendar.css";

then restart Waybar. In a terminal, try: jalali-calendar month
EOF
}

main "$@"
