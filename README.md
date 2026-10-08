# Schreinerei Wistinghausen – Website

Neue Website für www.schreinerei-wistinghausen.de. Reines HTML/CSS/JavaScript – läuft auf
GitHub Pages und auf jedem Webspace (FTP-Upload genügt).

## Aufbau
- `index.html`, `kuechen.html`, `moebel.html`, `innenausbau.html`, `tueren.html`, `aussen.html`,
  `faesser.html`, `impressum.html`, `datenschutz.html` – Seitengerüste (erzeugt, nicht von Hand ändern)
- `inhalt/*.json` – **alle Texte, Fotos und Bildbeschreibungen**; werden über `/admin` gepflegt
- `js/site.js` – setzt die Inhalte in die Seiten ein, Foto-Großansicht
- `admin/` – Admin-Bereich zum Bearbeiten (Texte, Stichpunkte, Fotos hochladen/sortieren/beschreiben, Kontaktdaten)
- `css/style.css`, `fonts/`, `icons/` – Gestaltung, lokale Schriften, Menüsymbole
- `bilder/` – Fotos; neue Uploads landen in `bilder/uploads/`
- `werkzeuge/seiten_erzeugen.py` – erzeugt die Seitengerüste neu (nur bei Änderungen an Menü/Aufbau/Impressum/Datenschutz;
  Impressum- und Datenschutztext liegen in `werkzeuge/teile/`)

## Admin-Bereich
Aufruf: `<website>/admin/`. Speicherorte (siehe `admin/config.js`):
- **GitHub**: speichert direkt ins Repository. Benötigt einen *Fine-grained Personal Access Token*,
  beschränkt auf dieses Repository mit der Berechtigung **Contents: Read and write**.
  GitHub Pages zeigt Änderungen nach 1–2 Minuten.
- **Testmodus**: alles ausprobieren, nichts wird gespeichert.
- *Später*: **Webspace** – kleines PHP-Skript auf dem eigenen Server, dann ohne GitHub.

## Offen
Neue große Fotos, Beispieltexte anpassen, Impressum/Datenschutz prüfen (gelb markiert),
Speicherort „Webspace“ für den eigenen Hoster, `noindex` vor dem Livegang entfernen.
