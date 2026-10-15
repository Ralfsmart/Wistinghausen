"""Legt die Zugangsdatei für den Admin-Bereich auf dem Webspace an (admin/zugang.php).

In der Datei steht nur ein Hash, nicht das Passwort selbst. Die Datei wird per FTP in den Ordner
admin/ auf dem Webspace hochgeladen und gehört NICHT ins Git-Repository (steht in .gitignore).

Aufruf:
    python werkzeuge/zugang_erzeugen.py                 fragt zweimal nach dem Passwort
    python werkzeuge/zugang_erzeugen.py --zufall        erzeugt ein zufälliges Passwort und zeigt es an
    python werkzeuge/zugang_erzeugen.py --ziel pfad     schreibt die Datei an einen anderen Ort
"""
import argparse
import getpass
import hashlib
import secrets
import sys
from pathlib import Path

ITERATIONEN = 200_000
MIN_LAENGE = 10
# ohne leicht verwechselbare Zeichen (0/O, 1/l/I)
ZEICHEN = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def hash_erzeugen(passwort: str, salt: str, iterationen: int = ITERATIONEN) -> str:
    return hashlib.pbkdf2_hmac("sha256", passwort.encode("utf-8"), salt.encode("ascii"), iterationen, dklen=32).hex()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ziel", default=str(Path(__file__).resolve().parent.parent / "admin" / "zugang.php"))
    ap.add_argument("--zufall", action="store_true", help="zufälliges Passwort erzeugen und anzeigen")
    args = ap.parse_args()

    if args.zufall:
        passwort = "".join(secrets.choice(ZEICHEN) for _ in range(16))
        print(f"\nNeues Passwort (bitte notieren, es wird nur jetzt angezeigt):\n\n    {passwort}\n")
    else:
        passwort = getpass.getpass("Neues Passwort für den Admin-Bereich: ")
        if getpass.getpass("Noch einmal: ") != passwort:
            sys.exit("Die beiden Eingaben stimmen nicht überein.")
    if len(passwort) < MIN_LAENGE:
        sys.exit(f"Das Passwort ist zu kurz (mindestens {MIN_LAENGE} Zeichen).")

    salt = secrets.token_hex(16)
    inhalt = (
        "<?php\n"
        "// Zugang zum Admin-Bereich. Enthält nur einen Hash, nicht das Passwort.\n"
        "// Diese Datei nicht weitergeben und nicht ins Git-Repository legen.\n"
        "return [\n"
        f"    'salt' => '{salt}',\n"
        f"    'hash' => '{hash_erzeugen(passwort, salt)}',\n"
        f"    'iterationen' => {ITERATIONEN},\n"
        "];\n"
    )
    ziel = Path(args.ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(inhalt, encoding="utf-8")
    print(f"Geschrieben: {ziel}")
    print("Diese Datei jetzt per FTP in den Ordner admin/ auf dem Webspace hochladen.")


if __name__ == "__main__":
    main()
