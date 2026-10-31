"""Run with: python3 -m unittest discover -s tests

The Python port is checked against Model.js itself, run under node, so the
Waybar and terminal front ends can never disagree with the Omarchy one.
"""
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'lib'))
import jalali  # noqa: E402

JS = r'''
const Model = require(process.argv[1] + "/lib/Model.js")
const fs = require("fs")
const read = n => JSON.parse(fs.readFileSync(process.argv[1] + "/events/" + n))
const events = { national: read("national.json"), international: read("international.json"),
  hijri: read("hijri.json"), hijriMonths: Model.hijriMonthTable(read("hijri-months.json")),
  once: read("once.json"), history: read("history.json"), titles: read("en.json") }
const out = { days: [], formats: [], grids: [], history: [] }
for (let jy = 1300; jy <= 1500; jy++)
  for (let jm = 0; jm < 12; jm++)
    for (let jd = 1; jd <= Model.monthLength(jy, jm); jd++) {
      const g = Model.toGregorian(jy, jm, jd)
      out.days.push([jy, jm, jd, g.year, g.month, g.day, Model.isLeapYear(jy) ? 1 : 0])
    }
const fmts = ["dddd d MMMM yyyy HH:mm:ss", "ddd dd/MM/yy h:mm AP", "MMM M 'week' d''", "yyyy-MM-dd"]
for (let i = 0; i < 400; i++) {
  const d = new Date(2010, 0, 1 + i * 37, (i * 7) % 24, (i * 13) % 60, (i * 17) % 60)
  for (const f of fmts) for (const l of ["en", "fa"])
    out.formats.push([d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes(), d.getSeconds(), f, l, Model.formatJalali(d, f, l)])
}
// Every month the Hijri table reaches, and a little past both of its ends.
for (let jy = 1394; jy <= 1408; jy++) for (let jm = 0; jm < 12; jm++) for (const ws of [6, 1])
  out.grids.push([jy, jm, ws, Model.monthGrid(jy, jm, ws, "", events).map(w =>
    [w.week, w.days.map(c => [c.year, c.month, c.day, c.inMonth, c.holiday, c.occasions,
                              c.hijri && [c.hijri.year, c.hijri.month, c.hijri.day, c.hijri.length]])])])
for (let jdn = 2460000; jdn < 2460366; jdn++) {
  const c = Model.dayForDate(new Date(2023, 1, 24 + jdn - 2460000), events)
  for (const l of ["en", "fa"]) out.history.push([c.j, c.g, l, Model.onThisDay(events, c.j, c.g, l).map(e => [e.year, e.title])])
}
process.stdout.write(JSON.stringify(out))
'''


@unittest.skipUnless(shutil.which('node'), 'node is needed to run Model.js')
class MatchesModelJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = json.loads(subprocess.run(['node', '-e', JS, str(ROOT)], capture_output=True,
                                           text=True, check=True).stdout)
        cls.events = jalali.load_events(ROOT / 'events')

    def test_every_day_1300_to_1500(self):
        self.assertGreater(len(self.js['days']), 73000)
        for jy, jm, jd, gy, gm, gd, leap in self.js['days']:
            self.assertEqual(jalali.to_gregorian(jy, jm, jd), (gy, gm, gd))
            self.assertEqual(jalali.to_jalali(gy, gm, gd), (jy, jm, jd))
            self.assertEqual(jalali.is_leap_year(jy), bool(leap))

    def test_formats(self):
        for y, m, d, h, mi, s, fmt, language, expected in self.js['formats']:
            self.assertEqual(jalali.format_jalali(datetime(y, m + 1, d, h, mi, s), fmt, language), expected)

    def test_month_grids_and_occasions(self):
        for jy, jm, ws, weeks in self.js['grids']:
            ours = jalali.month_grid(jy, jm, ws, self.events)
            hijri = lambda h: h and [h['year'], h['month'], h['day'], h['length']]
            self.assertEqual([[w['week'], [[c['year'], c['month'], c['day'], c['inMonth'], c['holiday'], c['occasions'],
                                            hijri(c['hijri'])] for c in w['days']]] for w in ours], weeks, (jy, jm, ws))

    def test_on_this_day(self):
        self.assertEqual(len(self.js['history']), 2 * 366)
        for j, g, language, expected in self.js['history']:
            ours = jalali.on_this_day(self.events, (j['year'], j['month'], j['day']), (g['year'], g['month'], g['day']), language)
            self.assertEqual([list(e) for e in ours], expected, (j, language))


