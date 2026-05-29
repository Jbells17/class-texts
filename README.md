# class-texts — Password-protected Quiz Reading Rooms

PDFs students can read **during a Lockdown Browser quiz**, protected by a shared
class password. Texts are AES-encrypted (StatiCrypt); raw PDFs never sit at a
public URL.

Two course pages (same repo, same domain — one LockDown whitelist covers both):

| Course | Live URL | PDFs go in |
|---|---|---|
| American Lit Reading Room | https://jbells17.github.io/class-texts/ | `texts/amlit/` |
| Philosophy in Lit Reading Room | https://jbells17.github.io/class-texts/philosophy/ | `texts/philosophy/` |

- Class password: stored in **`.password`** (NOT published)
- Design: each page is ONE self-contained page with **no links** — LockDown Browser
  blocks page-to-page navigation, so clicking a title reveals the PDF in place
  (built as an in-memory Blob, which avoids the ~2MB data-URL cap).

## Add / swap / remove a text

1. Put the PDF in the right course folder: `texts/amlit/` or `texts/philosophy/`.
2. Build (rebuilds both courses):  `./build.sh`
3. Push:  `git add -A && git commit -m "update texts" && git push`

(Or just ask Claude to do steps 2–3 once the PDF is in place.)

## Senior Thesis Research Rooms (separate, for writing the paper in LockDown)

A third use of the same pattern, for the second-semester senior thesis: a place
to hold each student's saved research sources so they can re-read them while
writing the paper in LockDown Browser. Built by **`build-research.sh`** /
**`make_research.py`** — fully independent of the quiz rooms above (it never
touches `build.sh` or the two course pages).

- **One page per section.** Each folder you create under `texts/research/` becomes
  its own page:  `texts/research/<section>/` → `https://jbells17.github.io/class-texts/research/<section>/`
- **Auto-grouped by student** from the filename — no manual sorting. Name each PDF:

      First.LastName - Source Title.pdf

  e.g. `Jane.Doe - Existentialism and the Absurd.pdf`. The part before the first
  ` - ` (space-hyphen-space) is the student; the rest is the source title. A file
  with no ` - ` lands under an "Unsorted" student so nothing is dropped silently.
- **Two-level, no-navigation:** student clicks their name → sees their sources →
  clicks one → it opens in Chrome's clean PDF reader (the readable rendering
  Hypothesis lacked). Same shared class password as the quiz rooms.
- **Sources must be PDFs.** Web articles: open the page → Print → "Save as PDF."
- **Students can't upload** (it's a static site). Collect their PDFs (Canvas /
  Drive / email), drop them in the section folder named per the convention, then:

      ./build-research.sh
      git add -A && git commit -m "update research" && git push

  (Or just hand Claude the PDFs.) The LockDown whitelist domain `jbells17.github.io`
  already covers these pages — paste each section's URL into that section's
  assignment instructions. The build warns if a section page gets too large
  (>45 MB); if so, that section is probably better split.

## Change the password

Edit `.password`, then re-run `./build.sh` (and `./build-research.sh`) and push.

## ⚠️ Per-quiz setup in Canvas + LockDown Browser

For each quiz, paste the right reading-room URL into the quiz instructions, and in
the **Respondus LockDown Browser** settings add the domain **`jbells17.github.io`**
under *Advanced Settings → "Allow access to specific external web domains."*
(Already done for the AmLit final; repeat for any Philosophy quiz.)

Tip: do one practice run in LockDown Browser before the real quiz.
