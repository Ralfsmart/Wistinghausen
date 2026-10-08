"""Legt die Startinhalte (Beispieltexte und Bildbeschreibungen) als JSON in /inhalt an.

Nur einmal zum Einrichten gedacht – danach werden die Inhalte über /admin gepflegt.
Aufruf:  python werkzeuge/startinhalte.py
"""
import json
from pathlib import Path

ZIEL = Path(__file__).resolve().parent.parent / "inhalt"


def bild(datei, titel, beschreibung=""):
    return {"datei": "bilder/" + datei, "titel": titel, "beschreibung": beschreibung}


firma = {
    "name": "Schreinerei Arnim v. Wistinghausen",
    "inhaber": "Arnim von Wistinghausen",
    "zusatz": "Meisterbetrieb",
    "strasse": "Untere Weitfeld Str. 14",
    "ort": "88690 Mühlhofen",
    "werkstatt_strasse": "Ralzhof 1",
    "werkstatt_ort": "88682 Salem",
    "telefon": "07556 / 932 948",
    "mobil": "01522 / 162 1601",
    "fax": "07556 / 932 949",
    "email": "info@schreinerei-wistinghausen.de",
    "aufruf_titel": "Sie haben eine Idee?",
    "aufruf_text": "Erzählen Sie mir davon – gemeinsam finden wir die passende Lösung aus Holz.",
}

start = {
    "hero_titel": "In der kleinen Werkstatt am Ralzhof entstehen Träume aus Holz",
    "hero_text": "Massive Bauweise, fast alle Wünsche realisierbar – alles aus einer Hand, von der Planung bis zur Montage.",
    "abschnitt_titel": "Handwerk mit Sorgfalt",
    "abschnitt_text": "Eine schnelle und sorgfältige Durchführung der Aufträge ist mir ein besonderes Anliegen.",
    "abschnitt_punkte": [
        "Individuelle, passgenaue Einbauküchen",
        "Möbel und Innenausbau nach Maß",
        "Rührfässer für die biodynamische Landwirtschaft, 75 – 750 L",
    ],
    "fotos": [
        bild("kueche-7.jpg", "Küche"),
        bild("moebel12.jpg", "Tisch mit Baumkante"),
        bild("innen2.jpg", "Treppe mit Regalfächern"),
        bild("tueren5.jpg", "Eingangstür"),
        bild("aussen7.jpg", "Baumbank"),
        bild("faesser2.jpg", "Holzfässer"),
    ],
}

