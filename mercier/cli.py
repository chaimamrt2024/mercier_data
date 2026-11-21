"""Ligne de commande : python -m mercier.cli <commande>."""

import argparse
import json

from mercier import config, entrepot, ingestion, qualite, securite, tarif_java

# Comptes de démonstration (environnement de développement uniquement)
COMPTES_DEMO = [
    ("claire", "Claire Mercier", "administrateur", None),
    ("julie", "Julie Martin", "gerant", "lyon-presquile"),
]
MOTDEPASSE_DEMO = "mercier2026"


def chaine():
    """Ingestion, contrôle et chargement d'un lot."""
    manifeste = ingestion.ingerer()
    lot = config.ZONE_BRUTE / manifeste["lot"]
    print(f"Lot {manifeste['lot']} : {len(manifeste['recus'])} fichiers reçus")

    catalogue = qualite.lire_catalogue(lot)
    configuration = qualite.lire_configuration(lot)
    codes = {b["code"] for b in configuration["boutiques"]}
    valides, rejets = qualite.controler_ventes(lot, catalogue, codes)
    r = qualite.rapport(valides, rejets)
    print(f"Contrôle : {r['acceptees']} acceptées, {r['rejetees']} rejetées "
          f"({r['taux_acceptation']} pour cent)")
    for rejet in rejets:
        print("   ", rejet)

    print(f"Moteur tarifaire : {tarif_java.moteur_disponible()}")
    resultat = entrepot.charger(manifeste["lot"], catalogue, configuration,
                                valides, rejets, tarif_java.montant_ligne)
    print(f"Chargement : {resultat['inserees']} nouvelles lignes de faits")


def comptes():
    """Crée les comptes de démonstration s'ils n'existent pas."""
    entrepot.creer_schema()
    con = entrepot.connexion()
    try:
        with con:
            for identifiant, nom, role, boutique in COMPTES_DEMO:
                if con.execute("SELECT 1 FROM utilisateur WHERE identifiant = ?",
                               (identifiant,)).fetchone():
                    print(f"{identifiant} existe déjà")
                    continue
                securite.creer_utilisateur(con, identifiant, nom, MOTDEPASSE_DEMO,
                                           role, boutique)
                print(f"compte créé : {identifiant} ({role})")
    finally:
        con.close()


def tarif():
    """Compare les voies de calcul du montant."""
    print("voie retenue :", tarif_java.moteur_disponible())
    for nom, fonction in [("sous-processus", tarif_java.montant_par_sous_processus),
                          ("jpype", tarif_java.montant_par_jpype),
                          ("python", tarif_java.montant_en_python)]:
        try:
            print(f"{nom:<15}: {fonction(19.90, 2, 10)}")
        except Exception as erreur:
            print(f"{nom:<15}: indisponible ({type(erreur).__name__})")
    print("point d'entrée :", tarif_java.montant_ligne(169.0, 1, 15))


def main():
    parseur = argparse.ArgumentParser(prog="mercier")
    parseur.add_argument("commande", choices=["chaine", "comptes", "tarif", "config"])
    args = parseur.parse_args()
    if args.commande == "chaine":
        chaine()
    elif args.commande == "comptes":
        comptes()
    elif args.commande == "tarif":
        tarif()
    else:
        print(json.dumps(config.resume(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
