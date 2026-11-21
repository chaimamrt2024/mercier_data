"""Étape 2 : contrôle de qualité des fichiers d'un lot."""

import csv
import json
from datetime import date
from pathlib import Path


class Rejet:
    """Une ligne écartée, avec sa raison."""

    def __init__(self, numero, motif, contenu):
        self.numero = numero
        self.motif = motif
        self.contenu = contenu

    def __str__(self):
        return f"ligne {self.numero:>3} | {self.motif}"

    def en_dictionnaire(self):
        return {"numero": self.numero, "motif": self.motif,
                "contenu": json.dumps(self.contenu, ensure_ascii=False)}


def lire_catalogue(lot):
    """Lit articles.csv et renvoie un dictionnaire indexé par référence."""
    catalogue = {}
    with open(Path(lot) / "articles.csv", encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            catalogue[ligne["reference"]] = {
                "reference": ligne["reference"],
                "nom": ligne["nom"],
                "categorie": ligne["categorie"],
                "taille": ligne["taille"],
                "couleur": ligne["couleur"],
                "prix_achat": float(ligne["prix_achat"]),
                "prix_vente": float(ligne["prix_vente"]),
            }
    return catalogue


def lire_configuration(lot):
    """Lit boutiques.json."""
    with open(Path(lot) / "boutiques.json", encoding="utf-8") as f:
        return json.load(f)


def controler_ventes(lot, catalogue, codes_boutiques):
    """Valide chaque vente du lot. Renvoie (ventes valides, rejets)."""
    valides, rejets, vues = [], [], set()

    with open(Path(lot) / "ventes_octobre.csv", encoding="utf-8") as f:
        for numero, ligne in enumerate(csv.DictReader(f), start=2):

            # 1. champs obligatoires
            if not all(ligne.get(c) for c in
                       ("date", "boutique", "reference", "quantite")):
                rejets.append(Rejet(numero, "champ obligatoire vide", ligne))
                continue

            # 2. date réelle
            try:
                jour = date.fromisoformat(ligne["date"])
            except ValueError:
                rejets.append(Rejet(numero, "date invalide", ligne))
                continue

            # 3. référence connue du catalogue
            if ligne["reference"] not in catalogue:
                rejets.append(Rejet(numero, "référence inconnue", ligne))
                continue

            # 4. boutique connue
            if ligne["boutique"] not in codes_boutiques:
                rejets.append(Rejet(numero, "boutique inconnue", ligne))
                continue

            # 5. valeurs numériques dans les bornes
            try:
                quantite = int(ligne["quantite"])
                remise = int(ligne["remise_pourcent"] or 0)
            except ValueError:
                rejets.append(Rejet(numero, "valeur non numérique", ligne))
                continue
            if quantite < 1:
                rejets.append(Rejet(numero, "quantité non positive", ligne))
                continue
            if not 0 <= remise <= 100:
                rejets.append(Rejet(numero, "remise hors bornes", ligne))
                continue

            # 6. doublon exact
            cle = (ligne["date"], ligne["boutique"], ligne["reference"],
                   quantite, remise)
            if cle in vues:
                rejets.append(Rejet(numero, "doublon exact", ligne))
                continue
            vues.add(cle)

            valides.append({"date": jour.isoformat(),
                            "boutique": ligne["boutique"],
                            "reference": ligne["reference"],
                            "quantite": quantite,
                            "remise_pourcent": remise})

    return valides, rejets


def rapport(valides, rejets):
    """Résumé chiffré du contrôle, à journaliser ou à afficher."""
    total = len(valides) + len(rejets)
    motifs = {}
    for rejet in rejets:
        motifs[rejet.motif] = motifs.get(rejet.motif, 0) + 1
    return {
        "lignes_lues": total,
        "acceptees": len(valides),
        "rejetees": len(rejets),
        "taux_acceptation": round(100 * len(valides) / total, 2) if total else 0.0,
        "motifs": motifs,
    }
