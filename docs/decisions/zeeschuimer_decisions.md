# ClearFeed Capture - Fork of Zeeschuimer Extension

## Repository
**https://github.com/teddykolios11/ClearFeed-Capture**

---

## Changes Made

### `manifest.json`
- Removed `update_url` from `browser_specific_settings.gecko` (required by Mozilla for unsigned local extensions)
- Added `id` field to `browser_specific_settings.gecko`: `clearfeed-zeeschuimer@clearfeed.com`
- Removed non-Twitter platform background scripts (Threads, RedNote etc.) — files kept but not loaded

### `popup/interface.html`
- Removed entire "Connect to 4CAT" section including the URL input field
- Moved upload-status paragraph inside the status section so progress messages still display correctly
- Rebranded UI to ClearFeed colors (`#01A9F6` bright blue, `#233849` muted blue, white background)
- Added ClearFeed logo to header
- Added animated gradient background using ClearFeed brand colors
- Reordered action buttons — "To ClearFeed" first (bolded), then "Raw Data", then "Delete"
- Renamed ".ndjson" button to "Raw Data"
- Removed "Delete all items" button — only X/Twitter supported, per-row delete is sufficient
- Added "View ClearFeed Report" button that opens the ClearFeed dashboard in a new tab
- Added warning note: "⚠️ Download raw data first — tweets delete on upload."

### `popup/interface.js`
- Added `const CLEARFEED_URL` and `const CLEARFEED_LOGIN_URL` constants at top for easy environment switching
- Modified `activate_buttons()` — removed `have_4cat` dependency so "To ClearFeed" button enables based only on whether items exist
- Replaced entire upload-to-4cat XHR block with `fetch` POST to Django endpoint sending raw NDJSON blob with `X-Zeeschuimer-Platform` header and `credentials: 'include'` for session cookie auth
- Added specific error handling:
  - `401` — "You're not logged in" with direct link to sign in page
  - `400` — "No data to upload. Browse X/Twitter, then try again."
  - Other — "Upload failed. Please try again."
- Tweets automatically deleted from local IndexedDB after successful upload to prevent duplicate sessions
- Added "View ClearFeed Report" button click handler opening `CLEARFEED_URL` in new tab
- Renamed `upload-to-4cat` class to `upload-to-clearfeed` throughout
- Removed dead 4CAT-specific code:
  - `upload_poll` object (XHR-based 4CAT status poller)
  - `get_4cat_url()` and `set_4cat_url()` functions
  - `have_4cat` variable
  - `var xhr` and `#cancel-upload` handler
  - `download_blob()` function (StreamSaver, unused)
  - Commented-out StreamSaver block
  - `set_4cat_url(true)` call in `get_stats()`
  - `keyup` and `change` event listeners for 4CAT URL input
- Filtered platform modules to only show X/Twitter in the UI table

### `README.md`
- Rewrote to reflect ClearFeed fork purpose
- Added installation instructions pointing to GitHub releases
- Added step-by-step usage instructions including login requirement
- Retained full credit to original Zeeschuimer project and Stijn Peeters / Digital Methods Initiative

---

## Signing & Releases

- Signed via `web-ext sign --channel=unlisted` (automatic Mozilla signing, no human review)
- UUID derived from extension ID `clearfeed-zeeschuimer@clearfeed.com` — stable across all Firefox installations once signed
- Releases hosted at: `https://github.com/teddykolios11/ClearFeed-Capture/releases`
- Current signed `.xpi`: `62fc9d80cc0f43f29587-1.1.3.xpi`
- Download link for onboarding page:
  ```
  https://github.com/teddykolios11/ClearFeed-Capture/releases/latest/download/62fc9d80cc0f43f29587-1.1.3.xpi
  ```
---

## Open Questions & TODOs

### Repository Structure
- [x] Set up `develop`/`main` branch structure
- [x] Main branch reset to match develop for clean production state

### Features
- [x] **Auto-clear after upload** — tweets cleared from local IndexedDB after successful upload
- [x] **Prevent duplicate uploads** — clearing data after upload prevents same session being uploaded twice
- [x] **Prevent empty sessions** — avoid creating `browse_session` records if all tweets already exist in database (backend `ingest_posts` check or frontend guard)

### Cleanup & Scoping
- [x] Remove platform options we aren't processing — only X/Twitter shown in UI
- [x] Remove "Uploaded Datasets" section from extension UI
- [x] Reformat UI to ClearFeed branding
- [x] Rename functions/remove references to 4CAT
- [ ] Update `CLEARFEED_URL` from `localhost:8000` to `https://clearfeed.civic.garden` for production and re-sign