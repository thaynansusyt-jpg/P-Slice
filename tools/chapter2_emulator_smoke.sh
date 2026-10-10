#!/usr/bin/env bash
# CI runtime smoke test: runs under Android Emulator 35; checks actual app launch.
set -euo pipefail
mkdir -p smoke-results
APP="com.thaynan.tankmanchapter2"
APK="$(find smoke-apk -type f -name '*.apk' -print -quit)"
if [[ -z "$APK" ]]; then
  echo "FAIL: APK artifact not found" | tee smoke-results/status.txt
  exit 1
fi
echo "APK: $APK"
echo "Emulator ABI: $(adb shell getprop ro.product.cpu.abilist)"
echo "APK size: $(stat -c %s "$APK") bytes"
adb shell getprop ro.build.version.release | tee smoke-results/android-version.txt
adb install -r -g "$APK" 2>&1 | tee smoke-results/install.txt
adb shell pm list packages | grep -F "$APP" | tee smoke-results/package.txt
adb logcat -c
echo "Launch Android application: $APP"
adb shell monkey -p "$APP" -c android.intent.category.LAUNCHER 1 2>&1 | tee smoke-results/launch.txt
sleep 32
adb exec-out screencap -p > smoke-results/after-launch.png || true
adb shell dumpsys activity activities > smoke-results/activities.txt || true
adb shell pidof "$APP" | tee smoke-results/pid-after-launch.txt || true
echo "Tapping through intro/tutorial to verify entry into game menu."
adb shell input tap 620 390 || true
sleep 3
adb shell input tap 620 390 || true
sleep 3
adb shell input tap 620 390 || true
sleep 19
adb exec-out screencap -p > smoke-results/after-taps.png || true
adb logcat -d -v time -b main -b crash > smoke-results/logcat.txt || true
adb shell dumpsys activity top > smoke-results/activity-top.txt || true
adb shell pidof "$APP" | tee smoke-results/pid-after-taps.txt || true
printf '%s\\n' '----- Chapter 2 startup traces -----'
grep -E 'CHAPTER2_MOD_|Starting game setup|Finished|MainMenuState|TitleState' smoke-results/logcat.txt | tail -60 || true
# Capture Android and engine failure signals even when the OpenFL handler swallows Java errors.
grep -E "FATAL EXCEPTION|Fatal signal|Process $APP .* died|Unable to start activity|UnsatisfiedLinkError|Failed to load.*ApplicationMain|Critical Error" smoke-results/logcat.txt > smoke-results/crash-signals.txt || true
if [[ -s smoke-results/crash-signals.txt ]]; then
  echo "CRASH SIGNALS DETECTED:"
  tail -35 smoke-results/crash-signals.txt
  echo "----- HXCPP CRASH CONTEXT (BEFORE AND AFTER ERROR) -----"
  grep -n -B 90 -A 30 -E 'Uncatchable Throw|Fatal signal 4|FATAL EXCEPTION|Critical Error' smoke-results/logcat.txt | tail -250 || true
  echo "----- ENGINE LOGS -----"
  grep -E 'I/HXCPP|D/HXCPP|W/HXCPP|E/HXCPP|I/trace|E/trace|SDLActivity|OpenFL|Lime' smoke-results/logcat.txt | tail -100 || true
  echo "FAIL: Runtime crash in Android logcat" | tee smoke-results/status.txt
  exit 1
fi
if [[ ! -s smoke-results/pid-after-taps.txt ]]; then
  echo "FAIL: Application process is no longer running" | tee smoke-results/status.txt
  tail -100 smoke-results/logcat.txt
  exit 1
fi
echo "PASS: Android app installed, launched, survived title interactions, and remained running. Full song gameplay still untested." | tee smoke-results/status.txt
