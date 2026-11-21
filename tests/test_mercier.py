import json

import pytest

from mercier import administration, entrepot, ingestion, qualite, securite, tarif_java
from mercier.config import SOURCES


@pytest.fixture
def base(tmp_path):
    """Un entrepôt vide et jetable, propre à chaque test."""
    chemin = tmp_path / "test.db"
    entrepot.creer_schema(chemin)
    con = entrepot.connexion(chemin)
    yield con
    con.close()


def test_ingestion_cree_un_manifeste(tmp_path):
    manifeste = ingestion.ingerer(SOURCES, tmp_path, "20261118_200000")
    assert manifeste["manquants"] == []
    assert len(manifeste["recus"]) == 4
    assert (tmp_path / "20261118_200000" / "_manifeste.json").exists()


def test_controle_qualite_sept_rejets():
    catalogue = qualite.lire_catalogue(SOURCES)
    codes = {b["code"] for b in qualite.lire_configuration(SOURCES)["boutiques"]}
    valides, rejets = qualite.controler_ventes(SOURCES, catalogue, codes)
    r = qualite.rapport(valides, rejets)
    assert r["acceptees"] == 122
    assert r["rejetees"] == 7
    assert r["taux_acceptation"] == 94.57


def test_chargement_idempotent(tmp_path):
    lot = SOURCES
    catalogue = qualite.lire_catalogue(lot)
    configuration = qualite.lire_configuration(lot)
    codes = {b["code"] for b in configuration["boutiques"]}
    valides, rejets = qualite.controler_ventes(lot, catalogue, codes)
    chemin = tmp_path / "e.db"
    premier = entrepot.charger("a", catalogue, configuration, valides, rejets,
                               tarif_java.montant_en_python, chemin)
    second = entrepot.charger("b", catalogue, configuration, valides, rejets,
                              tarif_java.montant_en_python, chemin)
    assert premier["inserees"] == 122
    assert second["inserees"] == 0


def test_trois_voies_meme_resultat():
    assert tarif_java.montant_en_python(19.90, 2, 10) == 35.82
    assert tarif_java.montant_ligne(19.90, 2, 10) == 35.82


def test_deux_comptes_meme_mot_de_passe_ont_des_empreintes_differentes(base):
    with base:
        securite.creer_utilisateur(base, "a", "A", "motdepasse1", "administrateur")
        securite.creer_utilisateur(base, "b", "B", "motdepasse1", "administrateur")
    empreintes = [l["empreinte"]
                  for l in base.execute("SELECT empreinte FROM utilisateur")]
    assert empreintes[0] != empreintes[1]


def test_code_boutique_invalide_refuse(base):
    with pytest.raises(ValueError):
        administration.creer_boutique(base, "Nantes Graslin", "Nantes", 70, 2600)


def test_cloisonnement(base):
    with base:
        administration.creer_boutique(base, "nantes-graslin", "Nantes", 70, 2600)
        administration.creer_boutique(base, "brest-siam", "Brest", 50, 1800)
        administration.nommer_gerant(base, "nantes-graslin", "sophie",
                                     "Sophie Garnier", "motdepasse1")
        securite.creer_utilisateur(base, "claire", "Claire", "motdepasse1",
                                   "administrateur")
    gerante = securite.authentifier(base, "sophie", "motdepasse1")
    admin = securite.authentifier(base, "claire", "motdepasse1")
    assert securite.boutiques_visibles(base, gerante) == ["nantes-graslin"]
    assert len(securite.boutiques_visibles(base, admin)) == 2
