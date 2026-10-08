/* Einstellungen für den Admin-Bereich.
   Speicherorte:
   - "github": Änderungen werden direkt ins GitHub-Repository geschrieben (GitHub Pages baut die Seite neu).
   - "test":   Nichts wird gespeichert – zum Ausprobieren.
   Später kommt "webspace" dazu (kleines PHP-Skript auf dem eigenen Server). */
window.ADMIN_CONFIG = {
  speicherorte: ['github', 'test'],
  github: {
    owner: 'Ralfsmart',
    repo: 'Wistinghausen',
    branch: 'main',
  },
  bildMaxKante: 1600,      // hochgeladene Fotos werden auf diese Kantenlänge verkleinert (Pixel)
  bildQualitaet: 0.85,     // JPEG-Qualität 0–1
  bildOrdner: 'bilder/uploads',
};
