# Changelog

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
