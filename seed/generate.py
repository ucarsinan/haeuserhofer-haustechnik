#!/usr/bin/env python3
"""Erzeugt alle Demo-Daten der Häuserhofer Haustechnik GmbH.

Demo-Firma, fiktive Daten. Die Firma existiert nicht.

Die Daten sind deterministisch: gleicher --seed und gleicher --stichtag ergeben
byte-gleiche CSV-, E-Mail- und JSON-Dateien. Datumsangaben laufen relativ zum
Stichtag (Standard: heute), damit die Firma "bis zum Aufnahmetag" lebt.

Aufruf:
    python3 seed/generate.py --out data/generated [--seed 2026] [--stichtag 2026-11-21]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path

from fpdf import FPDF

import namen

ROOT = Path(__file__).resolve().parent
FIRMA = json.loads((ROOT / "firma.json").read_text(encoding="utf-8"))
DOMAIN = FIRMA["domain"]
MWST = 0.19
DEMO_HINWEIS = "DEMO-FIRMA, FIKTIVE DATEN - Die Häuserhofer Haustechnik GmbH existiert nicht."

ANZAHL_KUNDEN = 300
ANZAHL_MAILS = 200
ANZAHL_ANGEBOTE = 30
ANZAHL_RECHNUNGEN = 30
ANZAHL_WARTUNGSVERTRAEGE = 30


# --------------------------------------------------------------------------- #
# Hilfen
# --------------------------------------------------------------------------- #

def slug(text: str) -> str:
    table = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})
    out = text.translate(table).lower()
    return "".join(c if c.isalnum() else "-" for c in out).strip("-").replace("--", "-")


def eur(betrag: float) -> str:
    s = f"{betrag:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".") + " EUR"


def telefon(rng: random.Random) -> str:
    return f"0000 000000-{rng.randint(10, 99)}"


@dataclass
class Person:
    vorname: str
    nachname: str
    abteilung: str
    rolle: str
    jahrgang: int
    eintritt: int
    persona: bool = False

    @property
    def name(self) -> str:
        return f"{self.vorname} {self.nachname}"

    @property
    def email(self) -> str:
        return f"{slug(self.vorname)}.{slug(self.nachname)}@{DOMAIN}"


@dataclass
class Kunde:
    nr: str
    art: str  # privat | wohnungswirtschaft | betrieb
    name: str
    ansprechpartner: str
    strasse: str
    plz: str
    ort: str
    email: str
    telefon: str
    anlage: str
    baujahr_anlage: int
    wartungsvertrag: bool = False
    extra: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Stammdaten
# --------------------------------------------------------------------------- #

def erzeuge_mitarbeiter(rng: random.Random, stichtag: date) -> list[Person]:
    personen: list[Person] = []
    belegt = set()
    for p in FIRMA["personas"]:
        eintritt = {"Werner": 1987, "Julia": 2015, "Petra": 1998, "Murat": 2009,
                    "Klaus": 1985, "Jonas": 2021, "Lea": 2026}[p["vorname"]]
        personen.append(Person(p["vorname"], p["nachname"], p["abteilung"], p["rolle"],
                               p["jahrgang"], eintritt, persona=True))
        belegt.add((p["vorname"], p["nachname"]))

    for abt in FIRMA["abteilungen"]:
        vorhanden = sum(1 for x in personen if x.abteilung == abt["name"])
        rollen = abt.get("rollen", ["Mitarbeiter/in"])
        for _ in range(abt["anzahl"] - vorhanden):
            while True:
                weiblich = rng.random() < (0.55 if abt["name"] == "Büro" else 0.12)
                vorname = rng.choice(namen.VORNAMEN_W if weiblich else namen.VORNAMEN_M)
                nachname = rng.choice(namen.NACHNAMEN)
                if (vorname, nachname) not in belegt and nachname != "Häuserhofer":
                    belegt.add((vorname, nachname))
                    break
            rolle = rollen[-1] if len(rollen) > 1 else rollen[0]
            if abt["name"] == "Büro":
                rolle = [r for r in rollen if r not in {x.rolle for x in personen if x.abteilung == "Büro"}][0]
            if abt["name"] == "Azubis":
                jahrgang = rng.randint(stichtag.year - 20, stichtag.year - 16)
                eintritt = rng.randint(stichtag.year - 3, stichtag.year)
            else:
                jahrgang = rng.randint(1963, 2003)
                eintritt = rng.randint(max(1990, jahrgang + 18), stichtag.year)
            personen.append(Person(vorname, nachname, abt["name"], rolle, jahrgang, eintritt))
    if len(personen) != FIRMA["beschaeftigte"]:
        raise SystemExit(f"Mitarbeiterzahl {len(personen)} passt nicht zur Firmenbibel ({FIRMA['beschaeftigte']})")
    return personen


ANLAGEN = [
    ("Gas-Brennwerttherme", 2006, 2022),
    ("Öl-Niedertemperaturkessel", 1992, 2010),
    ("Luft-Wasser-Wärmepumpe", 2016, 2026),
    ("Sole-Wasser-Wärmepumpe", 2012, 2025),
    ("Pelletkessel", 2010, 2023),
    ("Gas-Brennwertkessel Kaskade", 2008, 2021),
    ("Lüftungsanlage mit Wärmerückgewinnung", 2014, 2025),
]


def erzeuge_kunden(rng: random.Random) -> list[Kunde]:
    kunden: list[Kunde] = []
    anz_privat = round(ANZAHL_KUNDEN * FIRMA["kundenmix"]["privat"])
    anz_wohnung = round(ANZAHL_KUNDEN * FIRMA["kundenmix"]["wohnungswirtschaft"])
    anz_betrieb = ANZAHL_KUNDEN - anz_privat - anz_wohnung
    benutzt: set[str] = set()

    def eindeutig(basis: str) -> str:
        name, i = basis, 2
        while name in benutzt:
            name = f"{basis} {i}"
            i += 1
        benutzt.add(name)
        return name

    def adresse() -> tuple[str, str, str]:
        plz, ort = rng.choice(namen.ORTE)
        return f"{rng.choice(namen.STRASSEN)} {rng.randint(1, 120)}", plz, ort

    def anlage(art: str) -> tuple[str, int]:
        pool = ANLAGEN if art != "privat" else [a for a in ANLAGEN if "Kaskade" not in a[0]]
        typ, von, bis = rng.choice(pool)
        return typ, rng.randint(von, bis)

    nr = 10001
    for art, anzahl in (("privat", anz_privat), ("wohnungswirtschaft", anz_wohnung), ("betrieb", anz_betrieb)):
        for _ in range(anzahl):
            vorname = rng.choice(namen.VORNAMEN_W + namen.VORNAMEN_M)
            nachname = rng.choice(namen.NACHNAMEN)
            strasse, plz, ort = adresse()
            typ, baujahr = anlage(art)
            if art == "privat":
                name = eindeutig(f"{vorname} {nachname}")
                mail = f"{slug(name)}@privat.example"
                ansprech = name
            else:
                gattung = rng.choice(namen.GATTUNG_WOHNUNG if art == "wohnungswirtschaft" else namen.GATTUNG_BETRIEB)
                name = eindeutig(f"{gattung} {rng.choice(namen.NACHNAMEN)}")
                mail = f"{slug(vorname)}.{slug(nachname)}@{slug(name)}.example"
                ansprech = f"{vorname} {nachname}"
            kunden.append(Kunde(f"K{nr}", art, name, ansprech, strasse, plz, ort, mail,
                                telefon(rng), typ, baujahr))
            nr += 1
    rng.shuffle(kunden)
    return kunden


PREISLISTE = [
    # artikelnr, bezeichnung, einheit, netto
    ("WP-LW-08", "Luft-Wasser-Wärmepumpe 8 kW, Außenaufstellung, herstellerneutral", "Stk", 11800.00),
    ("WP-LW-12", "Luft-Wasser-Wärmepumpe 12 kW, Außenaufstellung, herstellerneutral", "Stk", 14900.00),
    ("WP-PAK-H1", "Häuserhofer Hydraulik-Paket H1 (vormontiert, bis 10 kW)", "Stk", 3450.00),
    ("WP-PAK-H2", "Häuserhofer Hydraulik-Paket H2 (vormontiert, bis 16 kW)", "Stk", 4290.00),
    ("SP-300", "Warmwasserspeicher 300 l für Wärmepumpe", "Stk", 1980.00),
    ("PS-200", "Pufferspeicher 200 l", "Stk", 1240.00),
    ("GBT-24", "Gas-Brennwerttherme 24 kW inkl. Regelung", "Stk", 4380.00),
    ("HK-FBH-M2", "Fußbodenheizung Nasssystem inkl. Verteiler", "m2", 62.50),
    ("HK-TAUSCH", "Heizkörpertausch inkl. Ventil und Thermostatkopf", "Stk", 640.00),
    ("HYD-ABGL", "Hydraulischer Abgleich nach Verfahren B (Einfamilienhaus)", "psch", 890.00),
    ("DEM-OEL", "Demontage und Entsorgung Ölkessel inkl. Tankreinigung", "psch", 1650.00),
    ("BAD-KOMP", "Badsanierung Komplettpaket Standard (ohne Fliesen)", "psch", 14800.00),
    ("LUE-KWL", "Kontrollierte Wohnraumlüftung zentral, Einfamilienhaus", "psch", 9600.00),
    ("WART-GAS", "Jahreswartung Gas-Brennwertgerät", "psch", 189.00),
    ("WART-WP", "Jahreswartung Wärmepumpe inkl. Dichtheitsprüfung", "psch", 249.00),
    ("WART-OEL", "Jahreswartung Ölheizung inkl. Abgasmessung", "psch", 219.00),
    ("MON-STD", "Monteurstunde", "Std", 72.00),
    ("SERV-STD", "Servicetechniker-Stunde", "Std", 79.00),
    ("NOT-ZUS", "Notdienstzuschlag Wochenende/Feiertag", "psch", 120.00),
    ("ANF-PAU", "Anfahrtspauschale bis 40 km", "psch", 45.00),
]


def schreibe_csv(pfad: Path, kopf: list[str], zeilen: list[list]) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(kopf)
        w.writerows(zeilen)


# --------------------------------------------------------------------------- #
# PDFs
# --------------------------------------------------------------------------- #

class DemoPDF(FPDF):
    def header(self) -> None:
        self.set_fill_color(255, 236, 153)
        self.set_font("Helvetica", "B", 8)
        self.cell(0, 6, DEMO_HINWEIS, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 7, FIRMA["name"], new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        a = FIRMA["adresse"]
        self.cell(0, 4, f"{a['strasse']} · {a['plz']} {a['ort']} · Tel. {FIRMA['telefon']} · info@{DOMAIN}",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-18)
        self.set_font("Helvetica", "", 7)
        self.multi_cell(0, 3.5,
                        f"Geschäftsführer: {FIRMA['geschaeftsfuehrer']} · USt-IdNr. {FIRMA['ust_id']} (Demo) · "
                        f"IBAN {FIRMA['iban']} (absichtlich ungültig)\n{DEMO_HINWEIS} · Seite {self.page_no()}",
                        align="C")


def pdf_beleg(pfad: Path, titel: str, nummer: str, datum: date, kunde: Kunde,
              positionen: list[tuple[str, str, float, str, float]], text_oben: str, text_unten: str) -> float:
    pdf = DemoPDF(format="A4")
    pdf.set_creation_date(datetime.combine(datum, time(9, 0), tzinfo=timezone.utc))
    pdf.set_title(f"{titel} {nummer} (Demo)")
    pdf.set_author(FIRMA["name"] + " (fiktiv)")
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(90, 5, f"{kunde.name}\n{'z. Hd. ' + kunde.ansprechpartner if kunde.art != 'privat' else ''}\n"
                          f"{kunde.strasse}\n{kunde.plz} {kunde.ort}".replace("\n\n", "\n"))
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, f"{titel} {nummer}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Datum: {datum:%d.%m.%Y} · Kundennummer: {kunde.nr}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, text_oben)
    pdf.ln(3)

    breiten = (20, 78, 14, 12, 32, 0)
    pdf.set_font("Helvetica", "B", 9)
    for b, t in zip(breiten, ("Art.-Nr.", "Bezeichnung", "Menge", "Einh.", "Einzel", "Gesamt")):
        pdf.cell(b if b else 0, 6, t, border="B", new_x="RIGHT", new_y="TOP")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 9)
    netto = 0.0
    for art, bez, menge, einheit, preis in positionen:
        gesamt = round(menge * preis, 2)
        netto += gesamt
        zeilen = pdf.multi_cell(breiten[1], 5, bez, dry_run=True, output="LINES")
        hoehe = 5 * max(1, len(zeilen))
        y0 = pdf.get_y()
        x0 = pdf.get_x()
        pdf.cell(breiten[0], 5, art)
        pdf.multi_cell(breiten[1], 5, bez, new_x="RIGHT", new_y="TOP")
        pdf.set_xy(x0 + breiten[0] + breiten[1], y0)
        pdf.cell(breiten[2], 5, f"{menge:g}".replace(".", ","), align="R")
        pdf.cell(breiten[3], 5, einheit, align="C")
        pdf.cell(breiten[4], 5, eur(preis), align="R")
        pdf.cell(0, 5, eur(gesamt), align="R")
        pdf.set_xy(x0, y0 + hoehe + 1)
    netto = round(netto, 2)
    mwst = round(netto * MWST, 2)
    brutto = round(netto + mwst, 2)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    for label, wert, fett in (("Summe netto", netto, False), ("zzgl. 19 % MwSt.", mwst, False),
                              ("Gesamtbetrag", brutto, True)):
        pdf.set_font("Helvetica", "B" if fett else "", 10)
        pdf.cell(150, 6, label, align="R")
        pdf.cell(0, 6, eur(wert), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, text_unten)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(pfad))
    return brutto


def pdf_wartungsvertrag(pfad: Path, nummer: str, beginn: date, kunde: Kunde, artikel: tuple) -> None:
    pdf = DemoPDF(format="A4")
    pdf.set_creation_date(datetime.combine(beginn, time(9, 0), tzinfo=timezone.utc))
    pdf.set_title(f"Wartungsvertrag {nummer} (Demo)")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, f"Wartungsvertrag {nummer}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    ende_kuendigung = "3 Monate zum Ende des Vertragsjahres"
    abschnitte = [
        ("Vertragspartner", f"{FIRMA['name']} (Auftragnehmer) und {kunde.name}, {kunde.strasse}, "
                            f"{kunde.plz} {kunde.ort}, Kundennummer {kunde.nr} (Auftraggeber)."),
        ("Anlage", f"{kunde.anlage}, Baujahr {kunde.baujahr_anlage}, Standort wie oben."),
        ("Leistung", f"Einmal jährlich Wartung nach Herstellervorgaben ({artikel[1]}). Dazu Sichtprüfung, "
                     "Reinigung, Funktionsprüfung, Einstellung der Regelung und ein schriftlicher Wartungsbericht. "
                     "Verschleißteile und Reparaturen werden gesondert nach Preisliste berechnet."),
        ("Termin", "Der Kundendienst schlägt den Termin vor. Wartungen für Heizungen finden bevorzugt zwischen "
                   "April und September statt."),
        ("Preis", f"{eur(artikel[3])} netto pro Wartung, zzgl. 19 % MwSt. Anfahrt ist enthalten. "
                  "Preisanpassung höchstens einmal jährlich mit 6 Wochen Vorankündigung."),
        ("Vorteile", "Bevorzugte Terminvergabe im Störungsfall. 10 % Rabatt auf Ersatzteile. "
                     "Kein Notdienstzuschlag an Werktagen."),
        ("Laufzeit", f"Beginn {beginn:%d.%m.%Y}, Laufzeit 1 Jahr, verlängert sich automatisch um je 1 Jahr. "
                     f"Kündigung mit {ende_kuendigung}."),
    ]
    for titel, text in abschnitte:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, titel, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, text)
    pdf.ln(8)
    pdf.cell(90, 5, "______________________________")
    pdf.cell(0, 5, "______________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 5, f"{FIRMA['name']}")
    pdf.cell(0, 5, kunde.name, new_x="LMARGIN", new_y="NEXT")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(pfad))


def positionen_fuer_angebot(rng: random.Random, kunde: Kunde) -> tuple[str, list]:
    p = {a[0]: a for a in PREISLISTE}

    def pos(nr: str, menge: float) -> tuple:
        a = p[nr]
        return (a[0], a[1], menge, a[2], a[3])

    vorhaben = rng.choice(["wp", "wp", "heizkoerper", "bad", "gas", "lueftung"])
    if vorhaben == "wp":
        gross = rng.random() < 0.4 or kunde.art != "privat"
        pos_ = [pos("WP-LW-12" if gross else "WP-LW-08", 1), pos("WP-PAK-H2" if gross else "WP-PAK-H1", 1),
                pos("SP-300", 1), pos("HYD-ABGL", 1), pos("MON-STD", rng.choice([24, 28, 32, 36]))]
        if "Öl" in kunde.anlage:
            pos_.insert(0, pos("DEM-OEL", 1))
        return "Umstellung auf Luft-Wasser-Wärmepumpe", pos_
    if vorhaben == "heizkoerper":
        n = rng.randint(3, 9)
        return "Heizkörpertausch", [pos("HK-TAUSCH", n), pos("HYD-ABGL", 1), pos("MON-STD", n * 2)]
    if vorhaben == "bad":
        return "Badsanierung", [pos("BAD-KOMP", 1), pos("MON-STD", rng.choice([8, 12, 16]))]
    if vorhaben == "gas":
        return "Austausch Gas-Brennwerttherme", [pos("GBT-24", 1), pos("MON-STD", rng.choice([10, 12, 14])),
                                                 pos("ANF-PAU", 1)]
    return "Kontrollierte Wohnraumlüftung", [pos("LUE-KWL", 1), pos("MON-STD", rng.choice([16, 20, 24]))]


# --------------------------------------------------------------------------- #
# E-Mails
# --------------------------------------------------------------------------- #

def mail_vorlagen(rng: random.Random, kunde: Kunde, stichtag: date) -> tuple[str, str, str, str]:
    """Gibt (kategorie, postfach, betreff, text) zurück."""
    anrede = "Sehr geehrte Damen und Herren"
    gruss = f"Viele Grüße\n{kunde.ansprechpartner}"
    if kunde.art != "privat":
        gruss += f"\n{kunde.name}"
    gruss += f"\nTel. {kunde.telefon}"
    a = kunde.anlage
    bj = kunde.baujahr_anlage
    kategorien = [
        ("anfrage_waermepumpe", 22), ("stoerung", 20), ("wartungstermin", 16), ("angebot_nachfrage", 10),
        ("rechnung_frage", 8), ("beschwerde", 6), ("ersatzteil", 7), ("foerderung", 5),
        ("sammelauftrag", 4), ("spam", 2),
    ]
    if kunde.art == "betrieb":
        kategorien = [("ersatzteil", 50), ("waermepumpen_paket", 35), ("rechnung_frage", 15)]
    elif kunde.art == "wohnungswirtschaft":
        kategorien = [("sammelauftrag", 30), ("stoerung", 30), ("wartungstermin", 20),
                      ("rechnung_frage", 10), ("beschwerde", 10)]
    kat = rng.choices([k for k, _ in kategorien], weights=[w for _, w in kategorien])[0]

    if kat == "anfrage_waermepumpe":
        flaeche = rng.choice([110, 130, 145, 160, 185, 210])
        return kat, "info", rng.choice([
            "Anfrage Wärmepumpe Einfamilienhaus", "Wärmepumpe statt alter Heizung?", "Angebot Wärmepumpe gewünscht"]), (
            f"{anrede},\n\nwir haben eine {a} von {bj} und überlegen, auf eine Wärmepumpe umzusteigen. "
            f"Unser Haus hat ca. {flaeche} m² Wohnfläche, Baujahr {rng.choice([1968, 1975, 1984, 1993, 2001])}, "
            f"{rng.choice(['überwiegend Heizkörper', 'teilweise Fußbodenheizung', 'nur Heizkörper, teils alt'])}.\n\n"
            "Lohnt sich das bei uns? Könnten Sie zu einer Besichtigung kommen und uns ein Angebot machen? "
            f"Am besten passt uns {rng.choice(['vormittags', 'nachmittags ab 15 Uhr', 'ein Samstag', 'jeder Tag nach 17 Uhr'])}.\n\n{gruss}")
    if kat == "stoerung":
        fehler_pool = [
            ("Heizung geht nicht mehr", "Die Heizung ist seit heute früh aus und zeigt eine Störung an. Wir haben kein Warmwasser."),
            ("Störung Heizung, Fehlercode", f"Am Display steht Fehler F{rng.randint(10, 99)}. Neustart hat nichts gebracht."),
            ("Heizkörper werden nicht warm", "In zwei Zimmern bleiben die Heizkörper kalt, der Rest geht."),
        ]
        if "Wärmepumpe" in a:
            fehler_pool.append(("Wärmepumpe sehr laut", "Die Außeneinheit brummt seit ein paar Tagen deutlich lauter, besonders nachts."))
        elif "Lüftung" in a:
            fehler_pool = [("Lüftung pfeift", "Die Lüftungsanlage pfeift seit gestern, und im Bad riecht es muffig."),
                           ("Lüftung Filterwechsel-Anzeige", "Die Anzeige für den Filterwechsel blinkt, obwohl die Filter neu sind.")]
        else:
            fehler_pool.append(("Wasser unter der Heizung", "Unter dem Kessel bildet sich eine kleine Pfütze. Druck ist auf 0,8 bar gefallen."))
        fehler = rng.choice(fehler_pool)
        dringend = rng.random() < 0.35
        return kat, "service", ("DRINGEND: " if dringend else "") + fehler[0], (
            f"Hallo,\n\n{fehler[1]} Anlage: {a}, Baujahr {bj}. Kundennummer {kunde.nr}.\n\n"
            + ("Wir haben kleine Kinder im Haus, bitte so schnell wie möglich!\n\n" if dringend and kunde.art == "privat" else "")
            + (f"Betroffen ist das Objekt {kunde.strasse}, {rng.randint(6, 24)} Wohneinheiten.\n\n" if kunde.art == "wohnungswirtschaft" else "")
            + f"Wann kann jemand vorbeikommen?\n\n{gruss}")
    if kat == "wartungstermin":
        return kat, "service", rng.choice(["Wartungstermin verschieben", "Termin für Wartung", "Jahreswartung"]), (
            f"Guten Tag,\n\nwir haben einen Wartungsvertrag für unsere {a}. "
            + rng.choice([
                "Der vorgeschlagene Termin passt uns leider nicht. Geht auch die Woche danach?",
                "Dieses Jahr war noch niemand da. Können wir einen Termin ausmachen?",
                "Bitte bestätigen Sie den Termin noch einmal schriftlich.",
            ]) + f"\n\nKundennummer: {kunde.nr}\n\n{gruss}")
    if kat == "angebot_nachfrage":
        return kat, "angebote", "Nachfrage zu Ihrem Angebot", (
            f"{anrede},\n\nwir warten noch auf das Angebot nach Ihrer Besichtigung vor "
            f"{rng.choice(['zwei', 'drei', 'vier'])} Wochen. Gibt es schon einen Stand? "
            "Wir würden gern bald entscheiden, weil wir noch ein zweites Angebot vorliegen haben.\n\n" + gruss)
    if kat == "rechnung_frage":
        return kat, "rechnung", rng.choice(["Frage zur Rechnung", "Rechnung unklar", "Rechnung doppelt erhalten?"]), (
            f"{anrede},\n\nzu Ihrer Rechnung RE-{rng.randint(2025, 2026)}-{rng.randint(1, 999):04d} habe ich eine Frage: "
            + rng.choice([
                "Es sind 6 Monteurstunden berechnet, Ihr Monteur war aber nur ca. 4 Stunden da.",
                "Die Anfahrtspauschale wurde berechnet, obwohl wir einen Wartungsvertrag haben.",
                "Ich habe die Rechnung zweimal bekommen. Muss ich beide bezahlen?",
                "Bitte schicken Sie uns die Rechnung als E-Rechnung (XRechnung).",
            ]) + f"\n\n{gruss}")
    if kat == "beschwerde":
        return kat, "info", rng.choice(["Beschwerde", "Sehr unzufrieden", "Termin nicht eingehalten"]), (
            f"{anrede},\n\n"
            + rng.choice([
                "gestern war ein Termin zwischen 8 und 12 Uhr vereinbart. Es kam niemand, und angerufen hat auch keiner. "
                "Ich habe mir dafür extra freigenommen.",
                "nach der Reparatur letzte Woche tritt derselbe Fehler wieder auf. Ich erwarte, dass das ohne weitere Kosten behoben wird.",
                "Ihr Monteur hat beim Einsatz den Flur nicht abgedeckt, jetzt sind Flecken auf dem Teppich.",
            ]) + f"\n\nKundennummer {kunde.nr}\n\n{gruss}")
    if kat == "ersatzteil":
        return kat, "einkauf" if kunde.art == "betrieb" else "info", "Ersatzteilbestellung", (
            f"Hallo,\n\nwir brauchen für eine {a} (Baujahr {bj}) folgende Teile:\n"
            + "\n".join(f"- {rng.randint(1, 4)} x {t}" for t in rng.sample(
                ["Zündelektrode", "Ausdehnungsgefäß 18 l", "Umwälzpumpe", "Sicherheitsventil 3 bar",
                 "Dichtungssatz Wärmetauscher", "Außenfühler", "Dreiwegeventil", "Strömungsschalter"], 2))
            + f"\n\nBitte mit Preis und Liefertermin. Abholung oder Lieferung, je nachdem was schneller geht.\n\n{gruss}")
    if kat == "waermepumpen_paket":
        anzahl = rng.choice([2, 3, 4, 6])
        typ = rng.choice(["H1", "H2"])
        return kat, "angebote", f"Bestellung Hydraulik-Paket {typ}", (
            f"Hallo zusammen,\n\nwir möchten {anzahl} Stück Hydraulik-Paket {typ} bestellen. "
            f"Liefertermin wäre ideal in KW {rng.randint(1, 52)}. Gilt noch der Staffelpreis vom letzten Mal?\n\n{gruss}")
    if kat == "foerderung":
        return kat, "info", "Förderung Wärmepumpe", (
            f"{anrede},\n\nwelche Förderung gibt es aktuell für eine Wärmepumpe, und kümmern Sie sich um den Antrag? "
            f"Wir haben eine {a} von {bj}.\n\n{gruss}")
    if kat == "sammelauftrag":
        n = rng.randint(4, 18)
        return kat, "service", f"Wartung {n} Objekte {stichtag.year + 1}", (
            f"{anrede},\n\nfür {n} unserer Objekte brauchen wir die Jahreswartung für {stichtag.year + 1}. "
            "Die Liste der Adressen hängen wir in der nächsten Mail an. Bitte schicken Sie uns einen Terminplan "
            "und ein Angebot auf Basis unseres Rahmenvertrags.\n\n" + gruss)
    # spam
    return "spam", "info", rng.choice(["Ihre Website auf Platz 1 bei Google", "Rechnung offen - bitte sofort zahlen",
                                       "Kooperationsanfrage"]), (
        "Sehr geehrter Geschäftsführer,\n\nwir bringen Ihre Firma garantiert auf Platz 1. "
        "Klicken Sie jetzt auf den Link, um Ihr Angebot zu sichern.\n\nMit freundlichen Grüßen\nOnline-Marketing-Team")


def erzeuge_mails(rng: random.Random, kunden: list[Kunde], stichtag: date,
                  out: Path) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for i in range(ANZAHL_MAILS):
        kunde = rng.choice(kunden)
        kat, postfach, betreff, text = mail_vorlagen(rng, kunde, stichtag)
        tage_zurueck = int(rng.triangular(0, 30, 0))
        while True:
            tag = stichtag - timedelta(days=tage_zurueck)
            if tag.weekday() < 6 or kat == "stoerung":
                break
            tage_zurueck += 1
        zeit = datetime.combine(tag, time(rng.randint(6, 21), rng.randint(0, 59)), tzinfo=timezone.utc)
        msg = EmailMessage()
        if kat == "spam":
            msg["From"] = f"Online Marketing <noreply@werbung-{rng.randint(100, 999)}.example>"
        else:
            msg["From"] = f"{kunde.ansprechpartner} <{kunde.email}>"
        msg["To"] = f"{FIRMA['kurz']} {postfach.capitalize()} <{postfach}@{DOMAIN}>"
        msg["Subject"] = betreff
        msg["Date"] = format_datetime(zeit)
        msg["Message-ID"] = f"<demo-{stichtag:%Y%m%d}-{i + 1:04d}@{DOMAIN}>"
        msg["X-Demo-Hinweis"] = "Demo-Firma, fiktive Daten"
        msg["X-Demo-Kategorie"] = kat
        msg["X-Demo-Kundennummer"] = kunde.nr if kat != "spam" else "-"
        msg.set_content(text + "\n")
        name = f"{i + 1:04d}-{kat}.eml"
        (out / name).write_bytes(bytes(msg))
        index.append({"datei": name, "kategorie": kat, "postfach": postfach, "betreff": betreff,
                      "kunde": kunde.nr if kat != "spam" else None, "datum": zeit.isoformat()})
    return index


# --------------------------------------------------------------------------- #
# Hauptprogramm
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("data/generated"))
    ap.add_argument("--seed", type=int, default=2026, help="Zufallsstartwert (Standard: Geschäftsjahr)")
    ap.add_argument("--stichtag", type=date.fromisoformat, default=date.today(),
                    help="Bis zu diesem Tag laufen die Daten (YYYY-MM-DD, Standard: heute)")
    args = ap.parse_args()

    out: Path = args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rng = random.Random(args.seed)
    stichtag: date = args.stichtag

    mitarbeiter = erzeuge_mitarbeiter(rng, stichtag)
    schreibe_csv(out / "tabellen" / "mitarbeiter.csv",
                 ["vorname", "nachname", "abteilung", "rolle", "jahrgang", "eintritt", "email", "durchwahl"],
                 [[p.vorname, p.nachname, p.abteilung, p.rolle, p.jahrgang, p.eintritt, p.email, f"-{i + 1:02d}"]
                  for i, p in enumerate(mitarbeiter)])

    kunden = erzeuge_kunden(rng)
    vertragskunden = rng.sample([k for k in kunden if k.art != "betrieb"], ANZAHL_WARTUNGSVERTRAEGE)
    for k in vertragskunden:
        k.wartungsvertrag = True

    schreibe_csv(out / "tabellen" / "preisliste.csv", ["artikelnr", "bezeichnung", "einheit", "netto_eur"],
                 [[a, b, e, f"{p:.2f}"] for a, b, e, p in PREISLISTE])

    # Wartungsverträge
    wart = {"Wärmepumpe": "WART-WP", "Öl": "WART-OEL"}
    vertraege = []
    for i, k in enumerate(sorted(vertragskunden, key=lambda x: x.nr)):
        art_nr = next((v for key, v in wart.items() if key in k.anlage), "WART-GAS")
        artikel = next(a for a in PREISLISTE if a[0] == art_nr)
        beginn = date(rng.randint(2012, stichtag.year - 1), rng.choice([1, 4, 7, 10]), 1)
        nummer = f"WV-{beginn.year}-{i + 1:03d}"
        pdf_wartungsvertrag(out / "dokumente" / "wartungsvertraege" / f"{nummer}.pdf", nummer, beginn, k, artikel)
        vertraege.append([nummer, k.nr, k.name, k.anlage, k.baujahr_anlage, beginn.isoformat(), art_nr,
                          f"{artikel[3]:.2f}"])
    schreibe_csv(out / "tabellen" / "wartungsvertraege.csv",
                 ["vertragsnr", "kundennr", "kunde", "anlage", "baujahr", "beginn", "leistung", "netto_eur"], vertraege)

    schreibe_csv(out / "tabellen" / "kunden.csv",
                 ["kundennr", "art", "name", "ansprechpartner", "strasse", "plz", "ort", "email", "telefon",
                  "anlage", "baujahr_anlage", "wartungsvertrag"],
                 [[k.nr, k.art, k.name, k.ansprechpartner, k.strasse, k.plz, k.ort, k.email, k.telefon, k.anlage,
                   k.baujahr_anlage, "ja" if k.wartungsvertrag else "nein"] for k in sorted(kunden, key=lambda x: x.nr)])

    # Angebote und Rechnungen
    belege = []
    p = {a[0]: a for a in PREISLISTE}
    for i in range(ANZAHL_ANGEBOTE):
        k = rng.choice([x for x in kunden if x.art != "betrieb"])
        datum = stichtag - timedelta(days=rng.randint(1, 90))
        nummer = f"AN-{datum.year}-{i + 1:04d}"
        vorhaben, pos = positionen_fuer_angebot(rng, k)
        brutto = pdf_beleg(out / "dokumente" / "angebote" / f"{nummer}.pdf", "Angebot", nummer, datum, k, pos,
                           f"Vielen Dank für Ihre Anfrage. Gern bieten wir Ihnen folgende Leistungen an: {vorhaben}.",
                           "Dieses Angebot gilt 30 Tage. Zahlung: 30 % bei Auftrag, 60 % bei Lieferung, 10 % nach "
                           "Abnahme. Ihr Ansprechpartner: Julia Häuserhofer, Tel. 0000 000000-02.")
        belege.append([nummer, "angebot", datum.isoformat(), k.nr, k.name, vorhaben, f"{brutto:.2f}"])
    for i in range(ANZAHL_RECHNUNGEN):
        k = rng.choice(kunden)
        datum = stichtag - timedelta(days=rng.randint(1, 60))
        nummer = f"RE-{datum.year}-{i + 1:04d}"
        if k.art == "betrieb":
            typ = rng.choice(["WP-PAK-H1", "WP-PAK-H2"])
            pos = [(typ, p[typ][1], rng.choice([2, 3, 4]), p[typ][2], p[typ][3])]
            vorhaben = "Lieferung Hydraulik-Pakete"
        else:
            wartung = "WART-WP" if "Wärmepumpe" in k.anlage else ("WART-OEL" if "Öl" in k.anlage else "WART-GAS")
            pos = [(wartung, p[wartung][1], 1, p[wartung][2], p[wartung][3])]
            if rng.random() < 0.5:
                pos.append(("SERV-STD", p["SERV-STD"][1], rng.choice([0.5, 1, 1.5, 2]), "Std", p["SERV-STD"][3]))
            if not k.wartungsvertrag:
                pos.append(("ANF-PAU", p["ANF-PAU"][1], 1, "psch", p["ANF-PAU"][3]))
            vorhaben = "Wartung"
        brutto = pdf_beleg(out / "dokumente" / "rechnungen" / f"{nummer}.pdf", "Rechnung", nummer, datum, k, pos,
                           f"Für unsere Leistungen ({vorhaben}) berechnen wir Ihnen:",
                           f"Zahlbar innerhalb von 14 Tagen ohne Abzug bis {datum + timedelta(days=14):%d.%m.%Y}. "
                           f"Bankverbindung: IBAN {FIRMA['iban']} (Demo, absichtlich ungültig).")
        belege.append([nummer, "rechnung", datum.isoformat(), k.nr, k.name, vorhaben, f"{brutto:.2f}"])
    schreibe_csv(out / "tabellen" / "belege.csv",
                 ["nummer", "typ", "datum", "kundennr", "kunde", "vorhaben", "brutto_eur"], belege)

    # E-Mails
    mails = erzeuge_mails(rng, kunden, stichtag, out / "mails")

    # Interne Dokumente
    docs_ziel = out / "wissen"
    docs_ziel.mkdir(parents=True)
    for md in sorted((ROOT.parent / "docs").glob("*.md")):
        shutil.copy2(md, docs_ziel / md.name)

    manifest = {
        "hinweis": "Demo-Firma, fiktive Daten",
        "firma": FIRMA["name"],
        "seed": args.seed,
        "stichtag": stichtag.isoformat(),
        "anzahl": {
            "mitarbeiter": len(mitarbeiter),
            "kunden": len(kunden),
            "wartungsvertraege": len(vertraege),
            "angebote": ANZAHL_ANGEBOTE,
            "rechnungen": ANZAHL_RECHNUNGEN,
            "mails": len(mails),
            "wissen": len(list(docs_ziel.glob("*.md"))),
        },
        "mails_nach_kategorie": {k: sum(1 for m in mails if m["kategorie"] == k)
                                 for k in sorted({m["kategorie"] for m in mails})},
        "mails": mails,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Demo-Daten erzeugt in {out} (Seed {args.seed}, Stichtag {stichtag:%d.%m.%Y}):")
    for k, v in manifest["anzahl"].items():
        print(f"  {k:<18} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
