# Pet artwork in Desk Buddy

The prototype reads a local exported Codex/ChatGPT pet PNG or an appearance
manifest with separate status skins. Diogenes V2 is bundled as the default.
Desk Buddy chooses the displayed state; the artwork does not supply live AI
activity or mirror another app's pet widget.

## Load an export

```powershell
python -m deskbuddy --pet-sheet 'C:\path\to\pet.png'
```

The PNG is read in place and is not recolored or overwritten. Both windows use
it. Native alpha is retained, and the UI adds a separate status border and label.
Reduced-motion mode uses the first frame; gentle animation is opt-in.

Supported PNG layouts are v1 (`1536 by 1872`) and v2 (`1536 by 2288`), using
`192 by 208` cells and eight columns. The reader checks file size, dimensions
and Tk decoding. It does not decode WebP or replace the Pets artwork validator.

The command-line option is not persisted. Without an override, the app reads
`assets/pets/diogenes/appearance.json`. Use `--default-buddy` for the original
robot or `--pet-config` for another appearance manifest. Refreshing an export
is manual; the app does not update or synchronize any remote pet record.

## Role mapping

| Desk Buddy role | Animation row | Meaning |
| --- | --- | --- |
| Idle | 0, idle | Resting animation |
| Working | 7, running | Focused work/thinking, rather than directional movement |
| AI input needed | 6, waiting | Expectant attention pose |
| Name alert | 6, waiting | Attention pose with a distinct label and app color |
| Reply ready / timer finished | 8, review | A checking pose; the label distinguishes the event |

A review pose does not imply that work has passed review. V2 look directions are
included in the sheet but are not used by this desktop reader yet.

## Appearance manifests

Paths are relative to the manifest. A status override can be either a prepared
`192 by 208` transparent still or a full supported sprite sheet. For example:

```json
{
  "version": 1,
  "base_sheet": "spritesheet.png",
  "status_skins": {
    "working": "skins/working.png",
    "attention": "skins/attention.png",
    "done": "skins/done.png",
    "name": "skins/name.png"
  }
}
```

Diogenes's white/cobalt default uses the animated V2 sheet. The four status pot
treatments are static cells with the same resting face, scale and baseline.
They do not animate or recolor his face. See the [artwork notes](../assets/pets/diogenes/README.md)
and [separate image license](../assets/pets/diogenes/LICENSE-ART.md).

## Verification and limits

The reader passed synthetic geometry and Tk decoding tests. The actual Diogenes
sheet and four status skins were checked in both desktop views at 250% Windows
scaling, including restoration of the default after clearing test signals.

The final V2 artwork passed the bundled production quality checks and independent
direction review. The public export has the exact validated file hash recorded
in its artwork notes. Private pet IDs, Library records and production archives
are not required to run the app and are excluded from the published Git files.

There is no prism export or firmware player yet. Desktop rendering does not
establish physical-device playback, viewing-distance legibility or compatibility.
