"""Étape 6 : création des boutiques et nomination des gérants."""

import re
from datetime import date

from mercier import securite

MOTIF_CODE = re.compile(r"^[a-z][a-z0-9-]{2,29}$")


def valider_code(code):
    """Un code de boutique : minuscules, chiffres et traits d'union."""
    if not MOTIF_CODE.match(code):
        raise ValueError(
            "Code invalide : minuscules, chiffres et traits d'union, "
            "de 3 à 30 caractères, commençant par une lettre.")
    return code


def creer_boutique(con, code, ville, surface_m2, objectif_mensuel,
                   ouverture=None):
    """Crée une boutique dans la dimension. Renvoie son code."""
    valider_code(code)
    if objectif_mensuel < 0:
        raise ValueError("L'objectif ne peut pas être négatif.")
    if con.execute("SELECT 1 FROM dim_boutique WHERE code = ?",
                   (code,)).fetchone():
        raise ValueError(f"La boutique {code} existe déjà.")

    con.execute("""
        INSERT INTO dim_boutique
            (code, ville, surface_m2, objectif_mensuel, ouverture, active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (code, ville or None, int(surface_m2), float(objectif_mensuel),
          ouverture or date.today().isoformat()))
    return code


def nommer_gerant(con, boutique, identifiant, nom, motdepasse):
    """Crée un compte gérant rattaché à une boutique existante."""
    if not con.execute("SELECT 1 FROM dim_boutique WHERE code = ?",
                       (boutique,)).fetchone():
        raise ValueError(f"Boutique inconnue : {boutique}")
    if con.execute("SELECT 1 FROM utilisateur WHERE identifiant = ?",
                   (identifiant,)).fetchone():
        raise ValueError(f"L'identifiant {identifiant} est déjà pris.")
    return securite.creer_utilisateur(con, identifiant, nom, motdepasse,
                                      "gerant", boutique)


def desactiver_boutique(con, code):
    """Rend une boutique inactive sans effacer son historique de ventes."""
    con.execute("UPDATE dim_boutique SET active = 0 WHERE code = ?", (code,))


def lister_boutiques(con):
    return [dict(l) for l in con.execute(
        "SELECT * FROM dim_boutique ORDER BY active DESC, code")]


def lister_utilisateurs(con):
    return [dict(l) for l in con.execute(
        "SELECT identifiant, nom, role, boutique FROM utilisateur ORDER BY role, identifiant")]
