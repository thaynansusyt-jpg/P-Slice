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
    """Distinct layered industrial night scene, generated only from geometric shapes."""
    from random import Random
    rng=Random(2026)
    sky=Image.new("RGBA",(1600,900),(0,0,0,255))
    d=ImageDraw.Draw(sky)
    for y in range(900):
        t=y/900
        d.line((0,y,1600,y),
            fill=(int(8+27*t),int(9+12*t),int(23+18*t),255))
    # Distinct moon with orange glow: black and violet, not a flat sunset.
    for rad in range(315,205,-6):
        k=(315-rad)/110
        d.ellipse((1180-rad,250-rad,1180+rad,250+rad),
            fill=(int(35+177*k),int(17+54*k),int(33-8*k),255))
    d.ellipse((958,25,1402,469),fill=(247,96,20,255))
    for j in range(28):
        px=995+rng.randint(0,360)
        py=35+rng.randint(0,380)
        size=rng.randint(5,30)
        d.ellipse((px-size,py-size,px+size,py+size),outline=(185,65,22,170),width=3)
    # Streaking clouds crossing the moon.
    for i in range(35):
        x=rng.randint(-150,1700)
        y=rng.randint(40,570)
        width=rng.randint(80,240)
        c=(16,13+rng.randint(0,9),31,230)
        d.ellipse((x,y,x+width,y+rng.randint(18,45)),fill=c)
    for i in range(95):
        x=rng.randint(0,1600)
        y=rng.randint(0,440)
        if 940<x<1410 and y<490:continue
        d.point((x,y),fill=(194,168,173,255))
    sky.save(mkdir(MOD/"images"/"chapter2"/"sky.png"))
    # Distant skyline as a separate transparent parallax layer.
    city=Image.new("RGBA",(1600,820),(0,0,0,0))
    d=ImageDraw.Draw(city)
    for i in range(29):
        x=i*62-32
        hh=rng.randint(155,430)
        y=710-hh
        fill=(12+rng.randint(0,9),12+rng.randint(0,7),23+rng.randint(0,7),255)
        d.rectangle((x,y,x+66,805),fill=fill)
        if i%4==0:
            d.line((x+22,y,x+22,y-105),fill=(16,13,23),width=7)
            d.line((x+10,y-55,x+42,y-55),fill=(18,16,28),width=3)
        for floor in range(7):
            for col in range(2):
                wy=y+16+floor*44;wx=x+11+col*29
                if wy<760 and rng.random()<.30:
                    d.rectangle((wx,wy,wx+10,wy+11),
                      fill=(237,91,30,220))
    # Elevated transmission bridges and guard towers.
    d.line((0,462,1600,438),fill=(9,11,19,255),width=22)
    for x in range(0,1600,180):
        d.line((x,465,x+80,380),fill=(12,13,19,255),width=10)
        d.line((x+80,380,x+180,462),fill=(12,13,19,255),width=9)
    for x in (98,488,1450):
        d.rectangle((x,225,x+78,710),fill=(14,13,21,255))
        d.rectangle((x-19,205,x+98,255),fill=(21,18,27,255),outline=(243,103,26,255),width=4)
        for c in range(3):
            d.rectangle((x+8+c*22,220,x+22+c*22,236),fill=(239,89,25,255))
    city.save(mkdir(MOD/"images"/"chapter2"/"city.png"))
    ground=Image.new("RGBA",(1600,330),(0,0,0,0))
    d=ImageDraw.Draw(ground)
    d.polygon(((0,39),(1600,19),(1600,330),(0,330)),fill=(20,21,31,255))
    d.line((0,39,1600,19),fill=(255,95,26,255),width=6)
    for k in range(32):
        x=rng.randint(0,1520);y=rng.randint(69,300)
        z=rng.randint(5,45)
        d.polygon(((x,y),(x+z,y-4),(x+z+11,y+7),(x+10,y+z//3)),
          fill=(10,11,18,255))
    for x in range(-70,1630,90):
        d.line((x,170,x+160,330),fill=(34,30,42,255),width=4)
    ground.save(mkdir(MOD/"images"/"chapter2"/"ground.png"))
    signal=Image.new("RGBA",(230,230),(0,0,0,0))
    d=ImageDraw.Draw(signal)
    for r in (45,73,103):
        d.arc((115-r,115-r,115+r,115+r),15,325,fill=(242,53,42,255),width=6)
    d.ellipse((108,108,123,123),fill=(255,142,42,255))
    signal.save(mkdir(MOD/"images"/"chapter2"/"signal.png"))
    # Export the main menu as a clean landscape composition WITHOUT rasterized
    # menu text: the layout and translations render on top in Haxe.
    menu=Image.new("RGBA",(1280,720),(0,0,0,255))
    menu.alpha_composite(sky.resize((1280,720)))
    menu.alpha_composite(city.resize((1280,656)),(0,64))
    menu.alpha_composite(ground.resize((1280,180)),(0,540))
    shade=Image.new("RGBA",menu.size,(0,0,0,0))
    q=ImageDraw.Draw(shade)
    for y in range(720):
        alpha=int(14+50*(y/720))
        q.line((0,y,1280,y),fill=(4,5,11,alpha))
    menu=Image.alpha_composite(menu,shade)
    menu.save(mkdir(SHARED/"chapter2"/"menu.png"))
    menu.save(mkdir(MOD/"images"/"menubackgrounds"/"menu_ch2-base.png"))
    # The animated main menu button has original highlight frames.
    btn=Image.new("RGBA",(530,256),(0,0,0,0))
    d=ImageDraw.Draw(btn)
    for i in range(2):
        y=i*128
        d.rounded_rectangle((4,y+8,526,y+118),18,
            fill=(22,24,33,244) if i==0 else (255,114,37,255),
            outline=(255,113,40,255) if i==0 else (255,242,221,255),width=5)
        text(d,(34,y+39),"TANKMAN CHAPTER 2",37,
             C["white"] if i==0 else C["ink"],stroke=1)
    out=mkdir(SHARED/"mainmenu"/"menu_chapter2.png")
    btn.save(out)
    xml=Element("TextureAtlas",imagePath="menu_chapter2.png")
    SubElement(xml,"SubTexture",name="chapter2 basic0000",x="0",y="0",width="530",height="128")
    SubElement(xml,"SubTexture",name="chapter2 white0000",x="0",y="128",width="530",height="128")
    ElementTree(xml).write(out.with_suffix(".xml"),encoding="utf-8",xml_declaration=True)

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
