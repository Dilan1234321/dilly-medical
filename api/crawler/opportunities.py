"""Live opportunity crawler — scribe cos, hospital volunteer boards, REU feeds.

Runs on a schedule via POST /cron/refresh-opportunities (X-Cron-Secret)
or at startup when CRON_SECRET is unset in dev. Results land in
live_opportunities and merge with the static catalog in the feed.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from ..config import config
from ..database import get_db

_HEADERS = {"User-Agent": "DillyMedicalCrawler/1.0 (+https://trydilly.com)"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _upsert(rows: list[dict]) -> int:
    n = 0
    use_pg = bool(config.database_url)
    with get_db() as conn:
        for r in rows:
            if use_pg:
                conn.execute(
                    """INSERT INTO live_opportunities
                       (id, title, org, url, category, source, location, paid, description, fetched_at, active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                       ON CONFLICT (id) DO UPDATE SET
                         title=EXCLUDED.title, org=EXCLUDED.org, url=EXCLUDED.url,
                         description=EXCLUDED.description, fetched_at=EXCLUDED.fetched_at, active=1""",
                    (r["id"], r["title"], r.get("org", ""), r.get("url", ""),
                     r["category"], r["source"], r.get("location", ""),
                     1 if r.get("paid") else 0, r.get("description", ""), _now()),
                )
            else:
                conn.execute(
                    """INSERT OR REPLACE INTO live_opportunities
                       (id, title, org, url, category, source, location, paid, description, fetched_at, active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (r["id"], r["title"], r.get("org", ""), r.get("url", ""),
                     r["category"], r["source"], r.get("location", ""),
                     1 if r.get("paid") else 0, r.get("description", ""), _now()),
                )
            n += 1
    return n


def crawl_nsf_reu() -> list[dict]:
    """NSF REU sites RSS — summer research programs."""
    out = []
    try:
        xml = _fetch("https://www.nsf.gov/rss/rss_reu.xml")
        root = ET.fromstring(xml)
        for item in root.findall(".//item")[:40]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            desc = re.sub(r"<[^>]+>", "", item.findtext("description") or "")[:400]
            if not title:
                continue
            out.append({
                "id": _id("nsf_reu", title, link),
                "title": title[:120],
                "org": "NSF REU",
                "url": link,
                "category": "research",
                "source": "nsf_reu",
                "location": "US",
                "paid": True,
                "description": desc,
            })
    except Exception as e:
        print(f"[crawler] nsf_reu failed: {e}", flush=True)
    return out


def crawl_usajobs_health() -> list[dict]:
    """USAJobs search for student trainee / medical support roles."""
    out = []
    try:
        url = (
            "https://data.usajobs.gov/api/search?"
            "Keyword=student%20trainee%20health&LocationName=United%20States&ResultsPerPage=25"
        )
        req = urllib.request.Request(url, headers={**_HEADERS, "Host": "data.usajobs.gov"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
        for item in data.get("SearchResult", {}).get("SearchResultItems", []):
            md = item.get("MatchedObjectDescriptor", {})
            title = md.get("PositionTitle", "")
            org = md.get("OrganizationName", "")
            locs = md.get("PositionLocation", [])
            loc = locs[0].get("LocationName", "") if locs else ""
            link = md.get("PositionURI", "")
            if not title:
                continue
            out.append({
                "id": _id("usajobs", title, org, link),
                "title": title[:120],
                "org": org[:80],
                "url": link,
                "category": "clinical_paid",
                "source": "usajobs",
                "location": loc,
                "paid": True,
                "description": (md.get("UserArea", {}).get("Details", {}).get("MajorDuties", [""])[0] or "")[:400],
            })
    except Exception as e:
        print(f"[crawler] usajobs failed: {e}", flush=True)
    return out


def crawl_scribeamerica() -> list[dict]:
    """ScribeAmerica careers page — medical scribe openings."""
    out = []
    try:
        html = _fetch("https://www.scribeamerica.com/careers/")
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            for a in soup.select("a[href*='job'], a[href*='career'], a[href*='apply']")[:30]:
                title = (a.get_text() or "").strip()
                href = a.get("href", "")
                if len(title) < 8 or len(title) > 100:
                    continue
                if not href.startswith("http"):
                    href = "https://www.scribeamerica.com" + href
                out.append({
                    "id": _id("scribe", title, href),
                    "title": title,
                    "org": "ScribeAmerica",
                    "url": href,
                    "category": "clinical_paid",
                    "source": "scribeamerica",
                    "location": "US",
                    "paid": True,
                    "description": "Medical scribe role — paid clinical hours with physician exposure.",
                })
        except ImportError:
            pass
    except Exception as e:
        print(f"[crawler] scribeamerica failed: {e}", flush=True)
    return out


def crawl_idealist_health() -> list[dict]:
    """Idealist.org volunteer health listings (RSS if available)."""
    out = []
    try:
        xml = _fetch("https://www.idealist.org/en/rss/volunteer?areaOfFocus=Health")
        root = ET.fromstring(xml)
        for item in root.findall(".//item")[:25]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title:
                continue
            out.append({
                "id": _id("idealist", title, link),
                "title": title[:120],
                "org": "Idealist listing",
                "url": link,
                "category": "clinical_volunteer",
                "source": "idealist",
                "location": "",
                "paid": False,
                "description": re.sub(r"<[^>]+>", "", item.findtext("description") or "")[:400],
            })
    except Exception as e:
        print(f"[crawler] idealist failed: {e}", flush=True)
    return out


def run_all_crawlers() -> dict:
    """Run every source, upsert, return counts."""
    all_rows: list[dict] = []
    sources = {
        "nsf_reu": crawl_nsf_reu,
        "usajobs": crawl_usajobs_health,
        "scribeamerica": crawl_scribeamerica,
        "idealist": crawl_idealist_health,
    }
    counts = {}
    for name, fn in sources.items():
        rows = fn()
        counts[name] = len(rows)
        all_rows.extend(rows)
    # dedupe by id
    seen = set()
    unique = []
    for r in all_rows:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)
    upserted = _upsert(unique)
    return {"sources": counts, "upserted": upserted, "fetched_at": _now()}
