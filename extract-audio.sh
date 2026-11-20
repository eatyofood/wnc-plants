#!/usr/bin/env bash
# Download the highest-quality audio with yt-dlp and save it as MP3.
# A video that is already on disk has its audio track encoded to MP3.
set -euo pipefail

YTDLP="/home/brandon/miniconda3/bin/yt-dlp"
FFMPEG="/usr/bin/ffmpeg"
FFPROBE="/usr/bin/ffprobe"

out_dir="."
out_file=""
force_mp3=1

usage() {
  cat <<'EOF'
Usage: extract-audio.sh [options] URL-or-file [URL-or-file...]

yt-dlp picks the highest-bitrate audio, downloads it, and saves an MP3
at the highest VBR setting. A video file that is already on disk is not
downloaded again; ffmpeg encodes its audio track to MP3.

Options:
  -o, --out PATH   A directory, or one filename when there is one input
  --mp3            Same as the default. Kept so older commands still run.
  -h, --help       Show this help

~/.config/yt-dlp/config still applies (Deno and IPv4). An output name is
saved as .mp3 even when you type another extension.

Examples:
  ./extract-audio.sh 'https://www.youtube.com/watch?v=...'
  ./extract-audio.sh -o sounds/carolina-chickadee.mp3 'https://...'
  ./extract-audio.sh -o sounds/clip.mp3 ~/Downloads/bird.webm
EOF
}

die() {
  echo "$1" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--out)
      [[ $# -ge 2 ]] || die "Missing path after $1"
      if [[ "$2" == */ || -d "$2" ]]; then
        out_dir="${2%/}"
        out_file=""
      else
        out_file="$2"
        out_dir=""
      fi
      shift 2
      ;;
    --mp3)
      force_mp3=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      die "Unknown option: $1"
      ;;
    *)
      break
      ;;
  esac
done

[[ $# -ge 1 ]] || { usage >&2; exit 2; }
[[ -n "$out_file" && $# -gt 1 ]] && die "One output filename needs exactly one input. Pass a directory to -o for several inputs."
[[ -x "$YTDLP" ]] || die "yt-dlp not found at $YTDLP"
[[ -x "$FFMPEG" && -x "$FFPROBE" ]] || die "ffmpeg and ffprobe are required"

want_mp3() {
  [[ "$force_mp3" -eq 1 || "$out_file" == *.mp3 ]]
}

ext_for_codec() {
  case "$1" in
    aac|alac) echo m4a ;;
    opus) echo opus ;;
    mp3) echo mp3 ;;
    flac) echo flac ;;
    vorbis) echo ogg ;;
    wav|pcm_s16le|pcm_s24le|pcm_f32le) echo wav ;;
    *) echo mka ;;
  esac
}

dest_for() {
  local src=$1 ext=$2 stem
  if [[ -n "$out_file" ]]; then
    if want_mp3; then
      echo "${out_file%.*}.mp3"
    else
      echo "${out_file%.*}.$ext"
    fi
    return
  fi
  stem=$(basename "$src")
  stem=${stem%.*}
  if want_mp3; then
    ext=mp3
  fi
  echo "$out_dir/$stem.$ext"
}

extract_file() {
  local src=$1 codec dest
  codec=$("$FFPROBE" -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$src" | head -n 1)
  [[ -n "$codec" ]] || die "No audio track in $src"
  dest=$(dest_for "$src" "$(ext_for_codec "$codec")")
  mkdir -p "$(dirname "$dest")"
  if want_mp3 && [[ "$codec" != mp3 ]]; then
    "$FFMPEG" -y -i "$src" -vn -map 0:a:0 -c:a libmp3lame -q:a 0 "$dest"
  elif "$FFMPEG" -y -i "$src" -vn -map 0:a:0 -c copy "$dest"; then
    :
  else
    rm -f "$dest"
    dest="${dest%.*}.mp3"
    "$FFMPEG" -y -i "$src" -vn -map 0:a:0 -c:a libmp3lame -q:a 0 "$dest"
  fi
  echo "$dest"
}

download_url() {
  local src=$1 template
  local -a args=(
    --no-playlist
    -f "ba/b"
    -S "abr,asr"
    -x
    --audio-quality 0
    --print "after_move:filepath"
  )
  if want_mp3; then
    args+=(--audio-format mp3)
  else
    args+=(--audio-format best)
  fi
  if [[ -n "$out_file" ]]; then
    template="${out_file%.*}.%(ext)s"
    mkdir -p "$(dirname "$out_file")"
  else
    template="$out_dir/%(title)s [%(id)s].%(ext)s"
    mkdir -p "$out_dir"
  fi
  "$YTDLP" "${args[@]}" -o "$template" -- "$src"
}

for src in "$@"; do
  if [[ -f "$src" ]]; then
    extract_file "$src"
  elif [[ "$src" == *://* ]]; then
    download_url "$src"
  else
    die "Not a file or a URL: $src"
  fi
done
