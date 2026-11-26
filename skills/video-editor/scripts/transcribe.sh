#!/usr/bin/env bash
# Word-level Whisper transcript. Usage: transcribe.sh <video> <out_dir> [model] [language]
# Writes <out_dir>/<basename>.json (segments[].words[] with start/end).
set -euo pipefail
IN="$1"; OUT="${2:-.}"; MODEL="${3:-medium}"; LANGUAGE="${4:-ms}"
mkdir -p "$OUT"
whisper "$IN" --model "$MODEL" --language "$LANGUAGE" --task transcribe \
  --word_timestamps True --output_format json --output_dir "$OUT" --fp16 False \
  --condition_on_previous_text False
echo "Transcript: $OUT/$(basename "${IN%.*}").json"
