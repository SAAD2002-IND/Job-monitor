# qatar-job-monitor

I kept missing the CMU-Q Teaching Assistant reopening (twice now 🙃) so I built this
to stop relying on remembering to check job boards. It scrapes a handful of Qatar
university/research career pages every day and flags anything new that matches
roles I'm actually going for — RA, TA, data analyst, that kind of thing.

Live page: `https://<your-username>.github.io/job-monitor/` (update this link once you know it)

## How it works

A python script (`scraper.py`) hits a few career sites once a day via GitHub Actions,
checks titles against a keyword list, and saves results to `data/jobs.json`. The
webpage (`index.html`) just reads that file and shows a little yellow banner if
anything's new since your last visit.

## Setup

1. Push this repo to GitHub (already done if you're reading this here)
2. Settings → Actions → General → give it "Read and write permissions"
3. Settings → Pages → Source → GitHub Actions
4. Actions tab → run the workflow once manually to seed the data
5. Grab your Pages URL from Settings → Pages

After that it just runs itself, once a day.

## Sources

CMU-Qatar, Georgetown Qatar, and Texas A&M Qatar are pulled straight from their
Workday API so those are solid. QCRI, HBKU, Qatar University and UDST are more of
a best-effort thing — their job listings load with JavaScript which a simple script
can't run, so don't be surprised if those stay at 0 matches. Worth checking those
four by hand every couple weeks:

- hbku.edu.qa/en/careers
- careers.qu.edu.qa
- nonacademiccareers-udst.icims.com/jobs/search
- cs.qcri.org/jobs

LinkedIn and Indeed aren't scraped here on purpose (against their ToS) — there are
quick-search links on the page instead.

## Editing the keyword list

It's just a list at the top of `scraper.py`. Add/remove whatever titles you're
targeting and it'll pick them up next run.
