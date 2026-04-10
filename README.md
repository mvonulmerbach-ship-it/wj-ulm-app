 WJ Ulm / Neu-Ulm App

A Progressive Web App (PWA) for the Wirtschaftsjunioren Ulm / Neu-Ulm — Germany's largest network of young entrepreneurs and business leaders under 40.

🌐 **Live:** https://mvonulmerbach-ship-it.github.io/wj-ulm-app/

---

## Features

- Quick access to the member portal (vereinonline.org)
- Event calendar & registration
- Member directory
- Documents & protocols
- Newsletter archive
- Interactive map of the WJ Ulm / Neu-Ulm area
- Links to WJ Baden-Württemberg, WJ Bayern, WJ Schwaben, and WJ Deutschland
- Installable as a PWA on Android and iPhone
- WJ corporate design (Chivo + Bitter fonts, WJD Blue #003594, Teal #47D7AC)

---

## Installation (Mobile)

**Android (Brave / Chrome):**
1. Open the live URL in Brave or Chrome
2. Tap menu → "Add to Home Screen"
3. The app launches fullscreen without browser UI

**iPhone (Safari only):**
1. Open the live URL in Safari
2. Tap Share → "Add to Home Screen"

---

## Tech Stack

- Pure HTML / CSS / JavaScript — no frameworks
- PWA with Service Worker for offline support
- Fonts: Chivo (headings), Bitter (body) via Google Fonts
- Icons: Custom SVG inline icons
- Hosting: GitHub Pages (free, no limits)

---

## Development

All files are static and can be edited directly on GitHub or locally.

To update the app:
1. Edit the relevant file on GitHub (e.g. `index.html`)
2. Commit changes to `main`
3. GitHub Pages deploys automatically within ~1 minute

# ---

## Structure

```
/
├── index.html          # Main app
├── manifest.json       # PWA manifest
├── sw.js               # Service Worker
├── icon-192.png        # App icon (192px)
├── icon-512.png        # App icon (512px)
├── icon-192-maskable.png
├── icon-512-maskable.png
├── apple-touch-icon.png        # iPhone icon (180px)
├── apple-touch-icon-120.png
├── apple-touch-icon-152.png
├── apple-touch-icon-167.png
├── logo-weiss.svg      # WJD logo white
└── logo-farbe.svg      # WJD logo color
```

---

## About

**Wirtschaftsjunioren Ulm / Neu-Ulm** is part of Wirtschaftsjunioren Deutschland (WJD), the largest network of young entrepreneurs in Germany with ~10,000 members across 215 regional chapters.

- Website: https://www.wj-ulm.de
- Portal: https://www.vereinonline.org/WJ_UlmNeuUlm/
- National: https://www.wjd.de
