# Regional Festival System (2026)

## What changed
- Added shared regional festival source of truth: `Data/festival_calendar_regional.json`
- Added state-level festival source: `Data/festival_calendar_state.json` (1-2 unique festivals/state)
- Added backend mapper: `backend/app/festival_mapper.py`
- Added API endpoint: `GET /festivals/region/{region_name}`
- Frontend now fetches festivals by selected region and shows only relevant markers
- ML pipeline now applies uplift only for festivals mapped to the store's region (plus pan-indian)
- Inventory and Shop Owner now resolve festivals using region + state context

## Festival selection rationale
- Each region contains 3-4 high-retail local festivals + 2-3 pan-indian events.
- Selection criteria used:
  - Strong retail/spending behavior (gifting, apparel, grocery, electronics)
  - Broad regional celebration coverage
  - Multi-category demand effect
  - Practical planning value for inventory and discounts
- Local festivals are mapped by region and state metadata for explainability.

## Impact multiplier logic
- `impact_multiplier` is the total demand multiplier (`2.5` means 2.5x baseline).
- Pipeline converts this to uplift weight using:
  - `festival_weight = impact_multiplier - 1.0`
- Final adjusted forecast uses:
  - `adjusted = baseline * (1 + festival_weight)`
- Diwali uplift is intentionally strongest in most non-South states, while East India state calendars keep Durga Puja stronger where realistic (for example West Bengal).
- FSI shown in chart points now represents percent uplift:
  - `FSI = festival_weight * 100`

## Frontend behavior
- Selected region controls festival set from API.
- Chart markers show only region-relevant festivals:
  - Local festival: green
  - Pan-indian festival: orange
- Chart tooltip shows:
  - Name
  - Date
  - Type
  - Impact multiplier
- `StockSection` and `ActionPanel` now choose period festivals from the fetched regional list, not global hardcoded list.

## Backend API contract
`GET /festivals/region/{region_name}` response:
- `region_name`
- `states`
- `festivals[]` with:
  - `id`, `name`, `date`, `duration_days`, `type`, `impact_multiplier`
  - `retail_score`, `affected_categories`, `description`
  - `chart_color`, `marker_emoji`, `states`
  - computed fields: `start_date`, `end_date`, `month`, `week`

## How to add new festivals
1. Update `Data/festival_calendar_regional.json`
2. For state-specific events, update `Data/festival_calendar_state.json`
3. Add/modify festival object with required fields
4. Keep `type` as `local` or `pan-indian`
5. Set realistic `impact_multiplier` (recommended range 1.5-3.0)
6. Restart backend to reload updated data

## Testing checklist
- [ ] Backend endpoint returns expected festivals for each region:
  - `/festivals/region/East%20India` includes `Durga Puja`
  - `/festivals/region/South%20India` includes `Onam`, `Pongal`
  - `/festivals/region/West%20India` includes `Ganesh Chaturthi`
  - `/festivals/region/Northeast%20India` includes `Rongali Bihu`
- [ ] Inventory Dashboard markers change when region changes
- [ ] Inventory Dashboard markers change when store/state changes within same region
- [ ] East India does not show Onam/Vishu markers
- [ ] West India does not show Durga Puja/Bihu markers
- [ ] Telangana/Hyderabad flow shows Bonalu/Bathukamma context
- [ ] Assam/Guwahati flow shows Bihu context
- [ ] Tooltips show Name/Date/Type/Impact
- [ ] ML pipeline output applies only regional festival names in `Festival` column per store region
- [ ] Pan-indian festivals appear across all regions
