"""Étape 3 : l'entrepôt SQLite, modèle en étoile."""

import sqlite3
from datetime import date

from mercier import config

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_article (
    reference  TEXT PRIMARY KEY,
    nom        TEXT NOT NULL,
    categorie  TEXT NOT NULL,
    taille     TEXT NOT NULL,
    couleur    TEXT NOT NULL,
    prix_achat REAL NOT NULL,
    prix_vente REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_boutique (
    code             TEXT PRIMARY KEY,
    ville            TEXT,
    surface_m2       INTEGER NOT NULL DEFAULT 0,
    objectif_mensuel REAL NOT NULL DEFAULT 0,
    ouverture        TEXT,
    active           INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dim_date (
    jour    TEXT PRIMARY KEY,
    annee   INTEGER NOT NULL,
    mois    INTEGER NOT NULL,
    semaine INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fait_vente (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    jour            TEXT NOT NULL REFERENCES dim_date (jour),
    boutique        TEXT NOT NULL REFERENCES dim_boutique (code),
    reference       TEXT NOT NULL REFERENCES dim_article (reference),
    quantite        INTEGER NOT NULL,
    remise_pourcent INTEGER NOT NULL,
    montant_brut    REAL NOT NULL,
    montant_net     REAL NOT NULL,
    UNIQUE (jour, boutique, reference, quantite, remise_pourcent)
);

CREATE TABLE IF NOT EXISTS rejet (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    lot     TEXT NOT NULL,
    numero  INTEGER NOT NULL,
    motif   TEXT NOT NULL,
    contenu TEXT,
    UNIQUE (lot, numero)
);

CREATE TABLE IF NOT EXISTS chargement (
    lot        TEXT PRIMARY KEY,
    execute_le TEXT NOT NULL,
    acceptees  INTEGER NOT NULL,
    rejetees   INTEGER NOT NULL,
    inserees   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS utilisateur (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    identifiant TEXT NOT NULL UNIQUE,
    nom         TEXT NOT NULL,
    sel         TEXT NOT NULL,
    empreinte   TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('administrateur', 'gerant')),
    boutique    TEXT REFERENCES dim_boutique (code)
);

CREATE INDEX IF NOT EXISTS idx_vente_boutique ON fait_vente (boutique);
CREATE INDEX IF NOT EXISTS idx_vente_jour ON fait_vente (jour);
"""


def connexion(chemin=None):
    """Ouvre une connexion avec les clés étrangères actives."""
    con = sqlite3.connect(chemin or config.ENTREPOT, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def creer_schema(chemin=None):
    con = connexion(chemin)
    try:
        con.executescript(SCHEMA)
    finally:
        con.close()


def charger_articles(con, catalogue):
    """Met à jour la dimension article, sans perdre les lignes existantes."""
    con.executemany("""
        INSERT INTO dim_article
            (reference, nom, categorie, taille, couleur, prix_achat, prix_vente)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (reference) DO UPDATE SET
            nom = excluded.nom,
            prix_achat = excluded.prix_achat,
            prix_vente = excluded.prix_vente
    """, [(a["reference"], a["nom"], a["categorie"], a["taille"],
           a["couleur"], a["prix_achat"], a["prix_vente"])
          for a in catalogue.values()])


def charger_boutiques(con, configuration):
    """Met à jour la dimension boutique à partir de boutiques.json."""
    con.executemany("""
        INSERT INTO dim_boutique (code, ville, surface_m2, objectif_mensuel, ouverture)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (code) DO UPDATE SET
            ville = excluded.ville,
            surface_m2 = excluded.surface_m2,
            objectif_mensuel = excluded.objectif_mensuel
    """, [(b["code"], b["ville"], b["surface_m2"], b["objectif_mensuel"],
           b["ouverture"]) for b in configuration["boutiques"]])


def charger_dates(con, ventes):
    """Ajoute les jours rencontrés dans la dimension date."""
    jours = {v["date"] for v in ventes}
    lignes = []
    for jour in sorted(jours):
        d = date.fromisoformat(jour)
        lignes.append((jour, d.year, d.month, d.isocalendar()[1]))
    con.executemany(
        "INSERT INTO dim_date VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING", lignes)


def charger_ventes(con, ventes, catalogue, calcul_montant):
    """Insère les faits. Renvoie le nombre de lignes réellement ajoutées."""
    avant = con.execute("SELECT COUNT(*) FROM fait_vente").fetchone()[0]
    lignes = []
    for vente in ventes:
        prix = catalogue[vente["reference"]]["prix_vente"]
        brut = round(prix * vente["quantite"], 2)
        net = calcul_montant(prix, vente["quantite"], vente["remise_pourcent"])
        lignes.append((vente["date"], vente["boutique"], vente["reference"],
                       vente["quantite"], vente["remise_pourcent"], brut, net))

    con.executemany("""
        INSERT INTO fait_vente
            (jour, boutique, reference, quantite, remise_pourcent,
             montant_brut, montant_net)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT DO NOTHING
    """, lignes)
    apres = con.execute("SELECT COUNT(*) FROM fait_vente").fetchone()[0]
    return apres - avant


def charger_rejets(con, lot, rejets):
    """Trace les lignes écartées du lot."""
    con.executemany("""
        INSERT INTO rejet (lot, numero, motif, contenu)
        VALUES (:lot, :numero, :motif, :contenu)
        ON CONFLICT DO NOTHING
    """, [{"lot": lot, **r.en_dictionnaire()} for r in rejets])


def charger(lot, catalogue, configuration, ventes, rejets, calcul_montant,
            chemin=None):
    """Charge un lot complet dans l'entrepôt, en une seule transaction."""
    creer_schema(chemin)
    con = connexion(chemin)
    try:
        with con:  # valide à la sortie, annule si erreur
            charger_articles(con, catalogue)
            charger_boutiques(con, configuration)
            charger_dates(con, ventes)
            inserees = charger_ventes(con, ventes, catalogue, calcul_montant)
            charger_rejets(con, lot, rejets)
            con.execute("""
                INSERT INTO chargement (lot, execute_le, acceptees, rejetees, inserees)
                VALUES (?, datetime('now'), ?, ?, ?)
                ON CONFLICT (lot) DO UPDATE SET
                    execute_le = excluded.execute_le,
                    inserees = excluded.inserees
            """, (lot, len(ventes), len(rejets), inserees))
        return {"lot": lot, "acceptees": len(ventes), "rejetees": len(rejets),
                "inserees": inserees}
    finally:
        con.close()
