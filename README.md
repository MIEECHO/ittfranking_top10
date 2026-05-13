# ITTF Ranking Race GitHub Pages 发布说明

已经生成好的公开页面文件：

- `docs/index.html`
- `docs/.nojekyll`

推荐 GitHub Pages 设置：

1. 新建一个公开 GitHub 仓库，例如 `ittf-ranking-race`。
2. 把当前项目推送到该仓库。
3. 进入仓库的 `Settings` -> `Pages`。
4. `Build and deployment` 选择 `Deploy from a branch`。
5. `Branch` 选择 `main`，目录选择 `/docs`。
6. 保存后等待 GitHub Pages 构建完成。

之后每周更新数据时，运行：

```bash
python3 scripts/update_weekly_rankings.py --men-week-csv data/weekly_updates/men_YYYY_WNN.csv --women-week-csv data/weekly_updates/women_YYYY_WNN.csv
```

脚本会自动重新生成 `docs/index.html`，提交并推送后，公开页面会更新。
