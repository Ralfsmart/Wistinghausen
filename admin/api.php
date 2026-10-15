<?php
/*
 * Speicher-Endpunkt für den Admin-Bereich auf dem eigenen Webspace.
 *
 * Tut dasselbe wie die GitHub-Anbindung: Inhalte (inhalt/*.json) lesen und speichern, Fotos hochladen.
 * Zusätzlich erzeugt er nach jedem Speichern die Seiten neu (Texte stehen fest im HTML, für Suchmaschinen).
 *
 * Voraussetzung: admin/zugang.php (Passwort-Hash, wird mit werkzeuge/zugang_erzeugen.py angelegt).
 * Ohne diese Datei ist der Admin-Bereich auf dem Webspace gesperrt.
 */
declare(strict_types=1);

// Keine PHP-Fehlermeldungen (mit Dateipfaden) an Besucher ausgeben
ini_set('display_errors', '0');
ini_set('html_errors', '0');
error_reporting(E_ALL);
set_exception_handler(function (Throwable $e): void {
    error_log('api.php: ' . $e->getMessage());
    if (!headers_sent()) {
        http_response_code(500);
        header('Content-Type: application/json; charset=utf-8');
        header('Cache-Control: no-store');
    }
    echo json_encode(['fehler' => 'Auf dem Server ist ein Fehler aufgetreten. Bitte noch einmal versuchen.'], JSON_UNESCAPED_UNICODE);
});

require_once __DIR__ . '/seiten.php';

const MAX_JSON_BYTES = 600 * 1024;
const MAX_FOTO_BYTES = 6 * 1024 * 1024;
const MAX_FOTO_KANTE = 6000;
const SITZUNG_SEKUNDEN = 8 * 3600;
const MAX_VERSUCHE = 8;
const SPERRE_SEKUNDEN = 15 * 60;
const SICHERUNGEN_JE_DATEI = 15;
const SEITEN = ['start', 'firma', 'kuechen', 'moebel', 'innenausbau', 'tueren', 'aussen', 'faesser', 'impressum', 'datenschutz'];

$WURZEL = dirname(__DIR__);

// ---- Hilfen -----------------------------------------------------------------------------------------
function antwort(int $status, array $daten): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($daten, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function fehler(int $status, string $text, array $zusatz = []): never
{
    antwort($status, ['fehler' => $text] + $zusatz);
}

function jsonText(array $daten): string
{
    $json = json_encode($daten, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT | JSON_PRESERVE_ZERO_FRACTION);
    // 2 statt 4 Leerzeichen Einrückung, wie die übrigen Dateien im Projekt
    $json = preg_replace_callback('/^( +)/m', fn(array $m): string => str_repeat(' ', intdiv(strlen($m[1]), 2)), $json);
    return $json . "\n";
}

function atomarSchreiben(string $pfad, string $inhalt): void
{
    $tmp = $pfad . '.tmp' . getmypid();
    if (file_put_contents($tmp, $inhalt, LOCK_EX) === false) {
        @unlink($tmp);
        fehler(500, 'Die Datei konnte nicht geschrieben werden. Fehlen die Schreibrechte für den Ordner?');
    }
    if (!@rename($tmp, $pfad)) {
        // manche Hoster erlauben rename über bestehende Dateien nicht
        $ok = file_put_contents($pfad, $inhalt, LOCK_EX) !== false;
        @unlink($tmp);
        if (!$ok) {
            fehler(500, 'Die Datei konnte nicht geschrieben werden. Fehlen die Schreibrechte für den Ordner?');
        }
    }
}

function eingabe(): array
{
    $roh = file_get_contents('php://input');
    if ($roh === false || $roh === '') {
        return [];
    }
    $d = json_decode($roh, true);
    return is_array($d) ? $d : [];
}

function versionVon(string $inhalt): string
{
    return substr(sha1($inhalt), 0, 20);
}

// ---- Sitzung ----------------------------------------------------------------------------------------
$https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https');
session_name('wst_admin');
session_set_cookie_params([
    'lifetime' => 0,
    'path' => rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? '/admin/api.php'), '/') . '/',
    'secure' => $https,
    'httponly' => true,
    'samesite' => 'Strict',
]);
ini_set('session.use_strict_mode', '1');
session_start();

// ---- Zugangsdaten -----------------------------------------------------------------------------------
$zugangsDatei = __DIR__ . '/zugang.php';
$zugang = is_file($zugangsDatei) ? (require $zugangsDatei) : null;
$eingerichtet = is_array($zugang) && isset($zugang['salt'], $zugang['hash'], $zugang['iterationen']);

$aktion = (string) ($_GET['aktion'] ?? '');
$methode = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$body = $methode === 'POST' ? eingabe() : [];
if ($methode === 'POST') {
    $aktion = (string) ($body['aktion'] ?? $aktion);
}

