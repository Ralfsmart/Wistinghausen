"""Stellt das Upload-Paket für den Webspace zusammen.

Ergebnis (im Ordner upload_paket/):
    webseite/                  alles, was per FTP in das Hauptverzeichnis des Webspace gehört
    schreinerei-wistinghausen-webseite.zip   dasselbe als ZIP (falls der Hoster ZIP entpacken kann)
    ANLEITUNG.md               Schritt für Schritt (gehört NICHT auf den Webspace)

Aufruf:
    python werkzeuge/upload_paket.py
    python werkzeuge/upload_paket.py --adresse https://www.schreinerei-wistinghausen.de/
    python werkzeuge/upload_paket.py --entwurf        (Seite bleibt für Suchmaschinen gesperrt)

Die Zugangsdatei admin/zugang.php ist NICHT enthalten. Sie wird einmal mit
werkzeuge/zugang_erzeugen.py angelegt und separat hochgeladen.
"""
import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent

# Was auf den Webspace gehört (alles andere bleibt im Repository)
ORDNER = ["admin", "bilder", "css", "fonts", "icons", "inhalt", "js"]
EINZELDATEIEN = [".htaccess", "favicon.ico", "favicon-32.png", "favicon-192.png", "apple-touch-icon.png", "einstellungen.json"]
NICHT = {
    "admin/zugang.php", "admin/_sperre.json",
}
NICHT_ORDNER = {"inhalt/_sicherung", "icons/alternativen"}
NICHT_ENDUNGEN = (".tmp", ".bak", ".log")


def kopieren(quelle: Path, ziel: Path):
    for datei in sorted(quelle.rglob("*")):
        if datei.is_dir():
            continue
        rel = datei.relative_to(WURZEL).as_posix()
        if rel in NICHT or datei.name.endswith(NICHT_ENDUNGEN) or ".tmp" in datei.name:
            continue
        if any(rel.startswith(o + "/") for o in NICHT_ORDNER):
            continue
        z = ziel / rel
        z.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(datei, z)


