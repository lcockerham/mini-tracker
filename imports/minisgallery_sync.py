"""Find WizKids minis on Minis Gallery that aren't in the collection yet and queue them for review.

Run monthly (see scripts/com.minitracker.minisgallery-sync.plist) or by hand:

    .venv/bin/python -m imports.minisgallery_sync

New minis land in the mini_candidates table; nothing is added to the collection until it is
approved on /minis/review.
"""

import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import Mini, MiniCandidate, Photo, mini_gallery_url

BASE_URL = "https://www.minisgallery.com/"
USER_AGENT = "mini-tracker/1.0 (personal collection sync)"
REQUEST_DELAY_SECONDS = 1.0
FETCH_ATTEMPTS = 3
MAX_PAGES = 600

# Index pages for WizKids D&D lines; each lists sets or further sub-indexes.
ROOT_PAGES = [
    "icons-of-the-realms-core-sets",
    "icons-of-the-realms-premium-sets",
    "icons-of-the-realms-special-release-sets",
    "icons-of-the-realms-promos",
    "icons-of-the-realms-premium-figures-gallery",
    "onslaught-miniatures",
]

ROMAN_NUMERALS = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5"}


@dataclass
class GalleryMini:
    mg_id: int
    name: str
    mini_number: Optional[str]
    size: Optional[str]
    rarity: Optional[str]
    image_url: Optional[str]


@dataclass
class SetPage:
    page_id: str
    title: str
    release_date: Optional[str]
    minis: list[GalleryMini] = field(default_factory=list)

    @property
    def url(self) -> str:
        return page_url(self.page_id)


@dataclass
class SyncResult:
    pages_crawled: int = 0
    set_pages: int = 0
    failed_pages: list[str] = field(default_factory=list)
    linked_minis: int = 0
    unreleased_sets: list[str] = field(default_factory=list)
    undated_sets: list[str] = field(default_factory=list)
    withdrawn_candidates: int = 0
    new_candidates: Counter = field(default_factory=Counter)


def page_url(page_id: str) -> str:
    return f"{BASE_URL}index.php?id={page_id}"


def _page_id(href: str) -> Optional[str]:
    if not href.startswith("index.php?"):
        return None
    ids = parse_qs(urlparse(href).query).get("id")
    return ids[0] if ids else None


def _text(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _is_placeholder(name: str) -> bool:
    # Unreleased sets list guesses like "Unknown Lich?" until the real lineup is known.
    return not name or name.lower().startswith("unknown") or name.endswith("?")


def _image_url(src: str) -> Optional[str]:
    # The URL ends up in <img src> and <a href> on the site; only allow plain web links so a
    # tampered page can't smuggle in a javascript: URL.
    url = urljoin(BASE_URL, src.strip())
    return url if urlparse(url).scheme in ("http", "https") else None


def parse_index_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for container in soup.select("div[class^=tabsMenuContainer]"):
        for anchor in container.select("a[href]"):
            page_id = _page_id(anchor["href"])
            if page_id and page_id not in links:
                links.append(page_id)
    return links


def parse_set_page(page_id: str, html: str) -> Optional[SetPage]:
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.select_one(".productTitle"))
    boxes = soup.select("div.miniboxStandard, div.miniboxPromo")
    if not title or not boxes:
        return None

    info_rows = [_text(row) for row in soup.select(".productInfo .productInfoRow")]
    info_rows = [row for row in info_rows if row]
    release_date = info_rows[-1] if info_rows and "miniature" not in info_rows[-1].lower() else None

    page = SetPage(page_id=page_id, title=title, release_date=release_date)
    for box in boxes:
        name = _text(box.select_one(".miniName"))
        link = box.select_one(".miniImage a[href]")
        mg_ids = parse_qs(urlparse(link["href"]).query).get("id") if link else None
        if _is_placeholder(name) or not mg_ids or not mg_ids[0].isdigit():
            continue
        rarity = _text(box.select_one(".miniRarity"))
        size = _text(box.select_one(".miniSize"))
        number = _text(box.select_one(".miniInfo2_num")).strip("()") or None
        img = box.select_one(".miniImage img[src]")
        page.minis.append(
            GalleryMini(
                mg_id=int(mg_ids[0]),
                name=name,
                mini_number=number,
                size=None if size in ("", "Unknown") else size,
                rarity=None if rarity in ("", "Unknown") else rarity.lower(),
                image_url=_image_url(img["src"]) if img else None,
            )
        )
    return page


def http_fetcher() -> Callable[[str], str]:
    import httpx

    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)

    def fetch(page_id: str) -> str:
        # The site occasionally stalls on a page; a short wait and retry usually clears it.
        for attempt in range(FETCH_ATTEMPTS):
            time.sleep(REQUEST_DELAY_SECONDS * (attempt * 5 + 1))
            try:
                response = client.get(page_url(page_id))
                response.raise_for_status()
                return response.text
            except httpx.TransportError:
                if attempt == FETCH_ATTEMPTS - 1:
                    raise

    return fetch


