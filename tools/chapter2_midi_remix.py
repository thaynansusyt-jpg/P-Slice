#!/usr/bin/env python3
"""Render the supplied Ugh MIDI with a new radio arrangement and sampled voices.

Inputs remain private. The voice addon supplies previously decoded DWP takes;
neither DirectWave files nor their machine metadata are copied into outputs.
Requires numpy, scipy and ffmpeg. MIDI format 0/1, PPQ, tempo events supported.
"""
import argparse, json, math, struct, subprocess
from pathlib import Path
import numpy as np
from scipy.signal import resample_poly
from chapter2_music_plus import RATE, tone, drum
from chapter2_revoice_dwp_addon import build_bank, ogg_from_audio

def vlq(data, pos):
    value = 0
    for _ in range(4):
        c = data[pos]; pos += 1; value = (value << 7) | (c & 127)
        if c < 128: return value, pos
    raise ValueError('Invalid MIDI variable-length integer')

def read_midi(path):
    data = path.read_bytes()
    if data[:4] != b'MThd': raise ValueError('Not a MIDI file')
    size = int.from_bytes(data[4:8], 'big')
    fmt, count, ppq = struct.unpack('>HHH', data[8:14])
    if fmt not in (0, 1) or ppq & 0x8000: raise ValueError('Requires format 0/1 PPQ MIDI')
    pos = 8 + size; tracks = []; tempos = [(0, 500000)]
    for index in range(count):
        if data[pos:pos+4] != b'MTrk': raise ValueError('Missing MIDI track')
        size = int.from_bytes(data[pos+4:pos+8], 'big'); chunk = data[pos+8:pos+8+size]; pos += size+8
        p = tick = 0; running = None; active = {}; notes = []; name = ''; program = 0
        while p < len(chunk):
            delta, p = vlq(chunk, p); tick += delta
            if chunk[p] >= 128:
                status = chunk[p]; p += 1
                if status < 240: running = status
            else:
                if running is None: raise ValueError('Missing running status')
                status = running
            if status == 255:
                kind = chunk[p]; p += 1; length, p = vlq(chunk,p); body = chunk[p:p+length]; p += length
                if kind == 3: name = body.decode('utf-8',errors='replace')
                if kind == 81: tempos.append((tick,int.from_bytes(body,'big')))
                if kind == 47: break
            elif status in (240,247):
                length,p = vlq(chunk,p);p += length
            else:
                kind = status >> 4; channel = status & 15
                length = 1 if kind in (12,13) else 2
                vals = chunk[p:p+length]; p += length
                if kind == 12: program = vals[0]
                elif kind == 9 and vals[1] > 0:
                    active.setdefault((channel,vals[0]),[]).append((tick,vals[1]))
                elif kind == 8 or (kind == 9 and vals[1] == 0):
                    key=(channel,vals[0]); queue=active.get(key,[])
                    if queue:
                        start,vel=queue.pop(0);notes.append((start,tick,vals[0],vel,channel))
        for (ch,pitch),queue in active.items():
            for start,vel in queue: notes.append((start,tick,pitch,vel,ch))
        tracks.append(dict(index=index,name=name,program=program,notes=sorted(notes)))
    tempo_map = dict(tempos); tempos=sorted(tempo_map.items())
    def seconds(tick):
        total=0.;last=0;tempo=500000
        for at,new in tempos:
            if at > tick: break
            total+=(at-last)*tempo/ppq/1e6;last=at;tempo=new
        return total+(tick-last)*tempo/ppq/1e6
    for tr in tracks:
        tr['events']=[(seconds(a),seconds(b)-seconds(a),p,v,ch,a/ppq) for a,b,p,v,ch in tr['notes']]
    return tracks,60e6/tempos[0][1],ppq

