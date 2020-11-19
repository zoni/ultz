import time
import pytz
import datetime as dt
import unittest

import main


def _assert_dt_almost_eq(actual, expected, message=""):
    unittest.TestCase().assertAlmostEqual(
        actual, expected, delta=dt.timedelta(milliseconds=1), msg=message
    )


class TestParseTime(unittest.TestCase):
    def test_HH(self):
        HH = 19
        expected = dt.time(HH)

        user_input = f"{HH:02}"
        parsed = main.parse_time(user_input)
        _assert_dt_almost_eq(parsed, expected)

    def test_HHMM(self):
        HH = 4
        MM = 6
        expected = dt.time(HH, MM)

        user_input = f"{HH:02}:{MM:02}"
        parsed = main.parse_time(user_input)
        _assert_dt_almost_eq(parsed, expected)

    def test_incorrect(self):
        parsed = main.parse_time("89:9")
        self.assertIsNone(parsed)


class TestParseDate(unittest.TestCase):
    def test_mmdd(self):
        mm = 10
        dd = 12
        expected = dt.date(dt.date.today().year, mm, dd)

        user_input = f"{mm:02}-{dd:02}"
        parsed = main.parse_date(user_input)
        _assert_dt_almost_eq(parsed, expected)

    def test_incorrect(self):
        parsed = main.parse_time("9-19")
        self.assertIsNone(parsed)


class TestParseDateTime(unittest.TestCase):
    def test_HHMM(self):
        HH = 14
        MM = 26
        date = dt.date.today()
        time = dt.time(HH, MM)
        expected = dt.datetime.combine(date, time)

        user_input = f"{HH:02}:{MM:02}"
        parsed = main.parse_datetime(user_input)
        _assert_dt_almost_eq(parsed, expected)

    def test_mmdd(self):
        mm = 10
        dd = 12
        date = dt.date(dt.date.today().year, mm, dd)
        time = dt.datetime.now().time()
        expected = dt.datetime.combine(date, time)

        user_input = f"{mm:02}-{dd:02}"
        parsed = main.parse_datetime(user_input)
        _assert_dt_almost_eq(parsed, expected)

    def test_mmddHHmm(self):
        mm = 2
        dd = 28
        HH = 4
        MM = 6
        expected = dt.datetime(dt.date.today().year, mm, dd, HH, MM)

        input_time = f"{mm:02}-{dd:02} {HH:02}:{MM:02}"
        parsed = main.parse_datetime(input_time)
        _assert_dt_almost_eq(parsed, expected)

    def test_incorrect(self):
        parsed = main.parse_datetime("IO:54 ZD-LK")
        self.assertIsNone(parsed)


class TestGetDatetime(unittest.TestCase):
    def test_nodatetime(self):
        when = dt.datetime(1998, 11, 2, 12, 23)
        datetime = main.get_datetime(main.ExprCode.TZ_ONLY, when)
        _assert_dt_almost_eq(datetime, dt.datetime.now())

    def test_date(self):
        when = dt.datetime(1989, 3, 15, 1, 50)
        datetime_at = main.get_datetime(main.ExprCode.TZ_DATEAT, when)
        datetime_in = main.get_datetime(main.ExprCode.TZ_DATEIN, when)
        _assert_dt_almost_eq(datetime_at, when)
        _assert_dt_almost_eq(datetime_in, when)

    def test_err(self):
        when = None
        datetime_at = main.get_datetime(main.ExprCode.TZ_DATEAT, when)
        datetime_in = main.get_datetime(main.ExprCode.TZ_DATEIN, when)
        self.assertIsNone(datetime_at)
        self.assertIsNone(datetime_in)


class TestGetTimezone(unittest.TestCase):
    def test_none(self):
        where = None
        tz = main.get_tz(where)
        self.assertIsNone(tz)

    def test_real(self):
        where = "Asia/Tokyo"
        tz = main.get_tz(where)
        self.assertEqual(tz, pytz.timezone(where))

    def test_wrong(self):
        where = "Hyrule/Cocorico"
        tz = main.get_tz(where)
        self.assertIsNone(tz)


