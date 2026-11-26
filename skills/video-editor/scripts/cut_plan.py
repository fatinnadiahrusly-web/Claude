#!/usr/bin/env python3
"""Build a keep-list from a Whisper word-level JSON.
Removes rejected-take ranges (--drop file: 'start end' per line, seconds) and any pause > --max-gap.
Prints JSON: {"keep": [[s,e],...], "words": [...retimed to the cut timeline...], "removed_seconds": x}
Usage: cut_plan.py transcript.json [--drop drop.txt] [--max-gap 0.5] [--pad 0.08] [--duration SECONDS]
"""
import argparse, json

def load_words(path):
    d = json.load(open(path))
    if isinstance(d, dict) and "keep" in d and "words" in d:
        return d["words"]
    if isinstance(d, list):
        return d
    return [w for s in d.get("segments", []) for w in s.get("words", [])]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript"); ap.add_argument("--drop")
    ap.add_argument("--max-gap", type=float, default=0.5)
    ap.add_argument("--pad", type=float, default=0.08)
    ap.add_argument("--duration", type=float)
    a = ap.parse_args()
    drops = []
    if a.drop:
        for line in open(a.drop):
            p = line.split()
            if len(p) >= 2: drops.append((float(p[0]), float(p[1])))
    inside = lambda w: any(s <= (w["start"] + w["end"]) / 2 <= e for s, e in drops)
    words = [w for w in load_words(a.transcript) if w["word"].strip() and not inside(w)]
    spans = []
    for w in words:
        s, e = w["start"], w["end"]
        if spans and s - spans[-1][1] <= a.max_gap:
            spans[-1][1] = max(spans[-1][1], e)
        else:
            spans.append([s, e])
    end_limit = a.duration if a.duration else float("inf")
    keep = []
    for s, e in spans:
        s, e = max(0.0, s - a.pad), min(end_limit, e + a.pad)
        if keep and s <= keep[-1][1]: keep[-1][1] = e
        else: keep.append([round(s, 3), round(e, 3)])
    # retime words onto the cut timeline
    out, offset_t, i = [], 0.0, 0
    for s, e in keep:
        for w in words:
            if s <= w["start"] and w["end"] <= e + 1e-6:
                out.append({"word": w["word"], "start": round(w["start"] - s + offset_t, 3),
                            "end": round(w["end"] - s + offset_t, 3)})
        offset_t += e - s
    total = (a.duration or (words[-1]["end"] if words else 0))
    print(json.dumps({"keep": keep, "words": out, "kept_seconds": round(offset_t, 2),
                      "removed_seconds": round(max(0, total - offset_t), 2)}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
