#!/usr/bin/env python3
"""Render only the keep ranges of a video at max quality (never touches the input).
Usage: render_cut.py in.mp4 keep.json out.mp4 [--vf "extra,video,filters"] [--af "extra,audio,filters"]
"""
import argparse, json, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("keep"); ap.add_argument("out")
ap.add_argument("--vf", default=""); ap.add_argument("--af", default="")
a = ap.parse_args()
keep = json.load(open(a.keep))["keep"]
parts, labels = [], ""
for i, (s, e) in enumerate(keep):
    parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}]")
    parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0,e-s-0.01):.3f}:d=0.01[a{i}]")
    labels += f"[v{i}][a{i}]"
parts.append(f"{labels}concat=n={len(keep)}:v=1:a=1[vc][ac]")
parts.append(f"[vc]{a.vf or 'null'}[vo]"); parts.append(f"[ac]{a.af or 'anull'}[ao]")
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.src,
       "-filter_complex", ";".join(parts), "-map", "[vo]", "-map", "[ao]",
       "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", a.out]
subprocess.run(cmd, check=True)
print(a.out)
