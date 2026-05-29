#!/bin/bash
# Build the encrypted reading rooms (one self-contained page per course).
#   - American Lit  -> root            https://jbells17.github.io/class-texts/
#   - Philosophy    -> /philosophy/    https://jbells17.github.io/class-texts/philosophy/
# Each page: all that course's PDFs embedded + encrypted with the class password.
set -e
cd "$(dirname "$0")"

if [ ! -f .password ]; then echo "ERROR: no .password file."; exit 1; fi
PW="$(cat .password)"

build_course () {  # <title> <texts_dir> <output_dir>
  local title="$1" texts="$2" outdir="$3"
  echo "==> $title"
  rm -f _build/src.html
  python3 make_pages.py "$title" "$texts" "_build/src.html"
  mkdir -p "$outdir"
  rm -f "$outdir/index.html"
  npx --yes staticrypt@3 _build/src.html -p "$PW" --remember 1 --short -d "$outdir"
  mv "$outdir/src.html" "$outdir/index.html"
}

build_course "American Lit Reading Room"      "texts/amlit"      "."
build_course "Philosophy in Lit Reading Room" "texts/philosophy" "philosophy"

echo "==> Done."
echo "   American Lit: https://jbells17.github.io/class-texts/"
echo "   Philosophy:   https://jbells17.github.io/class-texts/philosophy/"
