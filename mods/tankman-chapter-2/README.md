# Vs. Tankman Chapter 2 PLUS 0.3.0

Seven playable songs: Redeploy, Blackout, Onslaught, Warzone, Last Stand,
No More Heroes, and Ugh Radio Remix. Each has Easy, Normal and Hard charts.
The six Chapter 2 arrangements remain experimental original compositions.
Ugh Radio Remix now follows the user-supplied Ugh MIDI, with a new radio
arrangement and samples extracted from the supplied DWP-derived vocal addon.
No raw DWP files or their private machine metadata are distributed.

Changes: correct absolute P-Slice note ownership; selectable difficulty in
native War Room; song selection requires the explicit Play button on touch;
chart lookup failure gives a message instead of dereferencing a null song;
BF/Tankman feet aligned at stage Y=760; camera adjusted; bundled mod revision
replaces stale embedded content when updating the APK; graphics capped at
60 FPS; in-song editor hotkeys disabled for the standalone Android build.

ZIP installation: merge tankman-chapter-2 into the compatible engine's mods
folder and enable it. Standalone APK installs its bundled mod automatically.
The native menu changes need the new APK. The mod ZIP updates music, charts
and stage without compiling the engine. Custom HTML is an older concept.

Validation: JSON/chart/audio checks performed locally. Android startup/menu
and first-song startup are checked by CI on the new APK. Passing those does
not prove the full campaign or performance on the Samsung A15.

The playtest signing key is cached for future builds. The previously issued
APK used a randomly generated key, so an Android signature-conflict message
may require removing the previous playtest installation; back up its saves
before doing so. This is a test build, not a professionally mastered release.
