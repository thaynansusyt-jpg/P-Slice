#!/usr/bin/env bash
# Android 15 runtime verification of a real GitHub-built APK.
set -euo pipefail
mkdir -p smoke-results
APP="com.thaynan.tankmanchapter2"
APK="$(find smoke-apk -type f -name '*.apk' -print -quit)"
[[ -n "$APK" ]] || { echo "FAIL: APK absent" | tee smoke-results/status.txt; exit 1; }
echo "APK: $APK"
echo "Emulator ABI: $(adb shell getprop ro.product.cpu.abilist)"
adb shell getprop ro.build.version.release | tee smoke-results/android-version.txt
adb install -r -g "$APK" 2>&1 | tee smoke-results/install.txt
adb shell pm list packages | grep -F "$APP" | tee smoke-results/package.txt
adb logcat -c
# Stream logs while emulator is connected; Android test infrastructure may
# disconnect from ADB during Vulkan graphics initialization.
adb logcat -v time -b main -b crash > smoke-results/live-logcat.txt 2>&1 &
LOGCAT_PID=$!
trap 'kill "$LOGCAT_PID" 2>/dev/null || true' EXIT
echo "Launching Android application"
adb shell monkey -p "$APP" -c android.intent.category.LAUNCHER 1 2>&1 | tee smoke-results/launch.txt
# The Android 15 fullscreen tutorial blocks ALL gameplay input until 'Got it'
# is tapped. Verified location from the prior captured 2340x1080 screenshot.
sleep 9
echo "Dismiss Android fullscreen tutorial"
adb shell input tap 1700 525 || true
sleep 25
adb exec-out screencap -p > smoke-results/after-launch.png || true
adb shell dumpsys activity activities > smoke-results/activities.txt || true
adb shell pidof "$APP" | tee smoke-results/pid-after-launch.txt || true
echo "Proceed through FNF title and disclaimer"
adb shell input tap 1160 610 || true
sleep 4
adb shell input tap 1160 610 || true
sleep 4
adb shell input tap 1160 610 || true
sleep 12
adb exec-out screencap -p > smoke-results/after-taps.png || true
# Android beta FNF splash can open a flashing-lights notice on first launch.
# On the actual prior screenshot, bottom-left of mobile controls is virtual B.
echo "Dismiss the flashing-lights warning with in-game B button"
adb shell input tap 1845 970 || true
sleep 7
adb exec-out screencap -p > smoke-results/after-warning.png || true
echo "Continue through title using in-game A button"
adb shell input tap 2040 970 || true
sleep 5
adb shell input tap 2040 970 || true
sleep 9
adb exec-out screencap -p > smoke-results/after-menu.png || true
adb shell dumpsys activity top > smoke-results/activity-top.txt || true
# ADB sometimes goes offline in nested Android/ARM emulation under GitHub CI.
# Distinguish this infrastructure failure from the app actually dying.
if ! adb shell true 2>/dev/null; then
  echo "WARN: emulator ADB disconnected, trying to reconnect..."
  adb reconnect offline || true
  sleep 5
fi
adb logcat -d -v time -b main -b crash > smoke-results/logcat.txt 2>/dev/null || true
[[ -s smoke-results/logcat.txt ]] || cp smoke-results/live-logcat.txt smoke-results/logcat.txt
adb shell pidof "$APP" > smoke-results/pid-after-taps.txt 2>/dev/null || true
echo "--- Game-specific startup log ---"
grep -E 'CHAPTER2_MOD_|source/.*hx:|E/HXCPP|Critical Error|FATAL EXCEPTION|Fatal signal' smoke-results/logcat.txt | tail -75 || true
# Eliminate unrelated Google-internal dlopen errors.
grep -E "FATAL EXCEPTION|Fatal signal|Process $APP .* died|Unable to start activity|UnsatisfiedLinkError|Failed to load.*ApplicationMain|Critical Error|CHAPTER2_MOD_ERROR" smoke-results/logcat.txt > smoke-results/crash-signals.txt || true
if [[ -s smoke-results/crash-signals.txt ]]; then
  echo "FAIL: Android app crash or mod exception" | tee smoke-results/status.txt
  tail -75 smoke-results/crash-signals.txt
  exit 1
fi
if ! adb shell true >/dev/null 2>&1; then
  echo "INCONCLUSIVE: Android emulator ADB disconnected. Screenshots and streamed logs uploaded for inspection." | tee smoke-results/status.txt
  exit 1
fi
if [[ ! -s smoke-results/pid-after-taps.txt ]]; then
  echo "FAIL: Game process exited while emulator was healthy" | tee smoke-results/status.txt
  exit 1
fi
# Compilation and process survival are not enough. The build can be stuck on
# the splash/disclaimer; require the actual main menu's runtime marker.
if ! grep -q 'CHAPTER2_MAIN_MENU_READY' smoke-results/logcat.txt; then
  echo "FAIL: App remained alive but did not reach the main menu. Check after-menu.png." | tee smoke-results/status.txt
  grep -E 'CHAPTER2_|source/.*hx:' smoke-results/logcat.txt | tail -65 || true
  exit 1
fi
echo "PASS: Chapter 2 custom main menu reached in Android 15."
if grep -q "CHAPTER2_MOD_WARNING" smoke-results/logcat.txt; then
  echo "FAIL: Embedded Chapter 2 mod files were not available on startup" | tee smoke-results/status.txt
  exit 1
fi
echo "PASS: APK installed, survived, and reached the interactive main menu on Android 15. Chapter 2 track menu and complete songs not yet verified." | tee smoke-results/status.txt
