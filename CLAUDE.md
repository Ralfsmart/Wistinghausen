# Schreinerei Wistinghausen — Website (CLAUDE.md)

Reines HTML/CSS/JS, **kein Build-Schritt**, läuft als Entwurf auf GitHub Pages
(`https://ralfsmart.github.io/Wistinghausen/`) und soll später zusätzlich auf den Apache-Webspace
`greatnet.de` (PHP, per FTP) umziehen. `README.md` beschreibt Aufbau und Umzug für den Nutzer;
diese Datei ist für die Zusammenarbeit mit Claude: Architektur, Fallstricke, wie getestet wird.

## Architektur

- `index.html`, `kuechen.html`, `moebel.html`, `innenausbau.html`, `tueren.html`, `aussen.html`,
  `faesser.html`, `impressum.html`, `datenschutz.html` — **erzeugt**, nie von Hand ändern. Quelle
  der Wahrheit sind `inhalt/*.json` + `einstellungen.json`; die Seiten werden daraus von zwei
  **parallelen, gleichwertigen Generatoren** gebaut:
  - `werkzeuge/seiten_erzeugen.py` — läuft in GitHub Actions (`.github/workflows/website.yml`) bei
    jedem Push auf `main`.
  - `admin/seiten.php` (Klasse `SeitenErzeuger`) — läuft auf dem Webspace, direkt nach jedem
    Speichern im Admin (`aktion=schreiben`/`aktion=seiten` in `admin/api.php`).
  Beide müssen **byte-identische** Ausgabe liefern; `werkzeuge/pruefe_php.py` prüft das mit
  bewusst schwierigen Testinhalten (Anführungszeichen, `&`, Links, leere Felder, …). Nach jeder
  Änderung an einem der beiden Generatoren den anderen mitziehen und `pruefe_php.py` laufen lassen.
- `js/site.js` — setzt die Inhalte zur Laufzeit im Browser ein (Foto-Großansicht mit Zoom). Nur
  für die interaktiven Teile relevant, nicht für den Seiteninhalt selbst (der steht schon fest im
  erzeugten HTML, wichtig für Suchmaschinen).
- `admin/` — Editor für `inhalt/*.json`, siehe eigener Abschnitt unten.
- `werkzeuge/` — Python-Helfer, laufen nie automatisch außer `seiten_erzeugen.py` in CI:
  `pruefe_php.py` (Python-/PHP-Generator vergleichen), `zugang_erzeugen.py` (Passwort-Hash für
  Webspace anlegen), `upload_paket.py` (FTP-Paket für den Umzug/Updates zusammenstellen).
- `.htaccess` — nur für den Apache-Webspace relevant (Weiterleitungen, Schutz interner Dateien,
  Cache-Header), auf GitHub Pages wirkungslos.

## Admin-Bereich (`/admin/`) — drei Speicherorte

Welche Speicherorte zur Auswahl stehen, entscheidet `admin/config.js` **anhand des Hostnamens**
(`location.hostname`), nicht per Einstellung:

| Host | angebotene Speicherorte |
|---|---|
| `*.github.io` | `github`, `test` |
| `localhost` / `127.0.0.1` / leer | `webspace`, `github`, `test` |
| alles andere (künftig: `www.schreinerei-wistinghausen.de`) | `webspace`, `test` |

Die eigentliche Logik je Speicherort steht in `admin/admin.js` im Objekt `SPEICHER` (`github`,
`webspace`, `test`), austauschbar über ein gemeinsames Interface (`start`/`lesen`/`schreiben`, dazu
optional `seitenNeu`/`abmelden`).

- **`github`**: schreibt per GitHub Contents API direkt ins Repository (`PUT
  /repos/{owner}/{repo}/contents/{pfad}`, siehe `CFG.github` in `admin/config.js`). Braucht ein
  *Fine-grained Personal Access Token* mit **Contents: Read and write**, nur für dieses Repo. Token
  liegt nach Anmeldung in `sessionStorage`/`localStorage` (`wst-token`), **im Klartext**, nie im
  Repo. GitHub Actions baut und veröffentlicht danach neu (1–2 Minuten Verzögerung).
