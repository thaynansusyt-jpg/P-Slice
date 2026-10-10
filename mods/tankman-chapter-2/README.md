# Friday Night Funkin': Vs. Tankman — Chapter 2 (WIP)

This fan-made add-on uses the **actual Tankman** from P-Slice/FNF Week 7.

### What is actually here
- Original Week 7 Tankman character asset, animations and health icon resolved from the installed P-Slice base-game files.
- Custom Chapter 2 military/night stage and Lua HUD effect.
- Six **synthetic instrumental sketches** with 18 generated charts (Easy, Normal and Hard).
- A separate Chapter 2 menu available in builds compiled from this branch.
- A mod-only ZIP for importing into a compatible P-Slice install.

### What is **not** finished
- **No real singing vocal performances or Tankman dialogue recordings.** The melody you hear in the instrumentals is a synth guide, **not** Tankman's actual voice.
- These song structures and charts are algorithmic drafts rather than hand-charted production releases.
- New animated cinematics, polished music production and complete Android gameplay testing are not done.
- Do not advertise this ZIP as an entirely finished Chapter 2 mod or a ready-made Android APK.

### Install or test
Extract the ZIP and place its `tankman-chapter-2` folder inside the mods folder recognized by your compatible P-Slice build; enable it in Mods, then open Story Mode.
The special main-menu shortcut exists only in a newly compiled version of this source branch.

### Asset strategy
**Do not draw or generate Tankman's official sprites again.**
The week and chart now use ID `tankman`, matching the character JSON and sprite atlas shipped in the P-Slice base game.
`tools/chapter2_factory.py` only regenerates charts, audio sketches and Chapter 2 background/menu art.

### What to work on next
Replace the placeholder song arrangements with composed/mixed original tracks and recorded/licensed vocal takes, sync handwritten charts to those vocals, and test all six tracks on a real Android build.


## Tested DirectWave vocal addon (separate download)
The author provided two monolithic DWP voicebanks for Tankman (26 zones) and Boyfriend (48 zones). Their embedded 32-bit PCM samples were decoded and used to create six experimental vocal takes and three patched difficulty charts per track. The DWP binaries and their embedded machine-path metadata were **not** uploaded to GitHub.

To install: extract this main mod ZIP to `mods/`, then merge the companion `tankman-chapter-2/` folder from the voice addon ZIP supplied in the current chat. Each `songs/<track>/` directory will then contain both `Inst.ogg` and `Voices.ogg`; the overlay charts set `needsVoices: true`.

The debug APK workflow in this branch builds with the instrumental-only files committed here, as the voicebank files remain private. Install the voice addon separately after installing the mod. This is a draft arrangement, not professionally mastered audio.

## Menu / Android
The Chapter 2 menu is now proportional to screen dimensions and supports Android touch as well as keyboard/controller input; main-menu mobile button spacing was adjusted. The Android debug build has a distinct package ID so it does not overwrite the regular P-Slice engine.

Known limits: actual Android runtime verification, release signing and synced final vocal performances are outstanding.
