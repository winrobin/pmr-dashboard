# Add this at the top of deploy-downloads.sh
BACKUP=~/.openclaw/workspace/pmr/backup/$(date '+%Y%m%d_%H%M')
mkdir -p "$BACKUP"
cp -r ~/.openclaw/workspace/pmr/pmr-dashboard "$BACKUP/"
cp ~/.openclaw/workspace/pmr/*.py "$BACKUP/" 2>/dev/null
cp ~/.openclaw/workspace/pmr/*.json "$BACKUP/" 2>/dev/null
echo "📦 Backup saved to $BACKUP"

#!/bin/bash
DOWNLOADS=~/Downloads
PMR=~/.openclaw/workspace/pmr
DASHBOARD=~/.openclaw/workspace/pmr/pmr-dashboard

for file in "$DOWNLOADS"/*.py; do
    [ -f "$file" ] && mv "$file" "$PMR/pmr-data-fetcher.py" && echo "✅ py → pmr-data-fetcher.py"
done

for file in "$DOWNLOADS"/*.json; do
    [ -f "$file" ] && mv "$file" "$PMR/pmr-data-latest.json" && echo "✅ json → pmr-data-latest.json"
done

for file in "$DOWNLOADS"/*.html; do
    [ -f "$file" ] && mv "$file" "$DASHBOARD/index.html" && echo "✅ html → index.html"
done

for file in "$DOWNLOADS"/*.js; do
    [ -f "$file" ] && mv "$file" "$DASHBOARD/app.js" && echo "✅ js → app.js"
done

echo "🎉 Deploy done"
