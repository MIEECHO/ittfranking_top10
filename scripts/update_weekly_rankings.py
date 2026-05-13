#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path("/Users/yuyang/Documents/auto-obsidian")
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"

MEN_CSV = DATA / "ittf_men_top10_2024W32_2026W16_clean.csv"
WOMEN_CSV = DATA / "ittf_women_top10_2024W32_2026W16_clean.csv"

MEN_JS = DATA / "ittf_bar_race_data.js"
WOMEN_JS = DATA / "ittf_women_bar_race_data.js"

MEN_LATEST_CSV = DATA / "ittf_men_top10_latest.csv"
WOMEN_LATEST_CSV = DATA / "ittf_women_top10_latest.csv"
MEN_LATEST_JS = DATA / "ittf_men_top10_latest_data.js"
WOMEN_LATEST_JS = DATA / "ittf_women_top10_latest_data.js"
MEN_LATEST_HTML = DATA / "ittf_men_top10_latest.html"
WOMEN_LATEST_HTML = DATA / "ittf_women_top10_latest.html"
COMBINED_SITE_HTML = ROOT / "docs" / "index.html"

WOMEN_TEMPLATE_HTML = DATA / "ittf_women_top10_2024W32_2026W16_graypink.html"

REQUIRED_COLUMNS = ["week", "rank", "name", "assoc", "points"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge weekly ITTF top10 ranking updates and rebuild latest assets."
    )
    parser.add_argument("--men-week-csv", help="Optional men weekly update CSV.")
    parser.add_argument("--women-week-csv", help="Optional women weekly update CSV.")
    parser.add_argument("--skip-html", action="store_true", help="Only update CSV/JS files.")
    return parser.parse_args()


def week_key(week: str) -> tuple[int, int]:
    year, week_no = week.strip().split("-W")
    return int(year), int(week_no)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in fields]
        if missing:
            raise ValueError(f"{path} missing columns: {missing}")
        return [{c: (row.get(c) or "").strip() for c in REQUIRED_COLUMNS} for row in reader]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def normalize_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned = []
    for row in rows:
        cleaned.append(
            {
                "week": row["week"].strip(),
                "rank": str(int(row["rank"])),
                "name": row["name"].strip(),
                "assoc": row["assoc"].strip().upper(),
                "points": str(int(float(row["points"]))),
            }
        )
    cleaned.sort(key=lambda r: (*week_key(r["week"]), int(r["rank"])))
    return cleaned


def merge_weekly_update(base_csv: Path, update_csv: Path) -> tuple[int, list[str]]:
    base_rows = normalize_rows(read_rows(base_csv))
    update_rows = normalize_rows(read_rows(update_csv))
    update_weeks = sorted({r["week"] for r in update_rows}, key=week_key)
    merged = [r for r in base_rows if r["week"] not in set(update_weeks)]
    merged.extend(update_rows)
    merged = normalize_rows(merged)
    write_rows(base_csv, merged)
    return len(update_rows), update_weeks


def validate_csv(path: Path) -> dict[str, object]:
    rows = normalize_rows(read_rows(path))
    by_week: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_week[row["week"]].append(row)

    issues: list[str] = []
    for week in sorted(by_week, key=week_key):
        week_rows = sorted(by_week[week], key=lambda r: int(r["rank"]))
        ranks = [int(r["rank"]) for r in week_rows]
        points = [int(float(r["points"])) for r in week_rows]
        if ranks != list(range(1, 11)):
            issues.append(f"{week}: rank sequence is {ranks}")
        if any(points[i - 1] < points[i] for i in range(1, len(points))):
            issues.append(f"{week}: points are not descending")

    weeks = sorted(by_week, key=week_key)
    return {
        "rows": len(rows),
        "weeks": len(weeks),
        "first_week": weeks[0] if weeks else "",
        "last_week": weeks[-1] if weeks else "",
        "issues": issues,
    }


def frames_from_csv(path: Path) -> list[dict[str, object]]:
    rows = normalize_rows(read_rows(path))
    by_week: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_week[row["week"]].append(row)

    frames = []
    for week in sorted(by_week, key=week_key):
        frame_rows = []
        for row in sorted(by_week[week], key=lambda r: int(r["rank"]))[:10]:
            frame_rows.append(
                {
                    "rank": int(row["rank"]),
                    "name": row["name"],
                    "assoc": row["assoc"],
                    "points": int(float(row["points"])),
                }
            )
        frames.append({"week": week, "rows": frame_rows})
    return frames


