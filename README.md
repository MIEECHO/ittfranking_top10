# ITTF Rankings Singles Top 10

一个用于展示国际乒乓球世界排名变化的可视化项目。页面以 **bar chart race** 的形式追踪洛杉矶周期内男单、女单世界前十排名和积分变化。

在线访问：

[https://mieecho.github.io/ittfranking_top10/](https://mieecho.github.io/ittfranking_top10/)

## 项目内容

当前数据范围：`2024-W32` 至 `2026-W20`

覆盖榜单：

- 男单世界排名前十
- 女单世界排名前十

页面功能：

- 男单 / 女单榜单切换
- 自动播放排名变化动画
- 暂停、上一周、下一周、第一周、最后一周控制
- 速度滑块，范围为 `1-10`
- 运动员姓名后显示国家或地区旗帜

## 页面预览

主页面文件位于：

```text
docs/index.html
```

GitHub Pages 线上页面由 `gh-pages` 分支根目录的 `index.html` 发布。

## 数据文件

主要数据文件：

```text
data/ittf_men_top10_2024W32_2026W16_clean.csv
data/ittf_women_top10_2024W32_2026W16_clean.csv
```

虽然文件名保留了初始整理时的 `2026W16`，但当前内容已经持续更新到 `2026-W20`。

每周增量数据放在：

```text
data/weekly_updates/
```

示例：

```text
data/weekly_updates/men_2026_W20.csv
data/weekly_updates/women_2026_W20.csv
```

CSV 字段格式：

```csv
week,rank,name,assoc,points
2026-W20,1,WANG Chuqin,CHN,12152
```

字段说明：

- `week`：周次，例如 `2026-W20`
- `rank`：排名，1 到 10
- `name`：运动员姓名
- `assoc`：协会代码，例如 `CHN`、`JPN`、`MAC`
- `points`：积分

## 周更流程

准备好男单、女单本周 CSV 后，运行：

```bash
python3 scripts/update_weekly_rankings.py \
  --men-week-csv data/weekly_updates/men_YYYY_WNN.csv \
  --women-week-csv data/weekly_updates/women_YYYY_WNN.csv
```

脚本会自动完成：

- 合并本周数据到主 CSV
- 校验每周是否包含完整 `1-10` 名
- 校验积分是否按排名递减
- 生成男单 latest HTML
- 生成女单 latest HTML
- 生成合并版 GitHub Pages 页面 `docs/index.html`

如果只是重新生成页面，不新增周数据，可以直接运行：

```bash
python3 scripts/update_weekly_rankings.py
```

## 生成合并页面

也可以单独运行：

```bash
python3 scripts/render_combined_ranking_site.py \
  --men-csv data/ittf_men_top10_2024W32_2026W16_clean.csv \
  --women-csv data/ittf_women_top10_2024W32_2026W16_clean.csv \
  --output docs/index.html
```

## 发布方式

本项目使用 GitHub Pages 发布。

推荐发布路径：

1. 在 `main` 分支维护数据、脚本和 `docs/index.html`
2. 将生成好的 `docs/index.html` 同步到 `gh-pages` 分支根目录的 `index.html`
3. GitHub Pages 从 `gh-pages` 分支发布公开页面

当前公开地址：

[https://mieecho.github.io/ittfranking_top10/](https://mieecho.github.io/ittfranking_top10/)

## 目录结构

```text
.
├── data/
│   ├── ittf_men_top10_2024W32_2026W16_clean.csv
│   ├── ittf_women_top10_2024W32_2026W16_clean.csv
│   └── weekly_updates/
├── docs/
│   ├── index.html
│   └── .nojekyll
├── scripts/
│   ├── render_combined_ranking_site.py
│   └── update_weekly_rankings.py
└── README.md
```

## 数据说明

数据来自 ITTF 世界排名页面截图整理，并经过 OCR、人工校对和一致性检查。由于原始页面排名会随周次更新，建议每次新增数据后检查：

- 名字拼写是否准确
- 协会代码是否正确
- 积分是否与截图一致
- 同一周排名是否完整且无重复

## License

本仓库主要用于数据可视化展示与个人项目维护。ITTF 排名数据版权归原始发布方所有。
