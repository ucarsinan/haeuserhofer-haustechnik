"""Häufige Vor- und Nachnamen für fiktive Personen.

Regel aus der Firmenbibel: nur häufige Namen, keine Prominenten, damit niemand
Bestimmtes gemeint ist. Firmennamen von Masse-Kunden entstehen nur aus einem
häufigen Nachnamen plus Gattungsbegriff (z. B. "Hausverwaltung Schneider").
"""

VORNAMEN_W = [
    "Anna", "Maria", "Sabine", "Monika", "Claudia", "Andrea", "Stefanie", "Katrin",
    "Nicole", "Susanne", "Birgit", "Sandra", "Melanie", "Christina", "Laura", "Sarah",
    "Lisa", "Julia", "Jana", "Elena", "Ayse", "Fatma", "Agnieszka", "Ewa", "Ingrid",
    "Ursula", "Renate", "Helga", "Karin", "Heike", "Martina", "Tanja", "Nina",
    "Sophie", "Marie", "Emma", "Hannah", "Mia", "Lena", "Carina",
]

VORNAMEN_M = [
    "Thomas", "Michael", "Andreas", "Stefan", "Christian", "Markus", "Frank", "Peter",
    "Jürgen", "Wolfgang", "Uwe", "Matthias", "Daniel", "Tobias", "Florian", "Sebastian",
    "Alexander", "Jan", "Tim", "Lukas", "Felix", "Max", "Paul", "Niklas", "Mehmet",
    "Ali", "Piotr", "Tomasz", "Dimitri", "Manfred", "Günter", "Dieter", "Horst",
    "Rainer", "Bernd", "Ralf", "Sven", "Dirk", "Kevin", "Marco",
]

NACHNAMEN = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
    "Schulz", "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf",
    "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger", "Hofmann",
    "Hartmann", "Lange", "Schmitt", "Werner", "Schmitz", "Krause", "Meier", "Lehmann",
    "Schmid", "Schulze", "Maier", "Köhler", "Herrmann", "König", "Walter", "Mayer",
    "Huber", "Kaiser", "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß", "Jung",
    "Hahn", "Schubert", "Vogel", "Friedrich", "Keller", "Günther", "Frank", "Berger",
    "Winkler", "Roth", "Beck", "Lorenz", "Baumann", "Franke", "Albrecht", "Yilmaz",
    "Kaya", "Öztürk", "Nowak", "Kowalski", "Popescu", "Ivanov",
]

# Erfundene, sehr allgemeine Straßennamen. Kombiniert mit PLZ 00xxx, die es in
# Deutschland nicht gibt (niedrigste echte PLZ: 01067).
STRASSEN = [
    "Lindenweg", "Ahornstraße", "Birkenallee", "Am Mühlbach", "Gartenstraße",
    "Bergstraße", "Wiesenweg", "Am Sonnenhang", "Schulstraße", "Kirchgasse",
    "Feldweg", "Rosenstraße", "Tulpenweg", "Am Weiher", "Eichenring",
    "Brunnenstraße", "Talweg", "Hauptstraße", "Am Bahnhof", "Ulmenstraße",
]

ORTE = [
    ("00110", "Musterstadt (fiktiv)"),
    ("00120", "Musterstadt-Nord (fiktiv)"),
    ("00130", "Beispieldorf (fiktiv)"),
    ("00140", "Demohausen (fiktiv)"),
    ("00150", "Testingen (fiktiv)"),
]

GATTUNG_WOHNUNG = ["Hausverwaltung", "Immobilienverwaltung", "Wohnbau", "Grundstücksverwaltung"]
GATTUNG_BETRIEB = ["Sanitär", "Heizungsbau", "Haustechnik", "Installationen", "Bäderbau"]
