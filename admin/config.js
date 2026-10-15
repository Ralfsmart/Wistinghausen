/* Einstellungen für den Admin-Bereich.
   Speicherorte (welche angeboten werden, hängt davon ab, wo die Seite läuft):
   - "webspace": speichert über das PHP-Skript api.php auf dem eigenen Webspace (Passwort).
   - "github":   schreibt direkt ins GitHub-Repository (Zugangsschlüssel); GitHub Pages baut die Seite neu.
   - "test":     nichts wird gespeichert, zum Ausprobieren. */
(() => {
  const host = location.hostname;
  const lokal = host === 'localhost' || host === '127.0.0.1' || host === '';
  const githubPages = /\.github\.io$/.test(host);
  window.ADMIN_CONFIG = {
    speicherorte: githubPages ? ['github', 'test'] : lokal ? ['webspace', 'github', 'test'] : ['webspace', 'test'],
    github: {
      owner: 'Ralfsmart',
      repo: 'Wistinghausen',
      branch: 'main',
    },
    bildMaxKante: 1600,      // hochgeladene Fotos werden auf diese Kantenlänge verkleinert (Pixel)
    bildQualitaet: 0.85,     // JPEG-Qualität 0–1
    bildOrdner: 'bilder/uploads',
  };
})();
