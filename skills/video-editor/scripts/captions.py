#!/usr/bin/env python3
"""Brand captions (ASS) from word timings: Poppins Bold, white text, navy box, active word in gold.
Input: Whisper JSON, a cut_plan.py JSON, or a list of {word,start,end}.
Usage: captions.py words.json out.ass [--format vertical|wide] [--max-words 3] [--upper]
Burn in: ffmpeg -i in.mp4 -vf "ass=out.ass:fontsdir=/path/to/fonts" ...
"""
import argparse, json

NAVY, GOLD, WHITE = "&H008A3A1E", "&H0000B7F5", "&H00FFFFFF"   # ASS = &HAABBGGRR
FONT = "Poppins"

def load_words(p):
    d = json.load(open(p))
    if isinstance(d, list): return d
    if "words" in d: return d["words"]
    return [w for s in d.get("segments", []) for w in s.get("words", [])]

def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def chunks(words, max_words, max_chars):
    cur = []
    for w in words:
        txt = w["word"].strip()
        if not txt: continue
        w = dict(w, word=txt)
        too_long = len(" ".join(x["word"] for x in cur + [w])) > max_chars
        gap = cur and w["start"] - cur[-1]["end"] > 0.35
        if cur and (len(cur) >= max_words or too_long or gap):
            yield cur; cur = []
        cur.append(w)
        if txt[-1] in ".?!,;:": yield cur; cur = []
    if cur: yield cur

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words"); ap.add_argument("out")
    ap.add_argument("--format", choices=["vertical", "wide"], default="vertical")
    ap.add_argument("--max-words", type=int, default=3)
    ap.add_argument("--upper", action="store_true")
    a = ap.parse_args()
    if a.format == "vertical": W, H, size, mv, mc = 1080, 1920, 100, 560, 18
    else: W, H, size, mv, mc = 1920, 1080, 64, 110, 34
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},{size},{WHITE},{GOLD},{NAVY},&H66000000,-1,0,0,0,100,100,0,0,3,14,0,2,{int(W*0.1)},{int(W*0.1)},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for c in chunks(load_words(a.words), a.max_words, mc):
        for i, w in enumerate(c):
            start = w["start"]
            end = c[i + 1]["start"] if i + 1 < len(c) else w["end"] + 0.15
            parts = []
            for j, x in enumerate(c):
                t = x["word"].upper() if a.upper else x["word"]
                parts.append(f"{{\\c{GOLD}}}{t}{{\\c{WHITE}}}" if j == i else t)
            pop = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if i == 0 else ""
            lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{pop}{' '.join(parts)}")
    open(a.out, "w", encoding="utf-8").write(head + "\n".join(lines) + "\n")
    print(f"{a.out}: {len(lines)} caption events")

if __name__ == "__main__":
    main()