$angemeldet = !empty($_SESSION['ok']) && (time() - (int) ($_SESSION['zeit'] ?? 0)) < SITZUNG_SEKUNDEN;

if ($aktion === 'status') {
    antwort(200, [
        'eingerichtet' => $eingerichtet,
        'angemeldet' => $angemeldet,
        'token' => $angemeldet ? $_SESSION['token'] : null,
    ]);
}

if (!$eingerichtet) {
    fehler(503, 'Der Admin-Bereich ist auf diesem Webspace noch nicht eingerichtet (Datei admin/zugang.php fehlt).');
}

// ---- Anmeldung --------------------------------------------------------------------------------------
if ($aktion === 'login') {
    if ($methode !== 'POST' || ($_SERVER['HTTP_X_ADMIN'] ?? '') !== '1') {
        fehler(400, 'Ungültige Anfrage.');
    }
    $sperrDatei = __DIR__ . '/_sperre.json';
    $schluessel = hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '') . '|' . $zugang['salt']);
    $sperre = is_file($sperrDatei) ? (json_decode((string) file_get_contents($sperrDatei), true) ?: []) : [];
    $jetzt = time();
    foreach ($sperre as $k => $e) {   // Altes aufräumen
        if (($e['t'] ?? 0) + SPERRE_SEKUNDEN < $jetzt) {
            unset($sperre[$k]);
        }
    }
    $eintrag = $sperre[$schluessel] ?? ['n' => 0, 't' => $jetzt];
    if ($eintrag['n'] >= MAX_VERSUCHE) {
        $rest = max(1, (int) ceil(($eintrag['t'] + SPERRE_SEKUNDEN - $jetzt) / 60));
        fehler(429, "Zu viele Fehlversuche. Bitte in $rest Minuten noch einmal versuchen.");
    }
    $passwort = (string) ($body['passwort'] ?? '');
    $gepruft = hash_pbkdf2('sha256', $passwort, (string) $zugang['salt'], (int) $zugang['iterationen'], 64, false);
    if ($passwort === '' || !hash_equals((string) $zugang['hash'], $gepruft)) {
        $eintrag['n']++;
        $eintrag['t'] = $eintrag['t'] ?? $jetzt;
        $sperre[$schluessel] = $eintrag;
        @file_put_contents($sperrDatei, json_encode($sperre), LOCK_EX);
        usleep(700000);
        fehler(401, 'Das Passwort stimmt nicht.');
    }
    unset($sperre[$schluessel]);
    @file_put_contents($sperrDatei, json_encode($sperre), LOCK_EX);
    session_regenerate_id(true);
    $_SESSION['ok'] = true;
    $_SESSION['zeit'] = time();
    $_SESSION['token'] = bin2hex(random_bytes(24));
    antwort(200, ['angemeldet' => true, 'token' => $_SESSION['token']]);
}

// ab hier nur angemeldet ------------------------------------------------------------------------------
if (!$angemeldet) {
    fehler(401, 'Bitte anmelden.');
}
$_SESSION['zeit'] = time();

if ($methode === 'POST') {
    $token = (string) ($_SERVER['HTTP_X_CSRF_TOKEN'] ?? '');
    if ($token === '' || !hash_equals((string) $_SESSION['token'], $token)) {
        fehler(403, 'Die Anfrage wurde abgelehnt (Sicherheitsprüfung). Bitte Seite neu laden.');
    }
}

