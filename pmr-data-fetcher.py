#!/usr/bin/env python3
"""
PMR Data Fetcher Script
Fetches latest property data and updates the JSON file for the dashboard
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
import sys

def fetch_latest_properties():
    """
    Fetch latest property data from sources
    For now, we'll simulate by fetching from the existing gh-pages data
    In a real implementation, this would scrape accommodproperties.com.au, etc.
    """
    try:
        # For demonstration, we're fetching from the current gh-pages data
        # In production, this would be replaced with actual scraping/API calls
        response = urllib.request.urlopen('https://raw.githubusercontent.com/winrobin/pmr-dashboard/gh-pages/pmr-data-latest.json')
        data = json.loads(response.read().decode())
        
        # Add metadata about when this was fetched
        for prop in data:
            prop['last_fetched'] = datetime.now().isoformat()
            prop['data_source'] = 'fetcher_script'
        
        return data
    except Exception as e:
        print(f"Error fetching property data: {e}")
        return None

def update_json_file(data, filepath='/Users/oc/.openclaw/workspace/pmr-data-latest.json'):
    """Update the local JSON file with latest data"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated {filepath} with {len(data)} properties")
        return True
    except Exception as e:
        print(f"Error updating JSON file: {e}")
        return False

def create_summary(data):
    """Create a summary of the data for notifications"""
    if not data:
        return "No data to summarize"
    
    brisbane_count = len([p for p in data if p.get('region') == 'Brisbane'])
    gc_count = len([p for p in data if p.get('region') == 'Gold Coast'])
    total_count = len(data)
    
    # Count properties with good metrics
    good_bc = len([p for p in data if p.get('bc_percent') is not None and p['bc_percent'] < 70])
    good_mult = len([p for p in data if p.get('multiplier') is not None and p['multiplier'] <= 5])
    
    summary = f"""
PMR Data Update Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================
Total Properties: {total_count}
  - Brisbane: {brisbane_count}
  - Gold Coast: {gc_count}

Quality Indicators:
  - BC% < 70% (healthy): {good_bc}/{total_count}
  - Multiplier <= 5x (good value): {good_mult}/{total_count}

Latest Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    return summary.strip()

def main():
    print("Starting PMR data fetch...")
    
    # Fetch latest data
    properties = fetch_latest_properties()
    
    if properties is None:
        print("Failed to fetch property data")
        sys.exit(1)
    
    print(f"Fetched {len(properties)} properties")
    
    # Update local JSON file (this would be used by the dashboard)
    if not update_json_file(properties):
        print("Failed to update local JSON file")
        sys.exit(1)
    
    # Create and display summary
    summary = create_summary(properties)
    print("\n" + summary)
    
    # In a full implementation, this would also:
    # 1. Commit and push to GitHub
    # 2. Trigger Google Sheets update via Apps Script
    # 3. Send notification (Telegram, email, etc.)
    
    print("\n✅ Data fetch completed successfully!")

if __name__ == '__main__':
    main()