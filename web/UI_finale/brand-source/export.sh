#!/usr/bin/env bash
# Export du pack Empreinte politique : SVG -> PNG / WebP / ICO
# Prérequis : resvg (ou rsvg-convert), cwebp (libwebp), magick (ImageMagick 7)
# La police Manrope doit être INSTALLÉE sur le système (resvg ne charge pas les @import distants).
#   macOS   : brew install resvg webp imagemagick && brew install --cask font-manrope
#   Debian  : apt install librsvg2-bin webp imagemagick  (+ police Manrope dans ~/.fonts)
# Usage : bash brand/export.sh

set -euo pipefail
cd "$(dirname "$0")"
OUT=export
mkdir -p "$OUT"

render() { # render <svg> <w> <h> <out.png>
  if command -v resvg >/dev/null; then
    resvg --width "$2" --height "$3" "$1" "$4"
  else
    rsvg-convert -w "$2" -h "$3" "$1" -o "$4"
  fi
  echo "  ✓ $4"
}

echo "Logotypes 1200x600 (@1x) et 2400x1200 (@2x, ~300 DPI)"
for v in logotype-dark logotype-light logotype-transparent-on-dark logotype-transparent-on-light; do
  render "$v.svg" 1200 600  "$OUT/$v.png"
  render "$v.svg" 2400 1200 "$OUT/$v@2x.png"
done

echo "Avatars / symboles 500 et 1000 px"
for v in avatar-dark avatar-transparent-on-dark; do
  render "$v.svg" 500  500  "$OUT/$v-500.png"
  render "$v.svg" 1000 1000 "$OUT/$v-1000.png"
done

echo "Bannière LinkedIn 1128x191 et 2256x382"
render linkedin-banner.svg 1128 191 "$OUT/linkedin-banner.png"
render linkedin-banner.svg 2256 382 "$OUT/linkedin-banner@2x.png"

echo "Favicons"
render favicon.svg 32  32  "$OUT/favicon-32.png"
render favicon.svg 16  16  "$OUT/favicon-16.png"
render avatar-dark.svg 180 180 "$OUT/apple-touch-icon.png"
magick "$OUT/favicon-16.png" "$OUT/favicon-32.png" "$OUT/favicon.ico"
echo "  ✓ $OUT/favicon.ico"

echo "WebP (qualité 90, lossless pour les fonds transparents)"
for f in "$OUT"/*.png; do
  case "$f" in
    *transparent*|*favicon*|*apple*) cwebp -quiet -lossless "$f" -o "${f%.png}.webp" ;;
    *) cwebp -quiet -q 90 "$f" -o "${f%.png}.webp" ;;
  esac
done

echo "Terminé → brand/$OUT/"
