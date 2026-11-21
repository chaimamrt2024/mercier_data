"""Étape 7 : mots de passe, authentification et cloisonnement."""

import hashlib
import hmac
import secrets

ITERATIONS = 200_000


def hacher(motdepasse, sel=None):
    """Renvoie le couple (sel, empreinte) d'un mot de passe."""
    sel = sel or secrets.token_hex(16)
    empreinte = hashlib.pbkdf2_hmac("sha256", motdepasse.encode("utf-8"),
                                    bytes.fromhex(sel), ITERATIONS)
    return sel, empreinte.hex()


def verifier(motdepasse, sel, empreinte_attendue):
    """Vérifie un mot de passe en temps constant."""
    _, empreinte = hacher(motdepasse, sel)
    return hmac.compare_digest(empreinte, empreinte_attendue)


def creer_utilisateur(con, identifiant, nom, motdepasse, role, boutique=None):
    """Crée un compte. Le mot de passe n'est jamais stocké en clair."""
    if role not in ("administrateur", "gerant"):
        raise ValueError(f"Rôle inconnu : {role}")
    if len(motdepasse) < 8:
        raise ValueError("Le mot de passe doit faire au moins 8 caractères.")
    sel, empreinte = hacher(motdepasse)
    con.execute("""
        INSERT INTO utilisateur (identifiant, nom, sel, empreinte, role, boutique)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (identifiant, nom, sel, empreinte, role, boutique))
    return identifiant


def authentifier(con, identifiant, motdepasse):
    """Renvoie le compte si les identifiants sont bons, sinon None."""
    ligne = con.execute(
        "SELECT * FROM utilisateur WHERE identifiant = ?",
        (identifiant,)).fetchone()

    if ligne is None:
        # On hache quand même, pour que la durée de réponse ne révèle pas
        # si l'identifiant existe.
        hacher(motdepasse, secrets.token_hex(16))
        return None

    if not verifier(motdepasse, ligne["sel"], ligne["empreinte"]):
        return None

    return {"id": ligne["id"], "identifiant": ligne["identifiant"],
            "nom": ligne["nom"], "role": ligne["role"],
            "boutique": ligne["boutique"]}


def boutiques_visibles(con, compte):
    """Les boutiques que ce compte a le droit de consulter.

    C'est ici que se joue le cloisonnement : un gérant ne voit que la sienne.
    """
    if compte["role"] == "administrateur":
        return [l["code"] for l in con.execute(
            "SELECT code FROM dim_boutique WHERE active = 1 ORDER BY code")]
    return [compte["boutique"]] if compte["boutique"] else []