ANLEITUNG = """# Website auf den Webspace bei greatnet.de bringen

Stand: erzeugt am {datum} · Adresse der Website: {adresse}

## Vorher (einmalig)

1. **Zugangsdaten** von greatnet.de bereithalten (FTP-Benutzer, Passwort, Server). Diese Daten
   niemals in E-Mails, Chats oder ins GitHub-Repository schreiben.
2. Im **Verwaltungsprogramm** (LiveConfig, Plesk oder Confixx) prüfen:
   - **PHP-Version**: die **neueste angebotene** einstellen, mindestens 8.2 (greatnet bietet 5.6 bis 8.2 an).
     Alles unter 8.2 bekommt keine Sicherheitsupdates mehr. Beim Hoster nachfragen, ob 8.3 oder 8.4 kommt.
   - Ob das **SSL-Zertifikat (Let's Encrypt)** für die Domain aktiv ist.
   - Wie das **Hauptverzeichnis** der Domain heißt (Hilfe: FAQ von greatnet.de,
     „Ordnerstruktur (FTP, wohin muss meine Webseite?)“).
3. **Alte Website sichern**: den kompletten Inhalt des Hauptverzeichnisses per FTP auf den eigenen
   Rechner kopieren. Dann kann man jederzeit zurück.

## Passwort für den Admin-Bereich anlegen

Im Projektordner:

    python werkzeuge/zugang_erzeugen.py

Das Programm fragt zweimal nach dem Passwort (mindestens 10 Zeichen) und legt die Datei
`admin/zugang.php` an. Mit `--zufall` erzeugt es ein Passwort selbst und zeigt es einmal an.
Das Passwort gibt Herr von Wistinghausen später im Admin-Bereich ein.

## Hochladen

1. Mit FileZilla (oder einem anderen FTP-Programm) verbinden. Wenn möglich **FTPS/„explizit über TLS“**
   wählen.
2. **Den Inhalt des Ordners `webseite/`** (nicht den Ordner selbst) in das Hauptverzeichnis der Domain
   hochladen. Die alten Dateien (`index.htm`, `kuechen.htm`, `Bilder/` …) können bestehen bleiben oder
   danach gelöscht werden; die neuen Seiten haben andere Namen (`.html`). Die Weiterleitungen aus der
   `.htaccess` führen die alten Adressen auf die neuen Seiten.
3. Die Datei `admin/zugang.php` zusätzlich in den Ordner `admin/` auf dem Webspace hochladen.
4. **Schreibrechte** prüfen: PHP muss in den Ordnern `inhalt/`, `bilder/` und im Hauptverzeichnis
   schreiben dürfen (üblich: Ordnerrechte 755 oder 775). Die Prüfung macht der Admin-Bereich selbst
   (siehe unten).

## Prüfen

1. `{adresse}` öffnen: die Startseite erscheint, Menü und Fotos funktionieren.
2. `{adresse}admin/` öffnen und mit dem Passwort anmelden. Oben steht „Angemeldet (Webspace)“.
3. Eine Kleinigkeit ändern (zum Beispiel einen Satz), speichern, die Seite neu laden: die Änderung ist da.
4. Ein Foto hochladen und speichern.
5. Alte Adresse ausprobieren, zum Beispiel `{adresse}kuechen.htm`: sie führt zu `kuechen.html`.

## HTTPS erzwingen

Wenn `https://` funktioniert, in der Datei `.htaccess` die drei Zeilen unter „HTTPS erzwingen“
entkommentieren (das `#` am Anfang entfernen) und die Datei neu hochladen.

## Für Google

- In der **Google Search Console** die Website anmelden und die Sitemap `{adresse}sitemap.xml` einreichen.
- Ein **Google-Unternehmensprofil** (Google Maps) für „Schreinerei Wistinghausen“ anlegen oder
  aktualisieren, mit denselben Angaben wie im Impressum.

## Wenn etwas nicht klappt

| Symptom | Ursache und Lösung |
|---|---|
| Admin zeigt „noch nicht eingerichtet“ | `admin/zugang.php` fehlt auf dem Webspace |
| Admin zeigt „Der Server hat keine gültige Antwort gegeben“ | PHP läuft nicht: PHP-Version im Verwaltungsprogramm prüfen |
| Speichern meldet „Fehlen die Schreibrechte?“ | Ordner `inhalt/` und `bilder/` auf 755 oder 775 stellen |
| „Gespeichert, aber die Seiten konnten nicht neu erzeugt werden“ | Das Hauptverzeichnis ist nicht beschreibbar. Der Text erscheint trotzdem, nur Suchmaschinen sehen ihn erst später |
| Nach 8 falschen Passwörtern „Zu viele Fehlversuche“ | 15 Minuten warten oder `admin/_sperre.json` auf dem Webspace löschen |
| Passwort vergessen | neue `zugang.php` mit `zugang_erzeugen.py` erzeugen und hochladen |

## Sicherungen

Bei jedem Speichern legt der Admin-Bereich eine Kopie der alten Fassung in `inhalt/_sicherung/` ab
(die letzten 15 je Seite). Zusätzlich sollte alle paar Wochen der Inhalt des Webspace
heruntergeladen werden.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adresse", default="https://www.schreinerei-wistinghausen.de/")
    ap.add_argument("--entwurf", action="store_true", help="Seite für Suchmaschinen gesperrt lassen")
    ap.add_argument("--ziel", default=str(WURZEL / "upload_paket"))
    args = ap.parse_args()
    adresse = args.adresse if args.adresse.endswith("/") else args.adresse + "/"
    ziel = Path(args.ziel)
    seite = ziel / "webseite"
    if ziel.exists():
        # OneDrive oder ein Virenscanner halten Dateien manchmal kurz fest: mehrmals versuchen,
        # sonst in einen neuen Ordner ausweichen
        import os, stat, time

        def freigeben(funktion, pfad, _fehler):
            os.chmod(pfad, stat.S_IWRITE)
            funktion(pfad)

        for versuch in range(4):
            try:
                shutil.rmtree(ziel, onexc=freigeben)
                break
            except OSError:
                time.sleep(1.5)
        if ziel.exists():
            ziel = ziel.with_name(ziel.name + "_" + time.strftime("%Y%m%d_%H%M%S"))
            seite = ziel / "webseite"
            print(f"Hinweis: der alte Ordner ließ sich nicht löschen, das Paket entsteht in {ziel.name}")
    seite.mkdir(parents=True)

    # 1. Dateien kopieren
    for ordner in ORDNER:
        kopieren(WURZEL / ordner, seite)
    for name in EINZELDATEIEN:
        q = WURZEL / name
        if q.exists():
            shutil.copy2(q, seite / name)

    # 2. Einstellungen für die endgültige Adresse
    einst = json.loads((WURZEL / "einstellungen.json").read_text(encoding="utf-8"))
    einst["adresse"] = adresse
    einst["entwurf"] = bool(args.entwurf)
    (seite / "einstellungen.json").write_text(json.dumps(einst, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 3. Seiten, Sitemap und robots.txt für diese Adresse erzeugen
    kommando = [sys.executable, str(WURZEL / "werkzeuge" / "seiten_erzeugen.py"), "--ziel", str(seite), "--adresse", adresse]
    if not args.entwurf:
        kommando.append("--live")
    r = subprocess.run(kommando, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("Seiten konnten nicht erzeugt werden:\n" + r.stdout + r.stderr)

    # 4. Prüfungen
    fehler = []
    if (seite / "admin" / "zugang.php").exists():
        fehler.append("admin/zugang.php ist im Paket (darf nicht sein)")
    robots = (seite / "robots.txt").read_text(encoding="utf-8")
    if not args.entwurf and "Disallow: /\n" in robots:
        fehler.append("robots.txt sperrt die ganze Seite")
    for seitenname in ["index.html", "kuechen.html", "moebel.html", "innenausbau.html", "tueren.html", "aussen.html",
                       "faesser.html", "impressum.html", "datenschutz.html"]:
        text = (seite / seitenname).read_text(encoding="utf-8")
        if "ralfsmart.github.io" in text:
            fehler.append(f"{seitenname} enthält noch die GitHub-Adresse")
        if not args.entwurf and 'content="noindex"' in text:
            fehler.append(f"{seitenname} ist noch auf noindex gestellt")
    # alle von den Inhalten genannten Fotos vorhanden?
    import re
    fehlend = set()
    for j in (seite / "inhalt").glob("*.json"):
        for m in re.findall(r"bilder/[^\"]+", j.read_text(encoding="utf-8")):
            if not (seite / m).exists():
                fehlend.add(m)
    if fehlend:
        fehler.append("fehlende Fotos: " + ", ".join(sorted(fehlend)))
    if fehler:
        sys.exit("Prüfung fehlgeschlagen:\n  - " + "\n  - ".join(fehler))

    # 5. ZIP und Anleitung
    zip_pfad = ziel / "schreinerei-wistinghausen-webseite.zip"
    with zipfile.ZipFile(zip_pfad, "w", zipfile.ZIP_DEFLATED) as z:
        for datei in sorted(seite.rglob("*")):
            if datei.is_file():
                z.write(datei, datei.relative_to(seite).as_posix())
    from datetime import date
    (ziel / "ANLEITUNG.md").write_text(ANLEITUNG.format(adresse=adresse, datum=date.today().strftime("%d.%m.%Y")), encoding="utf-8")

    dateien = [p for p in seite.rglob("*") if p.is_file()]
    groesse = sum(p.stat().st_size for p in dateien) / (1024 * 1024)
    print(f"Paket fertig: {ziel}")
    print(f"  Adresse     : {adresse}  ({'GESPERRT für Suchmaschinen' if args.entwurf else 'freigegeben'})")
    print(f"  Dateien     : {len(dateien)} ({groesse:.1f} MB)")
    print(f"  ZIP         : {zip_pfad.name} ({zip_pfad.stat().st_size / (1024 * 1024):.1f} MB)")
    print("  Anleitung   : ANLEITUNG.md")
    print("Noch zu tun: Zugangsdatei erzeugen (werkzeuge/zugang_erzeugen.py) und nach admin/ hochladen.")


if __name__ == "__main__":
    main()
