/* Schreinerei Wistinghausen – setzt die Inhalte aus /inhalt/*.json in die Seiten ein.
   Welche Seite gerade angezeigt wird, steht in <body data-seite="...">. */
(() => {
  'use strict';

  const BASIS = document.documentElement.dataset.basis || '';   // relativer Pfad zur Website-Wurzel
  const seite = document.body.dataset.seite;

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  // Leerzeile = neuer Absatz, einfacher Zeilenumbruch = <br>
  const absaetze = s => String(s ?? '').trim().split(/\n\s*\n/).filter(Boolean)
    .map(p => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`).join('');
  const telLink = t => 'tel:' + String(t ?? '').replace(/[^\d+]/g, '');
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
      </section>`;
  }

  /* ---------- Rubrik-Seiten ---------- */
  function rubrik(d) {
    document.title = `${d.titel} – Schreinerei Wistinghausen`;
    const meta = document.querySelector('meta[name="description"]');
    if (meta && d.untertitel) meta.content = d.untertitel;

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
      <section class="cta wood">
        <div><h2 data-firma="aufruf_titel"></h2><p data-firma="aufruf_text"></p></div>
        <div>
          <a class="btn light" data-firma-tel="telefon" href="#"><span data-firma="telefon"></span></a>
          <a class="btn ghost light" data-firma-mail href="#">E-Mail schreiben</a>
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

  function fehler(e) {
    console.error(e);
    const ziel = document.getElementById('inhalt');
    if (ziel) ziel.innerHTML = '<p class="note">Die Inhalte konnten nicht geladen werden. Bitte Seite neu laden.</p>';
  }

  /* ---------- Ablauf ---------- */
  const inhalt = seite === 'start' ? laden('start').then(startseite)
    : seite && seite !== 'text' ? laden(seite).then(rubrik)
    : Promise.resolve();

  // Firmendaten erst nach dem Seiteninhalt einsetzen, weil der Inhalt Platzhalter dafür enthält
  Promise.allSettled([laden('firma'), inhalt]).then(([firma, seitenInhalt]) => {
    if (seitenInhalt.status === 'rejected') fehler(seitenInhalt.reason);
    if (firma.status === 'fulfilled') firmaEinsetzen(firma.value);
    else console.error(firma.reason);
  });
})();
