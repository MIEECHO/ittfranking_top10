#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


REQUIRED_COLUMNS = ["week", "rank", "name", "assoc", "points"]


def week_key(week: str) -> tuple[int, int]:
    year, week_no = week.strip().split("-W")
    return int(year), int(week_no)


def format_week_label(week: object) -> str:
    if not week:
        return ""
    year, week_no = week_key(str(week))
    return f"{year}年第{week_no}周"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in fields]
        if missing:
            raise ValueError(f"{path} missing columns: {missing}")
        rows = []
        for row in reader:
            rows.append({c: (row.get(c) or "").strip() for c in REQUIRED_COLUMNS})
        return rows


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


def page_html(men_frames: list[dict[str, object]], women_frames: list[dict[str, object]]) -> str:
    men_payload = json.dumps(men_frames, ensure_ascii=False)
    women_payload = json.dumps(women_frames, ensure_ascii=False)
    first_week = men_frames[0]["week"] if men_frames else ""
    last_week = men_frames[-1]["week"] if men_frames else ""
    first_week_label = format_week_label(first_week)
    last_week_label = format_week_label(last_week)
    cycle_range_label = f"{first_week_label} - {last_week_label}" if first_week_label and last_week_label else ""
    return f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ITTF Singles Top 10 Ranking Race</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #69758a;
      --card: rgba(255, 255, 255, 0.88);
      --line: rgba(91, 105, 130, 0.16);
      --men-a: #4d6a8d;
      --men-b: #7d9ec2;
      --women-a: #a77490;
      --women-b: #d2b0c0;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
      background:
        linear-gradient(180deg, #F5F7FB 0%, #EEF3F8 100%);
      padding: 28px;
    }}
    .shell {{
      max-width: 1120px;
      margin: 0 auto;
    }}
    .hero {{
      display: grid;
      gap: 28px;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      margin-bottom: 22px;
      padding: 2px 2px 4px;
    }}
    .title {{
      margin: 0;
      line-height: 1;
    }}
    .title-main {{
      display: block;
      color: #94A3B8;
      font-size: clamp(13px, 1.5vw, 16px);
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }}
    .title-sub {{
      display: block;
      margin-top: 8px;
      font-size: clamp(32px, 4.2vw, 40px);
      font-weight: 800;
      letter-spacing: -0.035em;
    }}
    .deck {{
      margin: 12px 0 0;
      max-width: 620px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.6;
    }}
    .range-card {{
      position: relative;
      overflow: hidden;
      padding: 18px 20px 20px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.48)),
        linear-gradient(135deg, rgba(125, 158, 194, 0.12), rgba(210, 176, 192, 0.14));
      backdrop-filter: blur(14px);
      box-shadow: 0 18px 46px rgba(38, 47, 67, 0.07);
    }}
    .range-card::before {{
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 5px;
      background: linear-gradient(180deg, var(--men-b), var(--women-b));
      opacity: 0.75;
    }}
    .range-card strong {{
      display: block;
      margin-top: 7px;
      margin-left: 0;
      font-size: clamp(17px, 1.8vw, 21px);
      line-height: 1.25;
      font-weight: 650;
      letter-spacing: -0.01em;
    }}
    .range-eyebrow {{
      display: block;
      color: var(--muted);
      font-size: 14px;
      font-weight: 650;
      letter-spacing: 0.04em;
    }}
    .range-dash {{
      color: #64748B;
      font-weight: 700;
    }}
    .tabs {{
      display: flex;
      gap: 10px;
      margin: 18px 0;
      flex-wrap: wrap;
    }}
    .tab {{
      appearance: none;
      border: 1px solid transparent;
      border-radius: 999px;
      padding: 10px 18px;
      font-weight: 800;
      color: #4a5568;
      background: rgba(255, 255, 255, 0.62);
      cursor: pointer;
      box-shadow: 0 8px 20px rgba(38, 47, 67, 0.07);
      transition: transform 180ms ease, background 180ms ease, color 180ms ease;
    }}
    .tab:hover {{
      transform: translateY(-1px);
    }}
    .tab.active[data-target="men"] {{
      color: white;
      background: linear-gradient(135deg, var(--men-a), var(--men-b));
    }}
    .tab.active[data-target="women"] {{
      color: white;
      background: linear-gradient(135deg, var(--women-a), var(--women-b));
    }}
    .race-card {{
      display: none;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--card);
      box-shadow: 0 24px 70px rgba(38, 47, 67, 0.12);
      backdrop-filter: blur(18px);
    }}
    .race-card.active {{
      display: block;
      animation: cardIn 360ms ease both;
    }}
    @keyframes cardIn {{
      from {{ opacity: 0; transform: translateY(8px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .race-head {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: center;
      padding: 18px 22px;
      color: white;
    }}
    .race-card.men .race-head {{
      background: linear-gradient(135deg, var(--men-a), var(--men-b));
    }}
    .race-card.women .race-head {{
      background: linear-gradient(135deg, var(--women-a), var(--women-b));
    }}
    .race-title {{
      font-size: 24px;
      font-weight: 900;
      letter-spacing: -0.02em;
    }}
    .week-label {{
      font-size: 18px;
      font-weight: 800;
      white-space: nowrap;
    }}
    .chart {{
      height: 530px;
      margin: 18px 22px 8px;
      position: relative;
      border: 1px solid rgba(105, 117, 138, 0.16);
      border-radius: 18px;
      overflow: hidden;
      padding-top: 8px;
      background:
        repeating-linear-gradient(to right, rgba(255,255,255,0.72) 0px, rgba(255,255,255,0.72) 70px, rgba(105,117,138,0.08) 70px, rgba(105,117,138,0.08) 71px),
        linear-gradient(180deg, rgba(255,255,255,0.54), rgba(255,255,255,0.22));
    }}
    .bar-row {{
      position: absolute;
      left: 10px;
      right: 10px;
      height: 46px;
      transition: transform 650ms ease, opacity 360ms ease;
    }}
    .bar {{
      position: absolute;
      left: 0;
      top: 5px;
      height: 36px;
      width: 0%;
      border-radius: 9px;
      box-shadow: 0 3px 10px rgba(66, 76, 96, 0.14);
      transition: width 650ms ease;
    }}
    .rank {{
      position: absolute;
      left: 10px;
      top: 9px;
      width: 30px;
      font-weight: 900;
      color: rgba(30, 39, 58, 0.78);
      z-index: 3;
    }}
    .name {{
      position: absolute;
      left: 42px;
      top: 8px;
      z-index: 3;
      display: flex;
      align-items: center;
      gap: 6px;
      max-width: calc(100% - 206px);
      overflow: hidden;
      color: white;
      font-weight: 800;
    }}
    .trend {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      min-width: 16px;
      font-size: 14px;
      line-height: 1;
      text-shadow: none;
    }}
    .trend.up {{
      color: #0f9f4f;
    }}
    .trend.down {{
      color: #e03131;
    }}
    .player {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .race-card.men .name {{
      text-shadow:
        0 1px 1px rgba(36, 56, 76, 0.30),
        0 0 1px rgba(36, 56, 76, 0.34);
    }}
    .race-card.women .name {{
      text-shadow:
        0 1px 1px rgba(98, 63, 78, 0.28),
        0 0 1px rgba(98, 63, 78, 0.34);
    }}
    .points {{
      position: absolute;
      right: 12px;
      top: 8px;
      z-index: 3;
      color: rgba(30, 39, 58, 0.78);
      font-weight: 900;
    }}
    .controls {{
      display: flex;
      gap: 9px;
      align-items: center;
      flex-wrap: wrap;
      padding: 10px 22px 22px;
    }}
    .controls button {{
      border: 0;
      border-radius: 10px;
      padding: 8px 12px;
      color: white;
      cursor: pointer;
      font-size: 14px;
      font-weight: 700;
    }}
    .men .controls button {{
      background: #6b87ac;
    }}
    .women .controls button {{
      background: #b3849c;
    }}
    .speed {{
      width: 140px;
      accent-color: #9e7890;
    }}
    .note {{
      color: var(--muted);
      font-size: 12px;
    }}
    .footnote {{
      margin: 16px 2px 0;
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }}
    @media (max-width: 760px) {{
      body {{
        padding: 16px;
      }}
      .hero {{
        grid-template-columns: 1fr;
        gap: 16px;
      }}
      .range-card {{
        padding: 16px 18px 18px;
      }}
      .race-head {{
        display: block;
      }}
      .week-label {{
        margin-top: 4px;
      }}
      .chart {{
        height: 510px;
        margin: 14px 12px 8px;
      }}
      .name {{
        max-width: calc(100% - 168px);
        font-size: 13px;
      }}
      .points {{
        font-size: 13px;
      }}
      .controls {{
        padding: 10px 12px 18px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div>
        <h1 class="title"><span class="title-main">ITTF RANKINGS</span><span class="title-sub">Singles Top 10</span></h1>
        <p class="deck">追踪 {first_week} 至 {last_week} 的男女单打世界前十变化</p>
      </div>
      <div class="range-card">
        <div class="range-eyebrow">洛杉矶周期</div>
        <strong>{first_week_label}<span class="range-dash"> - </span>{last_week_label}</strong>
      </div>
    </section>

    <nav class="tabs" aria-label="切换榜单">
      <button class="tab active" data-target="men">男单 Men's Singles</button>
      <button class="tab" data-target="women">女单 Women's Singles</button>
    </nav>

    <section id="menPanel" class="race-card men active">
      <div class="race-head">
        <div class="race-title">Men's Singles Top 10</div>
        <div class="week-label" data-role="week">周次：</div>
      </div>
      <div class="chart" data-role="chart"></div>
      <div class="controls">
        <button data-action="toggle">暂停</button>
        <button data-action="first">第一周</button>
        <button data-action="last">最后一周</button>
        <button data-action="prev">上一周</button>
        <button data-action="next">下一周</button>
        <input class="speed" data-action="speed" type="range" min="1" max="10" step="1" value="2" />
        <span class="note">速度</span>
      </div>
    </section>

    <section id="womenPanel" class="race-card women">
      <div class="race-head">
        <div class="race-title">Women's Singles Top 10</div>
        <div class="week-label" data-role="week">周次：</div>
      </div>
      <div class="chart" data-role="chart"></div>
      <div class="controls">
        <button data-action="toggle">暂停</button>
        <button data-action="first">第一周</button>
        <button data-action="last">最后一周</button>
        <button data-action="prev">上一周</button>
        <button data-action="next">下一周</button>
        <input class="speed" data-action="speed" type="range" min="1" max="10" step="1" value="2" />
        <span class="note">速度</span>
      </div>
    </section>

    <p class="footnote">数据来源：ITTF</p>
  </main>

  <script>
    const DATASETS = {{
      men: {men_payload},
      women: {women_payload}
    }};

    const assocMap = {{
      CHN: 'CN',
      MAC: 'MO',
      SWE: 'SE',
      BRA: 'BR',
      JPN: 'JP',
      FRA: 'FR',
      TPE: 'TW',
      SLO: 'SI',
      KOR: 'KR',
      GER: 'DE',
      HKG: 'HK',
      AIN: 'UN'
    }};

    function codeToFlag(code) {{
      if (!code) return '';
      const c = (assocMap[code] || code).toUpperCase();
      if (!/^[A-Z]{{2}}$/.test(c)) return '';
      return String.fromCodePoint(...[...c].map(ch => 127397 + ch.charCodeAt()));
    }}

    function shouldHideFlag(kind, name) {{
      const n = (name || '').replace(/\\s+/g, ' ').trim().toLowerCase();
      if (kind === 'men') return n === 'lin yun-ju';
      if (kind === 'women') return n === 'cheng i-ching';
      return false;
    }}

    function rankPalette(rank, kind) {{
      const men = [
        ['#6f8fb5', '#a8bfd8'],
        ['#7897ba', '#b0c5db'],
        ['#819fc0', '#b8cbe0'],
        ['#8aa6c5', '#c0d1e4'],
        ['#93aecb', '#c8d7e8'],
        ['#9cb6d0', '#d0ddec'],
        ['#a5bed5', '#d7e3f0'],
        ['#aec6da', '#dfe9f4'],
        ['#b7cede', '#e7eff7'],
        ['#c0d6e3', '#eff5fa']
      ];
      const women = [
        ['#a77490', '#c29fb1'],
        ['#ad7994', '#c7a5b6'],
        ['#b37f99', '#ccacbc'],
        ['#b9859e', '#d1b2c1'],
        ['#be8aa2', '#d6b9c7'],
        ['#c490a7', '#dbbfcc'],
        ['#ca96ac', '#dfc6d2'],
        ['#d09cb1', '#e4ccd7'],
        ['#d5a2b6', '#e9d3dd'],
        ['#dba8bb', '#edd9e2']
      ];
      const palette = kind === 'women' ? women : men;
      return palette[Math.max(0, Math.min(9, rank - 1))];
    }}

    function flagPalette(assoc, rank, kind) {{
      const byAssoc = {{
        CHN: ['#c96a6a', '#e6a064'],
        MAC: ['#2f8f63', '#76c79f'],
        SWE: ['#5f7fa8', '#d9bf6a'],
        BRA: ['#6ea27a', '#d9c074'],
        JPN: ['#eceff3', '#c98696'],
        FRA: ['#6d89ad', '#d19494'],
        TPE: ['#6b8fb1', '#d79b84'],
        KOR: ['#eceff3', '#8aa1c1'],
        GER: ['#6d6f76', '#ba8a8a'],
        HKG: ['#c27f8c', '#f2f4f7'],
        AIN: ['#8793a3', '#b2bac7']
      }};
      return byAssoc[assoc] || rankPalette(rank, kind);
    }}

    class RankingRace {{
      constructor(kind, panel, frames) {{
        this.kind = kind;
        this.panel = panel;
        this.frames = frames || [];
        this.chart = panel.querySelector('[data-role="chart"]');
        this.weekLabel = panel.querySelector('[data-role="week"]');
        this.toggleBtn = panel.querySelector('[data-action="toggle"]');
        this.speedInput = panel.querySelector('[data-action="speed"]');
        this.nodeByName = new Map();
        this.idx = 0;
        this.timer = null;
        this.running = true;
        this.rowHeight = 50;
        this.bind();
        if (this.frames.length) {{
          this.render(0);
          this.start();
        }} else {{
          this.weekLabel.textContent = '周次：未加载到数据';
        }}
      }}

      bind() {{
        this.toggleBtn.addEventListener('click', () => {{
          this.running = !this.running;
          if (this.running) {{
            this.toggleBtn.textContent = '暂停';
            this.start();
          }} else {{
            this.toggleBtn.textContent = '播放';
            clearInterval(this.timer);
          }}
        }});
        this.panel.querySelector('[data-action="first"]').addEventListener('click', () => this.jump(0));
        this.panel.querySelector('[data-action="last"]').addEventListener('click', () => this.jump(this.frames.length - 1));
        this.panel.querySelector('[data-action="prev"]').addEventListener('click', () => this.jump((this.idx - 1 + this.frames.length) % this.frames.length));
        this.panel.querySelector('[data-action="next"]').addEventListener('click', () => this.jump((this.idx + 1) % this.frames.length));
        this.speedInput.addEventListener('input', () => {{
          if (this.running) this.start();
        }});
      }}

      jump(nextIdx) {{
        if (!this.frames.length) return;
        this.idx = nextIdx;
        this.render(this.idx);
      }}

      ensureRow(name) {{
        if (this.nodeByName.has(name)) return this.nodeByName.get(name);
        const row = document.createElement('div');
        row.className = 'bar-row';
        row.innerHTML = `
          <div class="bar"></div>
          <div class="rank"></div>
          <div class="name"><span class="trend"></span><span class="player"></span></div>
          <div class="points"></div>
        `;
        this.chart.appendChild(row);
        this.nodeByName.set(name, row);
        return row;
      }}

      render(i) {{
        const frame = this.frames[i];
        if (!frame) return;
        const prevFrame = this.frames[i - 1] || null;
        const prevRankByName = new Map((prevFrame?.rows || []).map(r => [r.name, Number(r.rank)]));
        this.weekLabel.textContent = `周次：${{frame.week}}`;
        const maxPoints = Math.max(...frame.rows.map(r => Number(r.points)));
        const activeNames = new Set(frame.rows.map(r => r.name));

        for (const rowData of frame.rows) {{
          const row = this.ensureRow(rowData.name);
          const top = (rowData.rank - 1) * this.rowHeight + 8;
          row.style.transform = `translateY(${{top}}px)`;
          row.style.opacity = '1';

          const bar = row.querySelector('.bar');
          const rank = row.querySelector('.rank');
          const trend = row.querySelector('.trend');
          const player = row.querySelector('.player');
          const points = row.querySelector('.points');
          const width = maxPoints > 0 ? (Number(rowData.points) / maxPoints) * 88 : 0;
          const colors = flagPalette(rowData.assoc, rowData.rank, this.kind);
          const flag = shouldHideFlag(this.kind, rowData.name) ? '' : codeToFlag(rowData.assoc);
          const prevRank = prevRankByName.get(rowData.name);
          const isNewEntry = prevFrame && !Number.isFinite(prevRank);
          const rankDelta = Number.isFinite(prevRank) ? prevRank - Number(rowData.rank) : (isNewEntry ? 1 : 0);

          bar.style.background = `linear-gradient(90deg, ${{colors[0]}}, ${{colors[1]}})`;
          bar.style.width = `${{width.toFixed(2)}}%`;
          rank.textContent = `${{rowData.rank}}`;
          trend.className = `trend ${{rankDelta > 0 ? 'up' : rankDelta < 0 ? 'down' : ''}}`;
          trend.textContent = rankDelta > 0 ? '▲' : rankDelta < 0 ? '▼' : '';
          trend.title = isNewEntry ? '新进前十' : rankDelta > 0 ? `上升 ${{rankDelta}} 位` : rankDelta < 0 ? `下降 ${{Math.abs(rankDelta)}} 位` : '';
          player.textContent = `${{rowData.name}}${{flag ? ' ' + flag : ''}}`;
          points.textContent = Number(rowData.points).toLocaleString('en-US');
        }}

        for (const [name, row] of this.nodeByName.entries()) {{
          if (!activeNames.has(name)) row.style.opacity = '0';
        }}
      }}

      start() {{
        clearInterval(this.timer);
        const speed = Number(this.speedInput.value);
        const ms = Math.max(200, 1200 - speed * 100);
        this.timer = setInterval(() => {{
          this.idx = (this.idx + 1) % this.frames.length;
          this.render(this.idx);
        }}, ms);
      }}
    }}

    const races = {{
      men: new RankingRace('men', document.getElementById('menPanel'), DATASETS.men),
      women: new RankingRace('women', document.getElementById('womenPanel'), DATASETS.women)
    }};

    document.querySelectorAll('.tab').forEach(tab => {{
      tab.addEventListener('click', () => {{
        const target = tab.dataset.target;
        document.querySelectorAll('.tab').forEach(btn => btn.classList.toggle('active', btn === tab));
        document.querySelectorAll('.race-card').forEach(panel => panel.classList.toggle('active', panel.id === `${{target}}Panel`));
      }});
    }});
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a combined ITTF men/women ranking site.")
    parser.add_argument("--men-csv", required=True)
    parser.add_argument("--women-csv", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    men_csv = Path(args.men_csv)
    women_csv = Path(args.women_csv)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    html = page_html(frames_from_csv(men_csv), frames_from_csv(women_csv))
    output.write_text(html, encoding="utf-8")
    print(f"Saved combined site to: {output}")


if __name__ == "__main__":
    main()
