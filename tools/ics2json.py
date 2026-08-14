#!/usr/bin/env python3
"""Holt den oeffentlichen VereinOnline-Kalender und schreibt termine.json.

Aufruf:  python3 tools/ics2json.py
Wird von .github/workflows/termine.yml per Knopfdruck ausgefuehrt.
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, date, timezone, timedelta

FEED = "https://www.vereinonline.org/WJ_UlmNeuUlm/kalender.ics"
OUT = "termine.json"
MAX_EVENTS = 20          # so viele kuenftige Termine schreiben wir raus
UA = {"User-Agent": "wj-ulm-app/1.0 (+https://github.com/mvonulmerbach-ship-it/wj-ulm-app)"}


def unfold(raw: str) -> str:
    """iCal-Zeilenfaltung aufheben (RFC 5545: Folgezeile beginnt mit Space/Tab)."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n[ \t]", "", raw)


def unescape(value: str) -> str:
    return (value.replace("\\n", " ").replace("\\N", " ")
                 .replace("\\,", ",").replace("\\;", ";")
                 .replace("\\\\", "\\").strip())


def parse_dt(value: str):
    """Gibt (date, hat_uhrzeit) zurueck. Zeitzone ignorieren wir bewusst:
    der Feed liefert Europe/Berlin, und die App zeigt nur Datum + Uhrzeit an."""
    value = value.strip()
    m = re.match(r"^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})Z?)?$", value)
    if not m:
        return None, False
    y, mo, d, hh, mi, _ss = m.groups()
    if hh is None:
        return datetime(int(y), int(mo), int(d)), False
    dt = datetime(int(y), int(mo), int(d), int(hh), int(mi))
    if value.endswith("Z"):            # UTC -> Berlin (grob, reicht fuer Anzeige)
        dt = dt.replace(tzinfo=timezone.utc).astimezone(
            timezone(timedelta(hours=2))).replace(tzinfo=None)
    return dt, True


def field(block: str, name: str) -> str:
    m = re.search(r"^" + name + r"(?:;[^:\n]*)?:(.*)$", block, re.M)
    return unescape(m.group(1)) if m else ""


def main() -> int:
    try:
        req = urllib.request.Request(FEED, headers=UA)
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception as exc:                       # noqa: BLE001
        print(f"FEHLER beim Abruf: {exc}", file=sys.stderr)
        return 1

    text = unfold(raw)
    blocks = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S)
    if not blocks:
        print("FEHLER: keine VEVENT-Bloecke im Feed", file=sys.stderr)
        return 1

    today = date.today()
    events = []
    for block in blocks:
        summary = field(block, "SUMMARY")
        dtstart = field(block, "DTSTART")
        if not summary or not dtstart:
            continue
        dt, has_time = parse_dt(dtstart)
        if dt is None or dt.date() < today:
            continue
        events.append({
            "titel": summary,
            "datum": dt.strftime("%Y-%m-%d"),
            "zeit": dt.strftime("%H:%M") if has_time else "",
            "ort": field(block, "LOCATION"),
            "url": field(block, "URL"),
        })

    events.sort(key=lambda e: (e["datum"], e["zeit"]))
    events = events[:MAX_EVENTS]

    payload = {
        "stand": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "quelle": FEED,
        "termine": events,
    }

    # Nur schreiben, wenn sich inhaltlich etwas geaendert hat -> keine Leer-Commits
    try:
        with open(OUT, encoding="utf-8") as fh:
            alt = json.load(fh)
        if alt.get("termine") == events:
            print(f"unveraendert ({len(events)} Termine) — nicht geschrieben")
            return 0
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print(f"{len(events)} kuenftige Termine geschrieben")
    for e in events[:5]:
        print(f"  {e['datum']} {e['zeit']:<5} {e['titel'][:55]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
