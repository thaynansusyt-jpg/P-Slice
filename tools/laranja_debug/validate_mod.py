#!/usr/bin/env python3
"""Static preflight for P-Slice/Psych mods, no dependencies outside stdlib.
Usage: python tools/laranja_debug/validate_mod.py /path/to/VsSenhorLaranja_PSlice_Teste
"""
import json
import sys
import struct
from pathlib import Path
from xml.etree import ElementTree as ET

def check(mod: Path):
    problems, warnings = [], []
    def require(relative):
        path = mod / relative
        if not path.exists():
            problems.append("Missing: " + relative)
        return path

    require("pack.json")
    for path in mod.rglob("*.json"):
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            problems.append(f"Invalid JSON {path.relative_to(mod)}: {exc}")
            continue
        relative = path.relative_to(mod).as_posix()
        if relative.startswith("stages/") and isinstance(obj, dict):
            for key in ("boyfriend", "opponent", "girlfriend"):
                value = obj.get(key)
                if not (isinstance(value, list) and len(value) == 2 and all(isinstance(n,(int,float)) for n in value)):
                    problems.append(f"{relative}: {key} must have two numeric values")
            camera = obj.get("camera_boyfriend", [0, 0])
            if isinstance(camera, list) and len(camera) == 2 and abs(camera[1]) > 150:
                warnings.append(f"{relative}: large BF camera Y offset ({camera[1]}); check gameplay on Android")
        if relative.startswith("images/menucharacters/") and isinstance(obj, dict):
            position = obj.get("position", [0, 0])
            if isinstance(position, list) and len(position) == 2 and abs(position[1]) > 100:
                warnings.append(f"{relative}: extreme menu offset Y ({position[1]}); could clip the portrait")
        if relative.startswith("characters/") and isinstance(obj, dict):
            for anim in obj.get("animations", []):
                if not anim.get("anim") or not anim.get("name"):
                    problems.append(f"{relative}: an animation is missing anim/name")
        if relative.startswith("data/") and path.name.endswith("-hard.json"):
            song = obj.get("song") if isinstance(obj, dict) else None
            if not isinstance(song, dict) or not isinstance(song.get("notes"), list):
                problems.append(f"{relative}: invalid song.notes")
            else:
                for i, section in enumerate(song["notes"]):
                    for note in section.get("sectionNotes", []):
                        if not (isinstance(note, list) and len(note) >= 3 and 0 <= note[1] <= 7):
                            problems.append(f"{relative}: bad 4K note in section {i}")
    for path in mod.rglob("*.xml"):
        try:
            root = ET.parse(path).getroot()
            png = path.with_suffix(".png")
            if not png.exists():
                problems.append(f"{path.relative_to(mod)}: matching PNG missing")
                continue
            with png.open("rb") as f:
                header = f.read(24)
            if header[:8] != b"\\x89PNG\\r\\n\\x1a\\n":
                problems.append(f"{png.relative_to(mod)}: invalid PNG")
                continue
            w,h = struct.unpack(">II", header[16:24])
            for frame in root.findall("SubTexture"):
                x,y= int(frame.attrib["x"]),int(frame.attrib["y"])
                fw,fh=int(frame.attrib["width"]),int(frame.attrib["height"])
                if min(x,y,fw,fh) < 0 or x+fw>w or y+fh>h:
                    problems.append(f"{path.relative_to(mod)}: frame outside image: {frame.attrib.get('name')}")
        except Exception as exc:
            problems.append(f"Atlas error {path.relative_to(mod)}: {exc}")
    return problems,warnings

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    mod=Path(sys.argv[1])
    if not mod.is_dir():
        print(f"Not a mod directory: {mod}")
        return 2
    problems,warnings=check(mod)
    for warning in warnings: print("WARNING:", warning)
    for problem in problems: print("ERROR:", problem)
    print(f"Preflight: {len(problems)} errors, {len(warnings)} warnings")
    return 1 if problems else 0

if __name__ == "__main__":
    raise SystemExit(main())
