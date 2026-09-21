#!/usr/bin/env python3
"""Holt den oeffentlichen VereinOnline-Kalender und schreibt termine.json.

Aufruf:  python3 tools/ics2json.py
Wird von .github/workflows/termine.yml alle 3 Stunden und per Knopfdruck ausgefuehrt.
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

FEED = "https://www.vereinonline.org/WJ_UlmNeuUlm/kalender.ics"
OUT = "termine.json"
MAX_EVENTS = 20          # so viele kuenftige Termine schreiben wir raus
AUSBLENDEN = re.compile(r"blocker", re.I)
ABGESAGT = re.compile(r"^\s*(abgesagt\s*[:\-]?\s*)+", re.I)
try:
    BERLIN = ZoneInfo("Europe/Berlin")
except Exception:                                  # noqa: BLE001  (Windows ohne tzdata)
    BERLIN = datetime.now().astimezone().tzinfo
UA = {"User-Agent": "wj-ulm-app/1.0 (+https://github.com/mvonulmerbach-ship-it/wj-ulm-app)"}


def unfold(raw: str) -> str:
    """iCal-Zeilenfaltung aufheben (RFC 5545: Folgezeile beginnt mit Space/Tab)."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n[ \t]", "", raw)


def cp1252_reparieren(value: str) -> str:
    """VereinOnline liefert manche Zeichen (z. B. den Gedankenstrich) als
    Windows-1252-Byte, das als Steuerzeichen U+0080..U+009F im UTF-8-Feed
    landet. Diese Zeichen zurueck in das gemeinte Zeichen wandeln."""
    def ersetzen(m):
        try:
            return bytes([ord(m.group(0))]).decode("cp1252")
        except UnicodeDecodeError:
            return ""
    return re.sub(r"[\x80-\x9f]", ersetzen, value)


def unescape(value: str) -> str:
    value = cp1252_reparieren(value)
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
    if value.endswith("Z"):            # UTC -> Berlin, mit Sommer-/Winterzeit
        dt = dt.replace(tzinfo=timezone.utc).astimezone(BERLIN).replace(tzinfo=None)
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

    jetzt = datetime.now(BERLIN)
    today = jetzt.date()
    events = []
    for block in blocks:
        summary = field(block, "SUMMARY")
        dtstart = field(block, "DTSTART")
        if not summary or not dtstart:
            continue
        # Platzhalter ("Blocker") gehoeren nicht in die App, genau wie auf der Webseite
        if AUSBLENDEN.search(summary):
            continue
        dt, has_time = parse_dt(dtstart)
        if dt is None:
            continue

        # Letzter Tag: bei ganztaegigen Terminen ist DTEND der Tag DANACH (RFC 5545)
        ende = dt.date()
        ende_dt, ende_zeit = parse_dt(field(block, "DTEND")) if field(block, "DTEND") else (None, False)
        if ende_dt is not None:
            ende = ende_dt.date() if ende_zeit else (ende_dt - timedelta(days=1)).date()
            if ende < dt.date():
                ende = dt.date()
        if ende < today:                 # mehrtaegige Termine bleiben bis zum letzten Tag
            continue

        abgesagt = bool(ABGESAGT.match(summary)) or field(block, "STATUS").upper() == "CANCELLED"
        eintrag = {
            "titel": ABGESAGT.sub("", summary).strip(),
            "datum": dt.strftime("%Y-%m-%d"),
            "zeit": dt.strftime("%H:%M") if has_time else "",
            "ort": field(block, "LOCATION"),
            "url": field(block, "URL"),
        }
        if ende > dt.date():
            eintrag["bis"] = ende.strftime("%Y-%m-%d")
        if abgesagt:
            eintrag["abgesagt"] = True
        events.append(eintrag)

    events.sort(key=lambda e: (e["datum"], e["zeit"]))
    events = events[:MAX_EVENTS]

    payload = {
        "stand": jetzt.strftime("%Y-%m-%d %H:%M"),
        "quelle": FEED,
        "termine": events,
    }

    # Nur schreiben, wenn sich die Termine geaendert haben oder der Stand
    # aelter als einen Tag ist. So zeigt die App hoechstens einen Tag alten
    # Stand an, ohne bei jedem Lauf (alle 3 Stunden) einen Commit zu erzeugen.
    try:
        with open(OUT, encoding="utf-8") as fh:
            alt = json.load(fh)
        alt_stand = datetime.strptime(alt.get("stand", ""), "%Y-%m-%d %H:%M")
        frisch = jetzt.replace(tzinfo=None) - alt_stand < timedelta(hours=23)
        if alt.get("termine") == events and frisch:
            print(f"unveraendert ({len(events)} Termine), Stand {alt['stand']} - nicht geschrieben")
            return 0
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
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
