# CLAUDE.md – WJ Ulm / Neu-Ulm App (`wj-ulm-app`)

@~/Nextcloud/Claude/Projekte/MiniApps/REGELN.md

Die Regeln oben (REGELN.md) gelten für jede Session in diesem Repo, dazu das Mini-App-Muster aus den CLAUDE-Anweisungen. Hier steht nur, was **diese** App betrifft.

## Diese App

- **Live:** https://mvonulmerbach-ship-it.github.io/wj-ulm-app/ · Beschreibung und Abweichungen: `README.md`
- **Familie:** Einzelstück
- **Version:** `CORE` in `sw.js` – bei jeder Änderung hochzählen; die Zahl steht nur dort.
- WJ-Corporate-Design (WJD-Blau #003594, Teal #47D7AC, Chivo + Bitter als **lokale** Webfonts) geht dem allgemeinen Muster vor.
- Version ist `CORE` in `sw.js` (`PRAEFIX + "core-vN"`).

## Abschluss (DoD nach REGELN §2)

UI-Prüfung im Repo-Ordner, erwartet „UI-PRUEFUNG GRUEN“ (kein Befund der Schwere ≥ 2), danach die Bildschirmfotos aus dem genannten Ordner ansehen:

```powershell
& "$env:LOCALAPPDATA\Mietverwaltung\venv\Scripts\python.exe" "$env:USERPROFILE\Nextcloud\Claude\Projekte\App-Design-Datenbank\Werkzeuge\ui_pruefen.py" .
```

Am Ende Summary und Description für dieses Repo als eigene Codeblöcke; committet und gepusht wird von Max.
