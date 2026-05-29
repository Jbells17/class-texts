#!/bin/bash
# Build the encrypted reading room.
#   1. Embeds each PDF in texts/ into a source page (_build/src/*.html)
#   2. Encrypts each source page with the class password (.password)
#   3. Writes the public index.html + encrypted <text>.html files to the repo root
set -e
cd "$(dirname "$0")"

if [ ! -f .password ]; then echo "ERROR: no .password file."; exit 1; fi
PW="$(cat .password)"

echo "==> Embedding PDFs..."
rm -rf _build/src
python3 make_pages.py

echo "==> Encrypting pages with the class password..."
# Remove old encrypted text pages at root (keep index.html, README, etc.)
find . -maxdepth 1 -name '*.html' ! -name 'index.html' -delete
npx --yes staticrypt@3 _build/src/*.html -p "$PW" --remember 1 --short -d .

echo "==> Done. Published files at repo root:"
ls -1 *.html
