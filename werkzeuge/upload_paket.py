"""Stellt das Upload-Paket für den Webspace zusammen.

Ergebnis (im Ordner upload_paket/):
    webseite/                  alles, was per FTP in das Hauptverzeichnis des Webspace gehört
    schreinerei-wistinghausen-webseite.zip   dasselbe als ZIP (falls der Hoster ZIP entpacken kann)
    ANLEITUNG.md               Schritt für Schritt (gehört NICHT auf den Webspace)

Aufruf:
    python werkzeuge/upload_paket.py                     Erstlieferung (alles) für die Live-Adresse
    python werkzeuge/upload_paket.py --entwurf           Seite bleibt für Suchmaschinen gesperrt
    python werkzeuge/upload_paket.py --nur-code          NACH dem Livegang: nur Programm- und Gestaltungsdateien,
                                                         keine Inhalte, Fotos oder fertigen Seiten
    python werkzeuge/upload_paket.py --test test         Probelauf in /test/ auf dem Webspace, alte Seite bleibt unberührt
    python werkzeuge/upload_paket.py --ohne-pull         ohne vorher GitHub abzufragen (offline)

Vor dem Bauen holt das Skript immer die neuesten Daten von GitHub (git pull). Gibt es lokale,
nicht gesicherte Änderungen an Inhalten, bricht es ab, damit nichts verloren geht.

Wichtig: Nach dem Livegang liegen die aktuellen Inhalte auf dem Webspace (inhalt/, bilder/uploads/).
Ein komplettes Paket würde sie mit dem Stand von GitHub überschreiben. Dann nur --nur-code verwenden.

Die Zugangsdatei admin/zugang.php ist NICHT enthalten. Sie wird einmal mit
werkzeuge/zugang_erzeugen.py angelegt und separat hochgeladen.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent

# Was auf den Webspace gehört (alles andere bleibt im Repository)
ORDNER_ALLES = ["admin", "bilder", "css", "fonts", "icons", "inhalt", "js"]
ORDNER_CODE = ["admin", "css", "fonts", "icons", "js"]            # ohne inhalt/ und bilder/
EINZEL_ALLES = [".htaccess", "favicon.ico", "favicon-32.png", "favicon-192.png", "apple-touch-icon.png", "einstellungen.json"]
EINZEL_CODE = ["favicon.ico", "favicon-32.png", "favicon-192.png", "apple-touch-icon.png", "einstellungen.json"]
NICHT = {"admin/zugang.php", "admin/_sperre.json"}
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


# ---- Stand von GitHub ------------------------------------------------------------------------------
def git(*args):
    return subprocess.run(["git", "-C", str(WURZEL), *args], capture_output=True, text=True)


def stand_pruefen(ohne_pull: bool) -> str:
    """Holt die neuesten Daten von GitHub. Gibt eine Zeile zum Stand zurück."""
    if ohne_pull:
        return "Stand: lokaler Ordner, ohne Abgleich mit GitHub (--ohne-pull)"
    if not (WURZEL / ".git").exists():
        sys.exit("Dies ist kein Git-Ordner. Bitte im Projektordner mit dem GitHub-Stand arbeiten "
                 "(oder mit --ohne-pull bewusst auf den Abgleich verzichten).")
    r = git("fetch", "-q", "origin")
    if r.returncode != 0:
        sys.exit("GitHub ist nicht erreichbar, der aktuelle Stand lässt sich nicht holen.\n"
                 + r.stderr.strip() + "\nMit --ohne-pull kann das Paket aus dem lokalen Stand gebaut werden.")
    zweig = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    ziel = f"origin/{zweig}"
    if git("rev-parse", "--verify", "-q", ziel).returncode != 0:
        sys.exit(f"Der Zweig {zweig} ist auf GitHub nicht vorhanden.")
    zurueck = int(git("rev-list", "--count", f"HEAD..{ziel}").stdout.strip() or 0)
    voraus = int(git("rev-list", "--count", f"{ziel}..HEAD").stdout.strip() or 0)
    # lokale, nicht eingecheckte Änderungen an Dingen, die ins Paket kommen
    offen = git("status", "--porcelain", "--", "inhalt", "bilder", "admin", "css", "js", "einstellungen.json").stdout.strip()
    if zurueck:
        if offen:
            sys.exit(f"Auf GitHub gibt es {zurueck} neuere Änderung(en), lokal liegen aber nicht gesicherte Änderungen:\n"
                     f"{offen}\nBitte erst einchecken oder zurücksetzen, dann noch einmal starten.")
        r = git("pull", "--rebase", "-q", "origin", zweig)
        if r.returncode != 0:
            sys.exit("git pull ist fehlgeschlagen:\n" + r.stderr.strip())
        meldung = f"{zurueck} neuere Änderung(en) von GitHub geholt"
    else:
        meldung = "lokaler Ordner ist auf dem Stand von GitHub"
    if voraus:
        meldung += f"; ACHTUNG: {voraus} lokale Änderung(en) sind noch nicht auf GitHub"
    if offen and not zurueck:
        meldung += "; ACHTUNG: es gibt nicht eingecheckte lokale Änderungen, sie kommen mit ins Paket"
    kopf = git("log", "-1", "--format=%h, %ad", "--date=format:%d.%m.%Y %H:%M").stdout.strip()
    inhalt = git("log", "-1", "--format=%ad von %an", "--date=format:%d.%m.%Y %H:%M", "--", "inhalt", "bilder").stdout.strip()
    return f"Stand: {meldung}\n  Commit : {kopf}\n  Inhalte zuletzt geändert: {inhalt or 'unbekannt'}"


# ---- Anleitungen -------------------------------------------------------------------------------------
ANLEITUNG_ERST = """# Website auf den Webspace bei greatnet.de bringen (Erstlieferung)

