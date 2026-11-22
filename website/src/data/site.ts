// All facts come from kanal/demo-firma/firmenbibel.md (v0.4.2). Nothing here may contradict it.

export const site = {
  name: 'Häuserhofer Haustechnik GmbH',
  short: 'Häuserhofer',
  titleSuffix: 'Häuserhofer Haustechnik (Demo)',
  channelUrl: 'https://www.youtube.com/@SinanUcarKI',
  channelName: 'Sinan Uçar | KI für Unternehmen',
  operatorUrl: 'https://filandmuz.com',
  imprintUrl: 'https://filandmuz.com/impressum',
  privacyUrl: 'https://filandmuz.com/datenschutz',
};

export const nav = [
  { href: '/', label: 'Start' },
  { href: '/leistungen/', label: 'Leistungen' },
  { href: '/fuer-betriebe/', label: 'Für Betriebe' },
  { href: '/ueber-uns/', label: 'Über uns' },
  { href: '/team/', label: 'Team' },
  { href: '/so-arbeiten-wir/', label: 'So arbeiten wir' },
  { href: '/ki-weg/', label: 'KI-Weg' },
  { href: '/kontakt/', label: 'Kontakt' },
];

export const stats = [
  { label: 'GEGRÜNDET', value: '1987' },
  { label: 'BESCHÄFTIGTE', value: '46' },
  { label: 'WARTUNGSVERTRÄGE', value: '1.900' },
  { label: 'EINSATZGEBIET', value: '40 km' },
];

export type IconName = 'flame' | 'wind' | 'bath' | 'wrench' | 'siren' | 'package' | 'box' | 'truck' | 'check' | 'map' | 'users' | 'award';

export const services: {
  id: string; icon: IconName; label: string; title: string; short: string; text: string; points: string[];
  photo: { alt: string; caption: string };
}[] = [
  {
    id: 'heizung', icon: 'flame', label: 'Heizung und Wärmepumpe', title: 'Neue Heizung, sauber geplant',
    short: 'Heizungstausch und Luft-Wasser-Wärmepumpen für Bestand und Neubau.',
    text: 'Der größte Teil unserer Arbeit. Wir tauschen alte Öl- und Gasheizungen, bauen Wärmepumpen ein und planen die Anlage passend zum Haus. Die Hydraulik dafür montieren wir in der eigenen Werkstatt vor.',
    points: ['Vor-Ort-Termin mit Aufmaß', 'Wärmepumpen für Bestand und Neubau', 'Hydraulik vormontiert und auf dem Prüfstand getestet', 'Montage durch eingespielte Zweier-Teams'],
    photo: { alt: 'Platzhalter Foto: Monteur schließt eine Luft-Wasser-Wärmepumpe im Heizraum eines Einfamilienhauses an, KI-generiert', caption: 'Wärmepumpen-Einbau im Bestand' },
  },
  {
    id: 'lueftung', icon: 'wind', label: 'Lüftung', title: 'Frische Luft ohne offenes Fenster',
    short: 'Lüftungsanlagen für Neubau und Sanierung.',
    text: 'Gut gedämmte Häuser brauchen einen geregelten Luftaustausch. Wir planen und bauen Lüftungsanlagen und warten sie danach.',
    points: ['Planung und Einbau', 'Neubau und Sanierung', 'Wartung durch unseren Kundendienst'],
    photo: { alt: 'Platzhalter Foto: Lüftungsgerät mit Rohren im Technikraum, ohne Personen, KI-generiert', caption: 'Lüftungsgerät im Technikraum' },
  },
  {
    id: 'bad', icon: 'bath', label: 'Bad', title: 'Ein Bad aus einer Hand',
    short: 'Badsanierung und Neubau-Installation, mit kleiner Ausstellung im Haus.',
    text: 'Wir sanieren Bäder im Bestand und installieren im Neubau. In unserem Besprechungsraum steht eine kleine Bad-Ausstellung.',
    points: ['Badsanierung im Bestand', 'Neubau-Installation', 'Kleine Ausstellung im Besprechungsraum'],
    photo: { alt: 'Platzhalter Foto: fertig saniertes Bad mit bodengleicher Dusche, ohne Personen, KI-generiert', caption: 'Badsanierung' },
  },
  {
    id: 'kundendienst', icon: 'wrench', label: 'Kundendienst und Wartung', title: 'Damit die Anlage läuft',
    short: 'Rund 1.900 Wartungsverträge, Störungsdienst und Notdienst im Winter.',
    text: 'Zehn Servicetechniker kümmern sich um Wartung und Störungen. Wir melden uns, wenn die Wartung fällig ist. Jeder Servicewagen hat Abgasmessgerät, Druckprüfung und Kältemittel-Ausrüstung für Wärmepumpen dabei.',
    points: ['Rund 1.900 Wartungsverträge', 'Erinnerung, wenn die Wartung fällig ist', 'Wartungsprotokoll zu jedem Termin', '10 Servicetechniker'],
    photo: { alt: 'Platzhalter Foto: Servicetechniker misst an einem Gaskessel die Abgaswerte, KI-generiert', caption: 'Wartung mit Abgasmessung' },
  },
];

