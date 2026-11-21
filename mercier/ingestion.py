"""Étape 1 : ingestion des fichiers reçus dans la zone brute."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from mercier import config

FICHIERS_ATTENDUS = [
    "articles.csv",
    "ventes_octobre.csv",
    "boutiques.json",
    "journal_boutique.log",
]


def empreinte(chemin):
    """Renvoie l'empreinte SHA-256 d'un fichier, pour détecter les doublons."""
    calcul = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            calcul.update(bloc)
    return calcul.hexdigest()


def ingerer(sources=None, zone_brute=None, horodatage=None):
    """Copie les fichiers attendus dans un lot horodaté."""
    sources = Path(sources or config.SOURCES)
    zone_brute = Path(zone_brute or config.ZONE_BRUTE)
    horodatage = horodatage or datetime.now().strftime("%Y%m%d_%H%M%S")

    lot = zone_brute / horodatage
    lot.mkdir(parents=True, exist_ok=True)

    recus, manquants = [], []
    for nom in FICHIERS_ATTENDUS:
        origine = sources / nom
        if not origine.exists():
            manquants.append(nom)
            continue
        destination = lot / nom
        shutil.copy2(origine, destination)
        recus.append({"fichier": nom,
                      "octets": destination.stat().st_size,
                      "empreinte": empreinte(destination)[:16]})

    manifeste = {"lot": horodatage, "source": str(sources),
                 "recus": recus, "manquants": manquants}
    (lot / "_manifeste.json").write_text(
        json.dumps(manifeste, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifeste
