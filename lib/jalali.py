"""Jalali (Persian) calendar math, formatting and occasions.

A line-for-line port of Model.js, which the Omarchy front end loads; the two
are checked against each other for every day from 1300 to 1500
(tests/test_jalali.py). Change one, change the other.

Months are 0-based, like Model.js and JavaScript's Date: a Jalali date is
(year, month, day) with Farvardin as month 0.
"""
from datetime import date
import json
import math
from pathlib import Path
import re

# ---- Conversion: the break-table algorithm of jalaali-js (MIT), accurate for
#      years -61 to 3177.
BREAKS = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
          1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178]


def div(a, b):
    """Integer division truncating toward zero, like JavaScript's ~~(a / b)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def mod(a, b):
    return a - div(a, b) * b


def jal_cal(jy):
    gy = jy + 621
    leap_j = -14
    jp = BREAKS[0]
    jump = 0
    for jm in BREAKS[1:]:
        jump = jm - jp
        if jy < jm:
            break
        leap_j += div(jump, 33) * 8 + div(mod(jump, 33), 4)
        jp = jm
    n = jy - jp
    leap_j += div(n, 33) * 8 + div(mod(n, 33) + 3, 4)
    if mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1
    leap_g = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if jump - n < 6:
        n = n - jump + div(jump + 4, 33) * 33
    leap = mod(mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, gy, march


def g2d(gy, gm, gd):
    """Julian day number of a Gregorian date, month 1-based."""
    d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4) + div(153 * mod(gm + 9, 12) + 2, 5) + gd - 34840408
    return d - div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) + 752


def d2g(jdn):
    """(year, month 0-based, day) of a Julian day number."""
    j = 4 * jdn + 139361631
    j = j + div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = div(mod(j, 1461), 4) * 5 + 308
    gd = div(mod(i, 153), 5) + 1
    gm = mod(div(i, 153), 12) + 1
    gy = div(j, 1461) - 100100 + div(8 - gm, 6)
    return gy, gm - 1, gd


def is_leap_year(jy):
    return jal_cal(jy)[0] == 0


def month_length(jy, jm):
    if jm < 6:
        return 31
    if jm < 11:
        return 30
    return 30 if is_leap_year(jy) else 29


def days_in_year(jy):
    return 366 if is_leap_year(jy) else 365


def jalali_to_jdn(jy, jm, jd):
    _, gy, march = jal_cal(jy)
    offset = jm * 31 if jm < 6 else 186 + (jm - 6) * 30
    return g2d(gy, 3, march) + offset + jd - 1


def jdn_to_jalali(jdn):
    gy = d2g(jdn)[0]
    jy = gy - 621
    leap, _, march = jal_cal(jy)
    k = jdn - g2d(gy, 3, march)
    if k >= 0:
        if k <= 185:
            return jy, div(k, 31), mod(k, 31) + 1
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    return jy, 6 + div(k, 30), mod(k, 30) + 1


def to_jalali(gy, gm, gd):
    """Gregorian (year, month 0-based, day) to Jalali."""
    return jdn_to_jalali(g2d(gy, gm + 1, gd))


def to_gregorian(jy, jm, jd):
    return d2g(jalali_to_jdn(jy, jm, jd))


def jalali_for(day):
    return to_jalali(day.year, day.month - 1, day.day)


def weekday_of_jdn(jdn):
    """JavaScript's getDay(): Sunday 0 … Saturday 6. JDN 0 was a Monday."""
    return (jdn + 1) % 7


# ---- Names: English as printed on bilingual Iranian calendars, and Persian.
MONTHS = {
    'fa': ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
           'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'],
    'en': ['Farvardin', 'Ordibehesht', 'Khordad', 'Tir', 'Mordad', 'Shahrivar',
           'Mehr', 'Aban', 'Azar', 'Dey', 'Bahman', 'Esfand'],
}
WEEKDAYS = {
    'fa': ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه'],
    'en': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
}
WEEKDAY_SHORT = {
    'fa': ['ی', 'د', 'س', 'چ', 'پ', 'ج', 'ش'],
    'en': ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'],
}
MERIDIEM = {'fa': ['ق.ظ', 'ب.ظ'], 'en': ['AM', 'PM']}
GREGORIAN_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December']


def lang(value):
    return 'fa' if str(value or '').lower() == 'fa' else 'en'


def pad2(n):
    return '%02d' % int(n)


def localize_digits(text, language):
    if lang(language) != 'fa':
        return str(text)
    return re.sub(r'[0-9]', lambda m: chr(0x06F0 + int(m.group())), str(text)).replace('%', '٪')


def short_name(name, language):
    return name[:3] if lang(language) == 'en' else name


# ---- Formatting: Qt's date tokens, naming the Jalali day, month and year.
FORMAT_TOKENS = re.compile(r"'[^']*'|dddd|ddd|dd|d|MMMM|MMM|MM|M|yyyy|yy|HH|H|hh|h|mm|ss|AP|ap")


