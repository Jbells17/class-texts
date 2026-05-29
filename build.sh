#!/bin/bash
# Build the encrypted single-page reading room.
#   1. Embeds every PDF in texts/ into ONE source page (_build/src/index.html)
#   2. Encrypts that page with the class password (.password)
#   3. Publishes it as index.html at the repo root (the only page students need)
set -e
cd "$(dirname "$0")"

if [ ! -f .password ]; then echo "ERROR: no .password file."; exit 1; fi
PW="$(cat .password)"

echo "==> Embedding PDFs into one page..."
rm -rf _build/src
python3 make_pages.py

echo "==> Encrypting with the class password..."
# Remove any previously published pages (old per-text files + old index)
find . -maxdepth 1 -name '*.html' -delete
npx --yes staticrypt@3 _build/src/index.html -p "$PW" --remember 1 --short -d .

echo "==> Done. Published files at repo root:"
ls -1 *.html
