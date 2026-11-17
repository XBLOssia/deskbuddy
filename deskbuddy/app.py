"""Native desktop proof using only Python's standard library."""

import argparse
import ctypes
import math
from pathlib import Path
import tempfile
import time
import tkinter as tk
from tkinter import ttk

from .model import Model, SESSION_LABELS, load_state, save_state
from .sprites import PetAppearance, PetSpriteSheet


BG = "#101a24"
CARD = "#192733"
EDGE = "#314452"
TEXT = "#f0f3eb"
MUTED = "#b0bec8"
MINT = "#9ce2c0"
AMBER = "#ffcb8c"
PINK = "#e5b4e3"
BLUE = "#accfff"
FONT = "Segoe UI"
UI_SCALE = 1.0


def px(value):
    return round(value * UI_SCALE)


def scale_layout(widget):
    """Tk fonts use DPI-aware points; scale geometry's pixel units to match."""
    options = widget.keys()
    for name in ("padx", "pady", "borderwidth", "highlightthickness", "wraplength", "insertwidth"):
        if name in options:
            value = float(widget.cget(name))
            if value:
                widget.configure(**{name: px(value)})
    manager = widget.winfo_manager()
    if manager in ("pack", "grid"):
        info = widget.pack_info() if manager == "pack" else widget.grid_info()
        for name in ("padx", "pady", "ipadx", "ipady"):
            if name in info:
                value = info[name]
                values = (value,) if isinstance(value, (int, float)) else widget.tk.splitlist(value)
                scaled = tuple(px(float(v)) for v in values)
                if scaled:
                    if manager == "pack":
                        widget.pack_configure(**{name: scaled if name in ("padx", "pady") else scaled[0]})
                    else:
                        widget.grid_configure(**{name: scaled if name in ("padx", "pady") else scaled[0]})
    for child in widget.winfo_children():
        scale_layout(child)