Stand: erzeugt am {datum} · Adresse der Website: {adresse}
{stand}

> **Nur für das erste Hochladen.** Nach dem Livegang liegen die aktuellen Texte und Fotos auf dem
> Webspace. Dieses komplette Paket würde sie mit dem GitHub-Stand überschreiben. Für spätere
> Aktualisierungen gibt es das Paket „nur Code“ (siehe ganz unten).

## Vorher (einmalig)

1. **Zugangsdaten** von greatnet.de bereithalten (FTP-Benutzer, Passwort, Server). Diese Daten
   niemals in E-Mails, Chats oder ins GitHub-Repository schreiben.
2. Im **Verwaltungsprogramm** (LiveConfig, Plesk oder Confixx) prüfen:
   - **PHP-Version**: die **neueste angebotene** einstellen und beim Hoster bestätigen lassen, dass sie die
     Sicherheitsupdates vom 21.10.2026 (CVE-2026-109618/-109619, „php2shell“) hat: mindestens
     **8.2.35, 8.3.36, 8.4.27 oder 8.5.12**. Ältere Versionen (8.1 und darunter) nicht verwenden. Der Admin-Bereich
     zeigt nach der Anmeldung eine Warnung, wenn die Version zu alt ist. Hoster mit angepassten Paketen
     (Backports) lassen die Versionsnummer manchmal unverändert; dann die Bestätigung des Hosters einholen.
   - Ob das **SSL-Zertifikat (Let's Encrypt)** für die Domain aktiv ist.
   - Wie das **Hauptverzeichnis** der Domain heißt (Hilfe: FAQ von greatnet.de,
     „Ordnerstruktur (FTP, wohin muss meine Webseite?)“).
3. **Alte Website sichern**: den kompletten Inhalt des Hauptverzeichnisses per FTP auf den eigenen
   Rechner kopieren. Dann kann man jederzeit zurück.
4. **Redaktion abgeschlossen?** Dieses Paket enthält den Stand von GitHub zum oben genannten Zeitpunkt.
   Alles, was danach im Admin auf GitHub gespeichert wird, ist nicht enthalten.

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

## Nach dem Livegang: wo liegen die Inhalte?

- **Ab jetzt ist der Webspace maßgeblich.** Texte und Fotos werden im Admin der Live-Seite gepflegt und liegen
  dort in `inhalt/` und `bilder/uploads/`. Der Stand auf GitHub wird nicht mehr nachgeführt.
- **Den GitHub-Entwurf nicht mehr bearbeiten**, sonst gibt es zwei verschiedene Stände. Am besten den
  GitHub-Zugangsschlüssel löschen (GitHub → Settings → Developer settings → Fine-grained tokens) und
  den Entwurf bei Bedarf abschalten.
- **Sicherung:** alle paar Wochen die Ordner `inhalt/` und `bilder/` per FTP herunterladen und aufbewahren.
- **Aktualisierungen an Programm oder Gestaltung:** nie das komplette Paket erneut hochladen, sondern
  `python werkzeuge/upload_paket.py --nur-code` verwenden. Es enthält keine Inhalte, Fotos, fertigen
  Seiten und keine `.htaccess` (damit die HTTPS-Einstellung erhalten bleibt).
  Danach im Admin-Bereich auf **„Seiten neu erzeugen“** klicken, damit die fertigen Seiten das neue
  Aussehen bekommen.

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

ANLEITUNG_CODE = """# Aktualisierung von Programm und Gestaltung (nur Code)

Stand: erzeugt am {datum} · Adresse der Website: {adresse}
{stand}

Dieses Paket enthält **keine** Texte, Fotos, fertigen Seiten und keine `.htaccess`. Die Inhalte auf dem
Webspace bleiben unverändert.

## Vorher

1. **Sicherung:** den aktuellen Stand des Webspace per FTP herunterladen (mindestens `inhalt/` und `bilder/`).
2. Prüfen, dass im Admin-Bereich nicht gerade jemand arbeitet.

## Hochladen

1. Den **Inhalt des Ordners `webseite/`** in das Hauptverzeichnis der Domain hochladen und vorhandene
   Dateien überschreiben.
2. **`admin/zugang.php` nicht überschreiben oder löschen** (sie ist nicht im Paket enthalten).

## Danach

1. `{adresse}admin/` öffnen und anmelden.
2. Oben auf **„Seiten neu erzeugen“** klicken. Das erzeugt alle fertigen Seiten aus den vorhandenen
   Inhalten neu, mit dem neuen Aussehen.
3. Die Website kurz durchsehen (Startseite, eine Rubrik, Impressum) und mit **Strg+F5** neu laden.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adresse", default="https://www.schreinerei-wistinghausen.de/")
    ap.add_argument("--entwurf", action="store_true", help="Seite für Suchmaschinen gesperrt lassen")
    ap.add_argument("--nur-code", action="store_true", help="nur Programm und Gestaltung, keine Inhalte (nach dem Livegang)")
    ap.add_argument("--mit-htaccess", action="store_true", help="bei --nur-code auch die .htaccess ausliefern")
    ap.add_argument("--test", metavar="ORDNER", help="Probelauf in einem Unterordner des Webspace (z. B. test): "
                    "Adresse wird <adresse>ORDNER/, Seite gesperrt für Suchmaschinen, die alte Seite bleibt unberührt")
    ap.add_argument("--ohne-pull", action="store_true", help="vorher nicht von GitHub aktualisieren")
    ap.add_argument("--ziel", default=str(WURZEL / "upload_paket"))
    args = ap.parse_args()
    adresse = args.adresse if args.adresse.endswith("/") else args.adresse + "/"
    if args.test:
        if args.nur_code:
            sys.exit("--test und --nur-code lassen sich nicht kombinieren.")
        testname = args.test.strip("/")
        if not re.fullmatch(r"[a-z0-9-]+", testname):
            sys.exit("Der Testordner darf nur aus Kleinbuchstaben, Ziffern und Bindestrichen bestehen.")
        adresse += testname + "/"
        args.entwurf = True

    # 0. Aktuellen Stand von GitHub holen
    stand = stand_pruefen(args.ohne_pull)
    print(stand)

    ziel = Path(args.ziel)
    seite = ziel / "webseite"
    if ziel.exists():
        # OneDrive oder ein Virenscanner halten Dateien manchmal kurz fest: mehrmals versuchen,
        # sonst in einen neuen Ordner ausweichen
        import os
        import stat
        import time

        def freigeben(funktion, pfad, _fehler):
            os.chmod(pfad, stat.S_IWRITE)
            funktion(pfad)

        for _ in range(4):
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
    ordner = ORDNER_CODE if args.nur_code else ORDNER_ALLES
    einzel = list(EINZEL_CODE if args.nur_code else EINZEL_ALLES)
    if args.nur_code and args.mit_htaccess:
        einzel.append(".htaccess")
    for o in ordner:
        kopieren(WURZEL / o, seite)
    for name in einzel:
        q = WURZEL / name
        if q.exists():
            shutil.copy2(q, seite / name)

    if args.test and (seite / ".htaccess").exists():
        ht = seite / ".htaccess"
        text = ht.read_text(encoding="utf-8")
        assert "RewriteBase /\n" in text
        text = text.replace("RewriteBase /\n", f"RewriteBase /{testname}/\n", 1)
        ht.write_text(text, encoding="utf-8", newline="\n")

    # 2. Einstellungen für die endgültige Adresse
    einst = json.loads((WURZEL / "einstellungen.json").read_text(encoding="utf-8"))
    einst["adresse"] = adresse
    einst["entwurf"] = bool(args.entwurf)
    (seite / "einstellungen.json").write_text(json.dumps(einst, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fehler = []
    if (seite / "admin" / "zugang.php").exists():
        fehler.append("admin/zugang.php ist im Paket (darf nicht sein)")

    if not args.nur_code:
        # 3. Seiten, Sitemap und robots.txt für diese Adresse erzeugen
        kommando = [sys.executable, str(WURZEL / "werkzeuge" / "seiten_erzeugen.py"), "--ziel", str(seite), "--adresse", adresse]
        if not args.entwurf:
            kommando.append("--live")
        r = subprocess.run(kommando, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("Seiten konnten nicht erzeugt werden:\n" + r.stdout + r.stderr)

        # 4. Prüfungen
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
        fehlend = set()
        for j in (seite / "inhalt").glob("*.json"):
            for m in re.findall(r"bilder/[^\"]+", j.read_text(encoding="utf-8")):
                if not (seite / m).exists():
                    fehlend.add(m)
        if fehlend:
            fehler.append("fehlende Fotos: " + ", ".join(sorted(fehlend)))
    else:
        # im Code-Paket darf nichts enthalten sein, das Inhalte auf dem Webspace überschreiben würde
        for verboten in ("inhalt", "bilder", "index.html", "impressum.html", "sitemap.xml", "robots.txt"):
            if (seite / verboten).exists():
                fehler.append(f"{verboten} ist im Code-Paket (würde Inhalte überschreiben)")
        if not args.mit_htaccess and (seite / ".htaccess").exists():
            fehler.append(".htaccess ist im Code-Paket, obwohl --mit-htaccess fehlt")

    if fehler:
        sys.exit("Prüfung fehlgeschlagen:\n  - " + "\n  - ".join(fehler))

    # 5. ZIP und Anleitung
    zip_pfad = ziel / "schreinerei-wistinghausen-webseite.zip"
    with zipfile.ZipFile(zip_pfad, "w", zipfile.ZIP_DEFLATED) as z:
        for datei in sorted(seite.rglob("*")):
            if datei.is_file():
                z.write(datei, datei.relative_to(seite).as_posix())
    vorlage = ANLEITUNG_CODE if args.nur_code else ANLEITUNG_ERST
    if args.test:
        vorlage = ("> **PROBELAUF.** Dieses Paket gehört in den Unterordner `" + testname + "/` des Webspace, nicht ins "
                   "Hauptverzeichnis. Die alte Website bleibt unberührt. Zum Prüfen: Admin anmelden, ändern, speichern, "
                   "Foto hochladen, „Seiten neu erzeugen“, alte Adresse wie `" + testname + "/kuechen.htm` aufrufen. "
                   "Danach den Ordner komplett löschen.\n\n") + vorlage
    stand_md = "\n".join("> " + z.strip() for z in stand.splitlines())
    (ziel / "ANLEITUNG.md").write_text(
        vorlage.format(adresse=adresse, datum=date.today().strftime("%d.%m.%Y"), stand=stand_md), encoding="utf-8")

    dateien = [p for p in seite.rglob("*") if p.is_file()]
    groesse = sum(p.stat().st_size for p in dateien) / (1024 * 1024)
    print(f"Paket fertig: {ziel}")
    print(f"  Art         : {'NUR CODE (ohne Inhalte)' if args.nur_code else 'Erstlieferung (komplett)'}")
    print(f"  Adresse     : {adresse}  ({'GESPERRT für Suchmaschinen' if args.entwurf else 'freigegeben'})")
    print(f"  Dateien     : {len(dateien)} ({groesse:.1f} MB)")
    print(f"  ZIP         : {zip_pfad.name} ({zip_pfad.stat().st_size / (1024 * 1024):.1f} MB)")
    print("  Anleitung   : ANLEITUNG.md")
    if args.nur_code:
        print("Nach dem Hochladen im Admin auf „Seiten neu erzeugen“ klicken.")
    else:
        print("Noch zu tun: Zugangsdatei erzeugen (werkzeuge/zugang_erzeugen.py) und nach admin/ hochladen.")


if __name__ == "__main__":
    main()
