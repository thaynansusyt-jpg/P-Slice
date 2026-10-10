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
# Android fullscreen first-run dialog can intercept all in-game controls.
sleep 9
echo "Dismiss Android fullscreen tutorial"
adb shell input tap 1700 525 || true
sleep 5
adb exec-out screencap -p > smoke-results/after-launch.png || true

# Native asset preloading can take 60-100 seconds under GitHub's x86_64
# emulator (ARM emulation). The old test sent taps BEFORE TitleState was ready.
# The first-run flashing-lights warning must also be acknowledged.
echo "Wait for TitleState to be initialized (up to 150 seconds)"
title_ready=0
for attempt in $(seq 1 25); do
  if grep -Eq 'TitleState\.hx:[0-9]+: Enforcing log settings|CHAPTER2_MAIN_MENU_READY' smoke-results/live-logcat.txt; then
    title_ready=1
    echo "TitleState reached on attempt $attempt"
    break
  fi
  if (( attempt % 2 == 0 )); then
    # First-run warning: A accept; other screens: tap to continue.
    adb shell input tap 2040 970 >/dev/null 2>&1 || true
    adb shell input tap 1160 610 >/dev/null 2>&1 || true
  fi
  sleep 6
done
adb exec-out screencap -p > smoke-results/after-taps.png || true
if (( title_ready == 0 )); then
  echo "WARN: TitleState was not detected before menu input; examine logs."
fi

# Use Android's physical ENTER key as well as touch. Merely tapping before the
# preloader finishes cannot be counted as a menu test.
echo "Wait for confirmed Chapter 2 main menu"
for attempt in $(seq 1 12); do
  if grep -q 'CHAPTER2_MAIN_MENU_READY' smoke-results/live-logcat.txt; then
    echo "CHAPTER2_MAIN_MENU_READY observed on attempt $attempt"
    break
  fi
  adb shell input keyevent 66 >/dev/null 2>&1 || true
  sleep 4
  if grep -q 'CHAPTER2_MAIN_MENU_READY' smoke-results/live-logcat.txt; then
    echo "CHAPTER2_MAIN_MENU_READY observed after ENTER keyevent"
    break
  fi
  adb shell input tap 1160 610 >/dev/null 2>&1 || true
  sleep 3
done
adb exec-out screencap -p > smoke-results/after-warning.png || true
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