rubriken = {
    "kuechen": {
        "titel": "Küchen",
        "untertitel": "Einbauküchen nach Maß – geplant, gefertigt und montiert aus einer Hand",
        "beispieltext": True,
        "einleitung": (
            "Die Küche ist der Raum, in dem am meisten gelebt wird. Deshalb plane ich jede Küche individuell: "
            "passend zu Ihrem Raum, Ihren Abläufen und Ihrem Geschmack – mit Massivholzfronten, lackierten "
            "Oberflächen oder einer Kombination aus beidem.\n\n"
            "So läuft es ab: Zuerst komme ich zu Ihnen, wir besprechen Ihre Wünsche und ich nehme genau Maß. "
            "Danach erhalten Sie einen Entwurf mit Angebot. Nach Ihrer Freigabe fertige ich die Schränke in "
            "meiner Werkstatt am Ralzhof und montiere die Küche zum vereinbarten Termin bei Ihnen – sauber "
            "eingepasst an Wände, Nischen und Schrägen.\n\n"
            "Auch vorhandene Küchen bekommen bei mir ein zweites Leben: Ich erweitere sie, baue sie um oder "
            "ziehe sie mit Ihnen in die neue Wohnung um."
        ),
        "leistungen": [
            "Individuelle und passgenaue Einbauküchen",
            "Montage von Fertigküchen",
            "Erweiterung und Umbau gebrauchter Küchen",
            "Umzug von Einbauküchen",
        ],
        "bilder": [
            bild("kueche-6.JPG", "Weiße Eckküche", "Grifflose Fronten, hohe Schrankwand und Arbeitsplatte aus Massivholz mit Unterbaubeleuchtung."),
            bild("kueche-5.jpg", "Küche in L-Form", "Helles Holz, Oberschränke mit Glastüren und offenem Bord für den täglichen Bedarf."),
            bild("kueche-3.jpg", "Schubkästen unter dem Kochfeld", "Massivholz-Arbeitsplatte und Auszüge, die viel Platz für Töpfe und Pfannen bieten."),
            bild("kueche-7.jpg", "Küche in warmem Holzton", "Oberschränke bis unter die Decke und Backofen in bequemer Arbeitshöhe."),
            bild("kueche-2.jpg", "Küchenzeile mit roten Fronten", "Hochglänzende Schubkästen unter einer durchgehenden Holzarbeitsplatte."),
        ],
    },
    "moebel": {
        "titel": "Möbel",
        "untertitel": "Einzelstücke und Kleinserien – massiv oder in Plattenbauweise",
        "beispieltext": True,
        "einleitung": (
            "Ein gutes Möbelstück begleitet einen über viele Jahre. Ich baue Betten, Schränke, Kommoden und "
            "Tische genau nach Ihren Maßen und Vorstellungen – als freistehendes Einzelstück oder als Einbau, "
            "der eine Nische oder Dachschräge optimal nutzt.\n\n"
            "Am Anfang steht ein Gespräch, gern mit einer Skizze oder einem Foto als Idee. Gemeinsam wählen wir "
            "Holzart, Konstruktion und Oberfläche aus – ob geölt, gewachst oder lackiert. Dann entsteht das Möbel "
            "in meiner Werkstatt, mit klassischen Holzverbindungen dort, wo sie Sinn machen. Zum Schluss liefere "
            "ich es aus und baue es bei Ihnen auf."
        ),
        "leistungen": [
            "Betten, Schränke und Kommoden",
            "Tische – auch mit natürlicher Baumkante",
            "Einbaumöbel für Nischen und Dachschrägen",
            "Einzelstücke und Kleinserien",
            "Massivholz oder Plattenwerkstoff",
        ],
        "bilder": [
            bild("moebel9.jpg", "Regalwand mit Schiebetüren", "Offene Fächer in der Mitte, rot bespannte Schiebetüren an den Seiten."),
            bild("moebel10.jpg", "Massiver Tisch", "Kräftiges Wangengestell aus Massivholz."),
            bild("moebel4.jpg", "Detailaufnahme", "Bitte beschreiben."),
            bild("moebel12.jpg", "Tisch mit Baumkante", "Die natürliche Kante des Stammes bleibt sichtbar."),
            bild("moebel2.jpg", "Schreibtisch mit Rollcontainer", "Geschwungene Tischplatte mit passendem Schubkastenelement."),
            bild("moebel11.jpg", "Tischbein im Detail", "Schräg gestellte Beine aus dunklem Massivholz."),
            bild("moebel5.jpg", "Holzverbindung in Handarbeit", "Gezinkte Eckverbindung – stabil und schön anzusehen."),
            bild("moebel13.jpg", "Einbauschrank unter der Dachschräge", "Aus astigem Nadelholz, passgenau an die Schräge angepasst."),
            bild("moebel8.JPG", "Schrank mit Wandborden", "Zweitüriger Schrank mit Griffloch, links und rechts schwebende Ablagen."),
        ],
    },
    "innenausbau": {
        "titel": "Innenausbau",
        "untertitel": "Böden, Wände, Treppen und Einbauten – damit Räume besser funktionieren",
        "beispieltext": True,
        "einleitung": (
            "Oft sind es die kleinen Eingriffe, die einen Raum verändern: ein neuer Boden, eine versetzte Wand, "
            "eine renovierte Treppe oder Stauraum dort, wo vorher nur ungenutzter Platz war – unter der Treppe "
            "oder in der Dachschräge.\n\n"
            "Ich schaue mir die Situation bei Ihnen vor Ort an und mache Ihnen einen Vorschlag. Die Arbeiten "
            "stimme ich mit Ihnen und anderen Handwerkern zeitlich ab und achte auf eine saubere Baustelle. "
            "Vieles fertige ich vorab in der Werkstatt, damit die Zeit bei Ihnen im Haus möglichst kurz bleibt."
        ),
        "leistungen": [
            "Fußböden: Massiv- oder Fertigparkett, Kork, Laminat – verlegen, ausbessern, abschleifen",
            "Trennwände stellen, versetzen oder entfernen",
            "Fenster und Türen montieren",
            "Treppen ändern oder renovieren",
            "Stauraum unter Treppen und Dachschrägen",
        ],
        "bilder": [
            bild("innen1.jpg", "Auszugsschrank unter der Treppe", "Rollbarer Auszug für Schuhe und Helme – der Platz unter der Treppe wird voll genutzt."),
            bild("innen3.jpg", "Treppe renoviert", "Neue Massivholzstufen auf einer alten Treppe."),
            bild("innen2.jpg", "Treppe mit Regalfächern", "Offene Fächer unter den Stufen als Stauraum im Flur."),
            bild("innen4.jpg", "Schiebetüren unter der Dachschräge", "Leichte Rahmentüren verschließen den Stauraum hinter dem Kniestock."),
            bild("innen5.jpg", "Theke für ein Café", "Verkaufstheke mit Flaschenbord darüber."),
        ],
    },
    "tueren": {
        "titel": "Türen",
        "untertitel": "Haus- und Zimmertüren in Standard- und Sondermaßen",
        "beispieltext": True,
        "einleitung": (
            "Die Haustür ist die Visitenkarte eines Hauses. Gerade in Altbauten und Bauernhäusern passen "
            "Standardtüren oft nicht – hier fertige ich Türen und Tore genau nach Maß und passend zum Stil "
            "des Gebäudes.\n\n"
            "Nach dem Aufmaß beraten wir gemeinsam über Holzart, Gestaltung, Verglasung und Beschläge. Die Tür "
            "entsteht in meiner Werkstatt und wird von mir eingebaut und eingestellt, damit sie dicht schließt "
            "und lange Freude macht."
        ),
        "leistungen": [
            "Haustüren",
            "Zimmertüren",
            "Standard- und Sondergrößen",
            "Tore für Stall und Garage",
        ],
        "bilder": [
            bild("tueren1.jpg", "Haustür mit Oberlicht", "Blau lackierte Tür mit Sprossenfenstern in einem Sandsteingewände."),
            bild("tueren4.jpg", "Haustür im Fischgrätmuster", "Diagonal verlegte Bretter mit Rauten-Emblem."),
            bild("tueren5.jpg", "Eingangstür mit Sonnenmotiv", "Rot lackiert, mit verglasten Seitenteilen und Rundbogen."),
            bild("tueren2.jpg", "Zweiflügeliges Tor", "Holztor mit Bogen und kräftigen Bändern für Scheune oder Garage."),
            bild("tueren3.jpg", "Zimmertür mit Milchglas", "Rahmentür mit hellen Glasfeldern."),
            bild("tueren7.jpg", "Verglaste Doppeltür", "Zweiflügelige Tür mit Rundbogen und strahlenförmigen Sprossen."),
        ],
    },
    "aussen": {
        "titel": "Außenholzbau",
        "untertitel": "Für Garten, Hof und Hauseingang",
        "beispieltext": True,
        "einleitung": (
            "Holz im Freien muss Wind und Wetter standhalten. Deshalb achte ich auf die passende Holzart und "
            "auf eine Bauweise, bei der Wasser gut ablaufen kann und das Holz schnell wieder trocknet – so "
            "bleibt es lange schön.\n\n"
            "Ob Gartenlaube, Zaun, Terrasse oder Vordach: Wir besprechen Ihr Vorhaben vor Ort, ich mache Ihnen "
            "einen Vorschlag mit Angebot, fertige die Teile in der Werkstatt vor und baue sie bei Ihnen auf."
        ),
        "leistungen": [
            "Gartenlauben und Geräteschränke",
            "Gartenzäune und Tore",
            "Vordächer über der Haustür",
            "Terrassen",
            "Carports und Unterstände",
            "Gartenmöbel und Baumbänke",
        ],
        "bilder": [
            bild("aussen1.jpg", "Unterstand", "Offener Holzunterstand, z. B. für Fahrzeuge und Geräte."),
            bild("aussen4.jpg", "Gartentisch mit Bänken", "Massive Gartengarnitur für viele Gäste."),
            bild("aussen2.jpg", "Holzterrasse", "Terrasse mit Stufe am Haus."),
            bild("aussen6.jpg", "Geräteschrank", "Schrank mit Lamellenverkleidung und kleinem Vordach."),
            bild("aussen8.jpg", "Kleiner Unterstand", "Lattenkonstruktion mit Ziegeldach an einer alten Mauer."),
            bild("aussen7.jpg", "Baumbank", "Rundbank um einen Baumstamm – ein Lieblingsplatz im Schatten."),
        ],
    },
    "faesser": {
        "titel": "Rührfässer und Holzfässer",
        "untertitel": "Präparatefässer für die biologisch-dynamische Landwirtschaft – von 75 bis 750 Litern",
        "beispieltext": True,
        "einleitung": (
            "Für die biologisch-dynamische Landwirtschaft fertige ich Rührfässer für die Präparate in jeder "
            "Größe von 75 bis 750 Litern. Die Fässer werden aus einzelnen Holzdauben gebaut und mit Reifen "
            "zusammengehalten.\n\n"
            "Ebenso eignen sie sich zum Sammeln von Regenwasser oder für andere Zwecke im Garten. Sagen Sie mir, "
            "welche Größe und welches Zubehör – zum Beispiel einen Auslaufhahn – Sie brauchen. Lieferung oder "
            "Abholung nach Absprache."
        ),
        "leistungen": [
            "Präparate- und Rührfässer von 75 bis 750 Liter",
            "Regenfässer mit Auslaufhahn",
            "Sondergrößen auf Anfrage",
        ],
        "bilder": [
            bild("faesser1.jpg", "Holzfass", "Aus Holzdauben gebaut und von Metallreifen gehalten."),
            bild("faesser3.jpg", "Auslaufhahn", "Messinghahn zum Entnehmen von Regenwasser."),
            bild("faesser2.jpg", "Fässer in verschiedenen Größen", "Von klein bis groß – die Größe richtet sich nach dem Bedarf."),
        ],
    },
}


def schreibe(name, daten):
    pfad = ZIEL / f"{name}.json"
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("geschrieben:", pfad.name)


if __name__ == "__main__":
    ZIEL.mkdir(exist_ok=True)
    schreibe("firma", firma)
    schreibe("start", start)
    for key, daten in rubriken.items():
        schreibe(key, daten)
