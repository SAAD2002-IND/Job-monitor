"""
Qatar Education City job monitor.

Checks a fixed set of official career sources for postings whose title
matches Saad's target role list, and keeps a running record in
data/jobs.json. New matches get a first_seen timestamp; postings that
disappear from a source get marked "closed" (kept, not deleted, so the
"Closed positions worth monitoring" history builds up over time).

Run manually:  python scraper.py
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

KEYWORDS = [
    "teaching assistant", "teaching associate", "research assistant",
    "research associate", "research specialist", "research analyst",
    "research coordinator", "project assistant", "statistician",
    "statistical analyst", "data analyst", "data scientist",
    "data science assistant", "institutional research",
    "quantitative analyst", "bi analyst", "data engineer",
    "ai research", "ml research", "nlp research", "machine learning",
    "academic assistant", "academic coordinator", "lab assistant",
    "laboratory instructor", "stem assistant", "tutor",
    "python developer", "ai applications", "computational research",
    "instructor", "lecturer", "academic program assistant",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (personal job-monitor script)"}
DATA_PATH = "data/jobs.json"


def make_id(institution, title, url):
    return hashlib.sha1(f"{institution}|{title}|{url}".encode()).hexdigest()[:12]


def matches_keywords(title):
    t = title.lower()
    return any(k in t for k in KEYWORDS)


def fetch_workday(tenant, wd_host, site, institution, base_apply_url):
    """Query a Workday CXS jobs API (used by CMU-Q and Georgetown Qatar)."""
    results = []
    api = f"https://{tenant}.{wd_host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    offset, limit = 0, 20
    try:
        while True:
            payload = {"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""}
            r = requests.post(api, json=payload, headers=HEADERS, timeout=20)
            r.raise_for_status()
            data = r.json()
            postings = data.get("jobPostings", [])
            if not postings:
                break
            for p in postings:
                title = p.get("title", "")
                path = p.get("externalPath", "")
                url = base_apply_url.rstrip("/") + path
                if matches_keywords(title):
                    results.append({
                        "institution": institution,
                        "title": title,
                        "url": url,
                        "posted_on": p.get("postedOn", ""),
                    })
            total = data.get("total", 0)
            offset += limit
            if offset >= total:
                break
            time.sleep(1)
    except Exception as e:
        print(f"[WARN] Workday fetch failed for {institution}: {e}", file=sys.stderr)
    return results


def fetch_qcri():
    results = []
    url = "https://cs.qcri.org/jobs/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if title and matches_keywords(title):
                href = urljoin(url, a["href"])
                results.append({"institution": "QCRI", "title": title, "url": href, "posted_on": ""})
    except Exception as e:
        print(f"[WARN] QCRI fetch failed: {e}", file=sys.stderr)
    return results


def fetch_generic_text_search(url, institution):
    """Best-effort for sites that render at least some job titles server-side.
    Sites that are fully JS-rendered (some HBKU/QU/UDST pages) may return
    nothing here even when postings exist -- treat a zero result from these
    three as 'inconclusive', not 'no jobs', and check manually periodically."""
    results = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if title and matches_keywords(title):
                href = urljoin(url, a["href"])
                results.append({"institution": institution, "title": title, "url": href, "posted_on": ""})
    except Exception as e:
        print(f"[WARN] Generic fetch failed for {institution} ({url}): {e}", file=sys.stderr)
    return results


def collect_all():
    sources = [
        ("CMU-Qatar", lambda: fetch_workday(
            "cmu", "wd5", "CMU", "CMU-Qatar",
            "https://cmu.wd5.myworkdayjobs.com/en-US/CMU",
        )),
        ("Georgetown Qatar", lambda: fetch_workday(
            "georgetown", "wd1", "Georgetown_Qatar_Careers", "Georgetown Qatar",
            "https://georgetown.wd1.myworkdayjobs.com/en-US/Georgetown_Qatar_Careers",
        )),
        ("QCRI", fetch_qcri),
        ("HBKU", lambda: fetch_generic_text_search("https://www.hbku.edu.qa/en/careers", "HBKU")),
        ("Qatar University", lambda: fetch_generic_text_search("https://careers.qu.edu.qa", "Qatar University")),
        ("UDST", lambda: fetch_generic_text_search(
            "https://nonacademiccareers-udst.icims.com/jobs/search", "UDST"
        )),
    ]
    all_results = []
    print("\n--- Per-source match counts ---")
    for name, fn in sources:
        res = fn()
        print(f"{name}: {len(res)} matches")
        all_results += res
    print("--------------------------------\n")
    return all_results


def load_existing(path=DATA_PATH):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save(data, path=DATA_PATH):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    existing = load_existing()
    now = datetime.now(timezone.utc).isoformat()
    current = collect_all()

    seen_ids = set()
    new_count = 0
    for job in current:
        jid = make_id(job["institution"], job["title"], job["url"])
        seen_ids.add(jid)
        if jid in existing:
            existing[jid]["last_seen"] = now
            existing[jid]["status"] = "open"
            # backfill any fields that were missing/blank on earlier runs
            # (e.g. posted_on wasn't captured before this fix went in)
            for k, v in job.items():
                if v and not existing[jid].get(k):
                    existing[jid][k] = v
        else:
            existing[jid] = {**job, "id": jid, "first_seen": now, "last_seen": now, "status": "open"}
            new_count += 1

    for jid, rec in existing.items():
        if jid not in seen_ids and rec.get("status") == "open":
            rec["status"] = "closed"
            rec["closed_on"] = now

    save(existing)
    print(f"Run complete: {len(current)} matches found this run, {new_count} new.")


if __name__ == "__main__":
    main()
