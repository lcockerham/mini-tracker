"""Match cached manufacturer catalogs to minis and optionally attach photo URLs."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import sqlite3
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "media/mini-image-research"
DB = ROOT / "mini_tracker.db"


def norm(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower().replace("&", "and"))


def ratio(left: str | None, right: str | None) -> float:
    return difflib.SequenceMatcher(None, norm(left), norm(right)).ratio()


def allowed(manufacturer: str, slug: str) -> bool:
    if manufacturer == "WotC":
        return slug.startswith(("dungeons-and-dragons-miniatures", "dungeon-command"))
    if manufacturer == "Wizkids":
        return slug.startswith(
            ("icons-of-the-realms", "onslaught", "dungeons-and-dragons-the-wild")
        )
    return manufacturer == "Dragori Games" and slug.startswith("tanares")


def name_score(record: dict, candidate: dict) -> float:
    score = ratio(record["name"], candidate["name"])
    left_number, right_number = norm(record["mini_number"]), norm(candidate["number"])
    if left_number and right_number:
        score += 0.18 if left_number == right_number else -0.25
    return score


def choose_page(
    manufacturer: str, set_name: str | None, records: list[dict], pages: dict
) -> tuple[str | None, dict]:
    ranked = []
    record_names = {norm(record["name"]) for record in records}
    for slug, page in pages.items():
        if not page["minis"] or not allowed(manufacturer, slug):
            continue
        title = page["title"].replace("MinisGallery - ", "").replace("D&D ", "")
        set_similarity = max(ratio(set_name, title), ratio(set_name, slug.replace("-", " ")))
        page_names = {norm(mini["name"]) for mini in page["minis"]}
        coverage = len(record_names & page_names) / len(records)
        ranked.append((coverage * 4 + set_similarity * 2, coverage, set_similarity, slug))
    ranked.sort(reverse=True)
    if not ranked:
        return None, {"reason": "No manufacturer catalog page was found"}
    best = ranked[0]
    accepted = (best[2] >= 0.58 and best[1] >= 0.20) or best[1] >= 0.65
    evidence = {
        "page": best[3],
        "coverage": round(best[1], 3),
        "set_similarity": round(best[2], 3),
        "runner_up": ranked[1][3] if len(ranked) > 1 else None,
    }
    return (best[3] if accepted else None), evidence


def match_record(record: dict, candidates: list[dict]) -> tuple[dict | None, str]:
    if not candidates:
        return None, "the selected catalog page contains no figures"
    ranked = sorted(
        ((name_score(record, mini), mini) for mini in candidates),
        key=lambda item: item[0],
        reverse=True,
    )
    best_score, best = ranked[0]
    gap = best_score - (ranked[1][0] if len(ranked) > 1 else 0)
    same_number = bool(
        norm(record["mini_number"]) and norm(record["mini_number"]) == norm(best["number"])
    )
    exact_name = norm(record["name"]) == norm(best["name"])
    if exact_name and (same_number or not best["number"] or not record["mini_number"]):
        return best, "Exact normalized name match"
    if same_number and best_score >= 0.90 and gap >= 0.04:
        return best, "Figure number and close name match"
    if best_score >= 0.90 and gap >= 0.08:
        return best, "Unique close name match within the set"
    return None, f"best candidate was {best['name']!r} (score {best_score:.2f}, gap {gap:.2f})"


def build_manifest() -> tuple[list[dict], list[dict]]:
    pages = json.loads((CACHE / "gallery.json").read_text())
    reaper = json.loads((CACHE / "reaper.json").read_text())
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    records = [
        dict(row) for row in conn.execute("SELECT * FROM minis ORDER BY manufacturer, set_name, id")
    ]
    matches, exceptions = [], []
    grouped: dict[tuple[str, str | None], list[dict]] = defaultdict(list)
    for record in records:
        if record["manufacturer"] == "Reaper":
            product = reaper.get(record["mini_number"] or "")
            if product:
                matches.append(
                    {
                        "mini_id": record["id"],
                        "manufacturer": "Reaper",
                        "name": record["name"],
                        "set_name": record["set_name"],
                        "mini_number": record["mini_number"],
                        "url": product["image"],
                        "source": product["page"],
                        "evidence": "Exact manufacturer SKU",
                    }
                )
            else:
                exceptions.append(
                    {
                        "record": record,
                        "category": "Listing unavailable",
                        "evidence": (
                            f"SKU {record['mini_number'] or 'missing'} was not present "
                            "in the indexed official Reaper Bones/Bones USA catalog."
                        ),
                        "action": (
                            "Check an archived Reaper listing or supply another "
                            "authoritative image."
                        ),
                    }
                )
        else:
            grouped[(record["manufacturer"], record["set_name"])].append(record)

    for (manufacturer, set_name), set_records in grouped.items():
        slug, page_evidence = choose_page(manufacturer, set_name, set_records, pages)
        if manufacturer == "WotC" and set_name == "Promo":
            candidates = [
                mini
                for page_slug, page in pages.items()
                if page_slug.startswith("dungeons-and-dragons-miniatures-promos-")
                for mini in page["minis"]
            ]
            slug = "combined DDM promo galleries"
        elif manufacturer == "Dragori Games":
            candidates = [
                mini
                for page_slug, page in pages.items()
                if page_slug.startswith("tanares")
                for mini in page["minis"]
            ]
            slug = slug or "combined Tanares gallery"
        else:
            candidates = pages[slug]["minis"] if slug else []
        for record in set_records:
            if not slug:
                exceptions.append(
                    {
                        "record": record,
                        "category": "Set match unavailable",
                        "evidence": (
                            "No catalog set passed the matching threshold. "
                            f"Evidence: {page_evidence}."
                        ),
                        "action": "Confirm the corresponding gallery set or supply an image.",
                    }
                )
                continue
            mini, evidence = match_record(record, candidates)
            if mini:
                matches.append(
                    {
                        "mini_id": record["id"],
                        "manufacturer": manufacturer,
                        "name": record["name"],
                        "set_name": set_name,
                        "mini_number": record["mini_number"],
                        "url": mini["image"],
                        "source": mini["detail"],
                        "catalog_page": slug,
                        "evidence": evidence,
                    }
                )
            else:
                exceptions.append(
                    {
                        "record": record,
                        "category": "Figure match unavailable",
                        "evidence": f"Catalog page {slug!r} was selected, but {evidence}.",
                        "action": (
                            "Review the name/number variant and select the correct "
                            "gallery image manually."
                        ),
                    }
                )
    return matches, exceptions


def write_outputs(matches: list[dict], exceptions: list[dict]) -> None:
    (CACHE / "match-manifest.json").write_text(json.dumps(matches, indent=2) + "\n")
    by_manufacturer = defaultdict(list)
    matched_counts = defaultdict(int)
    for item in exceptions:
        by_manufacturer[item["record"]["manufacturer"]].append(item)
    for item in matches:
        matched_counts[item["manufacturer"]] += 1
    slugs = {
        "Dragori Games": "dragori-games",
        "Reaper": "reaper",
        "Wizkids": "wizkids",
        "WotC": "wotc",
    }
    for manufacturer in ("Reaper", "Wizkids", "WotC", "Dragori Games"):
        items = by_manufacturer[manufacturer]
        lines = [
            f"# {manufacturer} miniature image exceptions",
            "",
            f"Generated: {date.today().isoformat()}",
            "",
            f"Matched automatically: {matched_counts[manufacturer]}. "
            f"Open exceptions: {len(items)}.",
            "Only matches supported by an exact SKU or a high-confidence catalog "
            "set/name comparison were applied.",
            "",
            "| Mini ID | Name | Set | # | Category | Evidence | Required next action | Status |",
            "| ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in items:
            record = item["record"]
            values = [
                record["id"],
                record["name"],
                record["set_name"] or "",
                record["mini_number"] or "",
                item["category"],
                item["evidence"],
                item["action"],
                "Open",
            ]
            lines.append(
                "| "
                + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in values)
                + " |"
            )
        (ROOT / "docs" / f"{slugs[manufacturer]}-mini-image-exceptions.md").write_text(
            "\n".join(lines) + "\n"
        )


def apply_matches(matches: list[dict]) -> int:
    backups = ROOT / "backups"
    backups.mkdir(exist_ok=True)
    backup = backups / f"mini_tracker.{datetime.now():%Y%m%d%H%M%S}.db"
    shutil.copy2(DB, backup)
    existing = sorted(
        backups.glob("mini_tracker.*.db"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    for old in existing[3:]:
        old.unlink()
    conn = sqlite3.connect(DB)
    inserted = 0
    try:
        for match in matches:
            present = conn.execute(
                "SELECT 1 FROM photos WHERE mini_id = ? AND url = ?",
                (match["mini_id"], match["url"]),
            ).fetchone()
            if not present:
                conn.execute(
                    "INSERT INTO photos (mini_id, url) VALUES (?, ?)",
                    (match["mini_id"], match["url"]),
                )
                inserted += 1
        conn.commit()
    finally:
        conn.close()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    matches, exceptions = build_manifest()
    write_outputs(matches, exceptions)
    inserted = apply_matches(matches) if args.apply else 0
    print(f"matches={len(matches)} exceptions={len(exceptions)} inserted={inserted}")


if __name__ == "__main__":
    main()
