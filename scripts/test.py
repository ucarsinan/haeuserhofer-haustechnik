#!/usr/bin/env python3
"""Prüft, ob die Demo-Umgebung bereit für eine Aufnahme ist.

Demo-Firma, fiktive Daten.

Prüft Dienste, Datenmengen und (mit --ki) ob das lokale Modell Demo-Fragen
aus dem Mitarbeiterhandbuch richtig beantwortet. Exit-Code 0 = alles grün.

Aufruf:
    python3 scripts/test.py [--data data/generated] [--ki] [--ohne openwebui,ollama]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GRUEN, ROT, GELB, AUS = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

# Frage, erwartete Bestandteile der Antwort (alle müssen vorkommen), Quelle
DEMO_FRAGEN = [
    ("Wie viele Urlaubstage habe ich bei einer 5-Tage-Woche?", ["30"], "urlaubsregelung.md"),
    ("Wie hoch ist die Pauschale für eine Bereitschaftswoche im Notdienst?", ["150"], "mitarbeiterhandbuch.md"),
    ("Bis wann muss ich mich am ersten Krankheitstag melden?", ["7"], "mitarbeiterhandbuch.md"),
    ("Darf ich Kundendaten in mein privates ChatGPT-Konto eingeben?", ["nein"], "ki-richtlinie.md"),
]


def get(url: str, token: str | None = None, art: str = "Bearer", timeout: float = 10) -> tuple[int, object]:
    h = {"Accept": "application/json"}
    if token:
        h["Authorization"] = f"{art} {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            raw, status = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        return 0, str(getattr(e, "reason", e))
    try:
        return status, json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return status, raw.decode("utf-8", "replace")


def post(url: str, body: dict, token: str | None = None, art: str = "Bearer", timeout: float = 30) -> tuple[int, object]:
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"{art} {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, status = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        return 0, str(getattr(e, "reason", e))
    try:
        return status, json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return status, raw.decode("utf-8", "replace")


class Pruefer:
    def __init__(self) -> None:
        self.fehler = 0

    def ok(self, text: str) -> None:
        print(f"  {GRUEN}OK{AUS}    {text}")

    def fail(self, text: str) -> None:
        self.fehler += 1
        print(f"  {ROT}FEHLER{AUS} {text}")

    def warn(self, text: str) -> None:
        print(f"  {GELB}HINWEIS{AUS} {text}")

    def check(self, bedingung: bool, gut: str, schlecht: str) -> bool:
        (self.ok if bedingung else self.fail)(gut if bedingung else schlecht)
        return bedingung


def port(name: str, standard: str) -> str:
    return os.environ.get(name, standard)


def pruefe_mailpit(p: Pruefer, m: dict) -> None:
    print("Mailpit (Postfach)")
    basis = os.environ.get("MAILPIT_URL", f"http://localhost:{port('MAILPIT_WEB_PORT', '8025')}")
    s, b = get(f"{basis}/api/v1/messages?limit=1")
    if not p.check(s == 200, "erreichbar", f"nicht erreichbar ({s}: {b})"):
        return
    soll = m["anzahl"]["mails"]
    p.check(b.get("total") == soll, f"{soll} E-Mails im Postfach", f"{b.get('total')} statt {soll} E-Mails")
    s, b = get(f"{basis}/api/v1/search?query=" + urllib.parse.quote("subject:Störung") + "&limit=1")
    p.check(s == 200 and b.get("messages_count", 0) > 0, "Suche nach 'Störung' liefert Treffer",
            f"Suche nach 'Störung' ohne Treffer ({s})")


def pruefe_paperless(p: Pruefer, m: dict) -> None:
    print("paperless-ngx (Belege)")
    basis = os.environ.get("PAPERLESS_URL", f"http://localhost:{port('PAPERLESS_PORT', '8000')}")
    s, b = post(f"{basis}/api/token/", {"username": os.environ.get("DEMO_ADMIN_USER", "demo"),
                                        "password": os.environ.get("DEMO_ADMIN_PASSWORD", "")})
    if not p.check(s == 200 and isinstance(b, dict) and "token" in b, "Anmeldung", f"Anmeldung fehlgeschlagen ({s}: {b})"):
        return
    t = b["token"]
    soll = m["anzahl"]["angebote"] + m["anzahl"]["rechnungen"] + m["anzahl"]["wartungsvertraege"]
    s, b = get(f"{basis}/api/documents/?page_size=1", t, "Token")
    p.check(s == 200 and b.get("count") == soll, f"{soll} Dokumente", f"{b.get('count') if isinstance(b, dict) else b} statt {soll} Dokumente")
    s, b = get(f"{basis}/api/documents/?page_size=1&query=" + urllib.parse.quote("Hydraulik-Paket"), t, "Token")
    p.check(s == 200 and b.get("count", 0) > 0, "Volltextsuche (OCR) findet 'Hydraulik-Paket'",
            f"Volltextsuche findet 'Hydraulik-Paket' nicht ({s})")


def pruefe_openwebui(p: Pruefer, m: dict) -> None:
    print("Open WebUI (Chat)")
    basis = os.environ.get("OPEN_WEBUI_URL", f"http://localhost:{port('OPEN_WEBUI_PORT', '3000')}")
    s, _ = get(f"{basis}/health")
    if not p.check(s == 200, "erreichbar", f"nicht erreichbar ({s})"):
        return
    s, b = post(f"{basis}/api/v1/auths/signin", {"email": os.environ.get("DEMO_ADMIN_EMAIL", "admin@haeuserhofer.example"),
                                                 "password": os.environ.get("DEMO_ADMIN_PASSWORD", "")})
    if not p.check(s == 200 and isinstance(b, dict) and b.get("token"), "Anmeldung", f"Anmeldung fehlgeschlagen ({s})"):
        return
    token = b["token"]
    s, b = get(f"{basis}/api/v1/knowledge/", token)
    eintraege = b.get("items", b) if isinstance(b, dict) else (b or [])
    treffer = [k for k in eintraege if k.get("name") == "Häuserhofer Handbuch (Demo)"]
    if not p.check(len(treffer) == 1, "Wissenssammlung 'Häuserhofer Handbuch (Demo)' vorhanden",
                   f"Wissenssammlung {len(treffer)}x statt 1x vorhanden"):
        return
    soll = m["anzahl"]["wissen"]
    s, b = get(f"{basis}/api/v1/knowledge/{treffer[0]['id']}/files", token)
    dateien = b.get("items", []) if isinstance(b, dict) else (b or [])
    if s != 200:  # ältere Open-WebUI-Versionen liefern die Dateien direkt mit
        s, b = get(f"{basis}/api/v1/knowledge/{treffer[0]['id']}", token)
        dateien = (b.get("files") or []) if isinstance(b, dict) else []
    p.check(len(dateien) == soll, f"{soll} Dokumente in der Wissenssammlung", f"{len(dateien)} statt {soll} Dokumente")


def pruefe_ollama(p: Pruefer, m: dict, ki: bool, data: Path) -> None:
    print("Ollama (lokales Modell, nativ)")
    basis = os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
    chat = os.environ.get("CHAT_MODEL", "gemma3:12b")
    emb = os.environ.get("EMBEDDING_MODEL", "bge-m3")
    s, b = get(f"{basis}/api/tags")
    if not p.check(s == 200, "erreichbar", f"nicht erreichbar unter {basis}. Ollama-App gestartet?"):
        return
    modelle = {x["name"] for x in b.get("models", [])}

    def da(name: str) -> bool:
        return name in modelle or f"{name}:latest" in modelle

    p.check(da(chat), f"Chat-Modell {chat} geladen", f"Chat-Modell {chat} fehlt (make models)")
    p.check(da(emb), f"Embedding-Modell {emb} geladen", f"Embedding-Modell {emb} fehlt (make models)")
    if not ki:
        p.warn("Demo-Fragen übersprungen (mit 'make test-ki' prüfen)")
        return
    if not da(chat):
        return
    for frage, erwartet, quelle in DEMO_FRAGEN:
        text = (data / "wissen" / quelle).read_text(encoding="utf-8")
        s, b = post(f"{basis}/api/chat", {
            "model": chat, "stream": False, "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": "Du bist der interne Assistent einer Firma. Antworte kurz auf Deutsch "
                                              "und nur mit Informationen aus dem Dokument. Beginne Ja/Nein-Fragen mit Ja oder Nein.\n\n"
                                              f"DOKUMENT ({quelle}):\n{text}"},
                {"role": "user", "content": frage}]}, timeout=300)
        antwort = (b.get("message", {}).get("content", "") if isinstance(b, dict) else str(b)).strip()
        fehlt = [e for e in erwartet if e.lower() not in antwort.lower()]
        kurz = antwort.replace("\n", " ")[:110]
        p.check(s == 200 and not fehlt, f"'{frage}' -> {kurz}", f"'{frage}' -> erwartet {erwartet}, Antwort: {kurz}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data/generated"))
    ap.add_argument("--ki", action="store_true", help="Demo-Fragen an das lokale Modell stellen")
    ap.add_argument("--ohne", default="", help="Kommagetrennt überspringen: mailpit, paperless, openwebui, ollama")
    args = ap.parse_args()
    manifest = args.data / "manifest.json"
    if not manifest.exists():
        print(f"{ROT}FEHLER{AUS} {manifest} fehlt. Erst 'make data' oder 'make reset'.")
        return 1
    m = json.loads(manifest.read_text(encoding="utf-8"))
    ohne = {x.strip() for x in args.ohne.split(",") if x.strip()}
    print(f"Prüfe Demo-Umgebung ({m['firma']}, Stichtag {m['stichtag']}, Demo-Daten)\n")
    p = Pruefer()
    if "mailpit" not in ohne:
        pruefe_mailpit(p, m)
    if "paperless" not in ohne:
        pruefe_paperless(p, m)
    if "openwebui" not in ohne:
        pruefe_openwebui(p, m)
    if "ollama" not in ohne:
        pruefe_ollama(p, m, args.ki, args.data)
    print()
    if p.fehler:
        print(f"{ROT}{p.fehler} Prüfung(en) fehlgeschlagen. Nicht aufnehmen.{AUS}")
        return 1
    print(f"{GRUEN}Alles grün. Bereit für die Aufnahme.{AUS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