def clock_text(seconds):
    seconds = max(0, math.ceil(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def label(parent, text="", size=11, color=TEXT, bold=False, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                    font=(FONT, size, "bold" if bold else "normal"), **kwargs)


def button(parent, text, command, primary=False, **kwargs):
    options = {"padx": 13, "pady": 6}
    options.update(kwargs)
    return tk.Button(parent, text=text, command=command,
                     bg=MINT if primary else EDGE, fg=BG if primary else TEXT,
                     activebackground="#c4f3dc" if primary else "#435c6e",
                     activeforeground=BG if primary else TEXT, relief="flat", bd=0,
                     font=(FONT, 10, "bold"), cursor="hand2", takefocus=True,
                     highlightthickness=2, highlightbackground=parent.cget("bg"),
                     highlightcolor=TEXT, disabledforeground="#7a8994", **options)


class Buddy(tk.Canvas):
    """Original vector artwork at the target prism's 240-by-240 resolution."""

    def __init__(self, parent, pet=None):
        super().__init__(parent, width=px(240), height=px(240), bg="#0e2027", bd=0,
                         highlightthickness=1, highlightbackground=EDGE, takefocus=False)
        self.pet = pet
        self.last_mood = None
        self.animation_start = 0

    def draw(self, mood, animate=False):
        self.delete("all")
        if self.pet is not None:
            if self.last_mood != mood:
                self.animation_start = time.monotonic()
                self.last_mood = mood
            frames = self.pet.frames(mood, px(216))
            frame = int((time.monotonic() - self.animation_start) * 6) % len(frames) if animate else 0
            self.create_image(px(120), px(120), image=frames[frame])
            # Status decoration belongs to this app, not to the pet's skin/face.
            tint = {"idle": MINT, "working": BLUE, "attention": AMBER, "name": PINK, "done": MINT}[mood]
            self.create_rectangle(px(3), px(3), px(237), px(237), outline=tint, width=px(2))
            return
        offset = math.sin(time.monotonic() * 1.8) * 3 if animate else 0
        tint = {"idle": MINT, "working": BLUE, "attention": AMBER,
                "name": PINK, "done": MINT}[mood]
        self.create_oval(36, 33, 204, 201, outline="#264249", width=1)
        self.create_oval(61, 190, 179, 204, fill="#09151c", outline="")
        self.create_line(79, 160 + offset, 67, 185 + offset, fill=tint, width=10, capstyle="round")
        self.create_line(161, 160 + offset, 173, 185 + offset, fill=tint, width=10, capstyle="round")
        self.create_polygon(78, 68 + offset, 161, 68 + offset, 181, 89 + offset,
                            181, 158 + offset, 159, 179 + offset, 80, 179 + offset,
                            59, 158 + offset, 59, 90 + offset,
                            smooth=True, splinesteps=24, fill=tint, outline="")
        self.create_line(120, 69 + offset, 120, 48 + offset, fill=tint, width=5)
        self.create_oval(113, 36 + offset, 127, 50 + offset, fill=tint, outline="")
        self.create_polygon(87, 91 + offset, 153, 91 + offset, 163, 103 + offset,
                            163, 142 + offset, 152, 153 + offset, 87, 153 + offset,
                            77, 142 + offset, 77, 103 + offset,
                            smooth=True, splinesteps=16, fill=BG, outline="")
        if mood == "done":
            for x in (99, 141):
                self.create_line(x - 7, 119 + offset, x, 114 + offset, x + 7,
                                 119 + offset, fill=tint, width=3, smooth=True)
        else:
            for x in (100, 140):
                self.create_oval(x - 4, 111 + offset, x + 4, 124 + offset, fill=tint, outline="")
        if mood in ("attention", "name"):
            self.create_oval(116, 135 + offset, 124, 143 + offset, outline=tint, width=2)
        else:
            self.create_arc(107, 125 + offset, 133, 141 + offset, start=190, extent=160,
                            style="arc", outline=tint, width=2)
        if mood in ("attention", "name", "working"):
            self.create_oval(175, 31, 220, 76, fill=tint, outline="")
            symbol = {"attention": "!", "name": "?", "working": "···"}[mood]
            self.create_text(197, 53, text=symbol, fill=BG, font=(FONT, 21, "bold"))
        self.create_text(120, 223, text="DESK BUDDY", fill="#7eaca9", font=(FONT, 8, "bold"))
        self.scale("all", 0, 0, UI_SCALE, UI_SCALE)
        # Canvas coordinates scale, but line widths are separate pixel values.
        if UI_SCALE != 1:
            for item in self.find_all():
                if "width" in self.itemconfigure(item) and self.type(item) != "text":
                    self.itemconfigure(item, width=px(float(self.itemcget(item, "width"))))


class App:
    def __init__(self, root, state_path, pet_sheet=None, pet_config=None):
        global UI_SCALE
        UI_SCALE = max(1.0, round(root.winfo_fpixels("1i") / 96 * 4) / 4)
        self.root, self.state_path = root, Path(state_path)
        self.message = "Changes to the timer are saved on this PC."
        self.pet = (PetAppearance(root, pet_config) if pet_config else
                    PetSpriteSheet(root, pet_sheet) if pet_sheet else None)
        self.storage_ok = True
        try:
            self.model = load_state(self.state_path)
        except (ValueError, OSError, TypeError, KeyError) as exc:
            self.model = Model()
            # Leave an unreadable state untouched rather than overwriting it.
            self.storage_ok = False
            self.message = f"Saved state could not load; original retained. This run is not saved. ({exc})"
        self.compact = None
        self.last_persist = None
        self.last_render = None
        self.running = True
        self.started = self.model.timer.finished or self.model.timer.running or (
            self.model.timer.value != (self.model.timer.duration if self.model.timer.mode == "down" else 0))
        root.title("Desk Buddy — desktop prototype")
        root.configure(bg=BG)
        width = min(px(1080), root.winfo_screenwidth() - px(80))
        height = min(px(865), root.winfo_screenheight() - px(40))
        root.geometry(f"{width}x{height}")
        root.minsize(px(940), px(740))
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.setup_style()
        self.build()
        scale_layout(root)
        for key, callback in (("<F1>", self.name_alert), ("<F2>", lambda: self.simulate("working")),
                              ("<F3>", lambda: self.simulate("approval")),
                              ("<F4>", lambda: self.simulate("ready")),
                              ("<Control-m>", self.open_compact)):
            root.bind_all(key, lambda event, action=callback: action())
        self.refresh()

    def setup_style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=BG, background=EDGE,
                        foreground=TEXT, arrowcolor=TEXT, padding=px(6), font=(FONT, 11))
        style.map("TCombobox", fieldbackground=[("readonly", BG)],
                  selectbackground=[("readonly", BG)], selectforeground=[("readonly", TEXT)])
        style.configure("Buddy.Horizontal.TProgressbar", troughcolor=BG, background=MINT,
                        bordercolor=BG, lightcolor=MINT, darkcolor=MINT, thickness=px(12))
        self.root.option_add("*TCombobox*Listbox.background", BG)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)

    def card(self, parent, **grid):
        f = tk.Frame(parent, bg=CARD, padx=20, pady=12,
                     highlightthickness=1, highlightbackground=EDGE)
        f.grid(**grid)
        return f

    def build(self):
        self.scroller = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.scroller.yview)
        scrollbar.pack(side="right", fill="y")
        self.scroller.pack(side="left", fill="both", expand=True)
        self.scroller.configure(yscrollcommand=scrollbar.set)
        shell = tk.Frame(self.scroller, bg=BG, padx=22, pady=14)
        content = self.scroller.create_window((0, 0), window=shell, anchor="nw")
        self.scroller.bind("<Configure>", lambda event: self.scroller.itemconfigure(content, width=event.width))
        shell.bind("<Configure>", lambda event: self.scroller.configure(scrollregion=self.scroller.bbox("all")))
        self.root.bind_all("<MouseWheel>", self.scroll_main)
        self.root.bind_all("<Prior>", lambda event: self.scroller.yview_scroll(-1, "pages"))
        self.root.bind_all("<Next>", lambda event: self.scroller.yview_scroll(1, "pages"))
        self.root.bind_all("<FocusIn>", self.reveal_focus, add="+")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)
        header = tk.Frame(shell, bg=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        label(header, "A little company. A clearer day.", 21, bold=True).pack(side="left")
        button(header, "Floating view  Ctrl+M", self.open_compact).pack(side="right")

        body = tk.Frame(shell, bg=BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0, minsize=px(310))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        left = self.card(body, row=0, column=0, sticky="nsew", padx=(0, 14))
        label(left, "YOUR DESK BUDDY", 10, MINT, True).pack(anchor="w")
        label(left, "Desktop preview · 240 × 240", 10, MUTED).pack(anchor="w", pady=(3, 16))
        self.buddy = Buddy(left, self.pet)
        self.buddy.pack()
        self.buddy_status = label(left, size=14, bold=True, wraplength=265, justify="center")
        self.buddy_status.pack(fill="x", pady=(16, 10))
        self.counters = label(left, size=10, color=MUTED, wraplength=260, justify="center")
        self.counters.pack(fill="x")
        self.session_summary = label(left, size=10, color=MUTED, justify="left", wraplength=265)
        self.session_summary.pack(fill="x", pady=(15, 0))
        artwork = "Pet artwork: local status treatments\n" if isinstance(self.pet, PetAppearance) else "Pet artwork: local PNG export\n" if self.pet else ""
        label(left, artwork + "AI activity: test signals only\nMicrophone: off · no audio captured",
              10, MUTED, justify="left").pack(anchor="w", side="bottom", pady=(15, 0))

        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        timer = self.card(right, row=0, column=0, sticky="ew", pady=(0, 14))
        timer.columnconfigure(0, weight=1)
        label(timer, "MAKE TIME VISIBLE", 10, MINT, True).grid(row=0, column=0, sticky="w")
        self.task = tk.StringVar(value=self.model.timer.label)
        self.task_entry = tk.Entry(timer, textvariable=self.task, bg=BG, fg=TEXT,
                                   insertbackground=TEXT, relief="flat", font=(FONT, 11),
                                   highlightthickness=1, highlightbackground=EDGE,
                                   highlightcolor=MINT)
        self.task_entry.grid(row=1, column=0, sticky="ew", ipady=5, pady=(8, 5))
        options = tk.Frame(timer, bg=CARD)
        options.grid(row=2, column=0, sticky="ew")
        self.minutes = tk.StringVar(value=f"{self.model.timer.duration / 60:g}")
        self.minute_entry = tk.Entry(options, textvariable=self.minutes, width=7, bg=BG, fg=TEXT,
                                     insertbackground=TEXT, relief="flat", font=(FONT, 11))
        self.minute_entry.pack(side="left", ipady=7)
        label(options, " minutes  ", 10, MUTED).pack(side="left")
        self.mode = tk.StringVar(value="Countdown" if self.model.timer.mode == "down" else "Count up")
        self.mode_select = ttk.Combobox(options, textvariable=self.mode, values=("Countdown", "Count up"),
                                        state="readonly", width=12)
        self.mode_select.pack(side="left")
        self.clock_label = label(timer, size=36, bold=True)
        self.clock_label.grid(row=3, column=0, sticky="w", pady=(2, 0))
        self.progress = ttk.Progressbar(timer, style="Buddy.Horizontal.TProgressbar", maximum=1)
        self.progress.grid(row=4, column=0, sticky="ew", pady=(3, 5))
        self.timer_caption = label(timer, size=10, color=MUTED)
        self.timer_caption.grid(row=5, column=0, sticky="w")
        actions = tk.Frame(timer, bg=CARD)
        actions.grid(row=6, column=0, sticky="w", pady=(11, 0))
        self.start_button = button(actions, "Start timer", self.start_timer, True)
        self.start_button.pack(side="left", padx=(0, 5))
        self.pause_button = button(actions, "Pause", self.pause_timer)
        self.pause_button.pack(side="left", padx=(0, 5))
        button(actions, "Reset", self.reset_timer).pack(side="left", padx=(0, 5))
        self.quick_button = button(actions, "10 sec test", self.quick_timer)
        self.quick_button.pack(side="left")

        attention = self.card(right, row=1, column=0, sticky="nsew")
        attention.columnconfigure(0, weight=1)
        label(attention, "ATTENTION, WITHOUT THE NOISE", 10, PINK, True).grid(row=0, column=0, sticky="w")
        self.alert_title = label(attention, "All clear", 17, bold=True, anchor="w", justify="left", wraplength=480)
        self.alert_title.grid(row=1, column=0, sticky="ew", pady=(10, 3))
        self.alert_detail = label(attention, size=10, color=MUTED, justify="left", anchor="w", wraplength=480)
        self.alert_detail.grid(row=2, column=0, sticky="ew")
        self.queue_label = label(attention, size=10, color=MUTED, justify="left", anchor="w", wraplength=480)
        self.queue_label.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.ack_button = button(attention, "Got it", self.acknowledge, True)
        self.ack_button.grid(row=4, column=0, sticky="w", pady=(10, 0))

        tests = self.card(shell, row=2, column=0, sticky="ew", pady=(14, 0))
        top = tk.Frame(tests, bg=CARD)
        top.pack(fill="x")
        label(top, "TRY THE SIGNALS", 10, BLUE, True).pack(side="left")
        label(top, "Simulated inputs · your timer is real", 10, MUTED).pack(side="right")
        signals = tk.Frame(tests, bg=CARD)
        signals.pack(fill="x", pady=(10, 0))
        self.demo_session = tk.StringVar(value="Coding")
        ttk.Combobox(signals, textvariable=self.demo_session, values=("Coding", "Writing"),
                     width=10, state="readonly").pack(side="left", padx=(0, 8))
        for text, callback in (("Working  F2", lambda: self.simulate("working")),
                               ("Approval  F3", lambda: self.simulate("approval")),
                               ("Question", lambda: self.simulate("question")),
                               ("Reply ready  F4", lambda: self.simulate("ready")),
                               ("Interrupted", lambda: self.simulate("interrupted"))):
            button(signals, text, callback, padx=6).pack(side="left", padx=(0, 4))
        lower = tk.Frame(tests, bg=CARD)
        lower.pack(fill="x", pady=(7, 0))
        button(lower, "Test name alert  F1", self.name_alert).pack(side="left", padx=(0, 5))
        button(lower, "Clear test signals", self.clear_simulations).pack(side="left")
        self.motion = tk.BooleanVar(value=not self.model.reduced_motion)
        tk.Checkbutton(lower, text="Gentle animation", variable=self.motion, command=self.change_motion,
                       bg=CARD, fg=TEXT, selectcolor=BG, activebackground=CARD,
                       activeforeground=TEXT, font=(FONT, 10), takefocus=True).pack(side="right")
        self.footer = label(shell, self.message, 9, MUTED, anchor="w", justify="left", wraplength=990)
        self.footer.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def scroll_main(self, event):
        if event.widget.winfo_toplevel() == self.root:
            self.scroller.yview_scroll(-round(event.delta / 120) * 3, "units")

    def reveal_focus(self, event):
        widget = event.widget
        if widget.winfo_toplevel() != self.root or widget == self.root:
            return
        self.root.update_idletasks()
        top = widget.winfo_rooty() - self.scroller.winfo_rooty()
        bottom = top + widget.winfo_height()
        height = self.scroller.winfo_height()
        if top < 0 or bottom > height:
            box = self.scroller.bbox("all")
            if box and box[3] > height:
                offset = top if top < 0 else bottom - height
                self.scroller.yview_moveto((self.scroller.canvasy(0) + offset) / box[3])

    def persist(self):
        snapshot = self.model.snapshot()
        if snapshot != self.last_persist and self.storage_ok:
            try:
                save_state(self.state_path, self.model)
                self.last_persist = snapshot
            except OSError as exc:
                self.message = f"Could not save; timer is running in this window only. {exc}"
                self.footer.config(text=self.message, fg=AMBER)

    def start_timer(self):
        try:
            if not self.started:
                self.model.configure_timer(self.task.get(), float(self.minutes.get()),
                                           "up" if self.mode.get() == "Count up" else "down")
            self.model.start_timer()
            self.started = True
            self.footer.config(text="Time keeps elapsing while closed. Alerts appear when Desk Buddy is open.", fg=MUTED)
            self.changed()
        except (ValueError, OverflowError) as exc:
            self.footer.config(text=str(exc), fg=AMBER)

    def pause_timer(self):
        self.model.pause_timer()
        self.changed()

    def reset_timer(self):
        self.model.reset_timer()
        self.started = False
        self.footer.config(text="Timer reset. You can change its name, duration or mode.", fg=MUTED)
        self.changed()

    def quick_timer(self):
        if self.started:
            return
        self.task.set("Ten-second timer test")
        self.minutes.set(str(10 / 60))
        self.mode.set("Countdown")
        self.start_timer()

    def simulate(self, status):
        sid = self.demo_session.get()
        previous = self.model.sessions.get(sid)
        turn = previous.turn if previous else 1
        if status == "working" and previous and previous.status != "working":
            turn += 1
        self.model.update_session(sid, sid, turn, status)
        self.changed()

    def name_alert(self):
        self.model.test_name()
        self.changed()

    def clear_simulations(self):
        self.model.clear_simulations()
        self.changed()

    def change_motion(self):
        self.model.reduced_motion = not self.motion.get()
        self.changed()

    def acknowledge(self):
        queue = self.model.queue()
        if queue:
            self.model.acknowledge(queue[0].key)
            self.changed()

    def changed(self):
        self.last_render = None
        self.persist()
        self.render()

    def render(self):
        t = self.model.timer
        value = t.reading(self.model.clock())
        shown = value if self.started else self.preview_value()
        self.clock_label.config(text=clock_text(shown))
        fraction = value / t.duration if t.mode == "down" else min(1, value / t.duration)
        self.progress["value"] = fraction if self.started else (1 if self.mode.get() == "Countdown" else 0)
        if t.finished:
            caption = "Finished · reset to start another timer"
        elif self.started:
            caption = ("Running" if t.running else "Paused") + (" · time remaining" if t.mode == "down" else " · elapsed time; no automatic stop")
        else:
            caption = "Time remaining" if self.mode.get() == "Countdown" else "Elapsed time · duration sets the bar's reference"
        self.timer_caption.config(text=caption)
        self.start_button.config(text="Running" if t.running else ("Resume" if self.started and not t.finished else "Start timer"),
                                 state="disabled" if t.running or t.finished else "normal")
        self.pause_button.config(state="normal" if t.running else "disabled")
        self.quick_button.config(state="disabled" if self.started else "normal")
        for widget in (self.task_entry, self.minute_entry):
            widget.config(state="disabled" if self.started else "normal", disabledbackground=CARD, disabledforeground=MUTED)
        self.mode_select.config(state="disabled" if self.started else "readonly")
        mood = self.model.mood()
        queue = self.model.queue()
        signature = (mood, self.model.status(), tuple(self.model.counts()),
                     tuple((a.key, a.count) for a in queue),
                     tuple((k, v.turn, v.status) for k, v in self.model.sessions.items()))
        if signature != self.last_render:
            self.buddy_status.config(text=self.model.status())
            working, waiting, replies = self.model.counts()
            self.counters.config(text=f"{working} working   ·   {waiting} need input   ·   {replies} unread")
            summaries = [f"{s.label}: {SESSION_LABELS[s.status]}" for s in self.model.sessions.values()]
            self.session_summary.config(text="\n".join(summaries) or "No AI client connected.\nTry a signal below to see the buddy react.")
            if queue:
                a = queue[0]
                badge = "TEST · " if a.simulated else ""
                count = f"  (×{a.count})" if a.count > 1 else ""
                self.alert_title.config(text=badge + a.title + count, fg=PINK if a.kind == "name" else AMBER if a.kind == "input" else MINT)
                self.alert_detail.config(text=a.detail)
                rest = ";  ".join(("TEST: " if b.simulated else "") + b.title for b in queue[1:])
                self.queue_label.config(text=(f"Next: {rest}" if rest else "Stays here until you acknowledge it."))
                self.ack_button.config(text="Dismiss notice" if a.kind == "input" else "Got it", state="normal")
            else:
                self.alert_title.config(text="All clear", fg=TEXT)
                self.alert_detail.config(text="Alerts stay here until acknowledged. No flashing or sound.")
                self.queue_label.config(text="A dismissed input notice never approves an AI action.")
                self.ack_button.config(state="disabled", text="Got it")
            self.last_render = signature
        self.buddy.draw(mood, not self.model.reduced_motion)
        if self.compact is not None:
            self.compact_buddy.draw(mood, not self.model.reduced_motion)
            self.compact_status.config(text=self.model.status())
            self.compact_clock.config(text=f"{clock_text(shown)}  ·  {self.task.get() if not self.started else t.label}")
            self.compact_progress["value"] = self.progress["value"]
            self.compact_badge.config(text=("TEST ALERT" if queue[0].simulated else "TIMER ALERT") if queue else "AI test signals only · microphone off")
            self.compact_ack.config(state="normal" if queue else "disabled",
                                    text="Dismiss notice" if queue and queue[0].kind == "input" else "Got it")

    def preview_value(self):
        try:
            value = float(self.minutes.get()) * 60
            return value if self.mode.get() == "Countdown" and math.isfinite(value) and 0 < value <= 86400 else 0
        except ValueError:
            return 0

    def open_compact(self):
        if self.compact is not None:
            self.compact.lift()
            return
        compact = self.compact = tk.Toplevel(self.root)
        compact.title("Desk Buddy — floating view")
        compact.configure(bg=BG, padx=15, pady=12)
        compact.geometry(f"{px(330)}x{px(490)}")
        compact.resizable(False, False)
        compact.attributes("-topmost", True)
        compact.protocol("WM_DELETE_WINDOW", self.close_compact)
        self.compact_badge = label(compact, size=9, color=MUTED)
        self.compact_badge.pack(fill="x", pady=(0, 8))
        self.compact_buddy = Buddy(compact, self.pet)
        self.compact_buddy.pack()
        self.compact_status = label(compact, size=13, bold=True, wraplength=290, height=2)
        self.compact_status.pack(fill="x", pady=(8, 3))
        self.compact_clock = label(compact, size=11, wraplength=290, height=2)
        self.compact_clock.pack(fill="x")
        self.compact_progress = ttk.Progressbar(compact, style="Buddy.Horizontal.TProgressbar", maximum=1)
        self.compact_progress.pack(fill="x", pady=(5, 10))
        row = tk.Frame(compact, bg=BG)
        row.pack(fill="x")
        self.compact_ack = button(row, "Got it", self.acknowledge, True)
        self.compact_ack.pack(side="left")
        button(row, "Main window", self.show_main).pack(side="right")
        scale_layout(compact)
        compact.update_idletasks()
        compact.geometry(f"{px(330)}x{max(px(490), compact.winfo_reqheight())}")
        self.render()

    def show_main(self):
        self.root.deiconify()
        self.root.lift()

    def close_compact(self):
        self.compact.destroy()
        self.compact = None

    def refresh(self):
        if not self.running:
            return
        if self.model.tick():
            self.persist()
        self.render()
        self.root.after(200, self.refresh)

    def close(self):
        self.model.tick()
        self.persist()
        self.running = False
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="Desk Buddy local desktop prototype")
    parser.add_argument("--state", type=Path, default=Path(__file__).resolve().parents[1] / ".local" / "state.json")
    parser.add_argument("--smoke-test", action="store_true", help="Render both windows and exit using temporary state")
    appearance = parser.add_mutually_exclusive_group()
    appearance.add_argument("--pet-sheet", type=Path, help="Use a local exported Codex pet PNG (v1 or v2); does not modify the pet")
    appearance.add_argument("--pet-config", type=Path, help="Use a local appearance manifest with per-status pot treatments")
    appearance.add_argument("--default-buddy", action="store_true", help="Use the original robot instead of any project pet artwork")
    args = parser.parse_args()
    default_appearance = Path(__file__).resolve().parents[1] / "assets" / "pets" / "diogenes" / "appearance.json"
    if not args.pet_sheet and not args.pet_config and not args.default_buddy and default_appearance.is_file():
        args.pet_config = default_appearance
    if hasattr(ctypes, "windll"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    if args.smoke_test:
        with tempfile.TemporaryDirectory(prefix="deskbuddy-smoke-") as temp:
            app = App(root, Path(temp) / "state.json", args.pet_sheet, args.pet_config)
            app.name_alert()
            app.open_compact()
            root.after(300, app.close)
            root.mainloop()
        print("Both desktop windows rendered successfully.")
    else:
        try:
            App(root, args.state, args.pet_sheet, args.pet_config)
        except (ValueError, OSError) as exc:
            root.destroy()
            parser.error(str(exc))
        root.mainloop()


if __name__ == "__main__":
    main()