def fundamental(sample):
    # Pick a strong fundamental from a short voiced sample, avoiding DC/noise.
    a=sample.astype(float);a-=a.mean(); n=len(a)
    ac=np.fft.irfft(np.abs(np.fft.rfft(a,2*n))**2)[:n]
    lo=RATE//850;hi=min(n-1,RATE//75)
    lag=lo+int(np.argmax(ac[lo:hi]));hz=RATE/lag
    return 69+12*np.log2(hz/440)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--midi',type=Path,required=True)
    ap.add_argument('--voice-addon',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--opponent-track',type=int,default=8);ap.add_argument('--player-track',type=int,default=9)
    ap.add_argument('--inspect',action='store_true');args=ap.parse_args()
    tracks,bpm,ppq=read_midi(args.midi)
    for tr in tracks:
        pitches=[n[2] for n in tr['events']]
        print(tr['index'],tr['name'],'notes',len(pitches),'range',(min(pitches),max(pitches)) if pitches else '-')
    if args.inspect:return
    vocal_ids={args.opponent_track:'tankman',args.player_track:'bf'}
    bpm /= 2  # This source MIDI notates Ugh in double time (320 -> 160 BPM).
    duration=max(a+d for t in tracks for a,d,*_ in t['events'])+2
    inst=np.zeros(round(duration*RATE),np.float32);voices=np.zeros_like(inst)
    bank=build_bank(args.voice_addon)
    bank={s:[(a,fundamental(a)) for a,lane in arr] for s,arr in bank.items()}
    authored=[]
    for tr in tracks:
        singer=vocal_ids.get(tr['index'])
        for at,dur,pitch,vel,ch,beat in tr['events']:
            if singer:
                authored.append((at,dur,pitch,singer,beat))
                # Preserve MIDI melody while choosing the closest sampled root.
                source,root=min(bank[singer],key=lambda e:abs(e[1]-pitch))
                shift=np.clip(pitch-root,-12,12); factor=2**(shift/12)
                new=np.interp(np.arange(0,len(source),factor),np.arange(len(source)),source).astype(np.float32)
                target=max(round(.065*RATE),min(round(dur*RATE),round(.65*RATE)))
                new=np.tile(new,math.ceil(target/len(new)))[:target].copy()
                fade=min(round(.012*RATE),len(new)//3)
                new[:fade]*=np.linspace(0,1,fade);new[-fade:]*=np.linspace(1,0,fade)
                start=round(at*RATE);take=min(len(new),len(voices)-start)
                voices[start:start+take]+=new[:take]*(.90 if singer=='bf' else .95)
            elif ch==9:
                kind='kick' if pitch in (35,36) else 'snare' if pitch in (38,40) else 'tom' if pitch in (41,43,45,47,48,50) else 'hat'
                drum(inst,at,kind,int(at*1000)+pitch,vel/127*.8)
            else:
                palette='saw' if tr['index']==3 else 'bell' if tr['index']==7 else 'brass' if tr['index']==9 else 'bass'
                tone(inst,at,max(.04,dur),pitch,.09*vel/100,palette)
    # Radio identity: intro clicks and a restrained octave brass accent.
    for i in range(4):tone(inst,i*.12,.045,84,.03,'pulse')
    for at,dur,pitch,singer,beat in authored:
        if singer=='tankman' and int(beat)%8==0:tone(inst,at,max(.06,dur),pitch-12,.018,'brass')
    inst=np.tanh(inst)*.76;voices=np.tanh(voices*1.5)*.75
    slug='ugh-radio-remix';sd=args.out/'songs'/slug;sd.mkdir(parents=True,exist_ok=True)
    (sd/'Inst.ogg').write_bytes(ogg_from_audio(inst));(sd/'Voices.ogg').write_bytes(ogg_from_audio(voices))
    folder=args.out/'data'/slug;folder.mkdir(parents=True,exist_ok=True)
    bars=math.ceil(duration/(240/bpm))
    for diff in ('easy','normal','hard'):
        sections=[dict(sectionBeats=4,mustHitSection=False,sectionNotes=[],changeBPM=False,bpm=bpm) for _ in range(bars)]
        last={'bf':-1.,'tankman':-1.};held={'bf':[],'tankman':[]}
        for at,dur,pitch,singer,beat in sorted(authored):
            # One onset at a time per singer, with short holds leaving room for two thumbs.
            gap=.23 if diff=='easy' else .125 if diff=='normal' else .075
            if at-last[singer]<gap:continue
            last[singer]=at;bar=min(bars-1,int(at/(240/bpm)))
            lane=(pitch%4)+(0 if singer=='bf' else 4)
            sustain=max(0.,min(dur-.06,.36))*1000 if dur>.25 else 0
            sections[bar]['sectionNotes'].append([round(at*1000,3),lane,round(sustain,3)])
            if singer=='bf':sections[bar]['mustHitSection']=True
        # Cut holds before subsequent notes; never require three simultaneous fingers.
        for singer in ('bf','tankman'):
            ns=sorted([n for s in sections for n in s['sectionNotes'] if (n[1]<4)==(singer=='bf')])
            for a,b in zip(ns,ns[1:]):a[2]=round(max(0,min(a[2],b[0]-a[0]-35)),3)
        chart=dict(song='Ugh Radio Remix',notes=sections,events=[],bpm=bpm,needsVoices=True,speed={'easy':1.30,'normal':1.54,'hard':1.85}[diff],offset=0,player1='bf',player2='tankman',gfVersion='gf',stage='ch2-base',format='psych_v1',artist='Ugh MIDI fan remix / Senhor Laranja',charter='Chapter 2 MIDI notes, two-thumb arrangement')
        suffix='' if diff=='normal' else '-'+diff
        (folder/(slug+suffix+'.json')).write_text(json.dumps(chart,separators=(',',':'))+'\n')
    meta=dict(songRating=2,albumId='volume1',freeplayCharacter='',freeplayWeekName='Tankman Chapter 2',freeplaySongLength=round(duration),freeplayPrevStart=10,freeplayPrevEnd=28,allowErectVariants=False)
    (folder/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('Rendered Ugh MIDI remix:',bpm,'BPM',duration,'seconds',len(authored),'vocal events')
if __name__=='__main__':main()
