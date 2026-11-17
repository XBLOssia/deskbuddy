# Inspiration and attribution

Desk Buddy is an independent Windows desktop companion. Its Python/Tkinter
implementation was developed for this project with AI assistance. This repository
does not contain code or character assets copied from the projects below.

These creators made the ideas concrete enough to inspire this project:

- **[Joe Bentham's desk-buddy](https://github.com/joebentham/desk-buddy)**:
  the expressive physical desk companion, activity states, session counters and
  ESP32-S3-LCD-1.3 prism hardware direction. The original host bridge targets
  macOS and Claude; this project starts with a Windows desktop prototype.
- **[Steven Steele / MakerSteele's linear-clock-app](https://github.com/MakerSteele/linear-clock-app)**:
  visible time remaining, draining timer bars, count-up/countdown tasks and
  time-management ideas. Its public app is an Android/Capacitor project.
- **[Steven Steele / MakerSteele's name-alert](https://github.com/MakerSteele/name-alert)**:
  local name detection and visible alerts, especially useful for hearing and
  audio-processing accessibility. This prototype currently simulates name alerts;
  microphone recognition is still planned.

## Licenses and future reuse

The source-code licenses were checked on November 17, 2026:

| Project | License |
| --- | --- |
| Joe Bentham's desk-buddy software and enclosure | [MIT](https://github.com/joebentham/desk-buddy/blob/f8c5750c0ecd14d636c368f632f75a2f02d2f28e/LICENSE) |
| Joe Bentham's Lump character, drawings, animations and sounds | [CC BY-NC 4.0, separately licensed](https://github.com/joebentham/desk-buddy/blob/f8c5750c0ecd14d636c368f632f75a2f02d2f28e/LICENSE-ART.md) |
| MakerSteele's linear-clock-app | [MIT](https://github.com/MakerSteele/linear-clock-app/blob/8e3ad985098123bc9b6ebc85b915cbe831fd2fc8/LICENSE) |
| MakerSteele's name-alert | [MIT](https://github.com/MakerSteele/name-alert/blob/1a2659ad0c9da0696b3e68473f5a0f80d79e6a70/LICENSE) |

Lump artwork and sounds are not bundled here. Diogenes is a separate existing
custom character, redesigned with AI image generation for this project.

If upstream source, firmware or enclosure files are incorporated later, retain
their copyright and license notices alongside the imported material. Reusing Lump
would also require following its separate artwork license; this project's MIT
license does not cover it.

The original code here uses MIT. The bundled Diogenes artwork has a separate
[artwork license](assets/pets/diogenes/LICENSE-ART.md).
