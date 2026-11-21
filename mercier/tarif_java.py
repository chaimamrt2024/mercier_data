"""Étape 4 : appel du moteur tarifaire Java (JPype, sous-processus ou repli Python)."""

import subprocess
from functools import lru_cache

from mercier import config

_JVM = None


def demarrer_jvm():
    """Démarre la JVM une seule fois par programme."""
    global _JVM
    if _JVM is None:
        import jpype
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[str(config.CLASSES_JAVA)])
        _JVM = jpype.JClass("Tarif")
    return _JVM


def montant_par_jpype(prix, quantite, remise):
    """Appelle la classe Java dans la JVM du processus Python."""
    return float(demarrer_jvm().montantLigne(float(prix), int(quantite), int(remise)))


def montant_par_sous_processus(prix, quantite, remise):
    """Appelle la classe Java en lançant une JVM, via la ligne de commande."""
    resultat = subprocess.run(
        ["java", "-cp", str(config.CLASSES_JAVA), "Tarif",
         str(prix), str(quantite), str(remise)],
        capture_output=True, text=True, check=True)
    return float(resultat.stdout.strip().splitlines()[-1])


def montant_en_python(prix, quantite, remise):
    """Repli quand Java n'est pas disponible : même règle que Tarif.java."""
    if prix < 0 or quantite < 1:
        raise ValueError("Prix negatif ou quantite nulle.")
    if not 0 <= remise <= 100:
        raise ValueError("Remise hors bornes.")
    return round(prix * quantite * (1 - remise / 100.0), 2)


@lru_cache(maxsize=1)
def moteur_disponible():
    """Choisit la meilleure voie disponible sur cette machine."""
    try:
        import jpype  # noqa: F401
        demarrer_jvm()
        return "jpype"
    except Exception:
        pass
    try:
        subprocess.run(["java", "-version"], capture_output=True, check=True)
        return "sous-processus"
    except Exception:
        return "python"


def montant_ligne(prix, quantite, remise=0):
    """Point d'entrée unique du reste de la plateforme."""
    voie = moteur_disponible()
    if voie == "jpype":
        return montant_par_jpype(prix, quantite, remise)
    if voie == "sous-processus":
        return montant_par_sous_processus(prix, quantite, remise)
    return montant_en_python(prix, quantite, remise)
