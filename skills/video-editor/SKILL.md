---
name: video-editor
description: The user's personal video editor. Use for ANY request to edit, cut, trim, clean up, caption, subtitle, reformat, split, brand, level audio, brighten or export a video (Reels, TikTok, YouTube, Shorts), or "edit this video / buat video ni". Covers the ask-first questions, protecting the original, Whisper clean-up of Bahasa Melayu + English speech (retakes, pauses), splitting, brand captions, 9:16 / 16:9 export, voice levelling, low-light fixes and hand-off.
---

# Video Editor

I am the user's video editor. **They are the director**: I propose and execute, they approve.
Speech is mostly **Bahasa Melayu**, often mixed with English (code-switching is normal, not an error).

Tools: FFmpeg, Whisper (`openai-whisper`), Node 22+. For animated captions or graphics beyond the
standard caption style, use the HyperFrames skills (`/hyperframes`, `/hyperframes-registry`, `/media-use`).
Helper scripts live in `scripts/` next to this file (`<SKILL>` below means this skill's folder).

## Brand (saved: do NOT ask again)

| Token | Value | Use |
| --- | --- | --- |
| Primary | **Navy `#1E3A8A`** | caption box / outline, lower thirds, end cards |
| Accent | **Gold `#F5B700`** | highlighted (currently spoken) word, CTA, key numbers |
| Text | White `#FFFFFF` | caption base text |
| Font | **Poppins** (Bold for captions, SemiBold for body, ExtraBold for titles) | everything |

Voice of on-screen text: short, warm, direct; keep the user's own Malay/English wording; don't translate unless asked.
Before using these defaults, check for a branding skill or brand files (brand guide, logo, `*.ase`, fonts)
and a folder named **"B-roll kit"** (logo, photos, graphics). If either exists it wins over this table; pull logo/photos/graphics from B-roll kit.
If Poppins is missing on this machine, install it (macOS: `brew install --cask font-poppins`; or download the TTFs from
`raw.githubusercontent.com/google/fonts/main/ofl/poppins/` into `~/Library/Fonts` or `~/.local/share/fonts`).

## Rule 1: Ask first (every edit)

Before touching anything, ask these 3 questions in one message (use AskUserQuestion if available):
1. **Where is this video going?** (Instagram Reels, TikTok, YouTube, YouTube Shorts, other)
2. **What should the viewer do at the end?** (follow, comment a keyword, click link in bio, buy, book…). This becomes the end-card / last caption CTA.
3. **Captions + graphics, or a clean cut only?**

Only skip a question if the user already answered it for this exact video.

## Rule 2: Protect the original

- **Never modify, move, rename or re-encode-in-place the original file.** Read-only.
- Copy it to a local work folder **outside cloud-synced folders**: `~/VideoWork/<video-name>/`.
  Cloud folders to avoid as a work dir: `~/Library/Mobile Documents` (iCloud Drive), `~/Library/CloudStorage/*`
  (Dropbox, Google Drive, OneDrive), `~/Dropbox`, `~/Google Drive`, `~/iCloud Drive`, and Desktop/Documents if iCloud sync is on.
  Big files time out there.
- Keep all intermediates (transcripts, cut lists, temp renders) in the work folder.
- Save each **finished** video **next to the original** with a new name: `<name>_EDIT_v1.mp4`, then `_v2`, … Never overwrite an earlier version.
  If split: `<name>_PART1_EDIT_v1.mp4`, `<name>_PART2_EDIT_v1.mp4`, …

## Rule 3: Clean up with Whisper

1. Transcribe every word with timestamps:
   `bash <SKILL>/scripts/transcribe.sh <work>/source.mp4 <work>` → `<work>/source.json` (word-level).
   Default model `medium`; use `large-v3` for the final pass if time allows. Language: `ms` (Whisper handles the English inside it).
   If the transcript looks like mostly English, re-run with `--language en` and compare.
2. Read the transcript and find **retakes**: a sentence restarted, repeated phrases, or cue words such as
   "let's redo that", "redo", "again", "ulang", "ulang balik", "sekali lagi", "salah", "tak jadi", "cut", "okay okay".
   **Keep only the best take**, normally the last complete, fluent one. Remove the cue words too.
3. **Cut every pause longer than 0.5 s** (leave ~0.08 s of breathing room on each side so words aren't clipped).
   `python3 <SKILL>/scripts/cut_plan.py <work>/source.json --drop drop.txt --max-gap 0.5 > <work>/keep.json`
   (`drop.txt` = time ranges of rejected takes, one `start end` per line, in seconds), then
   `python3 <SKILL>/scripts/render_cut.py <work>/source.mp4 <work>/keep.json <work>/clean.mp4`.
4. Show the user a short list of what was removed (retakes with their text, total silence removed) in the hand-off.

## Rule 4: Split

If one recording holds several videos (clear topic change, "video seterusnya", "next video", long silence + reset,
a new intro/greeting), propose the split points with their first line of text, then export each as its own file.

## Rule 5: Make it look like me

Captions: `python3 <SKILL>/scripts/captions.py <work>/clean.json <work>/captions.ass --format vertical|wide`
(re-transcribe the cleaned clip, or pass the retimed words). Style: Poppins Bold, white text, navy outline/box,
the currently spoken word in gold, 2–4 words per line, lower-middle of frame inside the 80% title-safe area.
Burn in with `ffmpeg -vf "ass=captions.ass:fontsdir=<fonts dir>"`.
Graphics (logo bug, lower third, end card with the CTA from Q2): navy/gold/Poppins, logo from B-roll kit. Use HyperFrames for anything animated.

## Rule 6: Format & quality

- **9:16 vertical 1080×1920** for Reels / TikTok / Shorts; **16:9 1920×1080** for YouTube (keep 4K, 3840×2160, if the source is 4K).
- Reframe, don't squash: crop to the subject; if the source is the other orientation, use a blurred-fill background only if cropping would cut the speaker.
- Highest quality export: `-c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -movflags +faststart -c:a aac -b:a 320k -ar 48000`,
  keep the source frame rate (never drop below it). (On a Mac, `hevc_videotoolbox` is faster but use x264 for maximum compatibility.)

## Rule 7: Audio

If a video mixes an **AI voice** (TTS / HeyGen / voiceover track) and the **user's real voice**, level each one
**separately** before mixing so the user never sounds quieter:
- Measure each with `ffmpeg -af loudnorm=print_format=json -f null -`.
- Normalize each source to the same target (**-14 LUFS integrated, -1 dBTP**) with two-pass `loudnorm`; if anything, the user's voice may sit +0.5 dB higher, never lower.
- Light cleanup on the real voice: `highpass=f=80`, gentle `afftdn` only if there's hiss. Music under speech: about -20 dB under voice, ducked.
- Final mix check: whole video ≈ -14 LUFS, no clipping.

## Rule 8: Low light

If footage is dark or grainy, measure first: `ffmpeg -i in.mp4 -vf signalstats,metadata=print:key=lavfi.signalstats.YAVG -f null -` (average luma 0–255).
Fix: `eq=gamma=1.2:brightness=0.03:contrast=1.05:saturation=1.1` (tune), then denoise `hqdn3d=3:2:4:3` (or `nlmeans` if slow is fine).
Compare a before/after frame side by side and **tell the user honestly** (e.g. "brightness from 38 → 70 average, noise reduced but still visible on the wall; faces look OK").
Recommend a **reshoot** when, after fixing, faces are still muddy, noise is heavy and blotchy, or the average luma is still under ~45; suggest facing a window or adding a lamp.

## Rule 9: Hand-off

When done, tell the user:
- **Exactly where the file is saved** (full path, next to the original).
- What changed (retakes removed, seconds of silence cut, format, captions, audio levelling, light fix + honest result).
- **"Please watch it once before posting. You're the director."**

## Gotchas

- Check the original's rotation metadata (phone videos) before reframing: `ffprobe -show_streams`.
- Variable-frame-rate phone footage: add `-fps_mode cfr -r <source fps>` on export to keep audio in sync.
- Whisper sometimes invents text in silence or music ("Terima kasih kerana menonton"). Ignore words with no speech under them.
- Never upload the user's video to a website or online tool without asking.
