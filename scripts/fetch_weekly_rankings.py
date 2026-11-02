#!/usr/bin/env python3
"""Fetch reviewable weekly CSVs without changing the published ranking history."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BUTTERFLY = "https://butterflyonline.com/world-top-20/"
FIELDS = ["week", "rank", "name", "assoc", "points"]


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.text = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.table = {"id": dict(attrs).get("id"), "rows": []}
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        self.text.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table["rows"].append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def fetch(url):
    request = Request(url, headers={"User-Agent": "ITTFTop10Research/1.0"})
    with urlopen(request, timeout=25) as response:
        html = response.read().decode("utf-8-sig")
    if "Just a moment..." in html or "cf-chl-" in html:
        raise ValueError("Cloudflare verification page, not ranking data")
    return html


def parse(html, week, sex, source):
    parser = Tables()
    parser.feed(html)
    text = " ".join(parser.text)
    year, number = map(int, week.split("-W"))
    if not re.search(rf"\b{year}\s+Week\s*#?\s*0?{number}\b", text, re.I):
        raise ValueError(f"Page does not explicitly identify {week}")
    if source == "butterfly":
        table_id = "tablepress-72" if sex == "men" else "tablepress-73"
        candidates = [t for t in parser.tables if t["id"] == table_id]
    else:
        label = "Men's Singles" if sex == "men" else "Women's Singles"
        if label not in text.replace("\u2019", "'"):
            raise ValueError(f"Missing category heading: {label}")
        candidates = [t for t in parser.tables if t["rows"] and
                      [c.lower() for c in t["rows"][0]] ==
                      ["rank", "name", "assoc", "points"]]
    if len(candidates) != 1:
        raise ValueError("Expected exactly one category table")
    rows = []
    for cells in candidates[0]["rows"]:
        if len(cells) != 4 or not re.match(r"^\d+\b", cells[0]):
            continue
        rank = int(re.match(r"^\d+", cells[0])[0])
        if rank > 10:
            continue
        assoc = {"France": "FRA"}.get(cells[2], cells[2]).upper()
        if not re.fullmatch(r"[A-Z]{3}", assoc):
            raise ValueError(f"Unknown association: {cells[2]}")
        points = cells[3].replace(",", "")
        if not points.isdigit() or int(points) <= 0:
            raise ValueError(f"Invalid points: {cells[3]}")
        name = cells[1].replace("\u2013", "-")
        if not name:
            raise ValueError("Empty player name")
        rows.append(dict(zip(FIELDS, [week, str(rank), name, assoc, points])))
    if [int(r["rank"]) for r in rows] != list(range(1, 11)):
        raise ValueError("Missing or duplicate ranks in top ten")
    if len({r["name"] for r in rows}) != 10:
        raise ValueError("Duplicate player names")
    points = [int(r["points"]) for r in rows]
    if points != sorted(points, reverse=True):
        raise ValueError("Points are not descending")
    return rows


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--week", required=True, help="Explicit ISO week, e.g. 2026-W44")
    cli.add_argument("--allow-butterfly", action="store_true",
                     help="Allow the non-ITTF current-week table if official fetch fails")
    cli.add_argument("--output-dir", type=Path, default=Path("data/fetched_rankings"))
    args = cli.parse_args()
    if not re.fullmatch(r"\d{4}-W\d{2}", args.week):
        cli.error("--week must use YYYY-WNN")
    year, number = map(int, args.week.split("-W"))
    monday = date.fromisocalendar(year, number, 1)
    results = {}
    failures = []
    for sex, code in (("men", "MS"), ("women", "WS")):
        url = (f"https://www.ittf.com/wp-content/uploads/{monday:%Y/%m}/"
               f"{year}_{number:02d}_SEN_{code}.html")
        try:
            html = fetch(url)
            results[sex] = (parse(html, args.week, sex, "ittf"), url, html, "ittf")
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            failures.append(f"{sex}: {url}: {error}")
    if len(results) != 2:
        for failure in failures:
            print(f"Official source unavailable: {failure}", file=sys.stderr)
        if not args.allow_butterfly:
            raise ValueError("No complete official pair; no output written")
        html = fetch(BUTTERFLY)
        # Use one source for both categories, with an exact requested-week check.
        results = {sex: (parse(html, args.week, sex, "butterfly"),
                         BUTTERFLY, html, "butterfly") for sex in ("men", "women")}
    target = args.output_dir / args.week
    target.mkdir(parents=True, exist_ok=False)
    manifest = {"week": args.week, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "official_failures": failures, "sources": {}}
    for sex, (rows, url, html, source) in results.items():
        filename = f"{sex}_{year}_W{number:02d}.csv"
        with (target / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        (target / f"{sex}_source.html").write_text(html, encoding="utf-8")
        manifest["sources"][sex] = {"url": url, "source": source, "csv": filename,
                                    "html_sha256": hashlib.sha256(html.encode()).hexdigest()}
    (target / "sources.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Validated 20 rows for {args.week}: {target}")
    print("Review these files before passing them to update_weekly_rankings.py.")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError, ValueError, FileExistsError) as error:
        sys.exit(str(error))
