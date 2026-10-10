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
