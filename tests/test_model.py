import json
from pathlib import Path
import tempfile
import unittest

from deskbuddy.model import Model, load_state, save_state


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.model = Model(self.clock)

    def start(self, minutes=1, mode="down"):
        self.model.configure_timer("Focus", minutes, mode)
        self.model.start_timer()

    def test_pause_resume_excludes_paused_time(self):
        self.start()
        self.clock.now += 15
        self.model.pause_timer()
        self.clock.now += 100
        self.assertEqual(self.model.timer.reading(self.clock()), 45)
        self.model.start_timer()
        self.clock.now += 20
        self.assertEqual(self.model.timer.reading(self.clock()), 25)

    def test_expiration_after_sleep_creates_only_one_persistent_notice(self):
        self.start()
        self.clock.now += 10000
        self.assertTrue(self.model.tick())
        for _ in range(3):
            self.assertFalse(self.model.tick())
        self.assertEqual(len(self.model.alerts), 1)
        self.assertTrue(self.model.timer.finished)
        self.assertFalse(self.model.timer.running)

    def test_count_up_passes_reference_duration_without_finishing(self):
        self.start(mode="up")
        self.clock.now += 150
        self.model.tick()
        self.assertEqual(self.model.timer.reading(self.clock()), 150)
        self.assertFalse(self.model.timer.finished)
        self.assertEqual(self.model.alerts, [])

    def test_overlapping_alerts_reveal_next_without_losing_timer(self):
        self.start()
        self.model.update_session("coding", "Coding", 1, "approval")
        self.clock.now += 61
        self.model.tick()
        self.model.test_name()
        self.assertEqual([a.kind for a in self.model.queue()], ["name", "input", "timer"])
        self.model.acknowledge("demo:name")
        self.assertEqual(self.model.queue()[0].kind, "input")
        self.model.acknowledge(self.model.queue()[0].key)
        self.assertEqual(self.model.queue()[0].kind, "timer")
        self.assertEqual(self.model.sessions["coding"].status, "approval")

    def test_dismissing_input_does_not_approve_or_mark_session_done(self):
        self.model.update_session("coding", "Coding", 1, "approval")
        self.model.acknowledge(self.model.queue()[0].key)
        self.assertEqual(self.model.counts(), (0, 1, 0))
        self.assertEqual(self.model.mood(), "attention")

    def test_stale_turn_and_duplicate_ready_do_not_recreate_unread_notice(self):
        self.model.update_session("coding", "Coding", 2, "ready")
        self.model.acknowledge(self.model.queue()[0].key)
        self.assertFalse(self.model.update_session("coding", "Coding", 2, "ready"))
        self.assertFalse(self.model.update_session("coding", "Coding", 1, "working"))
        self.assertEqual(self.model.alerts, [])
        self.assertEqual(self.model.sessions["coding"].status, "ready")

    def test_two_sessions_are_independent(self):
        self.model.update_session("coding", "Coding", 1, "ready")
        self.model.update_session("writing", "Writing", 1, "approval")
        self.model.update_session("coding", "Coding", 2, "working")
        self.assertEqual(self.model.counts(), (1, 1, 0))
        self.assertIn("Writing", self.model.queue()[0].detail)

    def test_repeated_name_alerts_coalesce_until_acknowledged(self):
        for _ in range(5):
            self.model.test_name()
        self.assertEqual(len(self.model.alerts), 1)
        self.assertEqual(self.model.alerts[0].count, 5)

    def test_reset_and_clear_simulations_do_not_drop_other_alerts(self):
        self.start()
        self.clock.now += 61
        self.model.tick()
        self.model.test_name()
        self.model.clear_simulations()
        self.assertEqual(self.model.queue()[0].kind, "timer")
        self.model.test_name()
        self.model.reset_timer()
        self.assertEqual(self.model.queue()[0].kind, "name")
        self.assertEqual(self.model.timer.value, 60)

    def test_restart_recovers_overdue_running_timer_without_demo_sessions(self):
        self.start()
        self.model.update_session("coding", "Coding", 1, "working")
        self.model.test_name()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            save_state(path, self.model)
            self.clock.now += 70
            restored = load_state(path, self.clock)
            self.assertTrue(restored.timer.finished)
            self.assertEqual([a.kind for a in restored.alerts], ["timer"])
            self.assertEqual(restored.sessions, {})

    def test_acknowledged_completion_does_not_return_after_restart(self):
        self.start()
        self.clock.now += 61
        self.model.tick()
        self.model.acknowledge("timer:finished")
        restored = Model.restore(self.model.snapshot(), self.clock)
        self.assertTrue(restored.timer.finished)
        self.assertEqual(restored.alerts, [])

    def test_pending_completion_survives_restart(self):
        self.start()
        self.clock.now += 61
        self.model.tick()
        restored = Model.restore(self.model.snapshot(), self.clock)
        self.assertEqual(restored.queue()[0].kind, "timer")

    def test_invalid_durations_leave_existing_timer_untouched(self):
        original = self.model.timer
        for minutes in (float("nan"), float("inf"), -1, 0, 1441):
            with self.assertRaises(ValueError):
                self.model.configure_timer("Oops", minutes, "down")
            self.assertIs(self.model.timer, original)

    def test_corrupt_state_is_preserved_for_inspection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            path.write_text("not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_state(path, self.clock)
            self.assertEqual(path.read_text(encoding="utf-8"), "not json")

    def test_invalid_saved_deadlines_are_rejected(self):
        for invalid in ("yesterday", float("nan"), True):
            data = self.model.snapshot()
            data["timer"]["anchor"] = invalid
            data["timer"]["running"] = True
            with self.assertRaises(ValueError):
                Model.restore(data, self.clock)


if __name__ == "__main__":
    unittest.main()
