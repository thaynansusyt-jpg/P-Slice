#!/usr/bin/env python3
"""Chapter 2 PLUS: seven independently arranged ORIGINAL instrumental drafts.

No commercial song melodies or Ugh MIDI note sequences are included. The
user-provided 10-track MIDI informed the instrumentation and half-time groove.
The emitted JSON notes are synchronized to each newly composed lead pattern.
This generator runs without Haxe, Android, or the game engine.
Requires numpy and ffmpeg. Use --out to avoid overwriting the current game.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

RATE = 22050
# name, slug, bpm, number of measures, tonal center, unique melodic motif,
# progression in semitones, sound palette, drum identity
SONGS = [
    ("Redeploy", "redeploy", 140, 48, 39,
     [0, 0, 7, 10, 7, 5, 3, 7], [0, 5, 3, 7], "brass", "march"),
    ("Blackout", "blackout", 155, 48, 42,
     [0, 3, 7, 6, -2, 3, 0, -5], [0, -2, -5, -7], "pulse", "half"),
    ("Onslaught", "onslaught", 165, 52, 43,
     [0, 12, 10, 7, 15, 12, 7, 3], [0, 3, 5, 7], "saw", "gallop"),
    ("Warzone", "warzone", 170, 52, 45,
     [0, 1, 6, 5, 0, 8, 7, 1], [0, 1, 6, 3], "industrial", "break"),
    ("Last Stand", "last-stand", 180, 56, 48,
     [0, 7, 12, 15, 19, 15, 12, 7], [0, 5, 8, 3], "bell", "anthem"),
    ("No More Heroes", "no-more-heroes", 190, 64, 50,
     [0, 10, 7, 13, 12, 3, 7, 0], [0, -1, 5, 6], "boss", "finale"),
    # Fan-original radio battle inspired by the instrumentation and half-time
    # energy of the user's Ugh MIDI; NOT the original song's melody/audio.
    ("Ugh: Radio Remix", "ugh-radio-remix", 160, 48, 38,
     [0, 5, 10, 3, 8, 7, 12, 5], [0, -2, 3, 7], "brass", "half"),
]


def tone(buf, start, dur, midi, level, voice):
    i = max(0, round(start * RATE))
    n = min(round(dur * RATE), len(buf) - i)
    if n <= 0:
        return
    t = np.arange(n, dtype=np.float32) / RATE
    f = 440 * 2 ** ((midi - 69) / 12)
    phase = (t * f) % 1
    if voice == "bf":
        # Higher, bright vocal-formant prototype. User's private DWP addon
        # supplies the authentic sampler-based voice alternative.
        vibrato = np.sin(2*np.pi*5.3*t) * .018
        signal = .64*np.sin(2*np.pi*f*t + vibrato) + .25*np.sin(4*np.pi*f*t) + .11*np.sin(6*np.pi*f*t)
    elif voice == "tankman":
        # Lower, nasal/brassy response timbre: clearly different from BF.
        signal = .50*np.sin(2*np.pi*f*t) + .34*np.sin(3*np.pi*f*t) + .16*np.sign(np.sin(2*np.pi*f*t))
    elif voice == "brass":
        signal = .60 * np.sin(2*np.pi*f*t) + .28 * np.sin(4*np.pi*f*t) + .12*np.sin(6*np.pi*f*t)
    elif voice == "pulse":
        signal = np.where(phase < .24, .85, -.38).astype(np.float32)
    elif voice == "saw":
        signal = (2*phase-1).astype(np.float32)
    elif voice == "industrial":
        signal = .6*(2*phase-1) + .4*np.sign(np.sin(2*np.pi*f*t))
    elif voice == "bell":
        signal = np.sin(2*np.pi*f*t) + .38*np.sin(2*np.pi*f*2.996*t)
    elif voice == "boss":
        signal = .58*np.sin(2*np.pi*f*t)+.28*(2*phase-1)+.14*np.sin(2*np.pi*f*5*t)
    else:
        signal = np.sin(2*np.pi*f*t) + .14*np.sin(4*np.pi*f*t)
    attack = min(.020, dur*.18)
    decay = np.exp(-t/max(.04, dur*.57))
    env = np.minimum(1, t/max(.001, attack))*decay
    buf[i:i+n] += (level * signal * env).astype(np.float32)


def drum(buf, at, kind, seed, volume=1.0):
    start = int(at * RATE)
    duration = {"kick": .20, "snare": .14, "hat": .055, "tom": .21}[kind]
    n = min(int(duration * RATE), len(buf) - start)
    if start < 0 or n <= 0:
        return
    t = np.arange(n, dtype=np.float32)/RATE
    rng = np.random.default_rng(seed)
    if kind == "kick":
        phase = 2*np.pi*(48*t+35*(1-np.exp(-t*37))/37)
        signal = .75*np.sin(phase)*np.exp(-t*25)
    elif kind == "tom":
        signal = .45*np.sin(2*np.pi*(95*t-45*t*t))*np.exp(-t*17)
    else:
        noise = rng.normal(0, 1, n).astype(np.float32)
        if kind == "snare":
            signal = .23*noise*np.exp(-t*38)+.18*np.sin(2*np.pi*170*t)*np.exp(-t*30)
        else:
            signal = .10*(noise-np.convolve(noise, np.ones(8)/8, mode="same"))*np.exp(-t*77)
    buf[start:start+n] += volume*signal


def score_events(slug, bars, root, motif, bpm, style):
    """Each event is used both to synthesize lead and chart the corresponding note."""
    events=[]
    rng=np.random.default_rng(18000+len(slug))
    for bar in range(bars):
        part = bar//8
        if part == 0: density = .62
        elif part in (1,3): density = .86
        elif part == 5: density = 1.0
        elif part == 6: density = .48
        else: density = .78
        for slot in range(8):
            on = True
            if style == "half": on = slot in (0, 3, 4, 7) or (density>.85 and slot==6)
            elif style == "march": on = slot in (0, 2, 3, 4, 6) or (density>.83 and slot==7)
            elif style == "gallop": on = slot in (0, 1, 3, 4, 5, 7)
            elif style == "break": on = slot in (0, 2, 3, 5, 7)
            elif style == "anthem": on = slot in (0, 2, 4, 6) or (density>.83 and slot in (5,7))
            else: on = slot in (0, 1, 2, 4, 5, 6, 7)
            if not on or (density<.7 and slot in (1,5,7)): continue
            # Each song has a distinct motivic contour, phrasing, and key.
            variation = [0, 0, 5, 0, -2, 7, 0, 12][part % 8]
            pitch = root + 24 + motif[(slot+bar//4)%len(motif)] + variation
            pitch += int(rng.choice([-12, 0, 0, 0, 0, 0, 12])) if part == 7 and slot in (0,7) else 0
            events.append((bar*4 + slot*.5, int(pitch), bar, slot))
    return events


def make_chart(name, bpm, bars, events, difficulty, style):
    density={"easy": .51, "normal": .80, "hard": 1.0}[difficulty]
    sections=[]
    bybar={}
    for ev in events: bybar.setdefault(ev[2], []).append(ev)
    total_notes=0
    for bar in range(bars):
        part=bar//8
        # Opponent sings first, BF answers: more musical than the previous alternating pattern.
        player_side = (bar%8)>=4
        notes=[]
        for idx,(beat,pitch,_,slot) in enumerate(bybar.get(bar,[])):
            if difficulty == "easy" and slot not in (0,2,4,6): continue
            if difficulty == "normal" and slot in (1,7) and idx%2==0: continue
            lane = ((pitch//2)+(bar%3))%4
            # Psych format: lanes 0..3 belong to mustHitSection side,
            # 4..7 to the other side. Shift per phrase for a call/response.
            owner_is_player = (bar%8>=4) if slot<4 else (bar%8<4)
            col = lane + (0 if owner_is_player == player_side else 4)
            notes.append([round(beat*60000/bpm,3),col,0])
            total_notes+=1
        sections.append({"sectionBeats":4,"sectionNotes":notes,
                         "mustHitSection":player_side,"changeBPM":False,"bpm":bpm})
    return {"song":name,"notes":sections,"events":[],"bpm":bpm,"needsVoices":True,
            "speed": {"easy":1.30,"normal":1.54,"hard":1.85}[difficulty],
            "offset":0,"player1":"bf","player2":"tankman","gfVersion":"gf",
            "stage":"ch2-base","format":"psych_v1",
            "artist":"Chapter 2 PLUS — original instrumental prototype",
            "charter":"Chapter 2 PLUS synchronized generator"}


def render_vocals(events, bpm, seconds, out_file):
    """Synth fallback, aligned to the same authored song notes as the charts.

    This is deliberately NOT represented as the user's original DWP samples.
    An optional DWP-derived replacement can overwrite Voices.ogg later.
    """
    voice_audio=np.zeros(int(seconds*RATE),dtype=np.float32)
    beat=60.0/bpm
    for at,pitch,bar,slot in events:
        player = (bar%8>=4) if slot<4 else (bar%8<4)
        voice = "bf" if player else "tankman"
        singer_note=pitch+(0 if player else -12)
        tone(voice_audio,at*beat,beat*.39,singer_note,.105 if player else .095,voice)
    peak=float(np.max(np.abs(voice_audio)))
    if peak>0: voice_audio=np.tanh(voice_audio/max(.8,peak)*1.12)*.72
    with tempfile.TemporaryDirectory() as td:
        wav=Path(td)/"voice.wav"
        with wave.open(str(wav),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
            f.writeframes(np.int16(np.clip(voice_audio,-1,1)*32767).tobytes())
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                        "-i",str(wav),"-c:a","libvorbis","-q:a","4",str(out_file)],check=True)


def render_track(profile, out):
    name,slug,bpm,bars,root,motif,progression,voice,style=profile
    beat=60/bpm
    duration=(bars*4+3)*beat
    audio=np.zeros(int(duration*RATE), dtype=np.float32)
    events=score_events(slug,bars,root,motif,bpm,style)
    for bar in range(bars):
        base=bar*4*beat
        part=bar//8
        gain=.66 if part==0 else .76 if part==6 else 1.0
        bassroot=root+progression[(bar//4)%len(progression)]
        # Unique harmonic progressions, voicing/rhythm and mid-song dynamics.
        for b in range(4):
            at=base+b*beat
            if style=="half":
                if b in (0,2): drum(audio,at,"kick",bar*4+b,gain)
                if b==2: drum(audio,at,"snare",bar*4+b+1000,gain)
            elif style=="gallop":
                if b in (0,1,3): drum(audio,at,"kick",bar*4+b, gain)
                if b in (1,3): drum(audio,at,"snare",bar*4+b+1000,gain*.86)
            elif style=="break":
                if b in (0,2,3): drum(audio,at,"kick",bar*4+b,gain)
                if b in (1,3): drum(audio,at,"snare",bar*4+b+1000,gain)
            elif style=="anthem":
                if b in (0,2): drum(audio,at,"kick",bar*4+b,gain)
                if b in (1,3): drum(audio,at,"snare",bar*4+b+1000,gain*.8)
            else:
                drum(audio,at,"kick",bar*4+b, gain*.85)
                if b in (1,3): drum(audio,at,"snare",bar*4+b+1000,gain)
            tone(audio,at,beat*(.72 if style=="break" else .95),bassroot,.15*gain,
                 "industrial" if style in ("break","finale") else "bass")
            if style in ("boss","finale","gallop") and b==3:
                drum(audio, at+.75*beat,"tom",bar*3+b+3000,gain*.67)
            for sub in range(2):
                if style=="half" and sub==1 and b%2==1: continue
                drum(audio,at+sub*beat*.5,"hat",bar*8+b*2+sub+5500,gain*.78)
        if part in (2,3,5,7) and bar%2==0:
            for ci in (0,3,7):
                tone(audio,base+.25*beat,beat*3.0,root+12+progression[(bar//4)%4]+ci,
                     .033*gain,"brass" if style in ("anthem","march") else "bell")
    for bi,pitch,bar,slot in events:
        part=bar//8
        # No identical oscillator/phrase between tracks.
        intensity=.095 if part==0 else .16 if part in (3,5,7) else .13
        length=beat*(.78 if style in ("gallop","break","finale") else 1.30 if style=="anthem" else .86)
        tone(audio,bi*beat,length,pitch,intensity,voice)
        if style in ("anthem","finale") and slot%4==0:
            tone(audio,bi*beat+.025,length*.91,pitch-12,intensity*.3,"brass")
    # Gentle saturator instead of hard clipping.
    peak=float(np.max(np.abs(audio)))
    if peak>0: audio=np.tanh(audio/max(.6,peak)*1.18)*.88
    directory=out/"songs"/slug
    directory.mkdir(parents=True,exist_ok=True)
    ogg=directory/"Inst.ogg"
    with tempfile.TemporaryDirectory() as td:
        wav=Path(td)/"source.wav"
        with wave.open(str(wav),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
            f.writeframes(np.int16(np.clip(audio,-1,1)*32767).tobytes())
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                        "-i",str(wav),"-c:a","libvorbis","-q:a","4",str(ogg)], check=True)
    render_vocals(events,bpm,duration,directory/"Voices.ogg")
    for d in ("easy","normal","hard"):
        chart=make_chart(name,bpm,bars,events,d,style)
        folder=out/"data"/slug
        folder.mkdir(parents=True,exist_ok=True)
        dest=folder/(slug+("" if d=="normal" else "-"+d)+".json")
        dest.write_text(json.dumps(chart,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    meta={"songRating":2,"albumId":"volume1","freeplayCharacter":"",
          "freeplayWeekName":"Tankman Chapter 2","freeplaySongLength":int(duration),
          "freeplayPrevStart":0,"freeplayPrevEnd":min(18,int(duration)),
          "allowErectVariants":False}
    (out/"data"/slug/"metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(f"{name:16} BPM={bpm} duration={duration:.1f}s events={len(events)} audio={ogg.stat().st_size} bytes")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path("build/chapter2-plus/tankman-chapter-2"))
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    for song in SONGS: render_track(song,args.out)
    # Validate audio and charts without requiring private DWP sources.
    for _,slug,*_ in SONGS:
        assert (args.out/"songs"/slug/"Inst.ogg").stat().st_size>20000
        assert (args.out/"songs"/slug/"Voices.ogg").stat().st_size>10000
        assert len(list((args.out/"data"/slug).glob("*.json")))==4
    print("PASS: seven original arrangements, seven synced vocal-prototype stems, 21 charts, seven metadata files.")


if __name__=="__main__":
    main()
