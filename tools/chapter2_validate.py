#!/usr/bin/env python3
"""Check distributable content against P-Slice's absolute-lane chart loader."""
import collections, json, math, subprocess
from pathlib import Path

def validate(root):
    summary=[]
    week=json.loads((root/'weeks/tankman-chapter-2.json').read_text())
    assert len(week['songs'])==7
    for entry in week['songs']:
        slug=entry[0].lower().replace(' ','-')
        durations=[]
        for stem in ('Inst','Voices'):
            path=root/'songs'/slug/(stem+'.ogg')
            info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,sample_rate','-of','json',str(path)]))
            assert info['streams'][0]['codec_name']=='vorbis',path
            duration=float(info['format']['duration']);durations.append(duration)
            proc=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True)
            assert proc.returncode==0,proc.stderr.decode()
        assert abs(durations[0]-durations[1])<.05,slug
        counts=[]
        for diff in ('easy','normal','hard'):
            suffix='' if diff=='normal' else '-'+diff
            path=root/'data'/slug/(slug+suffix+'.json');d=json.loads(path.read_text())
            assert d['format']=='psych_v1' and d['needsVoices']
            assert d['player1']=='bf' and d['player2']=='tankman'
            assert d['song'].lower().replace(' ','-')==slug,(path,d['song'])
            player=[];opp=[]
            for section in d['notes']:
                for n in section['sectionNotes']:
                    assert len(n)>=3 and all(math.isfinite(x) for x in n[:3]),path
                    assert n[1]==int(n[1]) and 0<=n[1]<8
                    assert n[0]>=0 and n[2]>=0 and (n[0]+n[2])/1000<durations[0]
                    (player if n[1]<4 else opp).append(n)
            assert player and opp,path
            events=[]
            for n in player:
                events.append((n[0],1));events.append((n[0]+max(1,n[2]),-1))
            held=0;maximum=0
            for at,delta in sorted(events):held+=delta;maximum=max(maximum,held)
            assert maximum<=2,(path,'more than two simultaneous player fingers',maximum)
            counts.append(len(player))
        assert counts[0]<=counts[1]<=counts[2],(slug,counts)
        summary.append(dict(song=slug,duration=round(durations[0],2),player_notes=counts,max_fingers=2))
    stage=json.loads((root/'stages/ch2-base.json').read_text())
    assert stage['boyfriend'][1]+350+412==stage['opponent'][1]+240+573==760
    return summary

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);args=ap.parse_args()
    print(json.dumps(dict(status='PASS',songs=validate(args.root),charts=21,stems=14),indent=2))