def format_jalali(moment, fmt, language='en'):
    """`moment` is a datetime; tokens as in the README."""
    language = lang(language)
    jy, jm, jd = jalali_for(moment)
    weekday = (moment.weekday() + 1) % 7
    hours = moment.hour
    hours12 = 12 if hours % 12 == 0 else hours % 12

    def token(match):
        t = match.group()
        if t[0] == "'":
            return t[1:-1] if len(t) > 2 else "'"
        return {
            'dddd': lambda: WEEKDAYS[language][weekday],
            'ddd': lambda: short_name(WEEKDAYS[language][weekday], language),
            'dd': lambda: pad2(jd), 'd': lambda: str(jd),
            'MMMM': lambda: MONTHS[language][jm],
            'MMM': lambda: short_name(MONTHS[language][jm], language),
            'MM': lambda: pad2(jm + 1), 'M': lambda: str(jm + 1),
            'yyyy': lambda: str(jy), 'yy': lambda: pad2(jy % 100),
            'HH': lambda: pad2(hours), 'H': lambda: str(hours),
            'hh': lambda: pad2(hours12), 'h': lambda: str(hours12),
            'mm': lambda: pad2(moment.minute), 'ss': lambda: pad2(moment.second),
            'AP': lambda: MERIDIEM[language][0 if hours < 12 else 1],
            'ap': lambda: MERIDIEM[language][0 if hours < 12 else 1],
        }[t]()
    return localize_digits(FORMAT_TOKENS.sub(token, str(fmt)), language)


def shows_seconds(fmt):
    return 'ss' in re.sub(r"'[^']*'", '', str(fmt))


# ---- Occasions: solar national ones, Gregorian international ones, and
#      time.ir's official list per year (lunar occasions, holiday roster).
def load_events(directory, years=(), english=True):
    directory = Path(directory)

    def read(name):
        try:
            return json.loads((directory / name).read_text())
        except (OSError, ValueError):
            return {}
    events = {'national': read('national.json'), 'international': read('international.json'),
              'years': {}, 'titles': read('en.json') if english else None}
    for year in years:
        data = read('%d.json' % year)
        if data:
            events['years'][str(year)] = data
    return events


def occasions(events, j, g):
    """(holiday, titles) for Jalali j and Gregorian g, both (y, m0, d)."""
    titles, holiday = [], False
    for item in (events.get('national') or {}).get(pad2(j[1] + 1), []):
        if item.get('day') == j[2]:
            titles.append(item['title'])
            holiday = holiday or item.get('holiday') is True
    year = (events.get('years') or {}).get(str(j[0]))
    if year:
        official = year.get(pad2(j[1] + 1) + '-' + pad2(j[2]))
        holiday = bool(official and official.get('holiday'))
        if official:
            titles += official.get('events', [])
    gregorian = '%s %d' % (GREGORIAN_MONTHS[g[1]], g[2])
    for item in (events.get('international') or {}).get(pad2(j[1] + 1), []):
        if item.get('date') == gregorian:
            titles.append(item['title'])
    english = events.get('titles')
    if english:
        titles = [english.get(t, t) for t in titles]
    return holiday, titles


# ---- Weeks and the month grid.
WEEKDAY_KEYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']


def normalized_week_start(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.floor(value + 0.5) % 7  # Math.round, not Python's banker's rounding
    text = str(value if value is not None else '').strip().lower()
    for i, key in enumerate(WEEKDAY_KEYS):
        if text and (key == text or key[:3] == text):
            return i
    return 6


def week_of_year(jy, jm, jd):
    first = jalali_to_jdn(jy, 0, 1)
    leading = (weekday_of_jdn(first) + 1) % 7
    return (jalali_to_jdn(jy, jm, jd) - first + leading) // 7 + 1


def day_cell(jdn, events, today_jdn=None):
    j = jdn_to_jalali(jdn)
    g = d2g(jdn)
    weekday = weekday_of_jdn(jdn)
    holiday, titles = occasions(events, j, g)
    return {'jdn': jdn, 'year': j[0], 'month': j[1], 'day': j[2],
            'gregorian': g, 'weekday': weekday, 'weekend': weekday == 5,
            'holiday': weekday == 5 or holiday, 'occasions': titles, 'today': jdn == today_jdn}


def month_grid(jy, jm, week_start, events, today_jdn=None):
    """Six weeks of seven cells, each week numbered by its Friday."""
    start = normalized_week_start(week_start)
    first = jalali_to_jdn(jy, jm, 1)
    cursor = first - (weekday_of_jdn(first) - start + 7) % 7
    weeks = []
    for _ in range(6):
        days = []
        for _ in range(7):
            cell = day_cell(cursor, events, today_jdn)
            cell['inMonth'] = cell['month'] == jm and cell['year'] == jy
            days.append(cell)
            cursor += 1
        anchor = next((c for c in days if c['weekend']), days[0])
        weeks.append({'week': week_of_year(anchor['year'], anchor['month'], anchor['day']), 'days': days})
    return weeks


def step_month(jy, jm, delta):
    total = jy * 12 + jm + int(delta)
    return total // 12, total % 12


def jdn_of(day):
    return g2d(day.year, day.month, day.day)


def today_jdn():
    return jdn_of(date.today())