def export_js(csv_path: Path, output_path: Path) -> None:
    payload = json.dumps(frames_from_csv(csv_path), ensure_ascii=False)
    output_path.write_text(f"window.RANKING_FRAMES = {payload};\n", encoding="utf-8")


def render_men_latest() -> None:
    subprocess.check_call(
        [
            "python3",
            str(SCRIPTS / "render_ranking_animation.py"),
            "--input",
            str(MEN_CSV),
            "--output",
            str(MEN_LATEST_HTML),
            "--fps",
            "2",
        ]
    )


def render_women_latest() -> None:
    html = WOMEN_TEMPLATE_HTML.read_text(encoding="utf-8")
    payload = json.dumps(frames_from_csv(WOMEN_CSV), ensure_ascii=False)

    external_block = (
        '<script src="./ittf_women_bar_race_data.js"></script>\n'
        "<script>\n"
        "const frames = window.RANKING_FRAMES || [];"
    )
    inline_start = "<script>\nconst frames = "
    if external_block in html:
        html = html.replace(external_block, f"{inline_start}{payload};", 1)
    else:
        marker = "<script>\nconst frames = "
        start = html.find(marker)
        if start < 0:
            raise ValueError(f"Cannot find data block in {WOMEN_TEMPLATE_HTML}")
        data_start = start + len(marker)
        data_end = html.find(";\nconst chart =", data_start)
        if data_end < 0:
            raise ValueError(f"Cannot find frame payload end in {WOMEN_TEMPLATE_HTML}")
        html = html[:data_start] + payload + html[data_end:]

    WOMEN_LATEST_HTML.write_text(html, encoding="utf-8")


def render_combined_site() -> None:
    subprocess.check_call(
        [
            "python3",
            str(SCRIPTS / "render_combined_ranking_site.py"),
            "--men-csv",
            str(MEN_CSV),
            "--women-csv",
            str(WOMEN_CSV),
            "--output",
            str(COMBINED_SITE_HTML),
        ]
    )


def rebuild_assets(skip_html: bool) -> None:
    write_rows(MEN_LATEST_CSV, normalize_rows(read_rows(MEN_CSV)))
    write_rows(WOMEN_LATEST_CSV, normalize_rows(read_rows(WOMEN_CSV)))

    export_js(MEN_CSV, MEN_JS)
    export_js(WOMEN_CSV, WOMEN_JS)
    export_js(MEN_CSV, MEN_LATEST_JS)
    export_js(WOMEN_CSV, WOMEN_LATEST_JS)

    if not skip_html:
        render_men_latest()
        render_women_latest()
        render_combined_site()


def print_status(label: str, csv_path: Path) -> None:
    status = validate_csv(csv_path)
    print(
        f"{label}: {status['weeks']} weeks, {status['rows']} rows, "
        f"{status['first_week']} -> {status['last_week']}"
    )
    issues = status["issues"]
    if issues:
        print(f"{label} issues:")
        for issue in issues:
            print(f"  - {issue}")
        raise SystemExit(1)


def main() -> None:
    args = parse_args()

    if args.men_week_csv:
        count, weeks = merge_weekly_update(MEN_CSV, Path(args.men_week_csv))
        print(f"Merged men update: {count} rows for {', '.join(weeks)}")

    if args.women_week_csv:
        count, weeks = merge_weekly_update(WOMEN_CSV, Path(args.women_week_csv))
        print(f"Merged women update: {count} rows for {', '.join(weeks)}")

    print_status("Men", MEN_CSV)
    print_status("Women", WOMEN_CSV)
    rebuild_assets(skip_html=args.skip_html)
    print("Latest assets rebuilt.")
    print(f"Men latest HTML: {MEN_LATEST_HTML}")
    print(f"Women latest HTML: {WOMEN_LATEST_HTML}")
    print(f"Combined GitHub Pages HTML: {COMBINED_SITE_HTML}")


if __name__ == "__main__":
    main()
