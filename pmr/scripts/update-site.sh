#!/bin/bash
cd ~/.openclaw/workspace/pmr/

echo "🚀 开始抓取最新房源..."
python3 pmr-data-fetcher.py

echo "☁️ 正在推送到 GitHub 网站..."
git add .
git commit -m "Auto-update PMR data: $(date +'%Y-%m-%d')"
git push origin gh-pages

echo "🎉 网站更新完毕！"
