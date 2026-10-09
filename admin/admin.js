/* Admin-Bereich der Schreinerei-Website.
   Bearbeitet die Dateien in /inhalt/*.json und lädt Fotos hoch.
   Das Speichern übernimmt ein austauschbarer "Speicher" (GitHub jetzt, Webspace/PHP später). */
(() => {
  'use strict';
  const CFG = window.ADMIN_CONFIG;
  const $ = s => document.querySelector(s);

  /* ================= Bereiche und ihre Felder ================= */
  const RUBRIK_FELDER = [
    { gruppe: 'Kopf der Seite' },
    { key: 'titel', label: 'Überschrift', typ: 'text' },
    { key: 'untertitel', label: 'Untertitel', typ: 'text', hilfe: 'Ein kurzer Satz unter der Überschrift. Erscheint auch bei Google.' },
    { key: 'beispieltext', label: 'Hinweis „Beispieltext“ auf der Seite anzeigen', typ: 'haken' },
    { gruppe: 'Einleitung' },
    { key: 'einleitung', label: 'Einleitungstext', typ: 'langtext', format: true, hilfe: 'Eine leere Zeile beginnt einen neuen Absatz.' },
    { gruppe: 'Leistungen' },
    { key: 'leistungen', label: 'Stichpunkte', typ: 'liste', neu: 'Stichpunkt hinzufügen' },
    { gruppe: 'Fotos' },
    { key: 'bilder', label: 'Fotos', typ: 'fotos', beschreibung: true },
    { gruppe: 'Google-Suche' },
    { key: 'seo_titel', label: 'Seitentitel bei Google', typ: 'text',
      hilfe: 'Erscheint als blaue Überschrift in den Suchergebnissen. Ideal: bis 60 Zeichen, mit Ort, z. B. „Einbauküchen nach Maß in Salem | Schreinerei Wistinghausen“. Leer lassen = automatisch.' },
    { key: 'seo_beschreibung', label: 'Beschreibung bei Google', typ: 'textfeld',
      hilfe: 'Der kurze Text unter dem Titel in den Suchergebnissen. Ideal: 120–155 Zeichen. Leer lassen = Untertitel bzw. Einstiegstext.' },
  ];

  const FORMAT_HILFE = 'Eine leere Zeile beginnt einen neuen Absatz. Fett, Markierung, Aufzählung und Kontaktdaten gibt es über den Knöpfen oberhalb des Feldes.';

  const TEXTSEITE_FELDER = [
    { typ: 'info', text: FORMAT_HILFE },
    { gruppe: 'Kopf' },
    { key: 'titel', label: 'Überschrift', typ: 'text' },
    { key: 'hinweis', label: 'Gelber Hinweis oben', typ: 'textfeld', hilfe: 'Leer lassen, wenn kein Hinweis erscheinen soll.' },
    { gruppe: 'Abschnitte' },
    { key: 'abschnitte', label: 'Abschnitte', typ: 'abschnitte' },
    { gruppe: 'Abschluss' },
    { key: 'stand', label: 'Stand (z. B. „Oktober 2026“)', typ: 'text', hilfe: 'Leer lassen, um keinen Stand anzuzeigen.' },
  ];

  const BEREICHE = [
    { id: 'start', name: 'Startseite', icon: 'start', seite: 'index.html', felder: [
      { gruppe: 'Großer Einstieg' },
      { key: 'hero_titel', label: 'Große Überschrift', typ: 'text' },
      { key: 'hero_text', label: 'Text darunter', typ: 'textfeld' },
      { gruppe: 'Abschnitt mit Fotos' },
      { key: 'abschnitt_titel', label: 'Überschrift', typ: 'text' },
      { key: 'abschnitt_text', label: 'Text', typ: 'textfeld', format: true, hilfe: 'Eine leere Zeile beginnt einen neuen Absatz.' },
      { key: 'abschnitt_punkte', label: 'Stichpunkte', typ: 'liste', neu: 'Stichpunkt hinzufügen' },
      { key: 'fotos', label: 'Fotos (die ersten 6 werden gezeigt)', typ: 'fotos', beschreibung: false },
      { gruppe: 'Hervorgehobener Kasten (z. B. Rührfässer)' },
      { key: 'besonderheit_titel', label: 'Überschrift', typ: 'text', hilfe: 'Leer lassen, um den Kasten auszublenden.' },
      { key: 'besonderheit_text', label: 'Text', typ: 'textfeld', format: true, hilfe: FORMAT_HILFE },
      { key: 'besonderheit_link', label: 'Knopf führt zu', typ: 'auswahl', optionen: [
        ['', '– kein Knopf –'], ['kuechen.html', 'Küchen'], ['moebel.html', 'Möbel'], ['innenausbau.html', 'Innenausbau'],
        ['tueren.html', 'Türen'], ['aussen.html', 'Außen'], ['faesser.html', 'Fässer'], ['#kontakt', 'Kontakt'] ] },
      { key: 'besonderheit_link_text', label: 'Beschriftung des Knopfes', typ: 'text' },
      { key: 'besonderheit_fotos', label: 'Foto (das erste wird gezeigt)', typ: 'fotos', beschreibung: false },
      { gruppe: 'Über mich' },
      { key: 'ueber_titel', label: 'Überschrift', typ: 'text', hilfe: 'Überschrift und Text leer lassen, um den Abschnitt auszublenden.' },
      { key: 'ueber_text', label: 'Text', typ: 'langtext', format: true, hilfe: FORMAT_HILFE },
      { key: 'ueber_fotos', label: 'Foto (das erste wird gezeigt; der Titel erscheint als Bildunterschrift)', typ: 'fotos', beschreibung: false },
      { gruppe: 'Google-Suche' },
      { key: 'seo_titel', label: 'Seitentitel bei Google', typ: 'text',
        hilfe: 'Erscheint als blaue Überschrift in den Suchergebnissen. Ideal: bis 60 Zeichen, mit Ort, z. B. „Einbauküchen nach Maß in Salem | Schreinerei Wistinghausen“. Leer lassen = automatisch.' },
      { key: 'seo_beschreibung', label: 'Beschreibung bei Google', typ: 'textfeld',
        hilfe: 'Der kurze Text unter dem Titel in den Suchergebnissen. Ideal: 120–155 Zeichen. Leer lassen = Untertitel bzw. Einstiegstext.' },
    ] },
    { id: 'firma', name: 'Kontaktdaten', icon: 'kontakt', seite: 'index.html#kontakt', felder: [
      { gruppe: 'Firma' },
      { key: 'name', label: 'Firmenname', typ: 'text' },
      { key: 'inhaber', label: 'Inhaber', typ: 'text' },
      { key: 'zusatz', label: 'Zusatz unter dem Namen', typ: 'text' },
      { key: 'strasse', label: 'Straße', typ: 'text' },
      { key: 'ort', label: 'PLZ und Ort', typ: 'text' },
      { gruppe: 'Werkstatt' },
      { key: 'werkstatt_strasse', label: 'Straße', typ: 'text' },
      { key: 'werkstatt_ort', label: 'PLZ und Ort', typ: 'text' },
      { gruppe: 'Erreichbarkeit' },
      { key: 'telefon', label: 'Telefon', typ: 'text' },
      { key: 'mobil', label: 'Mobil', typ: 'text' },
      { key: 'fax', label: 'Fax', typ: 'text' },
      { key: 'email', label: 'E-Mail', typ: 'text' },
      { gruppe: 'Aufruf am Ende jeder Rubrik' },
      { key: 'aufruf_titel', label: 'Überschrift', typ: 'text' },
      { key: 'aufruf_text', label: 'Text', typ: 'textfeld' },
    ] },
    { trenner: true },
    ...[['kuechen', 'Küchen'], ['moebel', 'Möbel'], ['innenausbau', 'Innenausbau'],
        ['tueren', 'Türen'], ['aussen', 'Außen'], ['faesser', 'Fässer']]
      .map(([id, name]) => ({ id, name, icon: id, seite: `${id}.html`, felder: RUBRIK_FELDER })),
    { trenner: true },
    { id: 'impressum', name: 'Impressum', zeichen: '§', seite: 'impressum.html', felder: TEXTSEITE_FELDER },
    { id: 'datenschutz', name: 'Datenschutz', zeichen: '§', seite: 'datenschutz.html', felder: TEXTSEITE_FELDER },
  ];

  /* ================= Hilfsfunktionen ================= */
  function el(tag, attrs = {}, ...kinder) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
      else if (k in e && k !== 'list') e[k] = v;
      else e.setAttribute(k, v === true ? '' : v);
    }
    for (const kind of kinder.flat()) if (kind != null) e.append(kind);
    return e;
  }

  function status(text, art = '') {
    const s = $('#status');
    s.textContent = text;
    s.className = 'a-status ' + art;
  }

  const utf8ZuBase64 = text => blobZuBase64(new Blob([text]));
  function blobZuBase64(blob) {
    return new Promise((ok, fehler) => {
      const r = new FileReader();
      r.onload = () => ok(String(r.result).split(',')[1]);
      r.onerror = () => fehler(r.error);
      r.readAsDataURL(blob);
    });
  }
  function base64ZuUtf8(b64) {
    const bytes = Uint8Array.from(atob(b64.replace(/\n/g, '')), c => c.charCodeAt(0));
    return new TextDecoder().decode(bytes);
  }

  // Foto im Browser verkleinern -> JPEG-Blob
  async function fotoVorbereiten(datei) {
    const bmp = await createImageBitmap(datei);
    const faktor = Math.min(1, CFG.bildMaxKante / Math.max(bmp.width, bmp.height));
    const c = el('canvas', { width: Math.round(bmp.width * faktor), height: Math.round(bmp.height * faktor) });
    c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
    const blob = await new Promise(ok => c.toBlob(ok, 'image/jpeg', CFG.bildQualitaet));
    const basis = datei.name.replace(/\.[^.]+$/, '').toLowerCase()
      .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'foto';
    const stempel = new Date().toISOString().replace(/\D/g, '').slice(0, 14);
    return { blob, pfad: `${CFG.bildOrdner}/${basis}-${stempel}.jpg` };
  }

  /* ================= Speicherorte ================= */
  const SPEICHER = {
    github: {
      name: 'GitHub',
      async start({ token }) {
        this.token = token;
        this.sha = {};
        const { owner, repo } = CFG.github;
        const r = await fetch(`https://api.github.com/repos/${owner}/${repo}`, { headers: this.kopf() });
        if (r.status === 401) throw new Error('Der Zugangsschlüssel ist ungültig oder abgelaufen.');
        if (!r.ok) throw new Error(`GitHub antwortet mit Fehler ${r.status}.`);
        const info = await r.json();
        if (info.permissions && !info.permissions.push) throw new Error('Der Schlüssel hat keine Schreibrechte für diese Website.');
      },
      kopf() {
        return { Authorization: `Bearer ${this.token}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' };
      },
      url(pfad) {
        const { owner, repo } = CFG.github;
        return `https://api.github.com/repos/${owner}/${repo}/contents/${pfad.split('/').map(encodeURIComponent).join('/')}`;
      },
      async lesen(pfad) {
        const r = await fetch(`${this.url(pfad)}?ref=${CFG.github.branch}`, { headers: this.kopf(), cache: 'no-store' });
        if (!r.ok) throw new Error(`${pfad} konnte nicht geladen werden (${r.status}).`);
        const d = await r.json();
        this.sha[pfad] = d.sha;
        return JSON.parse(base64ZuUtf8(d.content));
      },
      async schreiben(pfad, base64, nachricht) {
        const body = { message: nachricht, content: base64, branch: CFG.github.branch };
        if (this.sha[pfad]) body.sha = this.sha[pfad];
        const r = await fetch(this.url(pfad), { method: 'PUT', headers: this.kopf(), body: JSON.stringify(body) });
        if (r.status === 409 || r.status === 422) {
          throw new Error('Die Datei wurde inzwischen an anderer Stelle geändert. Bitte die Seite neu laden und die Änderung wiederholen.');
        }
        if (!r.ok) throw new Error(`Speichern von ${pfad} fehlgeschlagen (${r.status}).`);
        const d = await r.json();
        this.sha[pfad] = d.content.sha;
      },
      hinweisNachSpeichern: 'Gespeichert. Die Website zeigt die Änderung in 1–2 Minuten.',
    },

    test: {
      name: 'Testmodus',
      async start() { this.speicher = {}; },
      async lesen(pfad) {
        if (this.speicher[pfad]) return JSON.parse(this.speicher[pfad]);
        const r = await fetch(`../${pfad}`, { cache: 'no-cache' });
        if (!r.ok) throw new Error(`${pfad} konnte nicht geladen werden (${r.status}).`);
        return r.json();
      },
      async schreiben(pfad, base64, nachricht) {
        if (pfad.endsWith('.json')) this.speicher[pfad] = base64ZuUtf8(base64);
        console.info('[Testmodus] würde speichern:', pfad, '–', nachricht);
      },
      hinweisNachSpeichern: 'Testmodus: Änderung übernommen, aber nicht auf der Website gespeichert.',
    },
  };

  /* ================= Zustand ================= */
  let speicher = null;
  let bereich = null;      // aktuell geöffneter Bereich
  let daten = null;        // bearbeitete Daten des Bereichs
  let original = '';       // JSON-Stand beim Laden, zum Vergleichen
  const neueFotos = new Map();  // pfad -> { blob, vorschau } – noch nicht hochgeladen
  const vorschauen = new Map(); // pfad -> Vorschau-URL, damit hochgeladene Fotos sofort sichtbar bleiben
  let grundStatus = ['', ''];

  const geaendert = () => JSON.stringify(daten) !== original;
  function aenderungPruefen() {
    const g = !!daten && geaendert();
    $('#speichern').disabled = !g;
    $('#verwerfen').disabled = !g;
    $('#ungespeichert').hidden = !g;
  }

  /* ================= Anmeldung ================= */
  function anmeldungVorbereiten() {
    const auswahl = $('#speicherort');
    CFG.speicherorte.forEach(id => auswahl.append(el('option', { value: id, textContent: SPEICHER[id].name })));
    const zeigeFelder = () => document.querySelectorAll('[data-fuer]').forEach(d => { d.hidden = d.dataset.fuer !== auswahl.value; });
    auswahl.addEventListener('change', zeigeFelder);

    let gemerkt = null;
    try { gemerkt = localStorage.getItem('wst-token') || sessionStorage.getItem('wst-token'); } catch { /* Speicher gesperrt */ }
    if (gemerkt) { $('#token').value = gemerkt; $('#merken').checked = !!localStorage.getItem('wst-token'); }
    zeigeFelder();

    $('#login-form').addEventListener('submit', async e => {
      e.preventDefault();
      const art = auswahl.value;
      const token = $('#token').value.trim();
      $('#login-fehler').textContent = '';
      if (art === 'github' && !token) { $('#login-fehler').textContent = 'Bitte den Zugangsschlüssel eingeben.'; return; }
      try {
        status('Anmeldung läuft …');
        await SPEICHER[art].start({ token });
        speicher = SPEICHER[art];
        if (art === 'github') {
          try {
            sessionStorage.setItem('wst-token', token);
            if ($('#merken').checked) localStorage.setItem('wst-token', token); else localStorage.removeItem('wst-token');
          } catch { /* Speicher gesperrt – dann eben ohne Merken */ }
        }
        $('#login').hidden = true;
        $('#app').hidden = false;
        $('#abmelden').hidden = false;
        grundStatus = art === 'test' ? ['Testmodus – nichts wird gespeichert', 'fehler'] : [`Angemeldet (${speicher.name})`, 'ok'];
        status(...grundStatus);
        navigationAufbauen();
        oeffnen(BEREICHE[0]);
      } catch (err) {
        status('');
        $('#login-fehler').textContent = err.message;
      }
    });

    $('#abmelden').addEventListener('click', () => {
      if (daten && geaendert() && !confirm('Es gibt ungespeicherte Änderungen. Trotzdem abmelden?')) return;
      try { sessionStorage.removeItem('wst-token'); localStorage.removeItem('wst-token'); } catch { /* egal */ }
      location.reload();
    });
  }

  /* ================= Navigation ================= */
  function navigationAufbauen() {
    const ul = $('#bereiche');
    ul.replaceChildren(...BEREICHE.map(b => b.trenner
      ? el('li', { className: 'trenner', 'aria-hidden': 'true' })
      : el('li', {}, el('button', { type: 'button', 'data-id': b.id, onclick: () => oeffnen(b) },
          b.icon ? el('img', { src: `../icons/${b.icon}.svg`, alt: '' }) : el('span', { className: 'a-zeichen', 'aria-hidden': 'true', textContent: b.zeichen }),
          b.name))));
  }

  async function oeffnen(b) {
    if (bereich === b) return;
    if (daten && geaendert() && !confirm('Es gibt ungespeicherte Änderungen. Wirklich wechseln und die Änderungen verwerfen?')) return;
    document.querySelectorAll('#bereiche button').forEach(k => k.toggleAttribute('aria-current', k.dataset.id === b.id));
    bereich = b;
    $('#titel').textContent = b.name;
    $('#ansehen').href = `../${b.seite}`;
    $('#editor').replaceChildren(el('p', { textContent: 'Wird geladen …' }));
    daten = null; aenderungPruefen();
    try {
      daten = await speicher.lesen(`inhalt/${b.id}.json`);
      original = JSON.stringify(daten);
      formularAufbauen();
    } catch (err) {
      $('#editor').replaceChildren(el('p', { className: 'a-fehler', textContent: err.message }));
    }
    aenderungPruefen();
  }

  /* ================= Formular ================= */
  function formularAufbauen() {
    const form = $('#editor');
    form.replaceChildren();
    let fs = null;
    for (const f of bereich.felder) {
      if (f.gruppe) { fs = el('fieldset', {}, el('legend', { textContent: f.gruppe })); form.append(fs); continue; }
      (fs || form).append(feld(f));
    }
  }

  /* ---------- Formatierungsleiste über Textfeldern ---------- */
  const PLATZHALTER = [
    ['telefon', 'Telefon'], ['mobil', 'Mobil'], ['email', 'E-Mail'], ['name', 'Firmenname'], ['inhaber', 'Inhaber'],
    ['strasse', 'Straße'], ['ort', 'PLZ und Ort'], ['werkstatt_strasse', 'Werkstatt: Straße'],
    ['werkstatt_ort', 'Werkstatt: PLZ und Ort'], ['fax', 'Fax'],
  ];

  // Text im Feld ersetzen und dabei die Rückgängig-Funktion (Strg+Z) des Browsers erhalten
  function ersetze(ta, von, bis, neu, selVon, selBis) {
    ta.focus();
    ta.setSelectionRange(von, bis);
    if (!document.execCommand('insertText', false, neu)) {
      ta.setRangeText(neu, von, bis, 'end');
      ta.dispatchEvent(new Event('input', { bubbles: true }));
    }
    ta.setSelectionRange(selVon, selBis);
  }

  // Markierten Text mit Zeichen umschließen (z. B. ** für fett). Nochmal klicken nimmt sie wieder weg.
  function umschliessen(ta, zeichen, beispiel) {
    const { selectionStart: a, selectionEnd: b, value } = ta;
    const n = zeichen.length;
    if (a >= n && value.slice(a - n, a) === zeichen && value.slice(b, b + n) === zeichen) {
      ersetze(ta, a - n, b + n, value.slice(a, b), a - n, b - n);
    } else if (a === b) {
      ersetze(ta, a, b, zeichen + beispiel + zeichen, a + n, a + n + beispiel.length);
    } else {
      ersetze(ta, a, b, zeichen + value.slice(a, b) + zeichen, a + n, b + n);
    }
  }

  // Zeilen zur Aufzählung machen (oder zurück). Eine Liste braucht Leerzeilen davor und danach.
  function aufzaehlung(ta) {
    const { value } = ta;
    const von = value.lastIndexOf('\n', ta.selectionStart - 1) + 1;
    let bis = value.indexOf('\n', ta.selectionEnd);
    if (bis === -1) bis = value.length;
    const zeilen = value.slice(von, bis).split('\n');
    const alleListe = zeilen.every(z => /^- /.test(z));
    let neu = zeilen.map(z => alleListe ? z.replace(/^- /, '') : (z.trim() ? '- ' + z.replace(/^- /, '') : z)).join('\n');
    if (!alleListe) {
      if (von > 0 && value.slice(Math.max(0, von - 2), von) !== '\n\n') neu = (value[von - 1] === '\n' ? '\n' : '\n\n') + neu;
      if (bis < value.length && value.slice(bis, bis + 2) !== '\n\n') neu += (value[bis + 1] === '\n' ? '\n' : '\n\n');
    }
    ersetze(ta, von, bis, neu, von, von + neu.length);
  }

  function knopf(inhalt, titel, aktion) {
    return el('button', { type: 'button', className: 'a-werkzeug', title: titel, 'aria-label': titel,
      onmousedown: e => e.preventDefault(),   // die Auswahl im Textfeld soll beim Klick erhalten bleiben
      onclick: aktion }, inhalt);
  }

  function textFeld(f, ta) {
    if (!f.format) return el('label', {}, f.label, hilfe(f), ta);
    const leiste = el('div', { className: 'a-leiste-text', role: 'toolbar', 'aria-label': 'Textformatierung' },
      knopf(el('b', {}, 'F'), 'Fett (Strg+B)', () => umschliessen(ta, '**', 'fetter Text')),
      knopf(el('span', { className: 'a-marker' }, 'M'), 'Gelb markieren (für Stellen, die noch geprüft werden müssen)',
        () => umschliessen(ta, '==', 'markierter Text')),
      knopf('• Liste', 'Aufzählung (markierte Zeilen werden Stichpunkte)', () => aufzaehlung(ta)),
      el('select', { className: 'a-platzhalter', 'aria-label': 'Kontaktdaten einfügen',
        onchange: e => {
          const k = e.target.value;
          e.target.value = '';
          if (!k) return;
          const pos = ta.selectionStart;
          ersetze(ta, pos, ta.selectionEnd, `{${k}}`, pos + k.length + 2, pos + k.length + 2);
        } },
        el('option', { value: '', textContent: 'Kontaktdaten einfügen …' }),
        PLATZHALTER.map(([k, t]) => el('option', { value: k, textContent: t }))));
    ta.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') { e.preventDefault(); umschliessen(ta, '**', 'fetter Text'); }
    });
    return el('div', { className: 'a-feld' },
      el('span', { className: 'a-feldname', textContent: f.label }), hilfe(f), leiste, ta);
  }


  function hilfe(f) { return f.hilfe ? el('span', { className: 'a-feldhilfe', textContent: f.hilfe }) : null; }

  function feld(f) {
    const setze = v => { daten[f.key] = v; aenderungPruefen(); };
    switch (f.typ) {
      case 'text':
        return el('label', {}, f.label, hilfe(f),
          el('input', { type: 'text', value: daten[f.key] ?? '', oninput: e => setze(e.target.value) }));
      case 'textfeld':
      case 'langtext':
        return textFeld(f, el('textarea', { className: f.typ === 'langtext' ? 'gross' : '', value: daten[f.key] ?? '', oninput: e => setze(e.target.value) }));
      case 'haken':
        return el('label', { className: 'a-check' },
          el('input', { type: 'checkbox', checked: !!daten[f.key], onchange: e => setze(e.target.checked) }), f.label);
      case 'auswahl':
        return el('label', {}, f.label, hilfe(f),
          el('select', { onchange: e => setze(e.target.value) },
            f.optionen.map(([wert, text]) => el('option', { value: wert, textContent: text, selected: (daten[f.key] ?? '') === wert }))));
      case 'info':
        return el('p', { className: 'a-info', textContent: f.text });
      case 'abschnitte':
        return abschnittFeld(f);
      case 'liste':
        return listenFeld(f);
      case 'fotos':
        return fotoFeld(f);
    }
    return el('p', { textContent: `Unbekannter Feldtyp: ${f.typ}` });
  }

  function verschieben(liste, i, richtung) {
    const j = i + richtung;
    if (j < 0 || j >= liste.length) return;
    [liste[i], liste[j]] = [liste[j], liste[i]];
  }

  function listenFeld(f) {
    if (!Array.isArray(daten[f.key])) daten[f.key] = [];
    const box = el('div');
    const zeichnen = (fokus = -1) => {
      const liste = daten[f.key];
      const zeilen = liste.map((wert, i) => {
        const eingabe = el('input', { type: 'text', value: wert, 'aria-label': `${f.label} ${i + 1}`,
          oninput: e => { liste[i] = e.target.value; aenderungPruefen(); } });
        if (i === fokus) setTimeout(() => eingabe.focus());
        return el('div', { className: 'a-zeile' }, eingabe,
          el('button', { type: 'button', className: 'a-mini', title: 'Nach oben', disabled: i === 0,
            onclick: () => { verschieben(liste, i, -1); zeichnen(); aenderungPruefen(); } }, '↑'),
          el('button', { type: 'button', className: 'a-mini', title: 'Nach unten', disabled: i === liste.length - 1,
            onclick: () => { verschieben(liste, i, 1); zeichnen(); aenderungPruefen(); } }, '↓'),
          el('button', { type: 'button', className: 'a-mini loeschen', title: 'Entfernen',
            onclick: () => { liste.splice(i, 1); zeichnen(); aenderungPruefen(); } }, '✕'));
      });
      box.replaceChildren(
        el('p', { className: 'a-listentitel', textContent: f.label }),
        el('div', { className: 'a-liste' }, zeilen),
        el('button', { type: 'button', className: 'a-plus',
          onclick: () => { liste.push(''); zeichnen(liste.length - 1); aenderungPruefen(); } }, `+ ${f.neu}`));
    };
    zeichnen();
    return box;
  }

  // Abschnitte aus Überschrift + Text (Impressum, Datenschutz)
  function abschnittFeld(f) {
    if (!Array.isArray(daten[f.key])) daten[f.key] = [];
    const box = el('div');
    const zeichnen = (fokus = -1) => {
      const liste = daten[f.key];
      const karten = liste.map((a, i) => {
        const titel = el('input', { type: 'text', value: a.ueberschrift ?? '',
          oninput: e => { a.ueberschrift = e.target.value; aenderungPruefen(); } });
        if (i === fokus) setTimeout(() => titel.focus());
        return el('div', { className: 'a-abschnitt' },
          el('div', { className: 'a-abschnitt-kopf' },
            el('label', {}, `Überschrift ${i + 1}`, titel),
            el('span', { className: 'a-abschnitt-knoepfe' },
              el('button', { type: 'button', className: 'a-mini', title: 'Nach oben', disabled: i === 0,
                onclick: () => { verschieben(liste, i, -1); zeichnen(); aenderungPruefen(); } }, '↑'),
              el('button', { type: 'button', className: 'a-mini', title: 'Nach unten', disabled: i === liste.length - 1,
                onclick: () => { verschieben(liste, i, 1); zeichnen(); aenderungPruefen(); } }, '↓'),
              el('button', { type: 'button', className: 'a-mini loeschen', title: 'Abschnitt entfernen',
                onclick: () => {
                  if (!confirm('Diesen Abschnitt entfernen?')) return;
                  liste.splice(i, 1); zeichnen(); aenderungPruefen();
                } }, '✕'))),
          textFeld({ label: 'Text', format: true },
            el('textarea', { value: a.text ?? '', oninput: e => { a.text = e.target.value; aenderungPruefen(); } })));
      });
      box.replaceChildren(...karten,
        el('button', { type: 'button', className: 'a-plus',
          onclick: () => { liste.push({ ueberschrift: '', text: '' }); zeichnen(liste.length - 1); aenderungPruefen(); } },
          '+ Abschnitt hinzufügen'));
    };
    zeichnen();
    return box;
  }

  function fotoFeld(f) {
    if (!Array.isArray(daten[f.key])) daten[f.key] = [];
    const box = el('div');
    const auswahl = el('input', { type: 'file', accept: 'image/*', multiple: true, hidden: true });
    auswahl.addEventListener('change', async () => {
      const dateien = [...auswahl.files];
      auswahl.value = '';
      for (const d of dateien) {
        try {
          status(`Foto wird vorbereitet: ${d.name}`);
          const { blob, pfad } = await fotoVorbereiten(d);
          const vorschau = URL.createObjectURL(blob);
          neueFotos.set(pfad, { blob, vorschau });
          vorschauen.set(pfad, vorschau);
          daten[f.key].push({ datei: pfad, titel: '', beschreibung: '' });
        } catch {
          alert(`„${d.name}“ konnte nicht als Foto gelesen werden.`);
        }
      }
      status(...grundStatus);
      zeichnen();
      aenderungPruefen();
    });

    const zeichnen = () => {
      const liste = daten[f.key];
      const karten = liste.map((b, i) => {
        const neu = neueFotos.get(b.datei);
        return el('div', { className: 'a-foto' },
          el('img', { src: vorschauen.get(b.datei) || `../${b.datei}`, alt: '' }),
          el('div', { className: 'a-foto-in' },
            el('label', {}, 'Titel',
              el('input', { type: 'text', value: b.titel ?? '', oninput: e => { b.titel = e.target.value; aenderungPruefen(); } })),
            f.beschreibung ? el('label', {}, 'Beschreibung',
              el('textarea', { value: b.beschreibung ?? '', oninput: e => { b.beschreibung = e.target.value; aenderungPruefen(); } })) : null,
            el('div', { className: 'a-foto-knoepfe' },
              el('span', {}, neu ? el('span', { className: 'a-neu', textContent: 'neu' }) : null),
              el('span', {},
                el('button', { type: 'button', className: 'a-mini', title: 'Nach vorne', disabled: i === 0,
                  onclick: () => { verschieben(liste, i, -1); zeichnen(); aenderungPruefen(); } }, '←'), ' ',
                el('button', { type: 'button', className: 'a-mini', title: 'Nach hinten', disabled: i === liste.length - 1,
                  onclick: () => { verschieben(liste, i, 1); zeichnen(); aenderungPruefen(); } }, '→'), ' ',
                el('button', { type: 'button', className: 'a-mini loeschen', title: 'Foto entfernen',
                  onclick: () => {
                    if (!confirm('Dieses Foto von der Seite entfernen?')) return;
                    liste.splice(i, 1); zeichnen(); aenderungPruefen();
                  } }, '✕')))));
      });
      box.replaceChildren(
        el('p', { className: 'a-listentitel', textContent: f.label }),
        el('div', { className: 'a-fotos' }, karten),
        el('button', { type: 'button', className: 'a-plus', onclick: () => auswahl.click() }, '+ Fotos hinzufügen'),
        auswahl);
    };
    zeichnen();
    return box;
  }

  /* ================= Speichern ================= */
  async function speichern() {
    const knopf = $('#speichern');
    knopf.disabled = true;
    try {
      // 1. neue Fotos hochladen, die noch verwendet werden
      const benutzt = JSON.stringify(daten);
      const hochladen = [...neueFotos].filter(([pfad]) => benutzt.includes(JSON.stringify(pfad)));
      for (const [n, [pfad, foto]] of hochladen.entries()) {
        status(`Foto ${n + 1} von ${hochladen.length} wird hochgeladen …`);
        await speicher.schreiben(pfad, await blobZuBase64(foto.blob), `Foto hochgeladen: ${pfad.split('/').pop()}`);
        neueFotos.delete(pfad);
      }
      // 2. Inhalte speichern
      status('Wird gespeichert …');
      const json = JSON.stringify(daten, null, 2) + '\n';
      await speicher.schreiben(`inhalt/${bereich.id}.json`, await utf8ZuBase64(json), `Inhalt geändert: ${bereich.name} (über Admin)`);
      original = JSON.stringify(daten);
      formularAufbauen();   // „neu“-Markierungen entfernen
      status(speicher.hinweisNachSpeichern, 'ok');
    } catch (err) {
      status(err.message, 'fehler');
    }
    aenderungPruefen();
  }

  function verwerfen() {
    if (!confirm('Alle Änderungen seit dem letzten Speichern verwerfen?')) return;
    daten = JSON.parse(original);
    formularAufbauen();
    aenderungPruefen();
    status('Änderungen verworfen.');
  }

  /* ================= Start ================= */
  anmeldungVorbereiten();
  $('#speichern').addEventListener('click', speichern);
  $('#verwerfen').addEventListener('click', verwerfen);
  window.addEventListener('beforeunload', e => { if (daten && geaendert()) e.preventDefault(); });
})();
