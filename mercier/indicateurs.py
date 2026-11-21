"""Requêtes de restitution, toujours filtrées par les boutiques autorisées."""

import json


def _filtre(boutiques, colonne="v.boutique"):
    """Fabrique la clause IN et ses paramètres, pour le cloisonnement."""
    marques = ", ".join("?" for _ in boutiques)
    return f"{colonne} IN ({marques})", list(boutiques)


def synthese(con, boutiques):
    if not boutiques:
        return {"ventes": 0, "pieces": 0, "chiffre_affaires": 0.0,
                "objectif": 0.0, "taux_objectif": 0.0}
    clause, params = _filtre(boutiques)
    ligne = dict(con.execute(f"""
        SELECT COUNT(*) AS ventes,
               COALESCE(SUM(v.quantite), 0) AS pieces,
               COALESCE(ROUND(SUM(v.montant_net), 2), 0) AS chiffre_affaires
        FROM fait_vente AS v WHERE {clause}
    """, params).fetchone())
    clause_b, params_b = _filtre(boutiques, "code")
    objectif = con.execute(
        f"SELECT COALESCE(SUM(objectif_mensuel), 0) FROM dim_boutique WHERE {clause_b}",
        params_b).fetchone()[0]
    ligne["objectif"] = objectif
    ligne["taux_objectif"] = round(100 * ligne["chiffre_affaires"] / objectif, 1) if objectif else 0.0
    return ligne


def par_boutique(con, boutiques):
    """Chiffre d'affaires de chaque boutique, comparé à son objectif."""
    if not boutiques:
        return []
    clause, params = _filtre(boutiques, "b.code")
    lignes = con.execute(f"""
        SELECT b.code, COALESCE(b.ville, 'En ligne') AS libelle,
               b.objectif_mensuel AS objectif,
               COUNT(v.id) AS ventes,
               COALESCE(ROUND(SUM(v.montant_net), 2), 0) AS chiffre_affaires
        FROM dim_boutique AS b
        LEFT JOIN fait_vente AS v ON v.boutique = b.code
        WHERE {clause}
        GROUP BY b.code
        ORDER BY chiffre_affaires DESC
    """, params).fetchall()
    resultat = []
    for l in lignes:
        d = dict(l)
        d["taux"] = round(100 * d["chiffre_affaires"] / d["objectif"], 1) if d["objectif"] else None
        resultat.append(d)
    return resultat


def par_categorie(con, boutiques):
    if not boutiques:
        return []
    clause, params = _filtre(boutiques)
    return [dict(l) for l in con.execute(f"""
        SELECT a.categorie, SUM(v.quantite) AS pieces,
               ROUND(SUM(v.montant_net), 2) AS chiffre_affaires
        FROM fait_vente AS v JOIN dim_article AS a ON a.reference = v.reference
        WHERE {clause}
        GROUP BY a.categorie ORDER BY chiffre_affaires DESC
    """, params)]


def meilleures_ventes(con, boutiques, limite=5):
    if not boutiques:
        return []
    clause, params = _filtre(boutiques)
    return [dict(l) for l in con.execute(f"""
        SELECT a.reference, a.nom, SUM(v.quantite) AS pieces,
               ROUND(SUM(v.montant_net), 2) AS chiffre_affaires
        FROM fait_vente AS v JOIN dim_article AS a ON a.reference = v.reference
        WHERE {clause}
        GROUP BY a.reference ORDER BY chiffre_affaires DESC LIMIT ?
    """, params + [limite])]


def evolution(con, boutiques):
    """Chiffre d'affaires par semaine."""
    if not boutiques:
        return []
    clause, params = _filtre(boutiques)
    return [dict(l) for l in con.execute(f"""
        SELECT d.semaine, COUNT(*) AS ventes,
               ROUND(SUM(v.montant_net), 2) AS chiffre_affaires
        FROM fait_vente AS v JOIN dim_date AS d ON d.jour = v.jour
        WHERE {clause}
        GROUP BY d.semaine ORDER BY d.semaine
    """, params)]


def qualite_dernier_lot(con):
    """Dernier chargement et ses rejets."""
    lot = con.execute(
        "SELECT * FROM chargement ORDER BY execute_le DESC, lot DESC LIMIT 1").fetchone()
    if lot is None:
        return None
    lot = dict(lot)
    total = lot["acceptees"] + lot["rejetees"]
    lot["taux_acceptation"] = round(100 * lot["acceptees"] / total, 2) if total else 0.0
    lot["rejets"] = [{"numero": r["numero"], "motif": r["motif"],
                      "contenu": json.loads(r["contenu"])}
                     for r in con.execute(
                         "SELECT * FROM rejet WHERE lot = ? ORDER BY numero", (lot["lot"],))]
    return lot
