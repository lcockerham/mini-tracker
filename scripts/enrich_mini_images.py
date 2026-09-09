"""Cached public catalog research for miniature image enrichment.

Requires beautifulsoup4, httpx and Pillow. Run crawl before matching.
"""

import concurrent.futures
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "media/mini-image-research"
CACHE.mkdir(parents=True, exist_ok=True)
BASE = "https://www.minisgallery.com/"


def fetch(url):
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".html")
    if path.exists():
        return path.read_text()
    for attempt in range(3):
        try:
            r = httpx.get(url, timeout=45, follow_redirects=True)
            r.raise_for_status()
            path.write_text(r.text)
            time.sleep(0.15)
            return r.text
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def crawl():
    pending = {"dungeons-and-dragons", "tanares-rpg"}
    seen = set()
    pages = {}
    errors = {}
    while pending:
        batch = sorted(pending - seen)
        if not batch:
            break
        pending.clear()

        def read(slug):
            url = BASE + "index.php?id=" + slug
            return slug, url, fetch(url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(read, slug): slug for slug in batch}
            for f in concurrent.futures.as_completed(futures):
                slug = futures[f]
                seen.add(slug)
                try:
                    _, url, html = f.result()
                except Exception as e:
                    errors[slug] = str(e)
                    continue
                soup = BeautifulSoup(html, "html.parser")
                minis = []
                for name in soup.select(".miniName"):
                    box = name.parent
                    img = box.select_one(".miniImage img")
                    if not img:
                        continue
                    number = box.select_one(".miniInfo2_num")
                    a = img.find_parent("a")
                    minis.append(
                        dict(
                            name=name.get_text(" ", strip=True),
                            number=number.get_text(" ", strip=True).strip("()") if number else "",
                            image=urljoin(BASE, img["src"]),
                            detail=urljoin(BASE, a["href"]) if a else url,
                        )
                    )
                pages[slug] = dict(
                    url=url, title=soup.title.get_text() if soup.title else slug, minis=minis
                )
                for a in soup.select("a[href]"):
                    p = urlparse(urljoin(BASE, a["href"]))
                    q = parse_qs(p.query)
                    target = q.get("id", [""])[0]
                    if p.netloc != "www.minisgallery.com" or q.get("task", [""])[0] not in (
                        "",
                        "sets",
                    ):
                        continue
                    if (
                        target
                        and not target.isdigit()
                        and target.startswith(
                            (
                                "dungeons-and-dragons",
                                "icons-of-the-realms",
                                "dnd-",
                                "dungeon-command",
                                "tanares",
                                "onslaught",
                            )
                        )
                        and target not in seen
                    ):
                        pending.add(target)
        (CACHE / "gallery.json").write_text(json.dumps(pages, indent=2))
        (CACHE / "crawl-errors.json").write_text(json.dumps(errors, indent=2))
        mini_count = sum(len(page["minis"]) for page in pages.values())
        print(
            f"pages={len(pages)} minis={mini_count} pending={len(pending)} errors={len(errors)}",
            flush=True,
        )


def reaper():
    records = {}
    errors = {}
    urls = [f"https://www.reapermini.com/Miniatures/Bones/sku-up/page{i}" for i in range(1, 25)]
    urls += [
        f"https://www.reapermini.com/Miniatures/Bones%20USA/sku-up/page{i}" for i in range(1, 9)
    ]

    def read(url):
        soup = BeautifulSoup(fetch(url), "html.parser")
        found = []
        for item in soup.select(".product-list__item"):
            sku = item.select_one(".product-item__sku")
            img = item.select_one("img")
            if sku and img:
                found.append(
                    dict(
                        number=sku.get_text(strip=True).split(":")[-1].strip(),
                        name=img.get("alt", ""),
                        image=img.get("src"),
                        page=url,
                    )
                )
        return found

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(read, url): url for url in urls}
        for f in concurrent.futures.as_completed(futures):
            try:
                for r in f.result():
                    records[r["number"]] = r
            except Exception as e:
                errors[futures[f]] = str(e)
    (CACHE / "reaper.json").write_text(json.dumps(records, indent=2))
    (CACHE / "reaper-errors.json").write_text(json.dumps(errors, indent=2))
    print(f"Reaper products={len(records)} errors={len(errors)}", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "crawl":
        crawl()
    elif sys.argv[1] == "reaper":
        reaper()