- **`webspace`**: spricht `admin/api.php` an (PHP, keine Datenbank, Session-Cookie `wst_admin`,
  CSRF-Token in `_SESSION['token']`). Passwort-Login mit Rate-Limit (8 Versuche, dann 15 Min
  Sperre, `admin/_sperre.json`, gitignored) und PBKDF2-Hash in `admin/zugang.php` (erzeugt von
  `werkzeuge/zugang_erzeugen.py`, **gehört nie ins Repo**, steht in `.gitignore`). Fehlt
  `admin/zugang.php`, meldet `aktion=status` `eingerichtet: false` und der Bereich ist gesperrt.
  Jedes Speichern einer `inhalt/*.json` legt vorher eine Sicherung an (`inhalt/_sicherung/`, max.
  15 Stände je Datei) und erzeugt danach sofort alle Seiten neu (`SeitenErzeuger`) — Änderungen
  sind ohne Deploy-Wartezeit live. Optimistic-Locking über einen `version`-Hash (sha1-Präfix) pro
  Datei, Konflikt → HTTP 409.
- **`test`**: speichert nichts (nur im Browser-Speicher für die laufende Sitzung), liest die
  echten `inhalt/*.json` per `fetch`. Für Spielerei ohne Risiko, auf **jedem** Host verfügbar.

## Wichtige Fallstricke

- **Cache nach Änderungen an `css/`, `js/` oder `admin/`**: `version` in `einstellungen.json`
  hochzählen **und** die `?v=NN`-Nummern direkt in `admin/index.html` (Zeilen mit `style.css`,
  `admin.css`, `config.js`, `admin.js`) anpassen — der Admin-Bereich zieht seine Version **nicht**
  aus `einstellungen.json`, sondern hat sie hart verdrahtet. Wird das vergessen, sieht man im
  Browser die alte Version aus dem Cache, nicht die eigene Änderung.
- **Zwei Generatoren, eine Wahrheit**: Jede inhaltliche Änderung an `seiten_erzeugen.py` ohne die
  passende Änderung an `admin/seiten.php` (oder umgekehrt) führt dazu, dass GitHub Pages und
  Webspace unterschiedliche Seiten anzeigen. Immer beide ändern, dann `pruefe_php.py` laufen
  lassen.
- **`admin/zugang.php` ist lokal bereits vorhanden** (von einer früheren Einrichtung, gitignored,
  nicht committet) — das echte Passwort dahinter ist nicht bekannt/dokumentiert. Für Tests lieber
  mit `werkzeuge/zugang_erzeugen.py --zufall --ziel <temp-Pfad>` einen eigenen Testzugang erzeugen,
  statt zu raten oder die vorhandene Datei zu verändern.
- **`admin/config.js` entscheidet rein nach Hostname.** Lokal mit `python -m http.server` (siehe
  `.claude/launch.json`, Konfiguration `entwurf`) läuft es unter `localhost` → `webspace` wird
  angeboten, aber ohne laufenden PHP-Server antwortet `api.php` nicht als PHP, sondern wird als
  Text ausgeliefert oder liefert 404 — das fängt `admin.js` ab (Fehlermeldung „Läuft hier PHP?“),
  ist aber beim Testen zu beachten.
- Bilder-Uploads landen über jeden Speicherort unter `bilder/uploads/<name>-<zeitstempel>.jpg` (JPEG,
  verkleinert auf `bildMaxKante`, siehe `admin/config.js`). `admin/api.php` erlaubt beim Speichern
  serverseitig nur Dateinamen, die exakt diesem Muster entsprechen (`aktion=datei`).

## Testen

Siehe Skill **`wistinghausen-test`** (`.claude/skills/wistinghausen-test/SKILL.md`) für den
kompletten Workflow (alle drei Speicherorte ohne echte Zugangsdaten/Live-Netzwerkaufrufe prüfen,
PHP-Fassung lokal starten, Diagnose auf der Live-Seite). Kurzfassung:

```powershell
# Statischer Server für GitHub-Pages-Verhalten (Testmodus + github-Pfad, ohne echten Token)
preview_start { "name": "entwurf" }   # .claude/launch.json, Port 8766

# PHP-Fassung lokal (Webspace-Verhalten inkl. api.php), falls PHP installiert ist
php -S localhost:8767
```

`node --check js/site.js` bzw. `node --check admin/admin.js` als schneller Syntax-Check vor dem
Commit (kein Linter/Formatter eingerichtet, keine automatisierten Tests außer `pruefe_php.py`).
