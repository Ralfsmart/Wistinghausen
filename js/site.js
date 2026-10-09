/* Schreinerei Wistinghausen – setzt die Inhalte aus /inhalt/*.json in die Seiten ein.
   Welche Seite gerade angezeigt wird, steht in <body data-seite="...">. */
(() => {
  'use strict';

  const BASIS = document.documentElement.dataset.basis || '';   // relativer Pfad zur Website-Wurzel
  const seite = document.body.dataset.seite;

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const telLink = t => 'tel:' + String(t ?? '').replace(/[^\d+]/g, '');
  let firma = {};

  /* Einfache Textformatierung für alle Texte aus dem Admin-Bereich:
     Leerzeile = neuer Absatz · Zeilenumbruch bleibt erhalten · Zeilen mit "- " = Aufzählung
     **fett** · ==gelb markiert== · Web-Adressen werden zu Links
     {telefon}, {email}, {name} … werden durch die Kontaktdaten ersetzt */
  function zeile(text) {
    let h = esc(text)
      // nur echte Adressen mit Domain verlinken (nicht z. B. ein alleinstehendes „https://“)
      .replace(/\b(https?:\/\/[\w-]+\.[^\s<“”"]*[^\s<.,;:!?)“”"])/g, '<a href="$1" rel="noopener">$1</a>')
      .replace(/(^|[\s(])(www\.[\w-]+\.[^\s<“”"]*[^\s<.,;:!?)“”"])/g, '$1<a href="https://$2" rel="noopener">$2</a>');
    h = h.replace(/\{([a-z_]+)\}/g, (m, k) => {
      if (!(k in firma)) return m;
      const w = esc(firma[k]);
      if (k === 'telefon' || k === 'mobil') return `<a href="${telLink(firma[k])}">${w}</a>`;
      if (k === 'email') return `<a href="mailto:${w}">${w}</a>`;
      return w;
    });
    return h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/==(.+?)==/g, '<mark class="todo">$1</mark>');
  }
  const absaetze = s => String(s ?? '').trim().split(/\n\s*\n/).filter(Boolean).map(block => {
    const zeilen = block.split('\n');
    if (zeilen.every(z => /^\s*- /.test(z))) {
      return `<ul>${zeilen.map(z => `<li>${zeile(z.replace(/^\s*- /, ''))}</li>`).join('')}</ul>`;
    }
    return `<p>${zeilen.map(zeile).join('<br>')}</p>`;
  }).join('');
  const url = pfad => BASIS + pfad;

  const laden = name => fetch(url(`inhalt/${name}.json`), { cache: 'no-cache' })
    .then(r => { if (!r.ok) throw new Error(`${name}.json: ${r.status}`); return r.json(); });

  /* ---------- Firmendaten überall einsetzen ---------- */
  function firmaEinsetzen(f) {
    document.querySelectorAll('[data-firma]').forEach(el => { el.textContent = f[el.dataset.firma] ?? ''; });
    document.querySelectorAll('[data-firma-tel]').forEach(el => { el.href = telLink(f[el.dataset.firmaTel]); });
    document.querySelectorAll('[data-firma-mail]').forEach(el => { el.href = 'mailto:' + (f.email ?? ''); });
  }

  /* ---------- Startseite ---------- */
  function startseite(d) {
    const ziel = document.getElementById('inhalt');
    const fotos = (d.fotos || []).slice(0, 6)
      .map(b => `<img src="${esc(url(b.datei))}" alt="${esc(b.titel)}">`).join('');
    const punkte = (d.abschnitt_punkte || []).filter(Boolean).map(p => `<li>${esc(p)}</li>`).join('');
    ziel.innerHTML = `
      <section class="hero">
        <h1>${esc(d.hero_titel)}</h1>
        <p>${esc(d.hero_text)}</p>
        <a class="btn" data-firma-tel="telefon" href="#"><span data-firma="telefon"></span> anrufen</a>
        <a class="btn ghost" href="#kontakt">Kontakt</a>
      </section>
      <section class="split">
        <div>
          <h2>${esc(d.abschnitt_titel)}</h2>
          ${absaetze(d.abschnitt_text)}
          ${punkte ? `<ul>${punkte}</ul>` : ''}
        </div>
        <div class="photos">${fotos}</div>
      </section>
      ${besonderheit(d)}
      ${ueberMich(d)}`;
  }

  const erstesFoto = liste => (liste || []).find(b => b && b.datei);

  // Hervorgehobener Kasten, z. B. für die Rührfässer
  function besonderheit(d) {
    if (!d.besonderheit_titel) return '';
    const foto = erstesFoto(d.besonderheit_fotos);
    const link = d.besonderheit_link && d.besonderheit_link_text
      ? `<a class="btn" href="${esc(url(d.besonderheit_link))}">${esc(d.besonderheit_link_text)}</a>` : '';
    return `
      <section class="besonders">
        ${foto ? `<img src="${esc(url(foto.datei))}" alt="${esc(foto.titel)}">` : ''}
        <div>
          <h2>${esc(d.besonderheit_titel)}</h2>
          ${absaetze(d.besonderheit_text)}
          ${link}
        </div>
      </section>`;
  }

  function ueberMich(d) {
    if (!d.ueber_titel && !d.ueber_text) return '';
    const foto = erstesFoto(d.ueber_fotos);
    return `
      <section class="ueber" id="ueber-mich">
        ${foto ? `<figure><img src="${esc(url(foto.datei))}" alt="${esc(foto.titel)}">${foto.titel ? `<figcaption>${esc(foto.titel)}</figcaption>` : ''}</figure>` : ''}
        <div>
          <h2>${esc(d.ueber_titel)}</h2>
          ${absaetze(d.ueber_text)}
        </div>
      </section>`;
  }

  /* ---------- Rubrik-Seiten ---------- */
  function rubrik(d) {
    document.title = d.seo_titel || `${d.titel} | Schreinerei Wistinghausen`;
    const meta = document.querySelector('meta[name="description"]');
    if (meta && (d.seo_beschreibung || d.untertitel)) meta.content = d.seo_beschreibung || d.untertitel;

    const leistungen = (d.leistungen || []).filter(Boolean).map(l => `<li>${esc(l)}</li>`).join('');
    const bilder = (d.bilder || []).filter(b => b.datei).map(b => `
      <figure>
        <button type="button" data-voll="${esc(url(b.datei))}" aria-label="Foto vergrößern: ${esc(b.titel)}">
          <img src="${esc(url(b.datei))}" alt="${esc(b.titel)}" loading="lazy">
        </button>
        ${b.titel || b.beschreibung ? `<figcaption>${b.titel ? `<b>${esc(b.titel)}</b>` : ''}${esc(b.beschreibung)}</figcaption>` : ''}
      </figure>`).join('');

    document.getElementById('inhalt').innerHTML = `
      <div class="r-head">
        <span class="r-icon" style="background-image:url(${url(`icons/${seite}.svg`)})" aria-hidden="true"></span>
        <div>
          <h1>${esc(d.titel)}</h1>
          ${d.untertitel ? `<p class="lead">${esc(d.untertitel)}</p>` : ''}
        </div>
      </div>
      ${d.beispieltext ? '<p class="note">Beispieltext: Bitte an die eigene Arbeitsweise anpassen und danach im Admin-Bereich den Haken bei „Beispieltext“ entfernen.</p>' : ''}
      <div class="r-body">
        <div class="r-text">${absaetze(d.einleitung)}</div>
        ${leistungen ? `<aside class="r-list"><h2>Leistungen</h2><ul>${leistungen}</ul></aside>` : ''}
      </div>
      ${bilder ? `<h2>Einblicke</h2><div class="galerie">${bilder}</div>` : ''}
      <section class="cta">
        <span class="cta-leiste wood" aria-hidden="true"></span>
        <div><h2 data-firma="aufruf_titel"></h2><p data-firma="aufruf_text"></p></div>
        <div class="cta-knoepfe">
          <a class="btn" data-firma-tel="telefon" href="#"><span data-firma="telefon"></span></a>
          <a class="btn ghost" data-firma-mail href="#">E-Mail schreiben</a>
        </div>
      </section>`;
    lightbox();
  }

  /* ---------- Fotos vergrößern ---------- */
  function lightbox() {
    const items = [...document.querySelectorAll('.galerie figure')];
    if (!items.length) return;
    const dlg = document.createElement('dialog');
    dlg.className = 'lightbox';
    dlg.setAttribute('aria-label', 'Foto');
    dlg.innerHTML = `
      <button type="button" class="lb-btn lb-close" aria-label="Schließen">×</button>
      <button type="button" class="lb-btn lb-prev" aria-label="Vorheriges Foto">‹</button>
      <button type="button" class="lb-btn lb-next" aria-label="Nächstes Foto">›</button>
      <figure><img alt=""><figcaption></figcaption></figure>`;
    document.body.append(dlg);
    const img = dlg.querySelector('img'), cap = dlg.querySelector('figcaption');
    let i = 0;
    const zeige = n => {
      i = (n + items.length) % items.length;
      const b = items[i].querySelector('button'), c = items[i].querySelector('figcaption');
      img.style.maxWidth = '';
      img.src = b.dataset.voll;
      img.alt = b.querySelector('img').alt;
      cap.innerHTML = c ? c.innerHTML : '';
    };
    // kleine Fotos höchstens auf doppelte Größe aufziehen, sonst werden sie unscharf
    img.onload = () => { img.style.maxWidth = Math.min(img.naturalWidth * 2, innerWidth * 0.9) + 'px'; };
    items.forEach((it, n) => it.querySelector('button').addEventListener('click', () => { zeige(n); dlg.showModal(); }));
    dlg.querySelector('.lb-close').onclick = () => dlg.close();
    dlg.querySelector('.lb-prev').onclick = () => zeige(i - 1);
    dlg.querySelector('.lb-next').onclick = () => zeige(i + 1);
    dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft') zeige(i - 1);
      if (e.key === 'ArrowRight') zeige(i + 1);
    });
  }

  /* ---------- Impressum, Datenschutz ---------- */
  function textseite(d) {
    document.title = `${d.titel} | Schreinerei Wistinghausen`;
    const teile = (d.abschnitte || []).map(a =>
      `${a.ueberschrift ? `<h2>${esc(a.ueberschrift)}</h2>` : ''}${absaetze(a.text)}`).join('');
    document.getElementById('inhalt').innerHTML = `
      <h1>${esc(d.titel)}</h1>
      ${d.hinweis ? `<p class="note">${esc(d.hinweis)}</p>` : ''}
      ${teile}
      ${d.stand ? `<p><em>Stand: ${esc(d.stand)}</em></p>` : ''}`;
  }

  function fehler(e) {
    console.error(e);
    const ziel = document.getElementById('inhalt');
    if (ziel) ziel.innerHTML = '<p class="note">Die Inhalte konnten nicht geladen werden. Bitte Seite neu laden.</p>';
  }

  /* ---------- Ablauf ---------- */
  const TEXTSEITEN = ['impressum', 'datenschutz'];
  const darstellen = seite === 'start' ? startseite : TEXTSEITEN.includes(seite) ? textseite : rubrik;

  // Kontaktdaten zuerst, weil die Texte Platzhalter dafür enthalten können
  Promise.allSettled([laden('firma'), seite ? laden(seite) : Promise.resolve(null)])
    .then(([f, inhalt]) => {
      if (f.status === 'fulfilled') firma = f.value; else console.error(f.reason);
      if (inhalt.status === 'rejected') fehler(inhalt.reason);
      else if (inhalt.value) {
        try { darstellen(inhalt.value); } catch (e) { fehler(e); }
      }
      firmaEinsetzen(firma);
    });
})();
