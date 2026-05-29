#!/bin/bash
# Build the Senior Thesis Research Rooms — one encrypted page PER SECTION.
# This is ADDITIVE and independent of build.sh; it never touches the two quiz
# reading rooms (American Lit / Philosophy).
#
# Put each student's PDFs in a per-section folder, named with the convention:
#     texts/research/<section>/First.LastName - Source Title.pdf
# Each section folder builds to:
#     research/<section>/index.html
#   -> https://jbells17.github.io/class-texts/research/<section>/
# The build auto-groups sources by student from the filename.
set -e
cd "$(dirname "$0")"

if [ ! -f .password ]; then echo "ERROR: no .password file."; exit 1; fi
PW="$(cat .password)"

if [ ! -d texts/research ] || [ -z "$(ls -d texts/research/*/ 2>/dev/null)" ]; then
  echo "No section folders found under texts/research/."
  echo "Create one, e.g.:  mkdir -p 'texts/research/period-3'"
  exit 0
fi

for dir in texts/research/*/; do
  section="$(basename "$dir")"
  title="Senior Thesis Research Room — ${section}"
  outdir="research/${section}"
  echo "==> ${title}"
  rm -f _build/research-src.html
  python3 make_research.py "$title" "$dir" "_build/research-src.html"
  mkdir -p "$outdir"
  rm -f "$outdir/index.html"
  npx --yes staticrypt@3 _build/research-src.html -p "$PW" --remember 1 --short -d "$outdir"
  mv "$outdir/research-src.html" "$outdir/index.html"
  echo "   https://jbells17.github.io/class-texts/research/${section}/"
done

echo "==> Done."
