# Qatar Education City Job Monitor

Checks CMU-Qatar, Georgetown Qatar, QCRI, HBKU, Qatar University, and UDST
daily for postings matching a fixed keyword list (Research Assistant,
Teaching Assistant, Statistician, Data Analyst, etc.), and shows results
on a simple webpage with a "new since last visit" notification bar.

## Setup (one-time, ~10 minutes)

1. **Create a new GitHub repository** (e.g. `qatar-job-monitor`), public or private — either works with GitHub Pages on a free personal account.
2. **Upload these files** to the repo, keeping the folder structure exactly as-is (the `.github/workflows/monitor.yml` path matters).
3. **Turn on write permissions for Actions:**
   Repo → Settings → Actions → General → "Workflow permissions" → select **Read and write permissions** → Save.
4. **Enable GitHub Pages via Actions:**
   Repo → Settings → Pages → Source → select **GitHub Actions**.
5. **Run it once manually to seed the data:**
   Repo → Actions tab → "Qatar Job Monitor" workflow → **Run workflow**.
   Wait ~1 minute, then check the Actions tab for a green checkmark.
6. **Find your page URL:**
   Repo → Settings → Pages will show something like
   `https://<your-username>.github.io/qatar-job-monitor/` — bookmark that.

After this, it re-runs automatically every day at 05:00 UTC (~08:00 Doha
time). Visit the page whenever you like; the yellow bar at the top tells
you how many new matches appeared since your last visit, and clicking
"Mark all as read" clears it.

## Known limitations (be honest with yourself about these)

- **CMU-Qatar and Georgetown Qatar** are queried through Workday's own
  API, so these two are reliable — if CMU-Q's Teaching Assistant role
  reopens, this will catch it the same day the workflow runs.
- **QCRI** is a plain HTML page and should also be reliable.
- **HBKU, Qatar University, and UDST** render their job lists with
  JavaScript that a simple script can't execute, so the scraper does a
  best-effort text search on the raw page and may miss postings on these
  three. Zero results from them means "inconclusive," not "no jobs" —
  worth glancing at their portals yourself every couple of weeks:
  - hbku.edu.qa/en/careers
  - careers.qu.edu.qa
  - nonacademiccareers-udst.icims.com/jobs/search
- The keyword list lives at the top of `scraper.py` — edit it any time
  your target roles change.
- If a workflow run fails, check the Actions tab for the error log
  (most likely cause: a site changed its page structure).