switch ($aktion) {
    case 'logout':
        $_SESSION = [];
        session_destroy();
        antwort(200, ['angemeldet' => false]);

    case 'diagnose':
        $ordner = ['inhalt' => $WURZEL . '/inhalt', 'bilder' => $WURZEL . '/bilder', 'wurzel (Seiten)' => $WURZEL];
        $schreibbar = [];
        foreach ($ordner as $name => $pfad) {
            $schreibbar[$name] = is_dir($pfad) && is_writable($pfad);
        }
        antwort(200, ['php' => PHP_VERSION, 'schreibbar' => $schreibbar, 'seiten_ok' => is_file($WURZEL . '/einstellungen.json')]);

    case 'lesen':
        $pfad = (string) ($_GET['pfad'] ?? '');
        $name = pfadPruefen($pfad);
        $datei = $WURZEL . '/inhalt/' . $name . '.json';
        $inhalt = @file_get_contents($datei);
        if ($inhalt === false) {
            fehler(404, "Die Datei $pfad wurde nicht gefunden.");
        }
        $daten = json_decode($inhalt, true);
        if (!is_array($daten)) {
            fehler(500, "Die Datei $pfad ist beschädigt.");
        }
        antwort(200, ['daten' => $daten, 'version' => versionVon($inhalt)]);

    case 'schreiben':
        if ($methode !== 'POST') {
            fehler(405, 'Nur POST erlaubt.');
        }
        $name = pfadPruefen((string) ($body['pfad'] ?? ''));
        $text = (string) ($body['inhalt'] ?? '');
        if (strlen($text) > MAX_JSON_BYTES) {
            fehler(413, 'Der Inhalt ist zu groß.');
        }
        $daten = json_decode($text, true);
        if (!is_array($daten)) {
            fehler(422, 'Der Inhalt ist kein gültiges JSON.');
        }
        $datei = $WURZEL . '/inhalt/' . $name . '.json';
        $alt = is_file($datei) ? (string) file_get_contents($datei) : '';
        $erwartet = (string) ($body['version'] ?? '');
        if ($alt !== '' && $erwartet !== '' && !hash_equals(versionVon($alt), $erwartet)) {
            fehler(409, 'Die Datei wurde inzwischen an anderer Stelle geändert. Bitte die Seite neu laden und die Änderung wiederholen.');
        }
        if ($alt !== '') {
            sichern($WURZEL, $name, $alt);
        }
        $neu = jsonText($daten);
        atomarSchreiben($datei, $neu);
        $antwort = ['ok' => true, 'version' => versionVon($neu)];
        try {
            $antwort['seiten'] = count((new SeitenErzeuger($WURZEL))->erzeugen());
        } catch (Throwable $e) {
            $antwort['warnung'] = 'Gespeichert, aber die Seiten konnten nicht neu erzeugt werden: ' . $e->getMessage();
        }
        antwort(200, $antwort);

    case 'seiten':
        if ($methode !== 'POST') {
            fehler(405, 'Nur POST erlaubt.');
        }
        try {
            antwort(200, ['ok' => true, 'seiten' => count((new SeitenErzeuger($WURZEL))->erzeugen())]);
        } catch (Throwable $e) {
            fehler(500, 'Die Seiten konnten nicht neu erzeugt werden: ' . $e->getMessage());
        }

    case 'datei':
        if ($methode !== 'POST') {
            fehler(405, 'Nur POST erlaubt.');
        }
        $pfad = (string) ($body['pfad'] ?? '');
        if (!preg_match('#^bilder/uploads/[a-z0-9][a-z0-9-]{0,60}\.jpg$#', $pfad)) {
            fehler(422, 'Ungültiger Dateiname für das Foto.');
        }
        $bin = base64_decode((string) ($body['base64'] ?? ''), true);
        if ($bin === false || $bin === '') {
            fehler(422, 'Das Foto konnte nicht gelesen werden.');
        }
        if (strlen($bin) > MAX_FOTO_BYTES) {
            fehler(413, 'Das Foto ist zu groß (höchstens 6 MB).');
        }
        if (substr($bin, 0, 3) !== "\xFF\xD8\xFF") {
            fehler(422, 'Es sind nur JPEG-Fotos erlaubt.');
        }
        $info = @getimagesizefromstring($bin);
        if (!$info || $info[2] !== IMAGETYPE_JPEG || $info[0] < 1 || $info[1] < 1 || $info[0] > MAX_FOTO_KANTE || $info[1] > MAX_FOTO_KANTE) {
            fehler(422, 'Das Foto ist kein gültiges JPEG oder zu groß (höchstens ' . MAX_FOTO_KANTE . ' Pixel).');
        }
        $ziel = $WURZEL . '/' . $pfad;
        if (is_file($ziel)) {
            fehler(409, 'Ein Foto mit diesem Namen gibt es schon.');
        }
        $ordner = dirname($ziel);
        if (!is_dir($ordner) && !@mkdir($ordner, 0755, true) && !is_dir($ordner)) {
            fehler(500, 'Der Ordner für Fotos konnte nicht angelegt werden.');
        }
        atomarSchreiben($ziel, $bin);
        antwort(200, ['ok' => true, 'pfad' => $pfad, 'breite' => $info[0], 'hoehe' => $info[1]]);

    default:
        fehler(404, 'Unbekannte Aktion.');
}

// ---- Funktionen, die oben benutzt werden ---------------------------------------------------------------
function pfadPruefen(string $pfad): string
{
    if (!preg_match('#^inhalt/([a-z]+)\.json$#', $pfad, $m) || !in_array($m[1], SEITEN, true)) {
        fehler(422, 'Dieser Pfad ist nicht erlaubt.');
    }
    return $m[1];
}

function sichern(string $wurzel, string $name, string $alt): void
{
    $ordner = $wurzel . '/inhalt/_sicherung';
    if (!is_dir($ordner) && !@mkdir($ordner, 0755, true)) {
        return;   // Sicherung ist nur ein Zusatz, kein Grund zum Abbruch
    }
    @file_put_contents($ordner . '/' . $name . '-' . date('Ymd-His') . '.json', $alt, LOCK_EX);
    $alle = glob($ordner . '/' . $name . '-*.json') ?: [];
    rsort($alle);
    foreach (array_slice($alle, SICHERUNGEN_JE_DATEI) as $weg) {
        @unlink($weg);
    }
}