export const emergency = {
  label: 'Notdienst', title: 'Heizung aus im Winter?',
  text: 'Von Oktober bis April haben wir einen Notdienst außerhalb der Geschäftszeiten.',
};

export const history = [
  { year: '1987', text: 'Werner Häuserhofer gründet mit 26 Jahren als frischer Meister, allein, in der Garage seiner Eltern.' },
  { year: '1995', text: 'Umzug ins Gewerbegebiet am Ortsrand: eigene Halle und kleines Bürogebäude. 9 Beschäftigte.' },
  { year: '2004', text: 'Umwandlung in die Häuserhofer Haustechnik GmbH.' },
  { year: '2009', text: 'Der Kundendienst wird eine eigene Abteilung mit Wartungsverträgen.' },
  { year: '2015', text: 'Julia Häuserhofer steigt ein, nach vier Jahren bei einem Heizungsgroßhändler.' },
  { year: '2018', text: 'Start der Werkstatt für vormontierte Wärmepumpen-Pakete.' },
  { year: '2026', text: '46 Beschäftigte, davon 4 Auszubildende. Die zweite Generation steht bereit.' },
];

export type Person = {
  slug: string; name: string; role: string; since: string; text: string; photoAlt: string;
  /** Generated portrait under public/images/; without it the slot shows a placeholder. */
  photo?: string;
};

export const people: Person[] = [
  { slug: 'werner', name: 'Werner Häuserhofer', role: 'Gründer und Geschäftsführer', since: 'seit 1987', text: 'Hat den Betrieb in der Garage seiner Eltern gegründet. Steht jeden Morgen als Erster auf dem Hof.', photoAlt: 'Porträt Werner Häuserhofer, 65, graues Haar, Schnauzer, Lesebrille im Haar, dunkelblaue Fleeceweste, im Büro. KI-generiert', photo: '/images/werner-portrait-640.webp' },
  { slug: 'julia', name: 'Julia Häuserhofer', role: 'Prokuristin, Vertrieb', since: 'seit 2015', text: 'Wirtschaftsingenieurin. Kümmert sich um Vertrieb und darum, dass der Betrieb mit der Zeit geht. Übernimmt 2029.', photoAlt: 'Porträt Julia Häuserhofer, 36, dunkelblondes Haar im Zopf, dunkelblauer Blazer, im Büro. KI-generiert', photo: '/images/julia-portrait-640.webp' },
  { slug: 'petra', name: 'Petra Hoffmann', role: 'Büroleitung', since: 'seit 1998', text: 'Kennt fast jeden Kunden beim Namen und weiß, wo was liegt.', photoAlt: 'Porträt Petra Hoffmann, 54, kurze rotbraune Haare, weinrote Strickjacke, im Großraumbüro. KI-generiert', photo: '/images/petra-portrait-640.webp' },
  { slug: 'murat', name: 'Murat Demir', role: 'Leitung Kundendienst', since: 'seit 2009', text: 'Meister SHK. Plant Wartung und Störungsdienst für zehn Servicetechniker.', photoAlt: 'Porträt Murat Demir, 42, kurze schwarze Haare, kurzer Vollbart, dunkelblaue Softshelljacke über grauem Polo, auf dem Betriebshof vor einem Servicewagen. KI-generiert', photo: '/images/murat-portrait-614.webp' },
  { slug: 'klaus', name: 'Klaus Wagner', role: 'Leitung Werkstatt', since: 'Altmeister', text: 'Hat die Hydraulik-Pakete erfunden. Was er nicht über Heizungshydraulik weiß, muss man nicht wissen.', photoAlt: 'Porträt Klaus Wagner, 64, fast kahl, Bleistift hinterm Ohr, dunkelblaue Latzhose über grauem Shirt, vor der Werkbank in der Werkstatt. KI-generiert', photo: '/images/klaus-portrait-614.webp' },
  { slug: 'jonas', name: 'Jonas Becker', role: 'IT', since: 'seit 2021', text: 'Sorgt in Teilzeit dafür, dass Server, Telefone und Tablets laufen.', photoAlt: 'Porträt Jonas Becker, 31, wuschelige braune Haare, runde Brille, grauer Hoodie unter dunkelblauer Arbeitsjacke, Schlüsselband, im Technikraum. KI-generiert', photo: '/images/jonas-portrait-614.webp' },
  { slug: 'lea', name: 'Lea Schmidt', role: 'Auszubildende Anlagenmechanikerin SHK', since: '1. Lehrjahr', text: 'Lernt bei uns Anlagenmechanikerin, mal in der Werkstatt, mal auf der Baustelle.', photoAlt: 'Platzhalter Porträt Lea Schmidt, 18, langer brauner Pferdeschwanz, Firmen-Pulli, KI-generiert' },
];

