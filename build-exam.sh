#!/bin/bash
# Build the encrypted EXAM rooms (separate from the quiz and research rooms).
#
# Each folder you create under texts/exam/ becomes its own room:
#     texts/exam/<room>/            (one PDF per student: First.LastName.pdf)
#  -> https://jbells17.github.io/class-texts/exam/<room>/
#
# Two layers:
#   1. The whole page is StatiCrypt-encrypted with the CLASS password (.password),
#      so the roster of names is never on the public web.
#   2. Inside, each student's exam is AES-encrypted with that student's PERSONAL
#      password (texts/exam/<room>/.passwords.csv — gitignored, auto-generated).
#      Printable slips land in _build/slips-<room>.html (also never published).
#
# The LockDown whitelist domain jbells17.github.io already covers these pages.
set -e
cd "$(dirname "$0")"

if [ ! -f .password ]; then echo "ERROR: no .password file."; exit 1; fi
PW="$(cat .password)"

shopt -s nullglob
found=0
for dir in texts/exam/*/; do
  room="$(basename "$dir")"
  found=1
  # Room title: texts/exam/<room>/.title if present, else prettified folder name
  if [ -f "$dir/.title" ]; then title="$(cat "$dir/.title")"; else title="$(echo "$room" | tr '-' ' ')"; fi
  echo "==> Exam room: $room  ($title)"
  node make_exam.mjs "$title" "$dir" "_build/exam-$room.html" "_build/slips-$room.html"
  mkdir -p "exam/$room"
  rm -f "exam/$room/index.html"
  npx --yes staticrypt@3 "_build/exam-$room.html" -p "$PW" --remember 1 --short -d "exam/$room"
  mv "exam/$room/exam-$room.html" "exam/$room/index.html"
  echo "   https://jbells17.github.io/class-texts/exam/$room/"
done

if [ "$found" = 0 ]; then
  echo "No exam rooms found. Create texts/exam/<room>/ and drop student PDFs in it."
fi
echo "==> Done."
