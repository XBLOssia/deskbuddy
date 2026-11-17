# Desk Buddy for ChatGPT: desktop prototype

Research and desktop prototype checked on November 16, 2026. A native Windows interaction prototype now runs locally, with a working timer, simulated AI/name signals, persistent visual alerts and an always-on-top floating view. No microphone, live AI hook, startup service, or hardware connection has been enabled.

Run `python -m deskbuddy` from this folder, or double-click `Desk Buddy.pyw` on Windows with Python file associations. See [prototype instructions and verification](PROTOTYPE.md) for controls, restart behavior and known limits. No third-party packages are needed.

Diogenes V2 is now the default project artwork, with separate pot colors and patterns for the desktop statuses. See [pet integration](PETS.md) and the [published artwork notes](../assets/pets/diogenes/README.md). Use `--default-buddy` for the original robot or `--pet-sheet` for another pet PNG. Pet-library synchronization remains manual.

The proposed product combines an expressive desk companion, visible time remaining, and visual alerts when someone may be calling your name. A small Windows companion should coordinate them, with a desktop display for development and a physical display as an additional output.

The user confirmed a desktop prototype first, followed by the **ESP32-S3-LCD-1.3 prism specified in desk-buddy's repository**, with its connected PC running the companion. The board is not available yet; physical work can follow after desktop development. Windows is the current host implementation. The exact ChatGPT surface remains an open integration choice.

## What the three projects contribute

