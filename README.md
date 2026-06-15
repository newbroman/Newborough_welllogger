# Newborough Warren Well Logger

A self‑contained, offline‑first field app for recording groundwater dipwell
readings at Newborough Warren (Cwningar Niwbwrch), Anglesey. It is a single
installable Progressive Web App (PWA) — no server, no accounts, no external
map service, and no network required in the field.

It is part of the long‑term groundwater monitoring study of the dune system
(see the parent project,
[Newborough_Hydrology](https://github.com/newbroman/Newborough_Hydrology)).

---

## What it does

- **Logs dipwell readings** — depth to water measured from the top of the
  dip pipe, and automatically computes the water‑table elevation in m AOD.
- **Captures GPS** per reading (latitude, longitude, altitude, accuracy),
  kept separate from the level data.
- **Finds the nearest well** and supports a defined **route** so a round can
  be walked in order, with on‑map progress.
- **Shows an offline DEM map** of the site with every well marked, the route
  highlighted, and a live "you are here" dot.
- **Stores everything on the device** in durable storage that survives app
  restarts and browser storage pressure.
- **Exports** the day's data as plain CSV files you can open in any app, and
  can transfer data between phones by **QR code** with no connection.

---

## Tabs

| Tab | Purpose |
|-----|---------|
| 📋 **Log** | Select a well (search or nearest), enter depth to water, log the reading. Water‑table elevation is computed and shown. |
| 🗺 **Route** | Walk the wells in a defined order; the app advances as you reach each one. |
| 📊 **Wells** | Per‑well history and simple charts of stored readings. |
| 🛰 **Map** | Offline hillshade map of the site with wells, route and live position. |
| 📲 **Share** | Export CSV, or generate / scan a QR code to move data between devices offline. |

---

## How a reading is recorded

Each reading stores:

| Field | Meaning |
|-------|---------|
| `date` / `dateDisplay` / `timeDisplay` | Timestamp (ISO + human‑readable) |
| `wellId`, `fieldName` | Well identifier and any field/alternative name |
| `depth` | Depth to water below the **top of the pipe** (m) |
| `wte` | Water‑table elevation (m AOD) |
| `pipeElev`, `groundElev` | Pipe‑top and ground elevation (m AOD) |
| `gpsLat`, `gpsLon`, `gpsAlt`, `gpsAcc` | Position fix for that reading |

**Water‑table elevation** is computed as:

```
wte (m AOD) = pipeElev − depth
pipeElev    = groundElev + upstand
```

i.e. the level is referenced to the surveyed **pipe‑top elevation**, not the
ground surface. Each well's geometry (`elev`, `upstand`, `pipe`) is held in the
embedded well database.

---

## Well database and coordinates

The app embeds a `WELL_LIST` of every monitored point with its identifier,
geometry (ground elevation, upstand, pipe‑top elevation) and a WGS84
latitude/longitude used for the map and the nearest‑well search.

**Coordinate note (important for maintainers).** The survey coordinates are in
the British National Grid (OSGB36, EPSG:27700). They are converted to WGS84
lat/lon using the **OSTN15** datum transform — *not* a plain ellipsoidal
re‑projection. Omitting the datum shift introduces a systematic offset of
roughly **80 m** against a phone's WGS84 GPS, which breaks the nearest‑well
and route features. Always regenerate coordinates with a transform that applies
OSTN15 (e.g. `pyproj` `EPSG:27700 → EPSG:4326`). Where a well has no grid
coordinate, a value digitised on aerial imagery (KML) is used as a fallback.

Well markers are positioned by their own WGS84 coordinates, so they remain
accurate regardless of the basemap.

---

## Offline storage and durability

- Readings are held in **IndexedDB** (object store `nw_well_logger`), with a
  **localStorage** mirror for compatibility.
- The app requests **persistent storage** (`navigator.storage.persist()`) so
  the browser will not evict the data under storage pressure.
- If localStorage is ever cleared, the data is **automatically restored** from
  IndexedDB on the next launch.
- A small status chip (bottom‑left) shows the live record count and the time of
  the last successful save.

**Tip:** always open the app from its installed home‑screen icon. Opening it
through an in‑app browser (e.g. a link inside a chat or email app) uses
throwaway storage.

---

## Exports

- **Save today's sheets** (button, bottom‑right) writes two dated CSV files to
  the Downloads folder, openable in any spreadsheet app:
  - `well-levels-YYYY-MM-DD.csv` — date, time, well, depth, water‑table and
    ground/pipe elevations.
  - `well-gps-YYYY-MM-DD.csv` — date, time, well and the GPS fix.

  GPS and level data are kept in **separate files** by design.
- **CSV export** (Share tab) for the current session or all stored data.
- **QR transfer** (Share tab) encodes the session or full dataset as a QR code
  (with error‑correction) that another device can scan to import — useful for
  moving data between phones with no signal.

---

## The map

The Map tab is fully offline and uses **no external map service or API key**.
It renders a hillshade of the site DEM (2 m resolution) as the basemap, with
[Leaflet](https://leafletjs.com/) bundled locally (no CDN at runtime). Wells,
the route and the live position are drawn as vector overlays, so there are no
icon or tile files to fetch.

The hillshade is placed by geographic bounds; markers are placed by true
lat/lon, so navigation to a well is exact even though the relief image itself
may stretch by a few metres at the edges.

---

## Files

```
index.html       The entire app (UI, logic, bundled Leaflet, embedded DEM hillshade)
sw.js            Service worker (offline caching of the app shell)
manifest.json    PWA manifest (name, icons, display mode)
icon-192.png     App icon
icon-512.png     App icon
```

Everything is static. There is no build step required to run it.

---

## Install and deploy

1. Host the files over **HTTPS** (geolocation, service workers and "install to
   home screen" all require a secure context). [GitHub Pages](https://pages.github.com/)
   is sufficient.
2. On the phone, open the hosted URL in Chrome and choose **Add to Home screen**.
3. Launch it from the home‑screen icon. After the first load it works fully
   offline.

When you publish an update, **bump the cache name in `sw.js`** (e.g.
`nw-well-logger-vN`) so installed copies fetch the new version instead of
serving the cached one.

---

## Regenerating the embedded data (maintainers)

Two assets are baked into `index.html` and are regenerated from the project data
when wells are added or the survey is corrected:

- **`WELL_LIST`** — built from the master workbook (`measured` sheet:
  identifier, ground elevation, upstand, pipe‑top elevation, easting/northing)
  with KML fallback for wells that have no grid coordinate. Eastings/northings
  are transformed `EPSG:27700 → EPSG:4326` with `pyproj` (OSTN15).
- **DEM hillshade** — rendered from the site DEM GeoTIFF (EPSG:27700, 2 m) and
  embedded as a base64 data URI. Its WGS84 bounds are set as the Leaflet image
  overlay bounds.

---

## Privacy

All data stays on the device. The app has no backend, sends nothing over the
network, and contains no analytics or third‑party services. Sharing happens only
when you explicitly export a CSV or generate a QR code.

---

## Browser support

Designed for **Chrome on Android**. Requires a browser with service‑worker,
IndexedDB and geolocation support, served over HTTPS. GPS accuracy degrades
under dense forest canopy, where the map and route are the more reliable guide.

---

## Author and licence

Martin Hollingham — ORCID
[0000‑0003‑0253‑9301](https://orcid.org/0000-0003-0253-9301).
Part of the Newborough Warren groundwater monitoring study
([Newborough_Hydrology](https://github.com/newbroman/Newborough_Hydrology)).

Choose a licence for the code before publishing (MIT is a reasonable default).
The site DEM and well data are part of the monitoring study and may carry their
own terms — see the parent repository.
