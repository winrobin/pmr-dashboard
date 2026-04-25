#!/bin/bash
WORKSPACE=~/.openclaw/workspace/pmr
REPO=~/repos/pmr-dashboard

echo "[$(date '+%Y-%m-%d %H:%M')] Starting update..."

# 1. 抓取数据
cd $WORKSPACE
python3 pmr-data-fetcher.py

# 2. 复制数据到 repo
cp $WORKSPACE/pmr-data-latest.json $REPO/data/

# 3. 推送到 GitHub
cd $REPO
git add data/pmr-data-latest.json
git commit -m "auto: update data $(date '+%Y-%m-%d %H:%M')"
git push

echo "[$(date '+%Y-%m-%d %H:%M')] Done!"