| Reference | Verified contribution | Adaptation needed |
| --- | --- | --- |
| [Joe Bentham's desk-buddy](https://github.com/joebentham/desk-buddy/tree/f8c5750c0ecd14d636c368f632f75a2f02d2f28e) | ESP32-S3 prism display, animated activity states, several-session counters, tap input, USB/Wi-Fi transport. The supplied host bridge targets macOS and Claude. | A Windows bridge and OpenAI event adapters. Existing firmware can show moods and counters; countdown bars and name-alert text need firmware/art changes. |
| [MakerSteele's linear-clock-app](https://github.com/MakerSteele/linear-clock-app/tree/8e3ad985098123bc9b6ebc85b915cbe831fd2fc8) | Draining timer bars, count-up/countdown tasks, projects, due dates, pop-out timer strips, milestone chimes, checklists and calendar features. | Its public implementation is an Android/Capacitor app. Native overlays, alarms and calendar integration need Windows equivalents. Its Raspberry Pi/LED-tower clock code is explicitly not public yet. |
| [MakerSteele's name-alert](https://github.com/MakerSteele/name-alert/tree/1a2659ad0c9da0696b3e68473f5a0f80d79e6a70) | Windows tray app, offline Vosk recognition, selectable microphone, names and decoy words, confidence threshold, cooldown, click-through visual alerts and optional sound. | Emit an event to the companion as another alert output; retain local recognition and tuning. Add a persistent, steady alert option. |

These are complementary references. The Android clock app is useful design and source material, but it is not a ready-made Windows or ESP32 clock service.

## ChatGPT and Codex integration

The first integration should observe activity from an existing AI client. It does not need to make additional model requests merely to animate a status indicator.

| Surface | Evidence and proposed route | What remains unverified |
| --- | --- | --- |
| Codex | Official [hooks documentation](https://learn.chatgpt.com/docs/hooks) describes prompt submission, permission requests, tool events, stop, interrupt and session lifecycle events. A local adapter can translate these into companion events. The installed CLI reports version 0.152.1 and exposes hook-trust controls. | Actual event delivery from this installed desktop app, trust/setup flow, ordering and restart behavior. |
| ChatGPT Work | OpenAI's [plugin architecture](https://developers.openai.com/plugins/concepts/plugins) explicitly includes lifecycle hooks in the Codex runtime used by ChatGPT Work and Codex. A plugin can package the adapter. | Which execution host runs it and how events reach the Windows companion. Installing a web plugin does not deploy local command scripts. |
| Other ChatGPT web, desktop or mobile chats | Treat as a separate integration investigation. | This review did not establish a general activity feed for every ChatGPT conversation. Do not advertise universal monitoring. |
| A client built around Codex App Server | The official [App Server guide](https://learn.chatgpt.com/docs/app-server) documents structured thread status notifications, including waiting for approval, and turn events. | Passive access to sessions owned by an existing app must be proven. Starting another server does not establish access to the app's live sessions. |

Initial labels should be **working**, **approval requested**, **reply ready**, **interrupted**, and **connection unknown**. A permission hook alone does not prove that a human prompt remains pending. A stopped turn does not prove that the user's whole task is complete, and a ready reply stays unacknowledged until there is a real acknowledgement signal.

Questions awaiting an answer need a verified input-request/status signal. Do not infer them by searching the assistant's prose for question marks. Do not infer subscription usage limits from elapsed time or token counts.

## Proposed Windows architecture

```text
Codex / supported ChatGPT Work events ----+
Local microphone -> name recognizer -----+--> local companion service
Tasks / timer deadlines -----------------+         |
Optional calendar reader ----------------+         +--> desktop buddy + timer strip
                                                  +--> visual alert overlay
                                                  +--> optional ESP32 display
```

Keep the character, timer and alerts as independent state. An incoming name alert can temporarily take visual priority while the timer keeps running and AI requests remain queued. Closing an overlay must not clear an unrelated AI request.

Use a local event boundary with event ID, source, session/turn ID where applicable, event type and timestamp. Deduplicate deliveries and reject stale transitions for a previous turn. Send state snapshots on display reconnect. A missing heartbeat should show an unknown connection state rather than successful completion.

The original [firmware protocol](https://github.com/joebentham/desk-buddy/blob/f8c5750c0ecd14d636c368f632f75a2f02d2f28e/firmware/src/main.cpp) already supports mood, color, counters and heartbeat commands. A first physical proof could use those without changing the art. A true time bar, readable name banner or different character is additional display work.

## Features to build first

1. **An expressive buddy with explicit labels.** Show AI activity and several-session counts. Color supports text and shape; it is never the only signal. A tap or hotkey can acknowledge a reply, with no automatic approval of AI actions.
2. **One useful timer.** A draining bar, task label, remaining minutes, pause/resume and a count-up option. Support staying visible along a screen edge. Completion persists until acknowledged. Handle sleep/wake from stored deadlines instead of assuming a UI tick always runs on time.
3. **Name alerts as a core feature.** Local recognition with a clear listening/paused/error indicator, a selected microphone, test control, and adjustable confidence/cooldown. Start with a steady labeled alert; make motion and sound optional. Tune names and decoys with examples from the actual room.
4. **A small alert queue.** Suggested initial priority: possible name call, AI input needed, timer finished, reply ready, routine activity. Make the order adjustable. Suppressing an interruption should defer it or leave a badge, not silently discard it.

The name-alert source checks finalized recognition results through `AcceptWaveform` / `Result`; its audio block duration is not its complete detection latency. Measure misses, false alerts and response delay before treating room performance as established. Use plain tuning labels such as “Catch more” and “Fewer false alarms.”

Listening to people in the room and detecting a name inside meeting/headphone audio are different inputs. The reviewed Windows implementation captures a microphone; system-audio/meeting capture is a separate feature to verify.

## Keep the first version bounded

- Local recognition, with no raw audio or transcripts retained by default. Discard prompts and assistant messages from hook payloads before forwarding status events.
- Microphone off until explicitly enabled, and fully released when paused. Show microphone failures rather than continuing to display “listening.”
- Local IPC or a loopback-only authenticated service for the PC. Hardware receives only the minimum display state, not AI credentials or audio.
- Quiet hours and reduced-motion/steady-alert settings apply across the companion. Allow a separate choice for name alerts during focus time.
- Start calendar work as an optional read-only feature. Voice task capture, calendar editing, phone sync, Slack and elaborate tap animations can follow the first useful build.
- Use the desktop view to develop behavior for the confirmed prism. Its 240-by-240 character screen can be paired with a PC timer strip and readable alert text rather than crowded with every feature. Plan USB as the first device transport.

## Implementation sequence and evidence

| Stage | Concrete result | Required verification |
| --- | --- | --- |
| Desktop interaction proof | Buddy, time bar and persistent alert queue driven by labeled synthetic events. | Simultaneous events, acknowledgement, keyboard access, multi-monitor layout and reduced motion. Clearly identify simulated inputs. |
| Real AI adapter | One supported client delivers activity to the companion. | Working, approval flow, ready reply, interruption, concurrent sessions, disconnect and reconnect. Confirm what the chosen client actually emits. |
| Real name detection | Opt-in microphone recognition produces the same alert events. | Real-room examples, decoys, detection delay, muted/disconnected microphone and sleep/wake. No performance claim from synthetic event tests. |
| Timer reliability | Timers survive app restart and system sleep. | Pause/resume, overdue deadlines, restart recovery and clock changes. Decide explicitly how elapsed timers behave during sleep. |
| Physical output | The chosen device mirrors verified state. | Device reconnect, stale connection indication, real viewing-distance legibility and tap behavior. Rich timer graphics require their own firmware proof. |

## Reuse and attribution

The two MakerSteele repositories list MIT licenses. Desk-buddy's firmware, bridge, tooling and enclosure use MIT, while Lump's character, drawings, baked animation and sounds have a separate [CC BY-NC 4.0 license](https://github.com/joebentham/desk-buddy/blob/f8c5750c0ecd14d636c368f632f75a2f02d2f28e/LICENSE-ART.md). Preserve applicable notices and third-party dependency licenses if code is incorporated. Keep the animation renderer independent of the character assets so an original character can be used later.

The desktop code and original robot artwork are original. Diogenes derives from the user's existing custom pet and approved redesign; no code or Lump artwork from the reference repositories was copied. The public repository contains the runnable prototype and a curated artwork export; private pet records and production archives remain local. Hardware has not been tested. The integration and hardware sections above describe work still to be done.
