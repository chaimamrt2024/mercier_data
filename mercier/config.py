"""Configuration de la plateforme, lue dans l'environnement."""

import os
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

SOURCES = Path(os.environ.get("MERCIER_SOURCES", RACINE / "donnees_sources"))
ZONE_BRUTE = Path(os.environ.get("MERCIER_ZONE_BRUTE", RACINE / "zone_brute"))
ENTREPOT = Path(os.environ.get("MERCIER_ENTREPOT", RACINE / "entrepot.db"))
CLASSES_JAVA = Path(os.environ.get("MERCIER_JAVA", RACINE / "java"))

CLE_SECRETE = os.environ.get("MERCIER_CLE_SECRETE", "cle-de-developpement-a-changer")

TAUX_TVA = float(os.environ.get("MERCIER_TVA", "0.20"))


def resume():
    """Renvoie la configuration effective, pour journalisation au démarrage."""
    return {
        "sources": str(SOURCES),
        "entrepot": str(ENTREPOT),
        "tva": TAUX_TVA,
        "cle_par_defaut": CLE_SECRETE.startswith("cle-de-developpement"),
    }
