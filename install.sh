#!/bin/bash

# Install or update the Jalali calendar for the Omarchy bar.
#
#   curl -fsSL https://raw.githubusercontent.com/AryanHamedani/jalali-calendar/main/install.sh | bash
#   ... | bash -s -- --replace-clock    # also take the stock clock's place
#
# Safe to run again: it updates the plugin and fixes whatever is missing.

set -euo pipefail

ID=io.github.aryanhamedani.jalali-calendar
REPO=https://github.com/AryanHamedani/jalali-calendar
DIR="$HOME/.config/omarchy/plugins/$ID"
SHELL_JSON="$HOME/.config/omarchy/shell.json"
replace_clock=0

step() { printf '\033[1m==>\033[0m %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

for arg in "$@"; do
  case $arg in
  --replace-clock) replace_clock=1 ;;
  *) die "unknown option: $arg" ;;
  esac
done

command -v omarchy >/dev/null || die "this plugin needs Omarchy 4 (https://omarchy.org): it runs inside the Omarchy shell"
for cmd in git jq; do
  command -v "$cmd" >/dev/null || sudo pacman -S --needed --noconfirm "$cmd"
done

if [[ -d $DIR/.git ]]; then
  step "Updating the plugin"
  git -C "$DIR" pull --ff-only --quiet
elif [[ -e $DIR ]]; then
  die "$DIR exists but is not a git checkout; move it away and run this again"
else
  step "Adding the plugin"
  omarchy plugin add "$REPO" --enable --yes
fi
omarchy plugin enable "$ID" >/dev/null 2>&1 || true

# Persian mode needs a face with the script; the bar's monospace has none.
if ! fc-list : family | grep -i vazirmatn >/dev/null; then
  step "Installing the Vazirmatn font, for Persian mode"
  omarchy pkg aur add vazirmatn-fonts || note "Could not install vazirmatn-fonts; set fontFamily to any Persian font instead"
fi

in_bar() { jq -e --arg id "$1" '[.bar.layout[]?[]? | .id] | index($id)' "$SHELL_JSON" >/dev/null 2>&1; }

if ((replace_clock)) && in_bar omarchy.clock; then
  step "Replacing the stock clock"
  cp "$SHELL_JSON" "$SHELL_JSON.bak-$(date +%s)"
  # The clock's slot, its settings and the center anchor all pass to the
  # calendar; its formats are Qt's, which this plugin reads the same way.
  jq --arg id "$ID" '
    def swap: if .id == "omarchy.clock" then .id = $id else . end;
    .bar.layout |= with_entries(.value |= (map(select(.id != $id)) | map(swap)))
    | if .bar.centerAnchor == "omarchy.clock" then .bar.centerAnchor = $id else . end
  ' "$SHELL_JSON" >"$SHELL_JSON.tmp" && mv "$SHELL_JSON.tmp" "$SHELL_JSON"
elif ! in_bar "$ID"; then
  step "Placing it in the bar, after the clock"
  omarchy bar put "$ID" --after omarchy.clock 2>/dev/null || omarchy bar put "$ID" --section center
fi

step "Done"
if in_bar omarchy.clock && ! ((replace_clock)); then
  note "To take the stock clock's place instead, run this again with --replace-clock"
fi
note "Persian, right to left:  omarchy bar set $ID language fa"
