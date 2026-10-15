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
     **fett** · *kursiv* · ++unterstrichen++ · ==gelb markiert (nur für Hinweise)== · Web-Adressen werden zu Links
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
    return h.replace(/\*\*\*([^\s*](?:[^*]*[^\s*])?)\*\*\*/g, '<strong><em>$1</em></strong>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^\s*](?:[^*]*[^\s*])?)\*/g, '<em>$1</em>')
            .replace(/\+\+(.+?)\+\+/g, '<u>$1</u>')
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
    // im Seitenkopf steht nur das erste Wort in Großbuchstaben: „MEISTERBETRIEB seit 2004“
    document.querySelectorAll('.brand [data-firma="zusatz"]').forEach(el => {
      const t = String(f.zusatz ?? ''), i = t.indexOf(' ');
      el.textContent = i < 0 ? t.toUpperCase() : t.slice(0, i).toUpperCase() + t.slice(i);
    });
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
        <a class="btn" data-firma-tel="mobil" href="#"><span data-firma="mobil"></span> anrufen</a>
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
    // bis zu zwei Bilder: Foto und z. B. der Meisterbrief (Klick öffnet das Bild in voller Größe)
    const karte = (b, klasse) => `<figure class="${klasse}"><a href="${esc(url(b.datei))}" target="_blank" rel="noopener"><img src="${esc(url(b.datei))}" alt="${esc(b.titel)}"></a>${b.titel ? `<figcaption>${esc(b.titel)}</figcaption>` : ''}</figure>`;
    const bilder = (d.ueber_fotos || []).filter(b => b && b.datei).slice(0, 2)
      .map((b, i) => karte(b, i ? 'beleg' : 'portrait')).join('');
    return `
      <section class="ueber" id="ueber-mich">
        ${bilder ? `<div class="ueber-bilder">${bilder}</div>` : ''}
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
      ${bilder ? `<h2>Einblicke</h2><p class="galerie-hinweis"><span class="nur-maus">Für Details einfach auf ein Foto klicken. Mit dem Mausrad lässt sich hinein- und herauszoomen.</span><span class="nur-touch">Für Details einfach auf ein Foto tippen. Mit zwei Fingern lässt sich hinein- und herauszoomen.</span></p><div class="galerie">${bilder}</div>` : ''}
      <section class="cta">
        <span class="cta-leiste wood" aria-hidden="true"></span>
        <div><h2 data-firma="aufruf_titel"></h2><p data-firma="aufruf_text"></p></div>
        <div class="cta-knoepfe">
          <a class="btn" data-firma-tel="mobil" href="#"><span data-firma="mobil"></span></a>
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
      <div class="lb-werkzeuge">
        <button type="button" class="lb-btn lb-plus" aria-label="Vergrößern" title="Vergrößern (+)">+</button>
        <button type="button" class="lb-btn lb-minus" aria-label="Verkleinern" title="Verkleinern (−)">−</button>
        <button type="button" class="lb-btn lb-eins" aria-label="Ganzes Foto zeigen" title="Ganzes Foto (0)">⤢</button>
      </div>
      <figure>
        <div class="lb-zoom"><img alt=""></div>
        <figcaption></figcaption>
        <p class="lb-hinweis">
          <span class="nur-maus">Zoomen mit dem Mausrad oder mit + und −. <br>Mit gedrückter Maustaste verschieben. <br>Doppelklick zum Heranzoomen.</span>
          <span class="nur-touch">Zoomen mit zwei Fingern. <br>Mit einem Finger verschieben. <br>Doppeltippen zum Heranzoomen.</span>
        </p>
      </figure>`;
    document.body.append(dlg);
    const img = dlg.querySelector('img'), cap = dlg.querySelector('figcaption');
    const zoomBox = dlg.querySelector('.lb-zoom');
    let i = 0;

    /* Zoom: s = Vergrößerung, x/y = Verschiebung in Pixeln (negativ = Bild nach links/oben geschoben) */
    const z = { s: 1, x: 0, y: 0, max: 4 };
    const anwenden = glatt => {
      const w = zoomBox.offsetWidth, h = zoomBox.offsetHeight;
      z.s = Math.min(z.max, Math.max(1, z.s));
      // das Bild darf den Rahmen nicht verlassen
      z.x = z.s === 1 ? 0 : Math.min(0, Math.max(w - w * z.s, z.x));
      z.y = z.s === 1 ? 0 : Math.min(0, Math.max(h - h * z.s, z.y));
      img.style.transition = glatt ? 'transform .18s ease-out' : 'none';
      img.style.transform = `translate(${z.x}px, ${z.y}px) scale(${z.s})`;
      zoomBox.classList.toggle('vergroessert', z.s > 1);
    };
    // auf neue Stufe zoomen, der Punkt (px, py) im Rahmen bleibt dabei an seiner Stelle
    const zoomUm = (neu, px, py, glatt) => {
      const s2 = Math.min(z.max, Math.max(1, neu));
      z.x = px - (px - z.x) * s2 / z.s;
      z.y = py - (py - z.y) * s2 / z.s;
      z.s = s2;
      anwenden(glatt);
    };
    const mitte = () => [zoomBox.offsetWidth / 2, zoomBox.offsetHeight / 2];
    const ganzes = glatt => { z.s = 1; z.x = z.y = 0; anwenden(glatt); };
    const imRahmen = e => {
      const r = zoomBox.getBoundingClientRect();
      return [Math.min(r.width, Math.max(0, e.clientX - r.left)), Math.min(r.height, Math.max(0, e.clientY - r.top))];
    };

    const zeige = n => {
      i = (n + items.length) % items.length;
      const b = items[i].querySelector('button'), c = items[i].querySelector('figcaption');
      img.style.maxWidth = '';
      ganzes(false);
      img.src = b.dataset.voll;
      img.alt = b.querySelector('img').alt;
      cap.innerHTML = c ? c.innerHTML : '';
    };
    // kleine Fotos höchstens auf doppelte Größe aufziehen, sonst werden sie unscharf;
    // gezoomt wird bis etwa zur doppelten Pixelgröße des Fotos (höchstens 8-fach)
    // Auf breiten Bildschirmen stehen Beschreibung (links) und Zoom-Hinweis (rechts) neben dem Foto;
    // dafür bleibt Platz für Beschreibung (rechts) und Blätterpfeile (außen) frei. Auf schmalen Bildschirmen steht der Text unter dem Foto.
    const breit = matchMedia('(min-width:1200px)');
    const bildbreite = () => {
      const platz = breit.matches ? innerWidth - (2 * 80 + 36 + 300) : innerWidth * 0.92;
      img.style.maxWidth = Math.min(img.naturalWidth * 2, Math.max(240, platz)) + 'px';
    };
    img.onload = () => {
      bildbreite();
      ganzes(false);
      z.max = Math.min(8, Math.max(2, img.naturalWidth / Math.max(1, zoomBox.offsetWidth) * 2));
    };
    addEventListener('resize', () => { if (dlg.open && img.naturalWidth) { bildbreite(); ganzes(false); } });

    // Mausrad (und Trackpad-Pinch): um die Mausposition zoomen
    dlg.addEventListener('wheel', e => {
      // über einer langen Beschreibung scrollt das Mausrad den Text, nur sonst zoomt es das Foto
      if (e.target.closest('figcaption') && cap.scrollHeight > cap.clientHeight) return;
      e.preventDefault();
      const [px, py] = imRahmen(e);
      zoomUm(z.s * Math.exp(-e.deltaY * 0.0018), px, py, false);
    }, { passive: false });

    // Ziehen mit gedrückter Maustaste bzw. Finger, Pinch mit zwei Fingern
    const zeiger = new Map();
    let letzterAbstand = 0;
    zoomBox.addEventListener('pointerdown', e => {
      try { zoomBox.setPointerCapture(e.pointerId); } catch { /* nicht jedes Gerät erlaubt es */ }
      zeiger.set(e.pointerId, { x: e.clientX, y: e.clientY });
      letzterAbstand = 0;
    });
    zoomBox.addEventListener('pointermove', e => {
      const p = zeiger.get(e.pointerId);
      if (!p) return;
      const dx = e.clientX - p.x, dy = e.clientY - p.y;
      zeiger.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (zeiger.size === 2) {
        const [a, b] = [...zeiger.values()];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (letzterAbstand) {
          const r = zoomBox.getBoundingClientRect();
          zoomUm(z.s * d / letzterAbstand, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top, false);
        }
        letzterAbstand = d;
      } else if (z.s > 1 && (dx || dy)) {
        z.x += dx;
        z.y += dy;
        anwenden(false);
      }
    });
    const loslassen = e => { zeiger.delete(e.pointerId); letzterAbstand = 0; };
    zoomBox.addEventListener('pointerup', loslassen);
    zoomBox.addEventListener('pointercancel', loslassen);
    zoomBox.addEventListener('dblclick', e => {
      if (z.s > 1) ganzes(true);
      else { const [px, py] = imRahmen(e); zoomUm(Math.min(z.max, 2.5), px, py, true); }
    });
    dlg.querySelector('.lb-plus').onclick = () => zoomUm(z.s * 1.5, ...mitte(), true);
    dlg.querySelector('.lb-minus').onclick = () => zoomUm(z.s / 1.5, ...mitte(), true);
    dlg.querySelector('.lb-eins').onclick = () => ganzes(true);
    items.forEach((it, n) => it.querySelector('button').addEventListener('click', () => { zeige(n); dlg.showModal(); }));
    dlg.querySelector('.lb-close').onclick = () => dlg.close();
    dlg.querySelector('.lb-prev').onclick = () => zeige(i - 1);
    dlg.querySelector('.lb-next').onclick = () => zeige(i + 1);
    dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', e => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;   // Browser-Zoom und Kürzel nicht stören
      const k = e.key, gezoomt = z.s > 1;
      if (k === '+' || k === '=' || k === 'Add') { e.preventDefault(); zoomUm(z.s * 1.4, ...mitte(), true); }
      else if (k === '-' || k === '_' || k === 'Subtract') { e.preventDefault(); zoomUm(z.s / 1.4, ...mitte(), true); }
      else if (k === '0') ganzes(true);
      // im gezoomten Foto verschieben die Pfeiltasten das Bild, sonst blättern sie
      else if (k === 'ArrowLeft') { e.preventDefault(); if (gezoomt) { z.x += 70; anwenden(true); } else zeige(i - 1); }
      else if (k === 'ArrowRight') { e.preventDefault(); if (gezoomt) { z.x -= 70; anwenden(true); } else zeige(i + 1); }
      else if (gezoomt && k === 'ArrowUp') { e.preventDefault(); z.y += 70; anwenden(true); }
      else if (gezoomt && k === 'ArrowDown') { e.preventDefault(); z.y -= 70; anwenden(true); }
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

  /* ---------- Leiste schrumpft stufenlos mit dem Scrollen ---------- */
  // --k geht von 0 (ganz oben) bis 1 (nach 140 px gescrollt); das CSS rechnet daraus die Größen
  const wurzel = document.documentElement;
  const kopf = document.querySelector('header.site');
  const STRECKE = 140;
  let geplant = false;
  const setzeK = () => {
    geplant = false;
    wurzel.style.setProperty('--k', Math.min(1, Math.max(0, scrollY / STRECKE)).toFixed(3));
  };
  // Platzhalter oben = Höhe der vollen Leiste, damit der Inhalt beim Schrumpfen nicht springt
  const kopfMessen = () => {
    if (!kopf) return;
    wurzel.style.setProperty('--k', '0');
    wurzel.style.setProperty('--kopf-h', kopf.offsetHeight + 'px');
    setzeK();
  };
  kopfMessen();
  addEventListener('resize', kopfMessen);
  addEventListener('scroll', () => { if (!geplant) { geplant = true; requestAnimationFrame(setzeK); } }, { passive: true });

  // Handy-Menü nach Auswahl eines Eintrags schließen (wichtig, weil die Leiste stehen bleibt)
  document.querySelectorAll('nav.main a').forEach(a => a.addEventListener('click', () => {
    document.querySelector('nav.main').classList.remove('open');
    document.querySelector('.menu-btn')?.setAttribute('aria-expanded', 'false');
  }));

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