def crawl(
    fetch: Callable[[str], str], result: SyncResult, roots: Optional[list[str]] = None
) -> list[SetPage]:
    queue = list(ROOT_PAGES if roots is None else roots)
    seen = set(queue)
    set_pages = []
    while queue and result.pages_crawled < MAX_PAGES:
        page_id = queue.pop(0)
        try:
            html = fetch(page_id)
        except Exception as exc:  # one bad page shouldn't sink the monthly run
            result.failed_pages.append(f"{page_id}: {exc}")
            continue
        result.pages_crawled += 1
        page = parse_set_page(page_id, html)
        if page:
            set_pages.append(page)
            continue
        for link in parse_index_links(html):
            if link not in seen:
                seen.add(link)
                queue.append(link)
    result.set_pages = len(set_pages)
    return set_pages


def _name_key(value: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _set_key(value: Optional[str]) -> str:
    words = re.findall(r"[a-z0-9]+", (value or "").lower())
    return "".join(ROMAN_NUMERALS.get(word, word) for word in words)


def _base_name_key(value: Optional[str]) -> str:
    # Collection names often carry a variant note the gallery leaves off: "Goblin (mace)".
    return _name_key(re.sub(r"\(.*?\)", "", value or ""))


def _number_key(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _primary_set(
    page: SetPage, set_names_by_key: dict[str, str], photo_sets: Counter
) -> Optional[str]:
    """The collection set a gallery page corresponds to, if any.

    Collection set names don't always match gallery titles ("Dragon Heist" vs "Waterdeep: Dragon
    Heist"), so fall back to the set most of the page's already-linked photos belong to. A stray
    hit or two isn't enough: premium figures and promos reuse images across sets.
    """
    exact = set_names_by_key.get(_set_key(page.title))
    if exact:
        return exact
    if photo_sets:
        set_name, hits = photo_sets.most_common(1)[0]
        if hits >= 3 or hits * 4 >= len(page.minis):
            return set_name
    return None


def find_new_minis(db: Session, set_pages: list[SetPage]) -> list[tuple[SetPage, str, GalleryMini]]:
    """Return (page, set_name, mini) for gallery minis that match nothing in the collection."""
    names_by_set: dict[str, set[str]] = {}
    numbers_by_set: dict[str, set[str]] = {}
    set_names_by_key: dict[str, str] = {}
    for name, set_name, number in db.query(Mini.name, Mini.set_name, Mini.mini_number):
        names_by_set.setdefault(set_name, set()).update({_name_key(name), _base_name_key(name)})
        if number:
            numbers_by_set.setdefault(set_name, set()).add(_number_key(number))
        set_names_by_key.setdefault(_set_key(set_name), set_name)

    set_by_photo = {
        url.lower(): set_name
        for url, set_name in db.query(Photo.url, Mini.set_name).join(Mini, Photo.mini_id == Mini.id)
    }
    known_mg_ids = {mg_id for (mg_id,) in db.query(MiniCandidate.mg_id)}

    new_minis = []
    for page in set_pages:
        photo_sets = Counter(
            set_by_photo[mini.image_url.lower()]
            for mini in page.minis
            if mini.image_url and mini.image_url.lower() in set_by_photo
        )
        primary = _primary_set(page, set_names_by_key, photo_sets)
        known_names = set().union(
            *(names_by_set.get(s, set()) for s in set(photo_sets) | {primary})
        )
        known_numbers = numbers_by_set.get(primary, set())

        for mini in page.minis:
            if mini.mg_id in known_mg_ids:
                continue
            if mini.image_url and mini.image_url.lower() in set_by_photo:
                continue
            if {_name_key(mini.name), _base_name_key(mini.name)} & known_names:
                continue
            if mini.mini_number and _number_key(mini.mini_number) in known_numbers:
                continue
            known_mg_ids.add(mini.mg_id)
            new_minis.append((page, primary or page.title, mini))
    return new_minis


def link_sources(db: Session, set_pages: list[SetPage]) -> int:
    """Point minis without a source_url at their Minis Gallery page; returns how many were linked.

    Match on the photo already linked from the gallery, else on the set number within the
    corresponding collection set when that number is unambiguous on both sides and the names
    agree ("Goblin (mace)" vs "Goblin").
    """
    gallery_by_photo = {
        mini.image_url.lower(): mini for page in set_pages for mini in page.minis if mini.image_url
    }
    minis = db.query(Mini).filter(Mini.source_url.is_(None)).all()
    set_names_by_key: dict[str, str] = {}
    minis_by_set: dict[str, list[Mini]] = {}
    for (set_name,) in db.query(Mini.set_name).distinct():
        set_names_by_key.setdefault(_set_key(set_name), set_name)
    for mini in minis:
        minis_by_set.setdefault(mini.set_name, []).append(mini)

    linked = 0
    for mini in minis:
        for photo in mini.photos:
            gallery_mini = gallery_by_photo.get(photo.url.lower())
            if gallery_mini:
                mini.source_url = mini_gallery_url(gallery_mini.mg_id)
                linked += 1
                break

    set_by_photo = {
        url.lower(): set_name
        for url, set_name in db.query(Photo.url, Mini.set_name).join(Mini, Photo.mini_id == Mini.id)
    }
    for page in set_pages:
        photo_sets = Counter(
            set_by_photo[m.image_url.lower()]
            for m in page.minis
            if m.image_url and m.image_url.lower() in set_by_photo
        )
        primary = _primary_set(page, set_names_by_key, photo_sets)
        unlinked = [m for m in minis_by_set.get(primary, []) if not m.source_url]
        if not primary or not unlinked:
            continue
        gallery_numbers = Counter(_number_key(m.mini_number) for m in page.minis)
        db_numbers = Counter(
            _number_key(m.mini_number) for m in db.query(Mini).filter(Mini.set_name == primary)
        )
        by_number = {_number_key(m.mini_number): m for m in page.minis}
        for mini in unlinked:
            number = _number_key(mini.mini_number)
            if not number or gallery_numbers[number] != 1 or db_numbers[number] != 1:
                continue
            ours, theirs = _base_name_key(mini.name), _base_name_key(by_number[number].name)
            if ours and theirs and (ours.startswith(theirs) or theirs.startswith(ours)):
                mini.source_url = mini_gallery_url(by_number[number].mg_id)
                linked += 1
    return linked


def is_released(release_date: Optional[str], today: date) -> Optional[bool]:
    """Whether a set is out, from the gallery's release date; None if the date can't be read.

    Minis Gallery posts images ahead of release, so a listed mini isn't necessarily available.
    A month-only date ("Feb 2027") counts as released once that month is over, and a year or
    year range ("2003 - 2010", "2022 - current") once its first year is over.
    """
    text = (release_date or "").replace("Release Date:", "").strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date() <= today
        except ValueError:
            pass
    for fmt in ("%b %Y", "%B %Y"):
        try:
            month = datetime.strptime(text, fmt)
            return (month.year, month.month) < (today.year, today.month)
        except ValueError:
            pass
    years = re.fullmatch(r"(\d{4})(\s*-\s*(\d{4}|current))?", text)
    if years:
        return int(years.group(1)) < today.year
    return None


def sync(db: Session, fetch: Callable[[str], str], today: Optional[date] = None) -> SyncResult:
    result = SyncResult()
    set_pages = crawl(fetch, result)
    today = today or date.today()
    released_pages, unreleased_urls = [], []
    for page in set_pages:
        released = is_released(page.release_date, today)
        if released:
            released_pages.append(page)
            continue
        unreleased_urls.append(page.url)
        label = f"{page.title} ({page.release_date or 'no date'})"
        (result.unreleased_sets if released is False else result.undated_sets).append(label)

    # Pull back anything queued before its release date moved (or before this check existed);
    # it's queued again once the set is out. Reviewed candidates are left alone.
    result.withdrawn_candidates = (
        db.query(MiniCandidate)
        .filter(MiniCandidate.status == "pending", MiniCandidate.source_url.in_(unreleased_urls))
        .delete(synchronize_session=False)
    )

    now = datetime.now()
    for page, set_name, mini in find_new_minis(db, released_pages):
        db.add(
            MiniCandidate(
                mg_id=mini.mg_id,
                set_name=set_name,
                source_url=page.url,
                name=mini.name,
                mini_number=mini.mini_number,
                size=mini.size,
                rarity=mini.rarity,
                image_url=mini.image_url,
                release_date=page.release_date,
                status="pending",
                found_at=now,
            )
        )
        result.new_candidates[set_name] += 1
    result.linked_minis = link_sources(db, set_pages)
    db.commit()
    return result


def main() -> int:
    from app.database import SessionLocal, upgrade_schema

    upgrade_schema()
    db = SessionLocal()
    try:
        result = sync(db, http_fetcher())
    finally:
        db.close()

    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Minis Gallery sync")
    print(f"  pages crawled: {result.pages_crawled}, set pages: {result.set_pages}")
    print(f"  existing minis linked to their gallery page: {result.linked_minis}")
    print(f"  new minis queued for review: {sum(result.new_candidates.values())}")
    for set_name, count in sorted(result.new_candidates.items()):
        print(f"    {count:4}  {set_name}")
    print(f"  not released yet, skipped ({len(result.unreleased_sets)}):")
    for label in sorted(result.unreleased_sets):
        print(f"    {label}")
    if result.withdrawn_candidates:
        print(f"  pending minis withdrawn until release: {result.withdrawn_candidates}")
    if result.undated_sets:
        print(f"  SKIPPED, couldn't read release date ({len(result.undated_sets)}):")
        for label in sorted(result.undated_sets):
            print(f"    {label}")
    if result.failed_pages:
        print(f"  FAILED pages ({len(result.failed_pages)}):")
        for failure in result.failed_pages:
            print(f"    {failure}")
    return 1 if result.failed_pages else 0


if __name__ == "__main__":
    sys.exit(main())
