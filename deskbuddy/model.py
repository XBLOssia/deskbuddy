"""Display-independent state shared by the desktop and future prism output."""

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import time


PRIORITY = {"name": 0, "input": 1, "timer": 2, "reply": 3}
SESSION_LABELS = {
    "working": "Working",
    "approval": "Approval requested",
    "question": "Answer requested",
    "ready": "Reply ready",
    "interrupted": "Interrupted",
}


@dataclass
class Alert:
    key: str
    kind: str
    title: str
    detail: str
    created: float
    simulated: bool = False
    count: int = 1


@dataclass
class Session:
    label: str
    turn: int
    status: str


@dataclass
class Timer:
    label: str = "A little focused time"
    mode: str = "down"
    duration: float = 25 * 60
    value: float = 25 * 60
    anchor: float | None = None
    running: bool = False
    finished: bool = False

    def reading(self, now):
        if not self.running:
            return self.value
        elapsed = max(0.0, now - self.anchor)
        return max(0.0, self.value - elapsed) if self.mode == "down" else self.value + elapsed


class Model:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.timer = Timer()
        self.alerts: list[Alert] = []
        self.sessions: dict[str, Session] = {}
        self.reduced_motion = True

    def notify(self, key, kind, title, detail, simulated=False):
        if kind not in PRIORITY:
            raise ValueError("Unknown alert kind")
        existing = next((a for a in self.alerts if a.key == key), None)
        if existing:
            existing.count += 1
            return
        self.alerts.append(Alert(key, kind, title, detail, self.clock(), simulated))

    def queue(self):
        return sorted(self.alerts, key=lambda a: (PRIORITY[a.kind], a.created, a.key))

    def acknowledge(self, key):
        # Dismissing an input notice never grants approval or changes its session.
        self.alerts = [a for a in self.alerts if a.key != key]

    def test_name(self):
        self.notify("demo:name", "name", "Someone may be calling you",
                    "Test name alert. Microphone is off; no audio was captured.", True)

    def update_session(self, session_id, label, turn, status):
        if status not in SESSION_LABELS:
            raise ValueError("Unknown session status")
        previous = self.sessions.get(session_id)
        if previous and (turn < previous.turn or (turn == previous.turn and status == previous.status)):
            return False
        self.sessions[session_id] = Session(label, turn, status)
        prefix = f"demo:session:{session_id}:"
        self.alerts = [a for a in self.alerts if not a.key.startswith(prefix)]
        if status in ("approval", "question", "ready"):
            title = SESSION_LABELS[status]
            detail = f"{label} · simulated activity"
            if status in ("approval", "question"):
                detail += ". Dismissing this notice does not answer or approve anything."
            self.notify(f"{prefix}{turn}:{status}", "reply" if status == "ready" else "input",
                        title, detail, True)
        return True

    def clear_simulations(self):
        self.sessions.clear()
        self.alerts = [a for a in self.alerts if not a.simulated]

    def counts(self):
        values = list(self.sessions.values())
        return (
            sum(s.status == "working" for s in values),
            sum(s.status in ("approval", "question") for s in values),
            sum(a.kind == "reply" for a in self.alerts),
        )

    def mood(self):
        queue = self.queue()
        if queue:
            return {"name": "name", "input": "attention", "timer": "done", "reply": "done"}[queue[0].kind]
        working, waiting, _ = self.counts()
        if waiting:
            return "attention"
        return "working" if working or self.timer.running else "idle"

    def status(self):
        if self.queue():
            return self.queue()[0].title
        working, waiting, _ = self.counts()
        if waiting:
            return "Demo session still needs input"
        if working:
            return "Working · simulated AI activity"
        if self.timer.running:
            return "Your timer is running"
        return "Ready when you are"

    def configure_timer(self, label, minutes, mode):
        if self.timer.running or self.timer.finished:
            raise ValueError("Reset the timer before changing its setup.")
        if mode not in ("up", "down"):
            raise ValueError("Choose countdown or count up.")
        if not math.isfinite(minutes) or not 0 < minutes <= 1440:
            raise ValueError("Enter a duration between 0 and 1,440 minutes.")
        duration = minutes * 60
        self.timer = Timer(label.strip()[:100] or "Focused time", mode, duration,
                           duration if mode == "down" else 0)

    def start_timer(self):
        if self.timer.finished:
            raise ValueError("Reset the finished timer to start again.")
        if not self.timer.running:
            self.timer.anchor = self.clock()
            self.timer.running = True

    def pause_timer(self):
        self.tick()
        if self.timer.running:
            self.timer.value = self.timer.reading(self.clock())
            self.timer.anchor = None
            self.timer.running = False

    def reset_timer(self):
        t = self.timer
        self.timer = Timer(t.label, t.mode, t.duration, t.duration if t.mode == "down" else 0)
        self.acknowledge("timer:finished")

    def tick(self):
        t = self.timer
        if t.running and t.mode == "down" and t.reading(self.clock()) <= 0:
            t.value, t.anchor, t.running, t.finished = 0, None, False, True
            self.notify("timer:finished", "timer", "Time is up", f"{t.label} · timer finished")
            return True
        return False

    def snapshot(self):
        # AI simulations intentionally do not survive a restart as if still live.
        return {"version": 1, "timer": asdict(self.timer),
                "alerts": [asdict(a) for a in self.alerts if not a.simulated],
                "reduced_motion": self.reduced_motion}

    @classmethod
    def restore(cls, data, clock=time.time):
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Unsupported saved state")
        t = data.get("timer")
        if not isinstance(t, dict) or set(t) != set(Timer.__dataclass_fields__):
            raise ValueError("Invalid saved timer")
        if not isinstance(t["label"], str) or len(t["label"]) > 100 or t["mode"] not in ("down", "up"):
            raise ValueError("Invalid saved timer label or mode")
        for field in ("duration", "value"):
            if type(t[field]) not in (int, float) or not math.isfinite(t[field]) or t[field] < 0:
                raise ValueError("Invalid saved timer value")
        if not 0 < t["duration"] <= 86400:
            raise ValueError("Invalid saved timer duration")
        if type(t["running"]) is not bool or type(t["finished"]) is not bool:
            raise ValueError("Invalid saved timer flags")
        anchor = t["anchor"]
        if anchor is not None and (type(anchor) not in (int, float) or not math.isfinite(anchor)):
            raise ValueError("Invalid saved deadline")
        if t["running"] != (anchor is not None) or (t["running"] and t["finished"]):
            raise ValueError("Inconsistent saved timer")
        if t["mode"] == "down" and t["value"] > t["duration"]:
            raise ValueError("Invalid remaining duration")
        alerts = data.get("alerts", [])
        if not isinstance(alerts, list) or len(alerts) > 20:
            raise ValueError("Invalid saved alerts")
        model = cls(clock)
        model.timer = Timer(**t)
        for a in alerts:
            # Only actual timer completion notices are persisted in this prototype.
            if (not isinstance(a, dict) or a.get("key") != "timer:finished"
                    or a.get("kind") != "timer" or a.get("simulated") is not False):
                raise ValueError("Invalid saved alert")
            if t["finished"] and not any(x.key == "timer:finished" for x in model.alerts):
                model.notify("timer:finished", "timer", "Time is up", f"{t['label']} · timer finished")
        motion = data.get("reduced_motion", True)
        if type(motion) is not bool:
            raise ValueError("Invalid motion preference")
        model.reduced_motion = motion
        model.tick()
        return model


def load_state(path, clock=time.time):
    path = Path(path)
    if not path.exists():
        return Model(clock)
    if path.stat().st_size > 1_000_000:
        raise ValueError("Saved state is too large")
    return Model.restore(json.loads(path.read_text(encoding="utf-8")), clock)


def save_state(path, model):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(model.snapshot(), indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)