class Basics(unittest.TestCase):
    def test_known_dates(self):
        self.assertEqual(jalali.to_jalali(2026, 2, 21), (1405, 0, 1))   # Nowruz 1405
        self.assertEqual(jalali.to_jalali(2026, 9, 30), (1405, 7, 8))   # 8 Aban 1405
        self.assertTrue(jalali.is_leap_year(1403))
        self.assertEqual(jalali.month_length(1403, 11), 30)

    def test_week_start(self):
        self.assertEqual(jalali.normalized_week_start('mon'), 1)
        self.assertEqual(jalali.normalized_week_start(None), 6)
        self.assertEqual(jalali.normalized_week_start(2.5), 3)

    def test_step_month(self):
        self.assertEqual(jalali.step_month(1405, 11, 1), (1406, 0))
        self.assertEqual(jalali.step_month(1405, 0, -1), (1404, 11))

    def test_holidays_match_time_ir(self):
        """Fridays, the solar list and the lunar list, placed by the Hijri table,
        give every one of time.ir's holidays for twelve years, and no others."""
        fixture = json.loads((ROOT / 'tests/timeir-holidays.json').read_text())
        events = jalali.load_events(ROOT / 'events', english=False)
        first, last = fixture['years']
        ours = []
        for jdn in range(jalali.jalali_to_jdn(first, 0, 1), jalali.jalali_to_jdn(last + 1, 0, 1)):
            cell = jalali.day_cell(jdn, events)
            if cell['holiday'] and not cell['weekend']:
                ours.append('%d-%02d-%02d' % (cell['year'], cell['month'] + 1, cell['day']))
        self.assertEqual(ours, fixture['holidays'])

    def test_every_title_has_english(self):
        events = ROOT / 'events'
        english = json.loads((events / 'en.json').read_text())
        read = lambda name: json.loads((events / name).read_text())
        titles = [item['title'] for name in ('national.json', 'hijri.json') for items in read(name).values() for item in items]
        titles += [title for items in read('international.json').values() for title in items]
        titles += [title for day in read('once.json').values() for title in day.get('events', [])]
        titles += [title for dates in read('history.json').values() for items in dates.values() for _, title in items]
        self.assertEqual([t for t in titles if t not in english], [], 'add these to events/en.json')


def load_cli():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader('jalali_cli', str(ROOT / 'bin/jalali-calendar'))
    spec = importlib.util.spec_from_loader('jalali_cli', loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class Cli(unittest.TestCase):
    cli = load_cli()

    def opts(self, *argv):
        return self.cli.parse_options(list(argv))[1]

    def test_waybar_label_and_tooltip(self):
        import xml.dom.minidom
        out = self.cli.waybar(self.opts(), now=datetime(2026, 10, 30, 14, 5))
        self.assertEqual(out['text'], 'Friday 8 Aban 14:05')
        self.assertEqual(out['class'], ['holiday'])  # a Friday
        self.assertIn('Aban 1405', out['tooltip'])
        self.assertIn("National Rangers' Day", out['tooltip'])
        # Pango markup is XML: it must parse, or Waybar shows nothing.
        xml.dom.minidom.parseString('<markup>%s</markup>' % out['tooltip'])

    def test_waybar_persian(self):
        out = self.cli.waybar(self.opts('--language', 'fa', '--format', 'yyyy/MM/dd'), now=datetime(2026, 10, 30, 9, 0))
        self.assertEqual(out['text'], '۱۴۰۵/۰۸/۰۸')

    def test_label_is_escaped(self):
        out = self.cli.waybar(self.opts('--format', "'R&D <' yyyy"), now=datetime(2026, 10, 30, 9, 0))
        self.assertEqual(out['text'], 'R&amp;D &lt; 1405')

    def test_options(self):
        args, opts = self.cli.parse_options(['waybar', '--language', 'FA', '--week-start', 'monday'])
        self.assertEqual((args, opts['language'], opts['week-start']), (['waybar'], 'fa', 'monday'))

    def test_shift_and_expiry(self):
        import os
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(self.cli, 'OFFSET', Path(tmp) / 'offset'), \
                    mock.patch.object(self.cli.subprocess, 'run'):
                self.cli.shift('+1')
                self.cli.shift('+1')
                self.assertEqual(self.cli.read_offset(), 2)
                os.utime(self.cli.OFFSET, (0, 0))  # long ago: back to today
                self.assertEqual(self.cli.read_offset(), 0)
                self.cli.shift('0')
                self.assertFalse(self.cli.OFFSET.exists())


if __name__ == '__main__':
    unittest.main()
