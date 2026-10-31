# Changelog

## Unreleased

- Omarchy, in Persian: the "On this day" header and years sit on the right,
  where the text starts, instead of the year running into its title.
- New screenshots, with the Hijri date and "On this day".

## 2.1.0 (2026-10-31)

Occasions no longer need a file per year.

- **Every list is keyed by its own calendar**, so it holds for any year: solar
  occasions by the Jalali date, international ones by the Gregorian date
  (before, one near a month boundary could go missing in some years), and
  lunar ones by the Hijri date.
- **Hijri months as Iran kept them.** `events/hijri-months.json` records the
  day each month began, from time.ir, Esfand 1394 to Esfand 1406. Lunar
  occasions are placed by it; a day outside it shows no lunar occasions
  rather than a guessed one. "The 30th" of a lunar month is its last day.
- **Holidays match time.ir** for every day from 1395 to 1406. Added 30 Esfand
  in leap years, and the occasions the lists were missing: World Poetry Day,
  World Water Day, World Health Day and others in Farvardin; National
  Mountaineering Day; Sattar Khan's birthday; Physical Education Day moved to
  26 Mehr.
- **On this day**: about 700 births, deaths and events from time.ir, with
  English titles, in the Waybar tooltip (`--on-this-day N`), the Omarchy panel
  (`onThisDay`) and a new `jalali-calendar on-this-day [DATE]` command. The
  year is shown in the reader's calendar.
- **The Hijri date** beside the Gregorian one, for every day the table covers.
- **Weekly sync with time.ir**: a GitHub Action runs `bin/fetch-events`, now
  Python, and opens a pull request when a Hijri month moves, a holiday is
  declared, or time.ir lists something new.
- `events/once.json` holds anything that happens on one date only.
- **Sturdier with hand-edited data**: a missing, broken or oddly shaped events
  file costs the affected days their occasions, never the grid or the bar
  label; the Waybar module always prints a label. Everything runs offline;
  only `bin/fetch-events` uses the network, and it changes no file when it
  can't reach time.ir.

## 2.0.1 (2026-10-30)

- Security: the month-scroll state no longer falls back to a world-writable
  `/tmp` when `XDG_RUNTIME_DIR` is unset, where another user could plant a
  symlink; it uses a private (0700) folder in `~/.cache` instead.

## 2.0.0 (2026-10-30)

Jalali Calendar is no longer tied to one desktop.

- **Waybar front end** for Hyprland, Sway, niri, river and other wlroots
  compositors: your date label, and a tooltip with the month, Fridays and
  holidays in red, today marked, and today's occasions; scroll through
  months, click to come back.
- **A terminal command**, `jalali-calendar`: `today`, `date FORMAT`,
  `convert`, and a `cal`-style `month`.
- **A Python core**, `lib/jalali.py`, checked against the JavaScript one
  (`lib/Model.js`) for every day from 1300 to 1500, formatted dates in both
  languages, and every month grid with its holidays.
- The Omarchy widget moved to `omarchy/`; `install.sh` picks the front end
  for your desktop (`--waybar` to choose) and works on any distribution.

Upgrading on Omarchy needs nothing: `install.sh` or `git pull` as before.

## 1.2.0 (2026-10-30)

- The repository is now `AryanHamedani/jalali-calendar` (the old address
  redirects).

## 1.1.1 (2026-10-30)

- Fixed: a dependency check piped into `grep -q` could misfire under
  `pipefail` and redo work that was already done.

## 1.1.0 (2026-10-30)

- One-command install and update (`install.sh`), with the Vazirmatn font for
  Persian mode and an optional `--replace-clock` that takes the stock clock's
  slot, settings and center anchor.
- The popup clips only when it has to scroll: at fractional display scales
  Qt's clip shaved the left border off cells on the grid's edge.

## 1.0.0 (2026-10-30)

First public release.

- Bar label on the Jalali calendar, with Qt-style format tokens, a
  right-click format ring and a seconds token that only ticks when shown.
- Month grid starting on Saturday, Gregorian day in each cell, Jalali week
  numbers, Fridays and official holidays in the theme's urgent color.
- Iran's official holidays and occasions, lunar ones included, for
  1404–1406, plus solar national and international occasions for every year.
- English by default; Persian, right to left with Persian digits, as a
  setting.
- Year progress rail, and an optional memento mori rail from your birth year.
- Keyboard: arrows and `[` `]` `{` `}` step months and years, `T` goes home,
  `W` flips the week start.
