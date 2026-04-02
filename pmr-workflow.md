# PMR Daily Brief - Automated Research Workflow

## Schedule
- **Every weekday 9:00 AM AEST** → Cron job `PMR Daily Brief` (fc822f26)

## Data Sources to Search
### Primary Brokers
1. `Accom Properties` (accomproperties.com.au/management-rights-for-sale-brisbane)
2. `Resort Brokers` (resortbrokers.com.au/management-rights-for-sale/queensland/brisbane)
3. `TheOnsiteManager.com.au` (industry portal, aggregates multiple brokers)
4. `RAS360` (ras360.com.au) - specialists in management rights
5. `Property Bridge` (propertybridge.com.au/management-rights/for-sale)
6. `MR Brokers` (mrbrokers.com.au)
7. `Calvin Bailey MR` (calvinbaileymanagementrights.com.au)

### Commercial Platforms
8. `RealCommercial.com.au` (commercialrealestate.com.au)
9. `Realestate.com.au` (Filter: Commercial > Management Rights)
10. `Domain.com.au` (Commercial section)
11. `Businessforsale.com.au`
12. `AnyBusiness.com.au` (anybusiness.com.au/management-rights-for-sale/qld)

### Industry & Aggregators
13. `HotelResortSales.com.au`
14. `BusinessesForSale.com.au`
15. `Management Rights Broker Network`
16. `QLDManagementRights.com.au`

### Extended Geographic
- Gold Coast management rights
- Sunshine Coast management rights
- Logan / Ipswich management rights
- Redcliffe / Moreton Bay management rights

## Tier Classification
| Tier | Price Range | Focus |
|------|------------|-------|
| 1 | $500k-$1M | Business Only preferred |
| 2 | $1M-$1.5M | Business or Freehold |
| 3 | $1.5M-$2M | Freehold + Business |

## Data Points to Extract per Property
- Property name, location, suburb
- Asking price (AUD)
- Net income (annual)
- Multiplier (price / net income)
- BC salary amount + % of net income
- Letting pool units count
- Total units (if available)
- Contract years remaining
- Per unit weekly commission
- On-site required? (yes/no)
- Property purchase required? (yes/no)
- Source URL
- Data source name + date

## Output Files
1. **HTML Report**: `pmr-daily-brief-{YYYY-MM-DD}.html` (pure static, zero JS)
   - Header with date
   - 3 tier sections
   - Each property as a card
   - Bottom comparison table
2. **JSON**: Update `pmr-data-latest.json` with new entries
3. **Google Sheet**: Update raw_data tab (user runs Apps Script manually)

## HTML Report Format Requirements
- **NO JavaScript** - pure static HTML only (iOS Safari `file://` blocks `<script>`)
- Dark theme (#0a0b0f background)
- Card layout per property
- Color-coded: 🟢 good / 🟡 caution / 🔴 risk
- Table at bottom for side-by-side comparison

## Decision Rules
- BC salary > 80% of net income → 🔴 red flag (caretaker model)
- Per unit commission < $40/wk → 🔴 red flag
- BC salary 60-70% → 🟢 healthy range
- Per unit commission $60-$85/wk → 🟢 normal range
- Multiplier 3-5x → 🟢 attractive

## Notes
- If no new properties found, search broader (QLD-wide, other suburbs)
- Log search results in `memory/YYYY-MM-DD.md`
- Mark properties as "new discovery" vs "follow-up"
