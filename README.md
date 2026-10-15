# Schreinerei Wistinghausen – Website

Neue Website für www.schreinerei-wistinghausen.de. Reines HTML/CSS/JavaScript. Läuft als Entwurf auf
GitHub Pages und später auf dem Apache-Webspace (greatnet.de, PHP) per FTP-Upload.

## Aufbau
- `index.html`, `kuechen.html`, `moebel.html`, `innenausbau.html`, `tueren.html`, `aussen.html`,
  `faesser.html`, `impressum.html`, `datenschutz.html` – **erzeugt**, nicht von Hand ändern
- `inhalt/*.json` – **alle Texte, Fotos und Bildbeschreibungen**; werden über `/admin` gepflegt
- `einstellungen.json` – Adresse der Website, `entwurf` (noindex an/aus), Versionsnummer für CSS/JS
- `js/site.js` – setzt die Inhalte im Browser ein, Foto-Großansicht mit Zoom
- `css/`, `fonts/`, `icons/` – Gestaltung, lokale Schriften, Menüsymbole
- `bilder/` – Fotos; neue Uploads aus dem Admin landen in `bilder/uploads/`
- `.htaccess` – Apache: Weiterleitungen der alten Adressen, Schutz interner Dateien, Zwischenspeicher

## Admin-Bereich (`/admin/`)
Speicherorte (siehe `admin/config.js`, abhängig davon, wo die Seite läuft):
- **GitHub** (auf GitHub Pages): schreibt direkt ins Repository. Braucht einen *Fine-grained Personal Access
  Token*, nur für dieses Repository, Berechtigung **Contents: Read and write**.
  Die Seiten werden von GitHub Actions neu erzeugt und veröffentlicht (1–2 Minuten).
- **Webspace** (auf dem eigenen Server): speichert über `admin/api.php` (PHP, ohne Datenbank), Anmeldung mit
  Passwort. Nach jedem Speichern erzeugt `admin/seiten.php` die Seiten neu, sofort sichtbar.
- **Testmodus**: nichts wird gespeichert.

## Werkzeuge (`werkzeuge/`)
| Datei | Zweck |
|---|---|
| `seiten_erzeugen.py` | erzeugt alle Seiten fest aus `inhalt/*.json` (für Suchmaschinen), `--ziel`, `--adresse`, `--live` |
| `pruefe_php.py` | prüft, dass der PHP-Generator (`admin/seiten.php`) dasselbe liefert wie `seiten_erzeugen.py` |
| `zugang_erzeugen.py` | legt `admin/zugang.php` (Passwort-Hash) für den Webspace an |
| `upload_paket.py` | stellt den Ordner `upload_paket/` mit allem für den FTP-Upload zusammen, inkl. `ANLEITUNG.md` |

Bei Änderungen an `css/`, `js/` oder `admin/`: in `einstellungen.json` die `version` hochzählen und
`admin/index.html` (dort stehen die Versionsnummern der Admin-Dateien) anpassen.

## Umzug auf den Webspace
1. `python werkzeuge/zugang_erzeugen.py` (Passwort festlegen)
2. `python werkzeuge/upload_paket.py` (Paket für die endgültige Adresse)
3. Inhalt von `upload_paket/webseite/` per FTP hochladen, dazu `admin/zugang.php` in den Ordner `admin/`
4. Weiteres siehe `upload_paket/ANLEITUNG.md`

`admin/zugang.php` gehört nie ins Repository (steht in `.gitignore`).

## Offen
Neue Fotos von Innentüren, Foto von Herrn v. Wistinghausen und gescannter Meisterbrief für „Über mich“,
gelb markierte Stellen im Admin klären, `noindex` zum Livegang entfernen (Paket mit `upload_paket.py`).
