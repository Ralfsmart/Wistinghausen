<?php
/*
 * Erzeugt alle HTML-Seiten aus inhalt/*.json (PHP-Fassung von werkzeuge/seiten_erzeugen.py).
 *
 * Läuft auf dem Webspace, wenn im Admin gespeichert wird, damit der Text auch fest in den Seiten
 * steht (Suchmaschinen). Beide Fassungen müssen dasselbe Ergebnis liefern; werkzeuge/pruefe_php.py
 * vergleicht sie.
 */

final class SeitenErzeuger
{
    private string $wurzel;
    private string $ziel;
    private array $firma;
    private string $adresse;
    private bool $entwurf;
    private string $version;
    private string $kurzname;

    private const MENUE = [
        ['Start', 'index.html', 'start'],
        ['Küchen', 'kuechen.html', 'kuechen'],
        ['Möbel', 'moebel.html', 'moebel'],
        ['Innenausbau', 'innenausbau.html', 'innenausbau'],
        ['Türen', 'tueren.html', 'tueren'],
        ['Außen', 'aussen.html', 'aussen'],
        ['Fässer', 'faesser.html', 'faesser'],
        ['Kontakt', 'index.html#kontakt', 'kontakt'],
    ];
    private const RUBRIKEN = ['kuechen', 'moebel', 'innenausbau', 'tueren', 'aussen', 'faesser'];
    private const TEXTSEITEN = ['impressum', 'datenschutz'];

    public function __construct(string $wurzel, ?string $ziel = null, array $ueberschreiben = [])
    {
        $this->wurzel = rtrim($wurzel, '/\\');
        $this->ziel = rtrim($ziel ?? $wurzel, '/\\');
        $einst = $this->json($this->wurzel . '/einstellungen.json');
        $einst = array_merge($einst, $ueberschreiben);
        $this->adresse = (string) $einst['adresse'];
        $this->entwurf = (bool) $einst['entwurf'];
        $this->version = (string) $einst['version'];
        $this->kurzname = (string) $einst['firmenname_kurz'];
        $this->firma = $this->laden('firma');
    }

    // ---- Hilfen ---------------------------------------------------------------------------------
    private function json(string $pfad): array
    {
        $roh = @file_get_contents($pfad);
        if ($roh === false) {
            throw new RuntimeException('Datei fehlt: ' . basename($pfad));
        }
        $d = json_decode($roh, true);
        if (!is_array($d)) {
            throw new RuntimeException('Ungültiges JSON: ' . basename($pfad));
        }
        return $d;
    }

    private function laden(string $name): array
    {
        return $this->json($this->wurzel . "/inhalt/$name.json");
    }

