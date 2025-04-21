import payouts, unittest, time, datetime, re, pytz
from payouts import TimeCell, PayoutDate

figures = [ "15m",
            "42m 27s",
            "2m 15s",
            "8m",
            "21m 2s",
            "48s",
            "11m 7s",
            "1h",
            "1h 13m 5s",
            ""]
TOTAL_SECONDS = 29631

class TestTimeCell(unittest.TestCase):
    def test_minutes(self):
        tc = TimeCell(figures[0])
        self.assertEqual(tc.minutes(), 15)
        tc = TimeCell(figures[1])
        self.assertEqual(tc.minutes(), 42)
        tc = TimeCell(figures[5])
        self.assertEqual(tc.minutes(), 0)

    def test_seconds(self):
        tc = TimeCell(figures[1])
        self.assertEqual(tc.seconds(), 27)
        tc = TimeCell(figures[5])
        self.assertEqual(tc.seconds(), 48)
        tc = TimeCell(figures[0])
        self.assertEqual(tc.seconds(), 0)
        self.assertEqual(tc.total_seconds(), 900)

    def test_total_seconds(self):
        tc = TimeCell(figures[0])
        self.assertEqual(tc.total_seconds(), 900)
        tc = TimeCell(figures[1])
        self.assertEqual(tc.total_seconds(), 2547)
        tc = TimeCell(figures[5])
        self.assertEqual(tc.total_seconds(), 48)
        tc = TimeCell(figures[3])
        self.assertEqual(tc.total_seconds(), 480)

    def test_hours(self):
        tc = TimeCell(figures[7])
        self.assertEqual(tc.hours(), 1)
        tc = TimeCell(figures[8])
        self.assertEqual(tc.hours(), 1)
        self.assertEqual(tc.minutes(), 13)
        self.assertEqual(tc.total_seconds(), 4385)

    def test_empty_string(self):
        tc = TimeCell(figures[9])
        self.assertEqual(tc.hours(), 0)
        self.assertEqual(tc.minutes(), 0)
        self.assertEqual(tc.total_seconds(), 0)

class TestPayoutDate(unittest.TestCase):
    def test_day_label(self):
        current_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
        pd = PayoutDate()
        self.assertEqual(
            pd.mdy(),
            current_time.strftime('%b %-d, %Y'))
        target_date = (1988, 6, 1, 0, 0, 0, 0, 0, 0)
        pd = PayoutDate(target_date = time.strftime('%y%m%d', target_date))
        self.assertEqual(
            pd.mdy(),
            time.strftime('%b %-d, %Y', target_date))

    def test_date_match(self):
        # Simulate working late into the evening, when
        # GMT has advanced to the day after EST
        # 9:30 PM on November 30...
        run_time_tuple = (2024, 11, 30, 21, 30, 0, 0, 0, 0)
        pd = PayoutDate(target_date = time.strftime('%y%m%d', run_time_tuple))
        gmt_tuple =      (2024, 12,  1, 2,  30, 0, 0, 0, 0)
        gmt_date_string = time.strftime('%b %-d, %Y', gmt_tuple)
        self.assertTrue(pd.includes(gmt_date_string))
        # November 26 is also in the test file, but it should
        # not count...
        earlier_tuple =  (2024, 11, 26, 14, 20, 0, 0, 0, 0)
        earlier_date_string = time.strftime('%b %-d, %Y', earlier_tuple)
        self.assertFalse(pd.includes(earlier_date_string))

class TestGlobalFunctions(unittest.TestCase):
    def test_cmdline_without_date(self):
        with self.assertRaises(Exception):
            payouts.payouts_main()
        totaltaskRE = re.compile('.*Total tasks found: [0-9]+.*')
        self.assertRegex(
            payouts.payouts_main(['test_payouts.csv']),
            totaltaskRE)
        missionRE = re.compile('.*Mission tasks found: [0-9]+.*')
        self.assertRegex(
            payouts.payouts_main(['test_payouts.csv']),
            missionRE)

    def test_cmdline_with_date(self):
        totaltaskRE = re.compile('.*Total tasks found: 141.*')
        self.assertRegex(
            payouts.payouts_main(['test_payouts.csv', '241130']),
            totaltaskRE)
        missionRE = re.compile('.*Mission tasks found: 23.*')
        self.assertRegex(
            payouts.payouts_main(['test_payouts.csv', '241130']),
            missionRE)
        timeworkedRE = re.compile(f".*Total time worked: {payouts.to_hhmmss(TOTAL_SECONDS)}.*")
        self.assertRegex(
            payouts.payouts_main(['test_payouts.csv', '241130']),
            timeworkedRE)
        payoutRE = re.compile(r".*Total earnings: \$354\.98.*")
        self.assertRegex(
            payouts.payouts_main(['test_payouts.csv', '241130']),
            payoutRE)

    def test_to_hhmmss(self):
        hhmmssRE = re.compile("8:13:51")
        self.assertRegex(
            payouts.to_hhmmss(TOTAL_SECONDS),
            hhmmssRE)
        withZeroRE = re.compile("1:01:01")
        self.assertRegex(
            payouts.to_hhmmss(3661),
            withZeroRE)
        withZeroMinutesRE = re.compile("1:00:01")
        self.assertRegex(
            payouts.to_hhmmss(3601),
            withZeroMinutesRE)


if __name__ == '__main__':
    unittest.main()