export const departments = [
  { name: 'Geschäftsführung', count: 2 },
  { name: 'Büro', count: 5 },
  { name: 'Projektleitung Montage', count: 2 },
  { name: 'Montage', count: 14 },
  { name: 'Kundendienst', count: 11 },
  { name: 'Werkstatt Wärmepumpen-Pakete', count: 5 },
  { name: 'Lager und Einkauf', count: 2 },
  { name: 'IT', count: 1 },
  { name: 'Auszubildende', count: 4 },
];

export const process = [
  { title: 'Anfrage', text: 'Sie melden sich per Telefon oder Mail. Wir notieren, worum es geht.', meta: 'Telefon oder E-Mail' },
  { title: 'Vor-Ort-Termin', text: 'Ein Projektleiter kommt vorbei, schaut sich die Anlage an und nimmt Maß.', meta: 'Aufmaß und Fotos' },
  { title: 'Angebot', text: 'Sie bekommen ein schriftliches Angebot.', meta: 'In 2 bis 5 Arbeitstagen' },
  { title: 'Montage', text: 'Ein eingespieltes Zweier-Team baut ein. Die Projektleitung bleibt Ihr Ansprechpartner.', meta: 'Teams zu zweit' },
  { title: 'Wartung', text: 'Wir erinnern Sie, wenn die Wartung fällig ist, und kommen mit Messgerät und Protokoll.', meta: 'Mit Wartungsvertrag' },
];

// "Unser KI-Weg": the stages the series shows, in the order of consulting system v1.0
// (kanal/beratungssystem/beratungssystem.md, section 5). No results are given away before an
// episode is published; when one is, add `episode: { title, url }` to its stage.
export type KiStage = {
  label: string; title: string; text: string; episode?: { title: string; url: string };
};

export const kiWeg: KiStage[] = [
  { label: 'Phase 1 bis 3', title: 'Wo steht der Betrieb?', text: 'Wir lassen uns genau ansehen: Abläufe, Daten, Programme, und wo heute im Büro die meiste Zeit verloren geht.' },
  { label: 'Phase 4', title: 'Wo lohnt sich KI, und wo nicht?', text: 'Aus den Ideen wird ein Fahrplan. Die Geschäftsführung entscheidet schriftlich, was zuerst kommt und was nicht.' },
  { label: 'Phase 5', title: 'Was darf das Team mit KI?', text: 'Klare Regeln für alle im Betrieb, eine Grundschulung und ein Weg, Bedenken zu melden.' },
  { label: 'Freigabe 6.0 und Pilot', title: 'Der erste Fall: das Postfach', text: 'Ein kleiner, befristeter Test mit echten Mails. Vorher steht fest, ab wann er als Erfolg zählt.' },
  { label: 'Phase 7 bis 9', title: 'Vom Test in den Alltag', text: 'Wenn der Test trägt: ein stabiles System, Schulung für alle, die damit arbeiten, und ein begleiteter Start.' },
  { label: 'Phase 10', title: 'Was bringt es wirklich?', text: 'Wir prüfen regelmäßig Nutzen, Kosten und Fehler. Dann kommt der nächste Fall an die Reihe.' },
];