    private function esc($text): string
    {
        $t = $this->text($text);
        return str_replace('&#039;', '&#x27;', htmlspecialchars($t, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'));
    }

    /** Wie Python: str(wert or "") */
    private function text($wert): string
    {
        if ($wert === null || $wert === false || $wert === '' || $wert === 0 || $wert === [] ) {
            return '';
        }
        return is_scalar($wert) ? (string) $wert : '';
    }

    private function g(array $a, string $k, $standard = '')
    {
        return array_key_exists($k, $a) && $a[$k] !== null ? $a[$k] : $standard;
    }

    private function liste($wert): array
    {
        return is_array($wert) ? array_values($wert) : [];
    }

    private function gross(string $s): string
    {
        if (function_exists('mb_strtoupper')) {
            return mb_strtoupper($s, 'UTF-8');
        }
        return strtoupper(strtr($s, ['ä' => 'Ä', 'ö' => 'Ö', 'ü' => 'Ü', 'ß' => 'SS']));
    }

    private function telLink($nummer): string
    {
        return 'tel:' . preg_replace('/[^\d+]/', '', $this->text($nummer));
    }

    // ---- Textformatierung (gleiche Regeln wie in js/site.js) -------------------------------------
    private function zeile($text): string
    {
        $h = $this->esc($text);
        $h = preg_replace('/\b(https?:\/\/[\w-]+\.[^\s<“”"]*[^\s<.,;:!?)“”"])/u', '<a href="$1" rel="noopener">$1</a>', $h);
        $h = preg_replace('/(^|[\s(])(www\.[\w-]+\.[^\s<“”"]*[^\s<.,;:!?)“”"])/u', '$1<a href="https://$2" rel="noopener">$2</a>', $h);

        $h = preg_replace_callback('/\{([a-z_]+)\}/', function (array $m): string {
            $k = $m[1];
            if (!array_key_exists($k, $this->firma)) {
                return $m[0];
            }
            $w = $this->esc($this->firma[$k]);
            if ($k === 'telefon' || $k === 'mobil') {
                return '<a href="' . $this->telLink($this->firma[$k]) . '">' . $w . '</a>';
            }
            if ($k === 'email') {
                return '<a href="mailto:' . $w . '">' . $w . '</a>';
            }
            return $w;
        }, $h);

        $h = preg_replace('/\*\*\*([^\s*](?:[^*]*[^\s*])?)\*\*\*/u', '<strong><em>$1</em></strong>', $h);
        $h = preg_replace('/\*\*(.+?)\*\*/u', '<strong>$1</strong>', $h);
        $h = preg_replace('/\*([^\s*](?:[^*]*[^\s*])?)\*/u', '<em>$1</em>', $h);
        $h = preg_replace('/\+\+(.+?)\+\+/u', '<u>$1</u>', $h);
        return preg_replace('/==(.+?)==/u', '<mark class="todo">$1</mark>', $h);
    }

    private function absaetze($text): string
    {
        $t = preg_replace('/^\s+|\s+$/u', '', $this->text($text));
        $teile = [];
        foreach (preg_split('/\n\s*\n/u', $t) as $block) {
            if ($block === '') {
                continue;
            }
            $zeilen = explode("\n", $block);
            $alleListe = true;
            foreach ($zeilen as $z) {
                if (!preg_match('/^\s*- /u', $z)) {
                    $alleListe = false;
                    break;
                }
            }
            if ($alleListe) {
                $li = '';
                foreach ($zeilen as $z) {
                    $li .= '<li>' . $this->zeile(preg_replace('/^\s*- /u', '', $z)) . '</li>';
                }
                $teile[] = '<ul>' . $li . '</ul>';
            } else {
                $teile[] = '<p>' . implode('<br>', array_map(fn($z) => $this->zeile($z), $zeilen)) . '</p>';
            }
        }
        return implode('', $teile);
    }

    /** Füllt Elemente mit data-firma / data-firma-tel / data-firma-mail (wie firmaEinsetzen in site.js). */
    private function firmaEinsetzen(string $html): string
    {
        $html = preg_replace_callback(
            '/<(\w+)([^>]*?\sdata-firma="(\w+)"[^>]*)>[^<]*<\/\1>/u',
            fn(array $m): string => '<' . $m[1] . $m[2] . '>' . $this->esc($this->firma[$m[3]] ?? '') . '</' . $m[1] . '>',
            $html
        );

        // im Seitenkopf steht nur das erste Wort in Großbuchstaben: „MEISTERBETRIEB seit 2004“
        $html = preg_replace_callback(
            '/(<div><b>[^<]*<\/b><span data-firma="zusatz">)([^<]*)(<\/span>)/u',
            function (array $m): string {
                $pos = strpos($m[2], ' ');
                $erstes = $pos === false ? $m[2] : substr($m[2], 0, $pos);
                $rest = $pos === false ? '' : substr($m[2], $pos + 1);
                return $m[1] . $this->gross($erstes) . ($rest !== '' ? ' ' . $rest : '') . $m[3];
            },
            $html
        );

        return preg_replace_callback('/<a\b[^>]*>/u', function (array $m): string {
            $tag = $m[0];
            if (preg_match('/data-firma-tel="(\w+)"/', $tag, $t)) {
                return str_replace('href="#"', 'href="' . $this->telLink($this->firma[$t[1]] ?? null) . '"', $tag);
            }
            if (strpos($tag, 'data-firma-mail') !== false) {
                return str_replace('href="#"', 'href="mailto:' . $this->esc($this->firma['email'] ?? null) . '"', $tag);
            }
            return $tag;
        }, $html);
    }

    // ---- Inhalte der einzelnen Seitentypen (Markup wie in js/site.js) ---------------------------
    private function startseite(array $d): string
    {
        $fotos = '';
        foreach (array_slice($this->liste($this->g($d, 'fotos', [])), 0, 6) as $b) {
            $fotos .= '<img src="' . $this->esc($b['datei'] ?? '') . '" alt="' . $this->esc($b['titel'] ?? '') . '">';
        }
        $punkte = '';
        foreach ($this->liste($this->g($d, 'abschnitt_punkte', [])) as $p) {
            if ($p) {
                $punkte .= '<li>' . $this->esc($p) . '</li>';
            }
        }
        $titel = $this->esc($this->g($d, 'hero_titel'));
        $hero = $this->esc($this->g($d, 'hero_text'));
        $abschnittTitel = $this->esc($this->g($d, 'abschnitt_titel'));
        $text = $this->absaetze($this->g($d, 'abschnitt_text'));
        $ul = $punkte !== '' ? "<ul>$punkte</ul>" : '';
        $besonders = $this->besonderheit($d);
        $ueber = $this->ueberMich($d);
        return "\n" . <<<HTML
      <section class="hero">
        <h1>{$titel}</h1>
        <p>{$hero}</p>
        <a class="btn" data-firma-tel="mobil" href="#"><span data-firma="mobil"></span> anrufen</a>
        <a class="btn ghost" href="#kontakt">Kontakt</a>
      </section>
      <section class="split">
        <div>
          <h2>{$abschnittTitel}</h2>
          {$text}
          {$ul}
        </div>
        <div class="photos">{$fotos}</div>
      </section>
      {$besonders}
      {$ueber}
HTML;
    }

    private function erstesFoto($liste): ?array
    {
        foreach ($this->liste($liste) as $b) {
            if (is_array($b) && !empty($b['datei'])) {
                return $b;
            }
        }
        return null;
    }

    private function besonderheit(array $d): string
    {
        if (!$this->g($d, 'besonderheit_titel')) {
            return '';
        }
        $foto = $this->erstesFoto($this->g($d, 'besonderheit_fotos', []));
        $bild = $foto ? '<img src="' . $this->esc($foto['datei']) . '" alt="' . $this->esc($foto['titel'] ?? '') . '">' : '';
        $link = ($this->g($d, 'besonderheit_link') && $this->g($d, 'besonderheit_link_text'))
            ? '<a class="btn" href="' . $this->esc($d['besonderheit_link']) . '">' . $this->esc($d['besonderheit_link_text']) . '</a>'
            : '';
        $titel = $this->esc($this->g($d, 'besonderheit_titel'));
        $text = $this->absaetze($this->g($d, 'besonderheit_text'));
        return "\n" . <<<HTML
      <section class="besonders">
        {$bild}
        <div>
          <h2>{$titel}</h2>
          {$text}
          {$link}
        </div>
      </section>
HTML;
    }

    private function ueberMich(array $d): string
    {
        if (!$this->g($d, 'ueber_titel') && !$this->g($d, 'ueber_text')) {
            return '';
        }
        $karten = [];
        $nr = 0;
        foreach ($this->liste($this->g($d, 'ueber_fotos', [])) as $b) {
            if (!is_array($b) || empty($b['datei'])) {
                continue;
            }
            if ($nr >= 2) {
                break;
            }
            $unterschrift = !empty($b['titel']) ? '<figcaption>' . $this->esc($b['titel']) . '</figcaption>' : '';
            $klasse = $nr ? 'beleg' : 'portrait';
            $karten[] = '<figure class="' . $klasse . '"><a href="' . $this->esc($b['datei']) . '" target="_blank" rel="noopener">'
                . '<img src="' . $this->esc($b['datei']) . '" alt="' . $this->esc($b['titel'] ?? '') . '"></a>' . $unterschrift . '</figure>';
            $nr++;
        }
        $bild = $karten ? '<div class="ueber-bilder">' . implode('', $karten) . '</div>' : '';
        $titel = $this->esc($this->g($d, 'ueber_titel'));
        $text = $this->absaetze($this->g($d, 'ueber_text'));
        return "\n" . <<<HTML
      <section class="ueber" id="ueber-mich">
        {$bild}
        <div>
          <h2>{$titel}</h2>
          {$text}
        </div>
      </section>
HTML;
    }

    private function bildKarte(array $b): string
    {
        $titelText = $this->g($b, 'titel');
        $titel = $titelText ? '<b>' . $this->esc($titelText) . '</b>' : '';
        $unterschrift = ($titelText || $this->g($b, 'beschreibung'))
            ? '<figcaption>' . $titel . $this->esc($this->g($b, 'beschreibung')) . '</figcaption>' : '';
        $datei = $this->esc($b['datei']);
        $alt = $this->esc($titelText);
        return "\n" . <<<HTML
      <figure>
        <button type="button" data-voll="{$datei}" aria-label="Foto vergrößern: {$alt}">
          <img src="{$datei}" alt="{$alt}" loading="lazy">
        </button>
        {$unterschrift}
      </figure>
HTML;
    }

    private function rubrik(string $kennung, array $d): string
    {
        $leistungen = '';
        foreach ($this->liste($this->g($d, 'leistungen', [])) as $l) {
            if ($l) {
                $leistungen .= '<li>' . $this->esc($l) . '</li>';
            }
        }
        $bilder = '';
        foreach ($this->liste($this->g($d, 'bilder', [])) as $b) {
            if (is_array($b) && !empty($b['datei'])) {
                $bilder .= $this->bildKarte($b);
            }
        }
        $hinweis = $this->g($d, 'beispieltext')
            ? '<p class="note">Beispieltext: Bitte an die eigene Arbeitsweise anpassen und danach im Admin-Bereich den Haken bei „Beispieltext“ entfernen.</p>'
            : '';
        $untertitel = $this->g($d, 'untertitel') ? '<p class="lead">' . $this->esc($d['untertitel']) . '</p>' : '';
        $liste = $leistungen !== '' ? '<aside class="r-list"><h2>Leistungen</h2><ul>' . $leistungen . '</ul></aside>' : '';
        $galerie = $bilder !== ''
            ? '<h2>Einblicke</h2><p class="galerie-hinweis"><span class="nur-maus">Für Details einfach auf ein Foto klicken. Mit dem Mausrad lässt sich hinein- und herauszoomen.</span><span class="nur-touch">Für Details einfach auf ein Foto tippen. Mit zwei Fingern lässt sich hinein- und herauszoomen.</span></p><div class="galerie">' . $bilder . '</div>'
            : '';
        $titel = $this->esc($this->g($d, 'titel'));
        $einleitung = $this->absaetze($this->g($d, 'einleitung'));
        return "\n" . <<<HTML
      <div class="r-head">
        <span class="r-icon" style="background-image:url(icons/{$kennung}.svg)" aria-hidden="true"></span>
        <div>
          <h1>{$titel}</h1>
          {$untertitel}
        </div>
      </div>
      {$hinweis}
      <div class="r-body">
        <div class="r-text">{$einleitung}</div>
        {$liste}
      </div>
      {$galerie}
      <section class="cta">
        <span class="cta-leiste wood" aria-hidden="true"></span>
        <div><h2 data-firma="aufruf_titel"></h2><p data-firma="aufruf_text"></p></div>
        <div class="cta-knoepfe">
          <a class="btn" data-firma-tel="mobil" href="#"><span data-firma="mobil"></span></a>
          <a class="btn ghost" data-firma-mail href="#">E-Mail schreiben</a>
        </div>
      </section>
HTML;
    }

    private function textseite(array $d): string
    {
        $teile = '';
        foreach ($this->liste($this->g($d, 'abschnitte', [])) as $a) {
            if (!is_array($a)) {
                continue;
            }
            if (!empty($a['ueberschrift'])) {
                $teile .= '<h2>' . $this->esc($a['ueberschrift']) . '</h2>';
            }
            $teile .= $this->absaetze($this->g($a, 'text'));
        }
        $hinweis = $this->g($d, 'hinweis') ? '<p class="note">' . $this->esc($d['hinweis']) . '</p>' : '';
        $stand = $this->g($d, 'stand') ? '<p><em>Stand: ' . $this->esc($d['stand']) . '</em></p>' : '';
        $titel = $this->esc($this->g($d, 'titel'));
        return "\n" . <<<HTML
      <h1>{$titel}</h1>
      {$hinweis}
      {$teile}
      {$stand}
HTML;
    }

    private function kontakt(string $karte): string
    {
        $html = <<<'HTML'

<div class="strip wood" aria-hidden="true"></div>
<section class="wrap" id="kontakt" style="padding-top:48px">
  <h2>Kontakt</h2>
  <div class="kontakt-reihe">
  <div class="contact">
    <div><h3 class="kontakt-logo"><img src="bilder/logo-wistinghausen.png" width="1182" height="460" alt="Schreinerei A. v. Wistinghausen" loading="lazy"></h3><p><span data-firma="strasse"></span><br><span data-firma="ort"></span></p></div>
    <div><h3>Werkstatt</h3><p><span data-firma="werkstatt_strasse"></span><br><span data-firma="werkstatt_ort"></span></p></div>
    <div><h3>Telefon</h3><p><a data-firma-tel="telefon" data-firma="telefon" href="#"></a><br>Mobil <a data-firma-tel="mobil" data-firma="mobil" href="#"></a></p></div>
    <div><h3>E-Mail</h3><p><a data-firma-mail data-firma="email" href="#"></a></p></div>
  </div>
  <figure class="anfahrt">
    <img src="bilder/anfahrt.svg" width="800" height="560" loading="lazy"
         alt="Anfahrtsskizze: von der B31-Ausfahrt Uhldingen-Mühlhofen über die Bahnhofstraße nach Mühlhofen zur Unteren Weitfeld Straße">
    <figcaption><a href="{KARTE}" target="_blank" rel="noopener">Route zur Schreinerei v. Wistinghausen in Google Maps ↗</a></figcaption>
  </figure>
  </div>
</section>
HTML;
        return str_replace('{KARTE}', $karte, $html);
    }

    // ---- Strukturierte Firmendaten für Google (schema.org) ---------------------------------------
    private function firmendatenJsonLd(): string
    {
        $ort = $this->text($this->firma['ort'] ?? '');
        $plz = preg_match('/^\s*(\d{5})\s+(.+)/u', $ort, $m) ? $m : null;
        $daten = [
            '@context' => 'https://schema.org',
            '@type' => 'HomeAndConstructionBusiness',
            'name' => $this->firma['name'] ?? null,
            'description' => 'Schreinerei und Meisterbetrieb: Küchen, Möbel, Innenausbau, Türen, Außenholzbau und Rührfässer.',
            'url' => $this->adresse,
            'logo' => $this->adresse . 'bilder/Wappen-2.gif',
            'image' => $this->adresse . 'bilder/kuechen-1.jpg',
            'telephone' => $this->firma['mobil'] ?? null,
            'email' => $this->firma['email'] ?? null,
            'address' => [
                '@type' => 'PostalAddress',
                'streetAddress' => $this->firma['strasse'] ?? null,
                'postalCode' => $plz ? $plz[1] : '',
                'addressLocality' => $plz ? $plz[2] : ($this->firma['ort'] ?? null),
                'addressCountry' => 'DE',
            ],
        ];
        $json = json_encode($daten, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
        // PHP rückt mit 4 Leerzeichen ein, die Python-Fassung mit 2
        $json = preg_replace_callback('/^( +)/m', fn(array $m): string => str_repeat(' ', intdiv(strlen($m[1]), 2)), $json);
        return str_replace('</', '<\\/', $json);
    }

    // ---- Seitengerüst ------------------------------------------------------------------------------
    private function seite(string $datei, string $kennung, string $titel, string $beschreibung, string $hauptteil, string $zusatzKopf = ''): string
    {
        $menue = [];
        foreach (self::MENUE as [$name, $ziel, $icon]) {
            $aktiv = $ziel === $datei ? ' aria-current="page"' : '';
            $menue[] = '        <li><a href="' . $ziel . '"' . $aktiv . '><span class="ni" style="background-image:url(icons/' . $icon . '.svg?v=' . $this->version . ')"'
                . ' aria-hidden="true"></span>' . $name . '</a></li>';
        }
        $menue = implode("\n", $menue);
        $url = $this->adresse . ($datei === 'index.html' ? '' : $datei);
        $robots = $this->entwurf ? '<meta name="robots" content="noindex">' : '';
        $t = $this->esc($titel);
        $b = $this->esc($beschreibung);
        $v = $this->version;
        $adr = $this->adresse;
        $kurz = $this->kurzname;
        $html = <<<HTML
<!doctype html>
<html lang="de" data-basis="">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{$t}</title>
<link rel="icon" href="favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="favicon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="description" content="{$b}">
{$robots}
<link rel="canonical" href="{$url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="{$kurz}">
<meta property="og:title" content="{$t}">
<meta property="og:description" content="{$b}">
<meta property="og:url" content="{$url}">
<meta property="og:image" content="{$adr}bilder/kuechen-1.jpg">
<link rel="stylesheet" href="css/style.css?v={$v}">
<script src="js/site.js?v={$v}" defer></script>{$zusatzKopf}
</head>
<body class="nav-badges" data-seite="{$kennung}">

<header class="site wood">
  <div class="wrap top">
    <a class="brand" href="index.html">
      <img src="bilder/Wappen-2.gif" alt="Wappen der Schreinerei">
      <div><b>{$kurz}</b><span data-firma="zusatz"></span></div>
    </a>
    <button class="menu-btn" aria-expanded="false" onclick="const n=document.querySelector('nav.main');this.setAttribute('aria-expanded',n.classList.toggle('open'))">☰ Menü</button>
    <nav class="main" aria-label="Hauptmenü">
      <ul>
{$menue}
      </ul>
    </nav>
  </div>
</header>

{$hauptteil}

<footer class="wood">
  <div class="wrap">
    <span>© <span data-firma="name"></span> · <span data-firma="zusatz"></span></span>
    <span><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></span>
  </div>
</footer>
</body>
</html>

HTML;
        return $this->firmaEinsetzen($html);
    }

    private function seo(array $d, string $titelAuto, ?string $beschreibungAuto): array
    {
        $titel = trim($this->text($this->g($d, 'seo_titel')) ?: $titelAuto);
        $beschr = trim($this->text($this->g($d, 'seo_beschreibung')) ?: ($beschreibungAuto ?? ''));
        return [$titel, $beschr];
    }

    // ---- alles erzeugen ---------------------------------------------------------------------------------
    /** @return array<string,string> Dateiname => Inhalt */
    public function seiten(): array
    {
        $aus = [];
        $k = $this->kurzname;
        $f = $this->firma;

        $d = $this->laden('start');
        [$titel, $beschr] = $this->seo($d, "$k – Schreiner-Meisterbetrieb am Bodensee", $this->text($this->g($d, 'hero_text')));
        $ld = "\n" . '<script type="application/ld+json">' . "\n" . $this->firmendatenJsonLd() . "\n" . '</script>';
        $suche = $this->text($f['name'] ?? '') . ', ' . $this->text($f['strasse'] ?? '') . ', ' . $this->text($f['ort'] ?? '');
        $karte = 'https://www.google.com/maps/search/?api=1&amp;query=' . str_replace('%20', '+', rawurlencode($suche));
        $aus['index.html'] = $this->seite('index.html', 'start', $titel, $beschr,
            '<main class="wrap" id="inhalt">' . $this->startseite($d) . "\n</main>\n" . $this->kontakt($karte), $ld);

        foreach (self::RUBRIKEN as $kennung) {
            $d = $this->laden($kennung);
            [$titel, $beschr] = $this->seo($d, $this->text($this->g($d, 'titel')) . " | $k", $this->text($this->g($d, 'untertitel')));
            $aus["$kennung.html"] = $this->seite("$kennung.html", $kennung, $titel, $beschr,
                '<main class="wrap rubrik" id="inhalt">' . $this->rubrik($kennung, $d) . "\n</main>");
        }

        foreach (self::TEXTSEITEN as $kennung) {
            $d = $this->laden($kennung);
            $t = $this->text($this->g($d, 'titel'));
            $aus["$kennung.html"] = $this->seite("$kennung.html", $kennung, "$t | $k", "$t der " . $this->text($f['name'] ?? ''),
                '<main class="wrap legal" id="inhalt">' . $this->textseite($d) . "\n</main>");
        }

        $heute = date('Y-m-d');
        $seiten = array_merge(['index.html'], array_map(fn($x) => "$x.html", array_merge(self::RUBRIKEN, self::TEXTSEITEN)));
        $urls = [];
        foreach ($seiten as $s) {
            $urls[] = '  <url><loc>' . $this->adresse . ($s === 'index.html' ? '' : $s) . '</loc><lastmod>' . $heute . '</lastmod></url>';
        }
        $aus['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>' . "\n"
            . '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n" . implode("\n", $urls) . "\n</urlset>\n";
        $regeln = $this->entwurf ? 'Disallow: /' : "Disallow: /admin/\nDisallow: /werkzeuge/";
        $aus['robots.txt'] = "User-agent: *\n$regeln\n\nSitemap: {$this->adresse}sitemap.xml\n";
        return $aus;
    }

    /** Schreibt alle Seiten. Zuerst wird alles im Speicher erzeugt, damit ein Fehler die alten Seiten nicht zerstört. */
    public function erzeugen(): array
    {
        $dateien = $this->seiten();
        foreach ($dateien as $name => $inhalt) {
            $pfad = $this->ziel . '/' . $name;
            $tmp = $pfad . '.tmp' . getmypid();
            if (file_put_contents($tmp, $inhalt, LOCK_EX) === false || !@rename($tmp, $pfad)) {
                @unlink($tmp);
                if (file_put_contents($pfad, $inhalt, LOCK_EX) === false) {
                    throw new RuntimeException("Seite konnte nicht geschrieben werden: $name");
                }
            }
        }
        return array_keys($dateien);
    }
}

// Aufruf von der Kommandozeile (zum Testen): php admin/seiten.php [ziel]
if (PHP_SAPI === 'cli' && realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    $wurzel = dirname(__DIR__);
    $ziel = $argv[1] ?? null;
    if ($ziel !== null && !is_dir($ziel)) {
        mkdir($ziel, 0777, true);
    }
    $liste = (new SeitenErzeuger($wurzel, $ziel))->erzeugen();
    echo 'erzeugt: ' . implode(', ', $liste) . "\n";
}
