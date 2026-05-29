# class-texts — Password-protected Quiz Reading Room

PDFs students can read **during a Lockdown Browser quiz**, protected by a shared
class password. Texts are AES-encrypted (via StatiCrypt) — the raw PDFs never sit
at a public URL, only encrypted blobs do.

- Live URL: **https://jbells17.github.io/class-texts/**
- Class password: stored in **`.password`** (this file is NOT published)

## How it's organized

| Path | Purpose | Published? |
|---|---|---|
| `texts/` | Drop your raw PDFs here | ❌ never (gitignored) |
| `.password` | The class password | ❌ never (gitignored) |
| `make_pages.py`, `build.sh` | Build the encrypted page | ✓ (no secrets) |
| `index.html` | The single encrypted, password-gated page (all texts in one) | ✓ |

> Design note: it's ONE page with no links — LockDown Browser blocks page-to-page
> navigation, so clicking a title reveals the PDF in place instead of opening a new page.

## To add, swap, or remove a text

1. Put the PDF in `texts/` (or delete one you don't want).
2. Run the build:  `./build.sh`
3. Push:  `git add -A && git commit -m "update texts" && git push`

(Or just ask Claude to do steps 2–3 once the PDF is in `texts/`.)

## To change the password

Edit `.password`, then re-run `./build.sh` and push.

## ⚠️ CRITICAL — make it work inside Lockdown Browser

Lockdown Browser blocks outside sites by default. In the **Respondus LockDown
Browser dashboard** for your quiz → **Advanced Settings** → **"Allow access to
specific external web domains"** → add **`jbells17.github.io`**. Then paste the
reading-room URL into your quiz instructions.

## ⚠️ TEST IT FIRST

Always run one **practice quiz in Lockdown Browser** before the real thing, to
confirm the password prompt and the embedded PDF both display correctly there.