class TestReverseTrip(unittest.TestCase):
    def test_reverse(self):
        tz_there = pytz.timezone("Africa/Dakar")
        datetime_here = dt.datetime(2012, 12, 21, 12, 21)
        datetime_there, tz_here = main.reverse_trip(datetime_here, tz_there)
        self.assertEqual(datetime_there, tz_there.localize(datetime_here))
        self.assertIsNone(tz_here)


class TestProcessing(unittest.TestCase):
    def setUp(self):
        self.expr_err_msg = "Incorrect expression"
        self.date_err_msg = "Incorrect date"
        self.tz_err_msg = "Incorrect timezone"
        self.ok_icon = "images/icon.png"

    def format_datetime(self, datetime):
        return datetime.strftime("%Y-%m-%d %H:%M")

    def format_description_tzonly(self, _, where):
        return f"Time in {where} now"

    def format_description_datein(self, when, where):
        return f'Time in {where}, at {when.strftime("%H:%M")} here'

    def format_description_dateat(self, when, where):
        return f'Time here, in {where} at {when.strftime("%H:%M")}'

    def assert_is_error(self, _, description, icon):
        self.assertEqual(description, "")
        self.assertEqual(icon, "")

    def test_none(self):
        result, description, icon = main.process_input(None)
        self.assert_is_error(result, description, icon)
        self.assertEqual(result, self.expr_err_msg)

    def test_empty(self):
        result, description, icon = main.process_input("")
        self.assert_is_error(result, description, icon)
        self.assertEqual(result, self.expr_err_msg)

    def test_dtin(self):
        mm = 12
        dd = 2
        HH = 12
        MM = 27
        year = dt.date.today().year
        when = dt.datetime(year, mm, dd, HH, MM)
        where = "Pacific/Chatham"
        expression = f"{mm:02}-{dd:02} {HH:02}:{MM:02} in {where}"

        result, description, icon = main.process_input(expression)

        expected_datetime = when.astimezone(pytz.timezone(where))

        print(description)
        print(result)

        self.assertEqual(result, self.format_datetime(expected_datetime))
        self.assertEqual(description, self.format_description_datein(when, where))
        self.assertEqual(icon, self.ok_icon)

    def test_dtat(self):
        mm = 1
        dd = 12
        HH = 21
        MM = 17
        year = dt.date.today().year
        when = dt.datetime(year, mm, dd, HH, MM)
        where = "Pacific/Chatham"
        expression = f"{where} at {mm:02}-{dd:02} {HH:02}:{MM:02}"

        result, description, icon = main.process_input(expression)

        tz = pytz.timezone(where)
        expected_datetime = tz.localize(when).astimezone(None)

        self.assertEqual(result, self.format_datetime(expected_datetime))
        self.assertEqual(description, self.format_description_dateat(when, where))
        self.assertEqual(icon, self.ok_icon)

    def test_tz(self):
        where = "Asia/Istanbul"
        result, description, icon = main.process_input(where)
        expected_datetime = dt.datetime.now().astimezone(pytz.timezone(where))
        self.assertEqual(result, self.format_datetime(expected_datetime))
        self.assertEqual(
            description, self.format_description_tzonly(expected_datetime, where)
        )
        self.assertEqual(icon, self.ok_icon)

    def test_wrong_dt(self):
        expression = "25:89 in Europe/Paris"
        result, description, icon = main.process_input(expression)
        self.assertEqual(result, self.date_err_msg)
        self.assert_is_error(result, description, icon)

    def test_wrong_expr(self):
        expression = "12:29 in America/New_York at 01:12"
        result, description, icon = main.process_input(expression)
        self.assertEqual(result, self.expr_err_msg)
        self.assert_is_error(result, description, icon)


if __name__ == "__main__":
    unittest.main()
