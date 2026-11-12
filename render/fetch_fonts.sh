#!/usr/bin/env bash
# Downloads the two open-licensed fonts used by the renderer (OFL / Apache 2.0).
set -euo pipefail
dir="$(cd "$(dirname "$0")" && pwd)/fonts"
mkdir -p "$dir"
curl -fsSL -o "$dir/Rye-Regular.ttf" https://github.com/google/fonts/raw/main/ofl/rye/Rye-Regular.ttf
curl -fsSL -o "$dir/LuckiestGuy-Regular.ttf" https://github.com/google/fonts/raw/main/apache/luckiestguy/LuckiestGuy-Regular.ttf

# Offline backup voice (Piper, MIT; voice model from rhasspy/piper-voices)
vdir="$(cd "$(dirname "$0")" && pwd)/voices"
mkdir -p "$vdir"
base=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high
curl -fsSL -o "$vdir/en_US-ryan-high.onnx" "$base/en_US-ryan-high.onnx"
curl -fsSL -o "$vdir/en_US-ryan-high.onnx.json" "$base/en_US-ryan-high.onnx.json"
