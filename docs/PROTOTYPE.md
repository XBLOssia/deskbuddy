# Running the desktop prototype

From this folder, run:

```powershell
python -m deskbuddy
```

On a Windows PC with Python file associations, double-click `Desk Buddy.pyw` for a launch without a terminal. `run.ps1` is another launcher. Requires Python 3.10 or newer with Tkinter; this development PC was tested with Python 3.13.15 and Tk 8.6. There are no third-party packages or API keys to install.

## What works now

- Diogenes V2 artwork with a white/cobalt animated default and four static status pot treatments; gentle animation is off by default.
- Optional exported Codex pet PNG artwork via `--pet-sheet`; `--default-buddy` restores the original robot. See [pet integration](PETS.md).
- A 240-by-240 artwork preview for the ESP32-S3-LCD-1.3 prism.
- A real countdown or count-up timer, a time bar, pause, resume and reset.
- Persistent visual alerts and a priority queue: name, input request, timer, reply.
- Two independent simulated AI sessions, unread reply counters and interrupt states.
- A movable, always-on-top floating view. Open it with the button or Ctrl+M.
- Keyboard shortcuts while either app window is focused: F1 tests a name alert; F2 shows working; F3 requests approval; F4 shows a ready reply.
- Local timer and motion-setting persistence. Saved state stays next to the application in `.local/state.json`.

Try **10 sec test**, then **Approval**, then **Test name alert**. The name alert appears first. After **Got it**, the approval notice appears; dismissing it reveals the timer completion. The simulated session still needs input until you choose another simulated state. Dismissing a notice never grants permission or sends an answer.

**Reset** clears only the timer and its completion notice. **Clear test signals** clears simulated AI and name activity, leaving a real timer and its notices intact. Repeated name tests coalesce into one notice with a count.

## Real and simulated inputs

The timer is functional. AI states and name alerts are manually triggered tests. They are labeled in the controls, alert text and floating view. There is no microphone capture, speech model, live ChatGPT/Codex adapter, network listener, serial connection, tray icon or startup registration in this version. The floating window is a regular interactive window, not a click-through full-screen overlay.

Simulated sessions and name alerts do not survive a restart. Timer state does: a running countdown continues to elapse while the application is closed or the PC sleeps. An overdue timer shows its completion notice when the app next opens or resumes. A paused timer remains paused. There is no notification while the app is closed. Closing the main window also closes the floating view; minimizing the main window leaves the floating view available.

Timer anchors use the PC's wall clock, allowing recovery across app restarts and sleep. Changing the system clock affects a running timer. The application does not yet compensate for manual clock changes. The count-up bar fills against the entered duration as a reference; count-up does not stop automatically.

Saved files are validated before loading and replaced atomically when saving. If a file cannot be loaded, the original is kept, a notice appears in the footer, and that run does not overwrite it. Stop the app and move the invalid file aside to create fresh state.

## Hardware direction

The confirmed target is the **ESP32-S3-LCD-1.3 prism specified by Joe Bentham's desk-buddy repository**, with its connected PC running the host companion. Hardware is not available yet. No board is needed to develop or run this prototype.

Plan USB as the first transport; keep all application state and name recognition on the connected PC. The display receives a small state snapshot. Physical firmware work and real serial/tap/disconnect tests are later stages. The preview establishes the artwork resolution, not physical display legibility, rendering compatibility or hardware support.

This is tested on Windows. Python/Tk may allow other host platforms later, but macOS/Linux packaging and mixed-DPI monitor movement have not been verified.

## Verification

```powershell
python -m unittest discover -s tests -v
python -m deskbuddy --smoke-test
```

The smoke check renders both windows using temporary state and exits. It does not change your saved timer.

Automated checks cover timer pause/resume, overdue recovery, count-up, persistence, stale/duplicate simulated turn events, two-session independence, alert ordering, acknowledgement isolation, invalid durations and saved-state validation. Windows UI checks covered the main layout at 250% display scaling, a real ten-second countdown, overlapping name/input/timer alerts, acknowledgement from both windows, and F1 from the floating view. The main view can scroll when content exceeds the window; focused controls are brought into view.

Screen-reader behavior, mixed-DPI/multi-monitor placement, actual OS sleep/wake, and physical hardware remain unverified. Restart and sleep time jumps were covered in model tests; those do not replace OS or device checks.
