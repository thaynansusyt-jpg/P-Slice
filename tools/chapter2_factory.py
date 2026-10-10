#!/usr/bin/env python3
"""Build Chapter 2 music, charts and backgrounds (Tankman sprite comes from P-Slice).

Dependencies: Pillow, NumPy, FFmpeg.
Reproducible, no copyrighted FNF songs/assets are used.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mods" / "tankman-chapter-2"
SHARED = ROOT / "assets" / "shared" / "images"
SR = 22050
SONGS = [
    ("Redeploy", "redeploy", 140, 0),
    ("Blackout", "blackout", 155, 1),
    ("Onslaught", "onslaught", 165, 2),
    ("Warzone", "warzone", 170, 3),
    ("Last Stand", "last-stand", 180, 4),
    ("No More Heroes", "no-more-heroes", 190, 5),
]
C = {"ink": (12, 14, 20, 255), "orange": (255, 105, 29, 255),
     "white": (244, 242, 233, 255), "red": (212, 34, 58, 255),
     "gray": (50, 51, 61, 255), "dark": (24, 24, 31, 255)}

def mkdir(file):
    file.parent.mkdir(parents=True, exist_ok=True)
    return file

def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def text(draw, xy, label, size, fill=None, stroke=0):
    draw.text(xy, label, font=font(size), fill=fill or C["white"],
              stroke_width=stroke, stroke_fill=C["ink"])

def background_art():
    sky=Image.new("RGBA",(1600,900),C["ink"])
    d=ImageDraw.Draw(sky)
    for y in range(900):
        blend=y/900
        d.line((0,y,1600,y),fill=(int(8+35*blend),int(14+11*blend),int(29+11*blend),255))
    d.ellipse((1060,90,1520,550),fill=(209,75,21,255))
    for i in range(14):
        x=70+(i*103)%1450
        d.line((x,600,x+30,300+(i*47)%240),fill=(31,33,44,180),width=9)
    sky.save(mkdir(MOD/"images"/"chapter2"/"sky.png"))
    city=Image.new("RGBA",(1600,820),(0,0,0,0));d=ImageDraw.Draw(city)
    for i in range(17):
        x=i*105-50
        height=220+(i*131)%240
        d.rectangle((x,720-height,x+90,800),fill=(12,15,22,255))
        for r in range(4):
            for col in range(2):
                if (i+r+col)%3==0:
                    d.rectangle((x+14+col*38,740-height+r*54,x+29+col*38,757-height+r*54),fill=(190,69,26,255))
        d.line((x+40,720-height,x+40,640-height),fill=(10,12,19,255),width=7)
    d.polygon(((1120,340),(1450,360),(1320,430)),fill=(3,8,13,255))
    city.save(mkdir(MOD/"images"/"chapter2"/"city.png"))
    ground=Image.new("RGBA",(1600,320),(0,0,0,0));d=ImageDraw.Draw(ground)
    d.polygon(((0,40),(1600,18),(1600,320),(0,320)),fill=(37,35,40,255))
    d.line((0,43,1600,21),fill=(255,95,29,255),width=9)
    for i in range(23):
        x=(i*127)%1560;y=95+(i*41)%190
        d.polygon(((x,y),(x+35,y-13),(x+72,y+12),(x+8,y+32)),fill=(19,20,25,255))
    ground.save(mkdir(MOD/"images"/"chapter2"/"ground.png"))
    signal=Image.new("RGBA",(230,230),(0,0,0,0));d=ImageDraw.Draw(signal)
    for r in range(105,25,-22):
        d.arc((115-r,115-r,115+r,115+r),15,325,fill=C["red"],width=7)
    d.ellipse((103,103,127,127),fill=C["orange"])
    signal.save(mkdir(MOD/"images"/"chapter2"/"signal.png"))
    # Main menu artwork, with open space in the middle for menu text.
    menu=sky.crop((0,0,1280,720)).copy()
    menu.alpha_composite(city.resize((1280,656)),(0,64))
    dd=ImageDraw.Draw(menu,"RGBA")
    dd.rounded_rectangle((75,68,1210,655),radius=28,fill=(5,7,13,215),outline=(255,116,31,255),width=6)
    text(dd,(132,92),"VS TANKMAN",72,stroke=3)
    text(dd,(141,180),"CHAPTER 2 // EMERGENCY SIGNAL",29,C["orange"])
    text(dd,(850,583),"SIX ORIGINAL TRACKS",24)
    text(dd,(142,587),"THE RADIO NEVER WENT QUIET",20,C["orange"])
    menu.save(mkdir(SHARED/"chapter2"/"menu.png"))
    menu.save(mkdir(MOD/"images"/"menubackgrounds"/"menu_ch2-base.png"))
    for p in range(2):
        pass
    btn=Image.new("RGBA",(530,256),(0,0,0,0));d=ImageDraw.Draw(btn)
    for i in range(2):
        y=i*128
        d.rounded_rectangle((2,y+7,525,y+117),20,
            fill=(34,34,45,250) if i==0 else (243,103,22,255),
            outline=C["orange"] if i==0 else C["white"],width=6)
        text(d,(30,y+35),"TANKMAN CH. 2",47,C["white"] if i==0 else C["ink"],stroke=1)
    path=mkdir(SHARED/"mainmenu"/"menu_chapter2.png");btn.save(path)
    xml=Element("TextureAtlas",imagePath="menu_chapter2.png")
    SubElement(xml,"SubTexture",name="chapter2 basic0000",x="0",y="0",width="530",height="128")
    SubElement(xml,"SubTexture",name="chapter2 white0000",x="0",y="128",width="530",height="128")
    ElementTree(xml).write(path.with_suffix(".xml"),encoding="utf-8",xml_declaration=True)

def compose_chart(name, slug, bpm, identity, difficulty):
    density={"easy":0.53,"normal":0.76,"hard":1.0}[difficulty]
    sections=[]
    beatms=60000/bpm
    for s in range(48):
        take=(s//2)%2==1
        notes=[]
        for j in range(8):
            if j%2 and density<0.7: continue
            if j==7 and density<0.9: continue
            if j==5 and density<0.8: continue
            lane=(j + s + identity*2 + (s//8))%4
            is_player = j%4 in (0,1,3)
            # Psych chart: columns 0-3 represent the section's lead side.
            col = lane + (0 if (take == is_player) else 4)
            timestamp=round((s*4+j*.5)*beatms,3)
            notes.append([timestamp,col,0])
        sections.append({"sectionBeats":4,"sectionNotes":notes,"mustHitSection":take,"changeBPM":False,"bpm":bpm})
    return {"song":name,"notes":sections,"events":[],"bpm":bpm,"needsVoices":False,
        "speed":1.45+identity*.09+(.18 if difficulty=="hard" else -.08 if difficulty=="easy" else 0),
        "offset":0,"player1":"bf","player2":"tankman","gfVersion":"gf",
        "stage":"ch2-base","format":"psych_v1","artist":"Chapter 2 Original Demo",
        "charter":"Chapter 2 Generator"}

SCALE=[0,3,5,7,10,12,15,17]
def add_wave(buf,start,duration,freq,amp=0.2,kind="lead"):
    length=int(SR*duration)
    pos=int(SR*start)
    length=min(length,len(buf)-pos)
    if length<=0:return
    t=np.arange(length,dtype=np.float32)/SR
    if kind=="bass": wavepart=np.sin(2*np.pi*freq*t)+.22*np.sin(4*np.pi*freq*t)
    else:wavepart=np.sin(2*np.pi*freq*t)+.25*np.sin(6*np.pi*freq*t)
    env=np.minimum(1,t/.015)*np.exp(-t/(duration*.62))
    buf[pos:pos+length] += (amp*wavepart*env).astype(np.float32)

def add_drum(buf,start,kind,seed):
    rng=np.random.default_rng(seed)
    length=int(SR*(.16 if kind=="kick" else .09))
    pos=int(SR*start)
    if pos+length>len(buf):return
    t=np.arange(length,dtype=np.float32)/SR
    if kind=="kick":
        hit=np.sin(2*np.pi*(65*t+35*t*np.exp(-t*28)))*np.exp(-t*27)*.55
    else:
        hit=rng.normal(size=length).astype(np.float32)*np.exp(-t*40)*(.23 if kind=="snare" else .12)
    buf[pos:pos+length]+=hit.astype(np.float32)

def export_audio(name,slug,bpm,identity):
    beat=60/bpm
    duration=48*4*beat+1.25
    audio=np.zeros(int(duration*SR),np.float32)
    root_note=[36,39,41,43,46,48][identity]
    for b in range(48*4):
        start=b*beat
        bar=b//4
        chord_degree=(bar//2+identity)%len(SCALE)
        midi=root_note+SCALE[chord_degree]
        freq=440*2**((midi-69)/12)
        add_wave(audio,start,beat*.88,freq,.13,"bass")
        add_drum(audio,start,"kick",b)
        if b%4 in (1,3):add_drum(audio,start,"snare",b+1000)
        for half in range(2):
            sub=start+half*beat*.5
            add_drum(audio,sub,"hat",b*2+half+5000)
            idx=(b*3+half+bar//4+identity)%len(SCALE)
            lead_midi=root_note+24+SCALE[idx]
            lead_f=440*2**((lead_midi-69)/12)
            amp=.13 + .03*(identity/5)
            add_wave(audio,sub,beat*.39,lead_f,amp)
        if b%8==0: add_wave(audio,start,beat*1.8,freq*2,.08)
    peak=np.max(np.abs(audio))
    if peak>0:audio=np.tanh(audio/(peak+1e-9)*1.35)*.84
    out=mkdir(MOD/"songs"/slug/"Inst.ogg")
    with tempfile.TemporaryDirectory() as td:
        wav=Path(td)/"scratch.wav"
        with wave.open(str(wav),"wb") as wf:
            wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(SR)
            wf.writeframes((audio*32767).astype("<i2").tobytes())
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
            "-i",str(wav),"-c:a","libvorbis","-q:a","4",str(out)],check=True)
    print(f"{name}: {duration:.1f}s, {bpm} BPM, {out.stat().st_size} bytes")

def main():
    background_art()
    for name,slug,bpm,identity in SONGS:
        for diff in ("easy","normal","hard"):
            path=mkdir(MOD/"data"/slug/(slug+("" if diff=="normal" else "-"+diff)+".json"))
            path.write_text(json.dumps(compose_chart(name,slug,bpm,identity,diff),
                ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
        export_audio(name,slug,bpm,identity)
    print("Chapter 2 music demos, backgrounds and 18 charts generated. Tankman is loaded from original P-Slice files.")

if __name__=="__main__":
    main()
