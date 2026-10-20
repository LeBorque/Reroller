import threading
import unittest

from reroller.domain import RerollError, Target, parse_item
from reroller.demo import sample_with
from reroller.engine import Engine, Timing


class FakeConnection:
    def __init__(self, stop):
        self.stop = stop
        self.time = 0.0
        self.clicks = 0
        self.reads_after_click = 0
        self.result_delay = 0
        self.focus = True
        self.identical = False
        self.bad_clipboard = False
        self.changed_identity = False
        self.changed_fracture = False
        self.currency_delay = 0
        self.currency_reads = 0
        self.no_consumption = False
        self.extra_consumption = False
        self.stop_at_click = False
        self.stop_after_click = False
        self.initial_target = False
        self.never_hit = False
        self.fingerprints_at_click = []
        self.begins = self.ends = self.total_currency_reads = 0

    def guard(self):
        if not self.focus:
            raise RerollError("fokusförlust")

    def wait(self, seconds):
        self.time += seconds

    def read_item(self):
        self.time += 0.01
        if self.clicks:
            self.reads_after_click += 1
        if self.bad_clipboard and self.clicks:
            return parse_item("")
        value = 5 if self.initial_target else 1
        if self.clicks and not self.identical and self.reads_after_click > self.result_delay:
            value = self.clicks + 1 if self.never_hit else 5
        raw = sample_with(f"+{value} to Level of all Melee Skills")
        if self.changed_identity and self.clicks:
            raw = raw.replace("Blight Weaver", "Different Item")
        if self.changed_fracture and self.clicks:
            raw = raw.replace("+4.99(4.41-5)", "+4.98(4.41-5)")
        return parse_item(raw)

    def read_currency(self):
        self.total_currency_reads += 1
        self.time += 0.01
        if self.clicks:
            self.currency_reads += 1
        if self.no_consumption or self.currency_reads <= self.currency_delay:
            return 100
        return 100 - self.clicks - (1 if self.extra_consumption else 0)

    def apply_once(self, before_click):
        if self.stop_at_click:
            self.stop.set()
        before_click()
        self.clicks += 1
        self.reads_after_click = 0
        if self.stop_after_click:
            self.stop.set()

    def begin_repeat(self):
        self.begins += 1

    def end_repeat(self):
        self.ends += 1


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.stop = threading.Event()
        self.fake = FakeConnection(self.stop)
        self.target = Target.create("+# to Level of all Melee Skills", ["5"])
        self.progress = []

    def run_engine(self, budget=20, repeat=False):
        return Engine(self.fake, self.target, budget, self.stop, self.progress.append,
                      Timing(0.04, 0.4, 0.01), lambda: self.fake.time, repeat=repeat).run()

    def test_repeat_budget_and_only_two_stack_reads(self):
        self.fake.never_hit = True
        result = self.run_engine(3, repeat=True)
        self.assertEqual((self.fake.clicks, result.verified), (3, 3))
        self.assertEqual(self.fake.total_currency_reads, 2)
        self.assertEqual((self.fake.begins, self.fake.ends), (1, 1))

    def test_repeat_stops_at_first_hit(self):
        result = self.run_engine(20, repeat=True)
        self.assertTrue(result.matched)
        self.assertEqual(self.fake.clicks, 1)
        self.assertEqual(self.fake.total_currency_reads, 1)
        self.assertEqual(self.fake.ends, 1)

    def test_repeat_identical_result_never_reclicks(self):
        self.fake.identical = True
        result = self.run_engine(20, repeat=True)
        self.assertFalse(result.matched)
        self.assertEqual(self.fake.clicks, 1)
        self.assertEqual(self.fake.ends, 1)

    def test_repeat_stop_always_releases(self):
        self.fake.stop_after_click = True
        self.run_engine(20, repeat=True)
        self.assertEqual((self.fake.clicks, self.fake.ends), (1, 1))

    def test_repeat_caps_applications_to_available_currency(self):
        self.fake.never_hit = True
        self.fake.read_currency = lambda: 2 - self.fake.clicks if self.fake.clicks else 2
        # Represent the depleted stack as zero in this protocol test; Win32 text reading stops conservatively.
        result = self.run_engine(20, repeat=True)
        self.assertEqual((self.fake.clicks, result.verified), (2, 2))
        self.assertIn('Tillgängliga', result.reason)

    def test_repeat_not_used_for_single_orb_budget(self):
        self.fake.never_hit = True
        self.run_engine(1, repeat=True)
        self.assertEqual(self.fake.begins, 0)

    def test_already_matched_no_click(self):
        self.fake.initial_target = True
        result = self.run_engine()
        self.assertTrue(result.matched)
        self.assertEqual((result.attempts, self.fake.clicks), (0, 0))

    def test_hit_no_next_click_or_bookkeeping_input(self):
        result = self.run_engine()
        self.assertTrue(result.matched)
        self.assertEqual(self.fake.clicks, 1)
        self.assertEqual(self.fake.currency_reads, 0)

    def test_fresh_copies_of_old_result_wait(self):
        self.fake.result_delay = 10
        result = self.run_engine()
        self.assertTrue(result.matched)
        self.assertEqual(self.fake.clicks, 1)
        self.assertGreater(self.fake.reads_after_click, 10)

    def test_identical_roll_stops(self):
        self.fake.identical = True
        result = self.run_engine()
        self.assertFalse(result.matched)
        self.assertIn("oförändrat", result.reason)
        self.assertEqual(self.fake.clicks, 1)

    def test_budget_never_exceeded(self):
        self.fake.never_hit = True
        result = self.run_engine(2)
        self.assertEqual(self.fake.clicks, 2)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.verified, 2)
        self.assertIn("Maxantal", result.reason)

    def test_stop_before_click(self):
        self.fake.stop_at_click = True
        result = self.run_engine()
        self.assertEqual(self.fake.clicks, 0)
        self.assertEqual(result.attempts, 0)

    def test_stop_after_click_no_next_click(self):
        self.fake.stop_after_click = True
        result = self.run_engine()
        self.assertEqual(self.fake.clicks, 1)
        self.assertFalse(result.matched)

    def test_focus_loss(self):
        self.fake.focus = False
        result = self.run_engine()
        self.assertEqual(self.fake.clicks, 0)
        self.assertIn("fokus", result.reason)

    def test_invalid_empty_text_stops(self):
        self.fake.bad_clipboard = True
        result = self.run_engine()
        self.assertEqual(self.fake.clicks, 1)
        self.assertFalse(result.matched)

    def test_identity_or_fracture_changed(self):
        for attribute in ("changed_identity", "changed_fracture"):
            with self.subTest(attribute=attribute):
                self.setUp()
                setattr(self.fake, attribute, True)
                result = self.run_engine()
                self.assertEqual(self.fake.clicks, 1)
                self.assertIn("identitet", result.reason)

    def test_unconfirmed_consumption_blocks_next_click(self):
        self.fake.never_hit = True
        self.fake.no_consumption = True
        result = self.run_engine()
        self.assertEqual(self.fake.clicks, 1)
        self.assertIn("Currencyförbrukningen", result.reason)

    def test_extra_consumption_stops(self):
        self.fake.never_hit = True
        self.fake.extra_consumption = True
        result = self.run_engine()
        self.assertEqual(self.fake.clicks, 1)
        self.assertIn("Oväntad", result.reason)

    def test_currency_server_delay(self):
        self.fake.never_hit = True
        self.fake.currency_delay = 5
        result = self.run_engine(1)
        self.assertEqual(result.verified, 1)
        self.assertEqual(self.fake.clicks, 1)
        self.assertGreater(self.fake.currency_reads, 5)

    def test_preexisting_stop(self):
        self.stop.set()
        self.assertEqual(self.run_engine().attempts, 0)

    def test_invalid_budget(self):
        for budget in (0, -1, True, 1.5):
            with self.subTest(budget=budget), self.assertRaises(RerollError):
                Engine(self.fake, self.target, budget, self.stop)


if __name__ == "__main__":
    unittest.main()
