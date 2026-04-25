#!/bin/bash
cd ~/.openclaw/workspace/pmr || exit 1
python3 pmr-data-fetcher.py
git add -A
if git diff --staged --quiet; then
  echo "No changes to commit"
else
  git commit -m "Auto-update PMR data $(date '+%Y-%m-%d %H:%M')"
  git push origin gh-pages
  echo "Changes pushed to GitHub gh-pages"
fi
