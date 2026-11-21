"""Étape 5 : restitution web (FastAPI), avec administration et sécurité."""

import os
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from mercier import __version__, administration, config, entrepot, indicateurs, securite

if config.resume()["cle_par_defaut"] and os.environ.get("MERCIER_ENV") == "production":
    raise SystemExit("Refus de démarrer : la clé secrète n'a pas été changée.")

DOSSIER = Path(__file__).parent

app = FastAPI(title="Mercier Data", version=__version__)
app.add_middleware(SessionMiddleware, secret_key=config.CLE_SECRETE,
                   session_cookie="mercier",
                   https_only=os.environ.get("MERCIER_ENV") == "production")
app.mount("/static", StaticFiles(directory=DOSSIER / "static"), name="static")
templates = Jinja2Templates(directory=DOSSIER / "templates")

entrepot.creer_schema()


def euros(montant, decimales=0):
    """12345.6 devient 12 345 : espace insécable, virgule décimale."""
    return f"{montant:,.{decimales}f}".replace(",", " ").replace(".", ",")


templates.env.filters["euros"] = euros


# --- Dépendances -----------------------------------------------------------

def base():
    """Ouvre une connexion par requête, et la referme à la fin."""
    con = entrepot.connexion()
    try:
        yield con
    finally:
        con.close()


def compte_courant(requete: Request):
    return requete.session.get("compte")


def exige_connexion(requete: Request):
    """Dépendance des routes protégées."""
    compte = requete.session.get("compte")
    if compte is None:
        raise HTTPException(status_code=401, detail="Connexion requise")
    return compte


def exige_administrateur(compte=Depends(exige_connexion)):
    """Dépendance des routes réservées à l'administrateur."""
    if compte["role"] != "administrateur":
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur")
    return compte


# --- Exploitation ----------------------------------------------------------

@app.get("/sante", tags=["exploitation"])
def sante(con=Depends(base)):
    """Point de contrôle, appelé par la supervision. Sans authentification."""
    ventes = con.execute("SELECT COUNT(*) FROM fait_vente").fetchone()[0]
    return {"etat": "ok", "version": __version__, "faits": ventes}


# --- Connexion -------------------------------------------------------------

@app.get("/connexion", response_class=HTMLResponse, tags=["pages"])
def page_connexion(requete: Request, erreur: str = ""):
    return templates.TemplateResponse(requete, "connexion.html", {"erreur": erreur})


@app.post("/connexion", tags=["pages"])
def valider_connexion(requete: Request, identifiant: str = Form(...),
                      motdepasse: str = Form(...), con=Depends(base)):
    compte = securite.authentifier(con, identifiant, motdepasse)
    if compte is None:
        return RedirectResponse("/connexion?erreur=1", status_code=303)
    requete.session["compte"] = compte
    return RedirectResponse("/", status_code=303)


@app.get("/deconnexion", tags=["pages"])
def deconnexion(requete: Request):
    requete.session.clear()
    return RedirectResponse("/connexion", status_code=303)


# --- Tableau de bord -------------------------------------------------------

@app.get("/", response_class=HTMLResponse, tags=["pages"])
def tableau_de_bord(requete: Request, boutique: str = "", con=Depends(base)):
    compte = compte_courant(requete)
    if compte is None:
        return RedirectResponse("/connexion", status_code=303)

    visibles = securite.boutiques_visibles(con, compte)

    # Le filtre ne peut jamais élargir le périmètre autorisé.
    perimetre = [boutique] if boutique in visibles else visibles
    if boutique not in visibles:
        boutique = ""

    return templates.TemplateResponse(requete, "tableau.html", {
        "compte": compte,
        "synthese": indicateurs.synthese(con, perimetre),
        "boutiques": indicateurs.par_boutique(con, perimetre),
        "categories": indicateurs.par_categorie(con, perimetre),
        "meilleures": indicateurs.meilleures_ventes(con, perimetre),
        "semaines": indicateurs.evolution(con, perimetre),
        "visibles": visibles,
        "filtre": boutique,
        "lot": indicateurs.qualite_dernier_lot(con),
    })


# --- Administration --------------------------------------------------------

@app.get("/administration", response_class=HTMLResponse, tags=["administration"])
def page_administration(requete: Request, message: str = "", erreur: str = "",
                        compte=Depends(exige_administrateur), con=Depends(base)):
    return templates.TemplateResponse(requete, "administration.html", {
        "compte": compte,
        "boutiques": administration.lister_boutiques(con),
        "utilisateurs": administration.lister_utilisateurs(con),
        "message": message,
        "erreur": erreur,
    })


@app.post("/administration/boutique", tags=["administration"])
def creation_boutique(code: str = Form(...), ville: str = Form(""),
                      surface_m2: int = Form(0),
                      objectif_mensuel: float = Form(0),
                      con=Depends(base),
                      compte=Depends(exige_administrateur)):
    try:
        with con:
            administration.creer_boutique(con, code.strip().lower(),
                                          ville.strip(), surface_m2,
                                          objectif_mensuel)
    except ValueError as erreur:
        return RedirectResponse(f"/administration?erreur={quote(str(erreur))}",
                                status_code=303)
    return RedirectResponse(f"/administration?message={quote(f'Boutique {code} créée')}",
                            status_code=303)


@app.post("/administration/gerant", tags=["administration"])
def creation_gerant(boutique: str = Form(...), identifiant: str = Form(...),
                    nom: str = Form(...), motdepasse: str = Form(...),
                    con=Depends(base), compte=Depends(exige_administrateur)):
    try:
        with con:
            administration.nommer_gerant(con, boutique, identifiant.strip().lower(),
                                         nom.strip(), motdepasse)
    except ValueError as erreur:
        return RedirectResponse(f"/administration?erreur={quote(str(erreur))}",
                                status_code=303)
    return RedirectResponse(
        f"/administration?message={quote(f'Gérant {identifiant} nommé pour {boutique}')}",
        status_code=303)


@app.post("/administration/desactiver", tags=["administration"])
def desactivation_boutique(code: str = Form(...), con=Depends(base),
                           compte=Depends(exige_administrateur)):
    with con:
        administration.desactiver_boutique(con, code)
    return RedirectResponse(f"/administration?message={quote(f'Boutique {code} désactivée')}",
                            status_code=303)


# --- API JSON --------------------------------------------------------------

@app.get("/api/synthese", tags=["api"])
def api_synthese(compte=Depends(exige_connexion), con=Depends(base)):
    """Chiffres globaux sur le périmètre du compte connecté."""
    return indicateurs.synthese(con, securite.boutiques_visibles(con, compte))


@app.get("/api/boutiques", tags=["api"])
def api_boutiques(compte=Depends(exige_connexion), con=Depends(base)):
    """Chiffre d'affaires par boutique, confronté à l'objectif."""
    return indicateurs.par_boutique(con, securite.boutiques_visibles(con, compte))


@app.get("/api/categories", tags=["api"])
def api_categories(compte=Depends(exige_connexion), con=Depends(base)):
    """Chiffre d'affaires par catégorie d'article."""
    return indicateurs.par_categorie(con, securite.boutiques_visibles(con, compte))


@app.get("/api/qualite", tags=["api"])
def api_qualite(compte=Depends(exige_administrateur), con=Depends(base)):
    """État du dernier chargement. Réservé à l'administrateur."""
    return indicateurs.qualite_dernier_lot(con) or {}
