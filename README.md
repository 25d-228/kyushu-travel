# KYUSHU TRAVEL

One Japanese-language travel planner for six independent journeys from Orio, Kitakyushu.

| ID | Mode | Plan | Days | Nights |
|---|---|---|---:|---:|
| bike-small | Cycling | Inland trial, Chikuho–Asakura–Hita | 4 | 3 |
| bike-kaikyo | Cycling with rail transfers | Kaikyokan and Tsunoshima trial | 5 | 4 |
| bike-main | Cycling with ferries | Kyushu circuit | 14 | 13 |
| bike-kyoto | Cycling, dismounted Kanmon crossing | Kyoto return via San'in | 28 | 27 |
| rail-kyushu | Rail | Kyushu circuit | 12 | 11 |
| rail-kyoto | Rail | Kyoto and San'in | 10 | 9 |

All six plans use the same catalog, map, daily navigation, sightseeing/rest-day details, lodging view, photographs, settings, and typography. Neither mode is hidden in an archive or an iframe. Daily routes, distances, overnight stops, rest days and train connections are preserved from the source snapshot. Travel information was not freshly researched as part of this UI migration.

## Usage and persistence

Open `index.html` from a static HTTP server. Choose a trip from the six cards or the trip selector. Display preferences belong in **設定**, not in the destination popup. All data is static: no booking API, live fares, tracking or account is required. Outbound official/Jalan links need an internet connection.

Dates, selected candidates and display preferences are stored in localStorage. The first visit imports recognized legacy cycling and rail keys on the same browser origin; it does not overwrite those old keys. The settings dialog can export/import a JSON backup. Importing a backup replaces the currently stored date/candidate/settings values. The display reset does not clear travel dates or candidates.

`cycling.html` and `rail.html` redirect to preselected trips in the same app. Deep links use `?trip=bike-kyoto` etc. The former `25d-228/kyushu-cycle-guide` repository is not modified.

## Building and checking

The migration source is pinned to `25d-228/kyushu-cycle-guide@eb6c04987062e68af31a23b6b2e6a7b597eb721a`.

```sh
python scripts/build.py /path/to/source
python -m pip install playwright
python -m playwright install chromium --with-deps
python scripts/test_unified.py
```

The source path must contain `cycling.html`, `assets/rail-data.js`, `assets/rail-context.js`, `assets/photos`, and the photo credit documents. The test checks all six trips, independent dates, route/rest navigation, photographs, settings, hotel dates, mobile sizes, backup/restore, legacy migration and restricted-storage behavior. Set `SITE_URL` to test the published site.

## Publishing

The `gh-pages` branch is the static publishing source. In repository **Settings → Pages**, use **Deploy from a branch → gh-pages → /(root)** if Pages is not already enabled. The expected site address is `https://25d-228.github.io/kyushu-travel/`; this README does not, by itself, confirm a successful deployment. Check GitHub Actions and the live test report.

## Attribution and limitations

`PHOTO-CREDITS.md` and `RAIL-PHOTO-CREDITS.md` retain photographic attribution. Each photo in the app links its source, creator and license. GSHHG/Basemap coastline data is simplified for overview only; see `MAP-LICENSES.txt`. Coordinates are included in editable form in `assets/data.js`.

Routes are planning schematics, not navigation or verified-open roads. Durations and budgets are estimates. Always verify train connections, closures, weather, accommodation availability and bicycle storage. No personal bookings or precise home address have been added.
