# class-texts — Quiz Reading Room

A simple public web page that holds PDFs students can read **during a Lockdown Browser quiz**.

Live URL (after setup): `https://YOUR-USERNAME.github.io/class-texts/`

---

## One-time setup (do this once)

1. Go to **https://github.com/new**
2. Repository name: **`class-texts`**  ·  set to **Public**  ·  click **Create repository**
3. On the new repo page, click **"uploading an existing file"**
4. Drag in **everything from this folder** (`index.html`, your PDFs) and click **Commit changes**
5. Go to **Settings → Pages**
6. Under *Source*, choose **Deploy from a branch** → Branch: **main** → Folder: **/ (root)** → **Save**
7. Wait ~1 minute, then refresh. Your URL appears at the top of the Pages settings.

## Adding or swapping texts later

1. Put the PDF in this folder (simple filename, no spaces: `great-gatsby.pdf`)
2. Open `index.html`, copy the example `<li>` block, change the filename + title
3. Upload the changed files to the repo the same way (drag-and-drop → Commit)

## ⚠️ CRITICAL — make the link work inside Lockdown Browser

By default Lockdown Browser blocks all outside websites. To let students reach this page:

- In the **Respondus LockDown Browser dashboard** for your quiz
- → **Advanced Settings** → **"Allow access to specific external web domains"**
- → add: **`YOUR-USERNAME.github.io`**

Then paste your reading-room URL into the quiz instructions. Only that domain will be
reachable — everything else stays locked.

## Copyright note

This page is public to the whole internet. Safe for **public-domain** texts
(e.g. *The Great Gatsby*). Be cautious posting full copyrighted works.
