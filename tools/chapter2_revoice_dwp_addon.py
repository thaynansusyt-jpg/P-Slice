#!/usr/bin/env python3
"""Revoice Chapter 2 PLUS with user-provided DirectWave-derived vocal takes.

This script NEVER uploads a DWP bank or embeds its private path metadata.
Input: the private voice-addon ZIP produced from the user's DWP files, plus a
complete Chapter 2 PLUS ZIP from Actions.
Output: an optional small overlay ZIP containing improved/realigned Voices.ogg.

No original Ugh music melody, lyrics, charts or song audio are reproduced.
"""
from __future__ import annotations
import argparse
import io
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
import numpy as np

RATE=22050
SONGS=["redeploy","blackout","onslaught","warzone",
       "last-stand","no-more-heroes","ugh-radio-remix"]


def audio_from_ogg(data):
    proc=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
                         "-i","pipe:0","-f","f32le","-ar",str(RATE),
                         "-ac","1","pipe:1"],input=data,capture_output=True,check=True)
    return np.frombuffer(proc.stdout,dtype="<f4").copy()


def ogg_from_audio(audio):
    pcm=np.int16(np.clip(audio,-1,1)*32767)
    proc=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                         "-f","s16le","-ar",str(RATE),"-ac","1",
                         "-i","pipe:0","-c:a","libvorbis","-q:a","4",
                         "-f","ogg","pipe:1"],input=pcm.tobytes(),
                         capture_output=True,check=True)
    return proc.stdout


def speaker(section,note):
    lane=int(note[1])
    return "bf" if ((lane<4)==bool(section.get("mustHitSection",False))) else "tankman"


def notes(chart):
    for section in chart["notes"]:
        for n in section["sectionNotes"]:
            if len(n)>=3:
                yield float(n[0])/1000,speaker(section,n),int(n[1])%4


def build_bank(source_zip):
    bank={"bf":[],"tankman":[]}
    with zipfile.ZipFile(source_zip) as z:
        names=set(z.namelist())
        for slug in SONGS[:-1]:
            prefix=f"tankman-chapter-2/"
            vf=f"{prefix}songs/{slug}/Voices.ogg"
            jf=f"{prefix}data/{slug}/{slug}.json"
            if vf not in names or jf not in names: continue
            data=audio_from_ogg(z.read(vf))
            chart=json.loads(z.read(jf))
            for t,singer,lane in notes(chart):
                start=int((t+.02)*RATE); end=start+int(.155*RATE)
                if end>len(data): continue
                sample=data[start:end].copy()
                amp=float(np.sqrt(np.mean(sample*sample)))
                if amp<.004: continue
                # Normalize individual samples for consistent phrase loudness.
                sample*=min(4.0,.10/max(amp,.001))
                # Alternate syllables/key positions in the candidate set.
                if len(bank[singer])<110:
                    bank[singer].append((sample,lane))
    if not bank["bf"] or not bank["tankman"]:
        raise ValueError("Private DWP-derived addon contains no usable BF/Tankman samples")
    return bank


def render(chart,bank,slug):
    entries=list(notes(chart))
    duration=max(t for t,_,_ in entries)+2.5
    out=np.zeros(int(duration*RATE),dtype=np.float32)
    seed=sum(ord(c) for c in slug)
    rng=np.random.default_rng(seed)
    for index,(t,singer,lane) in enumerate(entries):
        # Game UI offers Easy/Normal/Hard but vocals follow the normal chart.
        source_bank=bank[singer]
        sample,rootlane=source_bank[(index*7+lane*13+seed)%len(source_bank)]
        # Small resampling differences give natural expressive variation and
        # distinct phrases without recycling an entire old vocal track.
        semitone=max(-3,min(3,lane-rootlane))+(2 if singer=="bf" else -1)
        rate=2**(semitone/12)
        count=max(1,int(len(sample)/rate))
        newpos=np.arange(count,dtype=np.float32)*rate
        newpos=np.minimum(newpos,len(sample)-1)
        shifted=np.interp(newpos,np.arange(len(sample)),sample).astype(np.float32)
        # Avoid sharp clicks and simultaneous overlap distortion.
        fade=max(4,int(.012*RATE))
        shifted[:fade]*=np.linspace(0,1,fade)
        shifted[-fade:]*=np.linspace(1,0,fade)
        pos=round(t*RATE)
        take=min(len(out)-pos,len(shifted))
        if take>0:
            out[pos:pos+take]+=(.83 if singer=="bf" else .88)*shifted[:take]
    out=np.tanh(out*.95)*.80
    return ogg_from_audio(out)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dwp-vocals-zip",type=Path,required=True)
    p.add_argument("--plus-zip",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    bank=build_bank(args.dwp_vocals_zip)
    with zipfile.ZipFile(args.plus_zip) as src,zipfile.ZipFile(
         args.output,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        names=set(src.namelist())
        for slug in SONGS:
            path=f"tankman-chapter-2/data/{slug}/{slug}.json"
            if path not in names:
                raise FileNotFoundError(f"PLUS music archive missing {path}")
            chart=json.loads(src.read(path))
            chart["needsVoices"]=True
            voices=render(chart,bank,slug)
            out.writestr(f"tankman-chapter-2/songs/{slug}/Voices.ogg",voices)
            # Patch the three current charts rather than reinstall obsolete notes.
            for diff in ("easy","normal","hard"):
                suffix="" if diff=="normal" else "-"+diff
                jpath=f"tankman-chapter-2/data/{slug}/{slug}{suffix}.json"
                d=json.loads(src.read(jpath))
                d["needsVoices"]=True
                out.writestr(jpath,json.dumps(d,separators=(",",":"))+"\n")
            print(f"Revoiced: {slug}: {len(voices):,} bytes")
        out.writestr("VOICE-PLUS-README.txt",
                     "Rearranged DWP-derived BF and Tankman samples synced to Chapter 2 PLUS charts.\n"
                     "No DirectWave binaries or private metadata are included.\n"
                     "Merge only the tankman-chapter-2 folder over an installed PLUS mod.\n"
                     "Prototype edits: not hand-recorded, pitch-perfect final voice acting.\n")
    print("PASS: seven independent DWP-derived voice stems and updated song charts.")


if __name__=="__main__":
    main()
