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

## Change the password

Edit `.password`, then re-run `./build.sh` and push.

## ⚠️ Per-quiz setup in Canvas + LockDown Browser

For each quiz, paste the right reading-room URL into the quiz instructions, and in
the **Respondus LockDown Browser** settings add the domain **`jbells17.github.io`**
under *Advanced Settings → "Allow access to specific external web domains."*
(Already done for the AmLit final; repeat for any Philosophy quiz.)

Tip: do one practice run in LockDown Browser before the real quiz.
