#!/usr/bin/env python3
"""Lädt die erzeugten Demo-Daten in die laufenden Dienste.

Demo-Firma, fiktive Daten.

- Mailpit:      alle E-Mails aus data/generated/mails per SMTP einspielen
- paperless-ngx: Angebote, Rechnungen, Wartungsverträge hochladen und verschlagworten
- Open WebUI:   Admin-Konto anlegen, Wissenssammlung "Häuserhofer Handbuch" mit den internen Dokumenten

Nur Standardbibliothek. Zugangsdaten kommen aus der Umgebung (.env, siehe .env.example).

Aufruf:
    python3 seed/load.py --data data/generated [--nur mailpit,paperless,openwebui]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from email import message_from_bytes
from email.utils import parseaddr
from pathlib import Path

WISSEN_NAME = "Häuserhofer Handbuch (Demo)"


class LadeFehler(RuntimeError):
    pass


def env(name: str, default: str | None = None) -> str:
    wert = os.environ.get(name, default)
    if wert is None or wert == "":
        raise LadeFehler(f"Umgebungsvariable {name} fehlt. Ist .env angelegt (cp .env.example .env)?")
    return wert


# --------------------------------------------------------------------------- #
# HTTP-Hilfen
# --------------------------------------------------------------------------- #

def http(method: str, url: str, *, token: str | None = None, token_art: str = "Bearer",
         json_body: object | None = None, data: bytes | None = None, headers: dict | None = None,
         timeout: float = 60) -> tuple[int, object]:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    if token:
        h["Authorization"] = f"{token_art} {token}"
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
    except urllib.error.URLError as e:
        raise LadeFehler(f"{method} {url} nicht erreichbar: {e.reason}") from e
    try:
        body: object = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        body = raw.decode("utf-8", "replace")
    return status, body


def multipart(felder: dict[str, str | list[str]], dateien: dict[str, Path]) -> tuple[bytes, str]:
    grenze = f"----demo{uuid.uuid4().hex}"
    teile: list[bytes] = []
    for name, wert in felder.items():
        for w in (wert if isinstance(wert, list) else [wert]):
            teile.append(f'--{grenze}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{w}\r\n'.encode())
    for name, pfad in dateien.items():
        typ = mimetypes.guess_type(pfad.name)[0] or "application/octet-stream"
        kopf = (f'--{grenze}\r\nContent-Disposition: form-data; name="{name}"; '
                f'filename="{pfad.name}"\r\nContent-Type: {typ}\r\n\r\n').encode()
        teile.append(kopf + pfad.read_bytes() + b"\r\n")
    teile.append(f"--{grenze}--\r\n".encode())
    return b"".join(teile), f"multipart/form-data; boundary={grenze}"


def warte_auf(url: str, name: str, sekunden: int = 300, ok=(200, 401, 403)) -> None:
    ende = time.monotonic() + sekunden
    letzter = ""
    while time.monotonic() < ende:
        try:
            status, _ = http("GET", url, timeout=5)
            if status in ok:
                return
            letzter = f"HTTP {status}"
        except LadeFehler as e:
            letzter = str(e)
        time.sleep(3)
    raise LadeFehler(f"{name} ist nach {sekunden} s nicht bereit ({letzter}). Läuft 'make up'?")


# --------------------------------------------------------------------------- #
# Mailpit
# --------------------------------------------------------------------------- #

def lade_mailpit(data: Path) -> int:
    web = env("MAILPIT_URL", f"http://localhost:{os.environ.get('MAILPIT_WEB_PORT', '8025')}")
    host = env("MAILPIT_SMTP_HOST", "localhost")
    port = int(env("MAILPIT_SMTP_PORT", "1025"))
    warte_auf(f"{web}/readyz", "Mailpit", ok=(200,))
    status, _ = http("DELETE", f"{web}/api/v1/messages")
    if status != 200:
        raise LadeFehler(f"Mailpit: Postfach leeren fehlgeschlagen (HTTP {status})")
    dateien = sorted((data / "mails").glob("*.eml"))
    if not dateien:
        raise LadeFehler("Keine E-Mails gefunden. Erst 'make data' ausführen.")
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        for pfad in dateien:
            roh = pfad.read_bytes()
            msg = message_from_bytes(roh)
            absender = parseaddr(msg["From"])[1]
            empfaenger = [parseaddr(msg["To"])[1]]
            smtp.sendmail(absender, empfaenger, roh)
    print(f"  Mailpit: {len(dateien)} E-Mails eingespielt")
    return len(dateien)


# --------------------------------------------------------------------------- #
# paperless-ngx
# --------------------------------------------------------------------------- #

def lade_paperless(data: Path) -> int:
    basis = env("PAPERLESS_URL", f"http://localhost:{os.environ.get('PAPERLESS_PORT', '8000')}")
    warte_auf(f"{basis}/api/documents/", "paperless-ngx", sekunden=600)
    status, body = http("POST", f"{basis}/api/token/",
                        json_body={"username": env("DEMO_ADMIN_USER", "demo"), "password": env("DEMO_ADMIN_PASSWORD")})
    if status != 200 or not isinstance(body, dict) or "token" not in body:
        raise LadeFehler(f"paperless-ngx: Anmeldung fehlgeschlagen (HTTP {status}: {body})")
    token = body["token"]

    def tag_id(name: str, farbe: str) -> int:
        q = urllib.parse.quote(name)
        s, b = http("GET", f"{basis}/api/tags/?name__iexact={q}", token=token, token_art="Token")
        if s == 200 and isinstance(b, dict) and b.get("results"):
            return b["results"][0]["id"]
        s, b = http("POST", f"{basis}/api/tags/", token=token, token_art="Token",
                    json_body={"name": name, "color": farbe, "matching_algorithm": 0})
        if s not in (200, 201):
            raise LadeFehler(f"paperless-ngx: Tag {name} anlegen fehlgeschlagen (HTTP {s}: {b})")
        return b["id"]

    tags = {
        "angebote": tag_id("Angebot", "#1f78b4"),
        "rechnungen": tag_id("Rechnung", "#33a02c"),
        "wartungsvertraege": tag_id("Wartungsvertrag", "#ff7f00"),
    }
    demo_tag = tag_id("Demo-Daten", "#999999")

    status, body = http("GET", f"{basis}/api/documents/?page_size=1", token=token, token_art="Token")
    if status == 200 and isinstance(body, dict) and body.get("count", 0) > 0:
        raise LadeFehler(f"paperless-ngx enthält schon {body['count']} Dokumente. Für einen sauberen Stand 'make reset'.")

    belege = {}
    tabelle = data / "tabellen" / "belege.csv"
    for zeile in tabelle.read_text(encoding="utf-8").splitlines()[1:]:
        teile = zeile.split(";")
        belege[teile[0]] = teile[2]
    for zeile in (data / "tabellen" / "wartungsvertraege.csv").read_text(encoding="utf-8").splitlines()[1:]:
        teile = zeile.split(";")
        belege[teile[0]] = teile[5]

    aufgaben: list[str] = []
    for ordner, tag in tags.items():
        for pfad in sorted((data / "dokumente" / ordner).glob("*.pdf")):
            felder: dict[str, str | list[str]] = {"title": pfad.stem, "tags": [str(tag), str(demo_tag)]}
            if pfad.stem in belege:
                felder["created"] = belege[pfad.stem]
            body_bytes, typ = multipart(felder, {"document": pfad})
            s, b = http("POST", f"{basis}/api/documents/post_document/", token=token, token_art="Token",
                        data=body_bytes, headers={"Content-Type": typ}, timeout=120)
            if s != 200:
                raise LadeFehler(f"paperless-ngx: Upload {pfad.name} fehlgeschlagen (HTTP {s}: {b})")
            task_id = b.get("task_id") if isinstance(b, dict) else b
            if not task_id:
                raise LadeFehler(f"paperless-ngx: keine Task-ID für {pfad.name} ({b})")
            aufgaben.append(str(task_id).strip('"'))

    # Auf die Verarbeitung (OCR) warten
    offen = set(aufgaben)
    fehler: list[str] = []
    ende = time.monotonic() + 900
    while offen and time.monotonic() < ende:
        for task_id in list(offen):
            s, b = http("GET", f"{basis}/api/tasks/?task_id={task_id}", token=token, token_art="Token")
            eintraege = b.get("results", []) if isinstance(b, dict) else (b if isinstance(b, list) else [])
            if s == 200 and eintraege:
                t = eintraege[0]
                st = str(t.get("status", "")).upper()
                if st == "SUCCESS":
                    offen.discard(task_id)
                elif st in ("FAILURE", "REVOKED"):
                    name = t.get("task_file_name") or t.get("input_data", {}).get("filename", task_id)
                    fehler.append(f"{name}: {t.get('result') or t.get('result_data')}")
                    offen.discard(task_id)
        if offen:
            time.sleep(3)
    if fehler:
        raise LadeFehler("paperless-ngx: Verarbeitung fehlgeschlagen:\n  " + "\n  ".join(fehler))
    if offen:
        raise LadeFehler(f"paperless-ngx: {len(offen)} Dokumente nach 15 min noch nicht verarbeitet")
    print(f"  paperless-ngx: {len(aufgaben)} Dokumente verarbeitet")
    return len(aufgaben)


# --------------------------------------------------------------------------- #
# Open WebUI
# --------------------------------------------------------------------------- #

def openwebui_token(basis: str) -> str:
    email = env("DEMO_ADMIN_EMAIL", "admin@haeuserhofer.example")
    passwort = env("DEMO_ADMIN_PASSWORD")
    s, b = http("POST", f"{basis}/api/v1/auths/signin", json_body={"email": email, "password": passwort})
    if s == 200 and isinstance(b, dict) and b.get("token"):
        return b["token"]
    s, b = http("POST", f"{basis}/api/v1/auths/signup",
                json_body={"name": "Demo Admin", "email": email, "password": passwort})
    if s == 200 and isinstance(b, dict) and b.get("token"):
        return b["token"]
    raise LadeFehler(f"Open WebUI: Anmeldung und Registrierung fehlgeschlagen (HTTP {s}: {b})")


def lade_openwebui(data: Path) -> int:
    basis = env("OPEN_WEBUI_URL", f"http://localhost:{os.environ.get('OPEN_WEBUI_PORT', '3000')}")
    warte_auf(f"{basis}/health", "Open WebUI", sekunden=600, ok=(200,))
    token = openwebui_token(basis)

    s, b = http("GET", f"{basis}/api/v1/knowledge/", token=token)
    if s != 200:
        raise LadeFehler(f"Open WebUI: Wissenssammlungen abrufen fehlgeschlagen (HTTP {s}: {b})")
    eintraege = b.get("items", b) if isinstance(b, dict) else b
    for k in eintraege or []:
        if k.get("name") == WISSEN_NAME:
            s, _ = http("DELETE", f"{basis}/api/v1/knowledge/{k['id']}/delete", token=token)
            if s != 200:
                raise LadeFehler(f"Open WebUI: alte Wissenssammlung löschen fehlgeschlagen (HTTP {s})")

    s, b = http("POST", f"{basis}/api/v1/knowledge/create", token=token,
                json_body={"name": WISSEN_NAME,
                           "description": "Interne Dokumente der fiktiven Häuserhofer Haustechnik GmbH (Demo-Daten)"})
    if s != 200 or not isinstance(b, dict) or "id" not in b:
        raise LadeFehler(f"Open WebUI: Wissenssammlung anlegen fehlgeschlagen (HTTP {s}: {b})")
    wissen_id = b["id"]

    dateien = sorted((data / "wissen").glob("*.md"))
    for pfad in dateien:
        body_bytes, typ = multipart({}, {"file": pfad})
        s, b = http("POST", f"{basis}/api/v1/files/?process=true", token=token, data=body_bytes,
                    headers={"Content-Type": typ}, timeout=300)
        if s != 200 or not isinstance(b, dict) or "id" not in b:
            raise LadeFehler(f"Open WebUI: Upload {pfad.name} fehlgeschlagen (HTTP {s}: {b})")
        datei_id = b["id"]
        ende = time.monotonic() + 300
        while time.monotonic() < ende:
            s, st = http("GET", f"{basis}/api/v1/files/{datei_id}/process/status", token=token)
            zustand = st.get("status") if isinstance(st, dict) else None
            if s == 404 or zustand in (None, "completed"):
                break
            if zustand == "failed":
                raise LadeFehler(f"Open WebUI: Verarbeitung {pfad.name} fehlgeschlagen: {st}. "
                                 "Ist das Embedding-Modell in Ollama geladen (make models)?")
            time.sleep(2)
        s, b = http("POST", f"{basis}/api/v1/knowledge/{wissen_id}/file/add", token=token,
                    json_body={"file_id": datei_id}, timeout=300)
        if s != 200:
            raise LadeFehler(f"Open WebUI: {pfad.name} zur Wissenssammlung hinzufügen fehlgeschlagen "
                             f"(HTTP {s}: {b}). Ist das Embedding-Modell in Ollama geladen (make models)?")
    print(f"  Open WebUI: Wissenssammlung '{WISSEN_NAME}' mit {len(dateien)} Dokumenten")
    return len(dateien)


# --------------------------------------------------------------------------- #

LADER = {"mailpit": lade_mailpit, "paperless": lade_paperless, "openwebui": lade_openwebui}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data/generated"))
    ap.add_argument("--nur", default=",".join(LADER), help="Kommagetrennt: " + ", ".join(LADER))
    args = ap.parse_args()
    if not (args.data / "manifest.json").exists():
        print(f"FEHLER: {args.data}/manifest.json fehlt. Erst 'make data' ausführen.", file=sys.stderr)
        return 1
    print("Lade Demo-Daten (Demo-Firma, fiktive Daten):")
    try:
        for name in [n.strip() for n in args.nur.split(",") if n.strip()]:
            if name not in LADER:
                raise LadeFehler(f"Unbekannter Dienst '{name}'. Erlaubt: {', '.join(LADER)}")
            LADER[name](args.data)
    except LadeFehler as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    print("Fertig.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
