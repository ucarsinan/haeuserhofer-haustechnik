# haeuserhofer-haustechnik: Häuserhofer Haustechnik GmbH

> **Demo-Firma, fiktive Daten.** Die Häuserhofer Haustechnik GmbH existiert nicht. Alle Personen, Kunden, Zahlen und Dokumente sind erfunden. Ähnlichkeiten mit echten Firmen oder Personen sind nicht beabsichtigt.

Diese Umgebung gehört zum YouTube-Kanal **„Sinan Uçar | KI für Unternehmen“**. Alles, was in den Videos gezeigt wird, läuft hier vorher wirklich. Du kannst es auf deinem eigenen Rechner nachbauen.

## Die Firma in einem Satz

Ein Heizungs- und Sanitärbetrieb mit 46 Leuten, der Heizungen, Wärmepumpen, Lüftung und Bäder einbaut und wartet und in einer eigenen Werkstatt Wärmepumpen-Pakete für andere Betriebe vormontiert.

## Was drin ist

| Dienst | Zweck | Adresse |
|---|---|---|
| Ollama (nativ, nicht im Container) | lokale KI-Modelle | http://localhost:11434 |
| Open WebUI | Chat „ChatGPT im eigenen Haus“, mit Wissenssammlung aus den Firmendokumenten | http://localhost:3000 |
| paperless-ngx | Belege und Dokumente mit Texterkennung | http://localhost:8000 |
| Mailpit | Fake-Postfach mit 200 Kundenmails | http://localhost:8025 |

Alle Ports sind nur auf `127.0.0.1` gebunden.

| Demo-Daten | Menge |
|---|---|
| Mitarbeitende | 46 |
| Kunden (60 % privat, 25 % Wohnungswirtschaft, 15 % Betriebe) | 300 |
| Kunden-E-Mails (Anfragen, Störungen, Beschwerden, Spam …) | 200 |
| Angebote, Rechnungen, Wartungsverträge (PDF) | je 30 |
| Interne Dokumente (Mitarbeiterhandbuch, Urlaubsregelung, KI-Richtlinie) | 3 |
| Preisliste | 20 Positionen |

Die Daten erzeugt `seed/generate.py`. Gleicher Seed und gleicher Stichtag ergeben dieselben Daten. Datumsangaben laufen bis zum Stichtag (Standard: heute), damit die Firma „lebt“.

## Voraussetzungen

- macOS mit Apple Silicon und mindestens 32 GB RAM (getestet wird auf einem MacBook Pro mit 32 GB). Linux mit NVIDIA-GPU geht auch, dann `OLLAMA_BASE_URL` anpassen.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) oder OrbStack
- [Ollama](https://ollama.com/download) als App
- Python 3.11 oder neuer, `make`

## Start

```bash
cp .env.example .env          # Schlüssel ersetzen: openssl rand -hex 32
make models                   # Chat- und Embedding-Modell in Ollama laden (einmalig, mehrere GB)
make reset                    # alles neu: Daten erzeugen, Dienste starten, Daten laden
make test                     # prüfen, ob alles bereit ist
make test-ki                  # zusätzlich Demo-Fragen an das lokale Modell
```

Anmeldung in Open WebUI und paperless-ngx mit den Demo-Zugangsdaten aus `.env` (`DEMO_ADMIN_EMAIL` bzw. `DEMO_ADMIN_USER` und `DEMO_ADMIN_PASSWORD`).

| Befehl | Was passiert |
|---|---|
| `make reset` | löscht **alle** Volumes, erzeugt Daten neu, startet und befüllt alles. Vor jeder Aufnahme |
| `make up` / `make down` | starten / stoppen, Daten bleiben |
| `make data STICHTAG=2026-11-21` | nur Daten erzeugen, mit festem Stichtag |
| `make test` | prüft Dienste, Datenmengen, Volltextsuche, Modelle |
| `make logs`, `make status` | Logs und Status |

## Regeln für die Demo-Daten

- Domains nur `*.example` (RFC 2606, nie registrierbar)
- Postleitzahlen `00xxx` (gibt es in Deutschland nicht), Orte mit Zusatz „(fiktiv)“
- Telefonnummern `0000 000000-xx`, IBAN `DE00 0000 0000 0000 0000 00` (absichtlich ungültig)
- Personen nur mit häufigen Vor- und Nachnamen, keine echten Fotos oder Stimmen
- Jedes PDF trägt den Hinweis „Demo-Firma, fiktive Daten“, jede Mail den Header `X-Demo-Hinweis`
- Keine Herstellerhandbücher, alle technischen Texte selbst geschrieben

## Lizenz

Code: MIT (siehe `LICENSE`). Demo-Daten und Texte in `docs/`: CC BY 4.0.

Zum Kanal: YouTube „Sinan Uçar | KI für Unternehmen“ · Beratung: [filandmuz.com](https://filandmuz.com)
