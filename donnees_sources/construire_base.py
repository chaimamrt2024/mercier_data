"""Construit la base boutique.db a partir des fichiers CSV du dossier donnees.

Usage : python construire_base.py
Le script est fourni pour montrer comment la base a ete fabriquee.
Le fichier boutique.db est deja livre : il n'est pas necessaire de le rejouer.
"""

import csv
import sqlite3
from pathlib import Path

DONNEES = Path(__file__).parent
BASE = DONNEES / "boutique.db"

SCHEMA = """
DROP TABLE IF EXISTS vente;
DROP TABLE IF EXISTS article;

CREATE TABLE article (
    reference   TEXT PRIMARY KEY,
    nom         TEXT    NOT NULL,
    categorie   TEXT    NOT NULL,
    taille      TEXT    NOT NULL,
    couleur     TEXT    NOT NULL,
    prix_achat  REAL    NOT NULL,
    prix_vente  REAL    NOT NULL,
    stock       INTEGER NOT NULL
);

CREATE TABLE vente (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    date             TEXT    NOT NULL,
    boutique         TEXT    NOT NULL,
    reference        TEXT    NOT NULL,
    quantite         INTEGER NOT NULL,
    remise_pourcent  INTEGER NOT NULL,
    FOREIGN KEY (reference) REFERENCES article (reference)
);

CREATE INDEX idx_vente_boutique ON vente (boutique);
CREATE INDEX idx_vente_date ON vente (date);
"""


def lire(nom):
    """Renvoie la liste des lignes d'un CSV sous forme de dictionnaires."""
    with open(DONNEES / nom, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def construire():
    connexion = sqlite3.connect(BASE)
    connexion.execute("PRAGMA foreign_keys = ON")
    connexion.executescript(SCHEMA)

    articles = [(a["reference"], a["nom"], a["categorie"], a["taille"],
                 a["couleur"], float(a["prix_achat"]), float(a["prix_vente"]),
                 int(a["stock"]))
                for a in lire("articles.csv")]
    connexion.executemany(
        "INSERT INTO article VALUES (?, ?, ?, ?, ?, ?, ?, ?)", articles)

    ventes = [(v["date"], v["boutique"], v["reference"],
               int(v["quantite"]), int(v["remise_pourcent"]))
              for v in lire("ventes_octobre.csv")]
    connexion.executemany(
        "INSERT INTO vente (date, boutique, reference, quantite, remise_pourcent)"
        " VALUES (?, ?, ?, ?, ?)", ventes)

    connexion.commit()
    print(f"{len(articles)} articles et {len(ventes)} ventes ecrits dans {BASE.name}")
    connexion.close()


if __name__ == "__main__":
    construire()
