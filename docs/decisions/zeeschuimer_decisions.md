# Zeeschuimer Extension — ClearFeed Fork

## Repository
**https://github.com/teddykolios11/capp-zeeschuimer**

---

## Changes Made

### `manifest.json`
- Removed `update_url` from `browser_specific_settings.gecko` (required by Mozilla for unsigned local extensions)
- Added `id` field to `browser_specific_settings.gecko`: `clearfeed-zeeschuimer@clearfeed.com`

### `popup/interface.html`
- Removed entire "Connect to 4CAT" section including the URL input field
- Moved upload-status paragraph inside the status section so progress messages still display correctly

### `popup/interface.js`
- Added `const CLEARFEED_URL = 'http://localhost:8000'` at the top
- Modified `activate_buttons()` — removed `have_4cat` dependency so "To FeedFreak" button enables based only on whether items exist, not on whether a 4CAT URL is set
- Replaced entire upload-to-4cat XHR block with a simple `fetch` POST to Django endpoint at `http://localhost:8000/api/import-dataset/` sending raw NDJSON blob with `X-Zeeschuimer-Platform` header
- Removed two lines from `DOMContentLoaded` that referenced the now-deleted 4CAT URL input field (`#fourcat-url`)

---

## Open Questions & TODOs

### Repository Structure
- [ ] Set up `develop`/`main` branch structure and branch protection rules

### Features
- [ ] **Auto-clear after upload** — clear extension's local data after a successful upload so each new browsing session starts fresh. This prevents duplicate sessions where posts were already uploaded in a previous session
- [ ] **Prevent empty sessions** — related to above, avoid creating `browse_session` records with no associated posts because the data was already uploaded

### Cleanup & Scoping
- [ ] Remove platform options we aren't processing — keep only Twitter/X, remove Instagram, TikTok etc.
- [ ] Remove "Uploaded Datasets" section from the extension UI
- [ ] Reformat UI to ClearFeed branding — decide whether to keep the Zeeschuimer name or rebrand entirely
- [ ] Rename functions/remove references to 4Cat
