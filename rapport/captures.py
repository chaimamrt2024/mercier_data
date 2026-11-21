"""Prend les captures d'écran du projet avec Edge (Playwright)."""
import html
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJET = Path(sys.argv[1])
SORTIES = PROJET / "rapport" / "sorties"
CAPTURES = PROJET / "captures"
CAPTURES.mkdir(exist_ok=True)
URL = "http://127.0.0.1:8000"
MDP = "mercier2026"

TERMINAL = """<html><body style="margin:0;background:#0c0c0c">
<div style="background:#2d2d2d;color:#ccc;font:13px Segoe UI;padding:6px 12px">{titre}</div>
<pre style="margin:0;padding:14px 16px;color:#e6e6e6;font:14px Consolas,monospace;
white-space:pre-wrap">{texte}</pre></body></html>"""


def terminal(page, nom, titre, texte):
    page.set_viewport_size({"width": 1000, "height": 200})
    page.set_content(TERMINAL.format(titre=html.escape(titre), texte=html.escape(texte)))
    page.screenshot(path=CAPTURES / nom, full_page=True)


def capture(page, nom, chemin, pleine=True):
    page.goto(URL + chemin)
    page.wait_for_load_state("networkidle")
    page.screenshot(path=CAPTURES / nom, full_page=pleine)


def connecter(page, identifiant, mdp=MDP):
    page.goto(URL + "/connexion")
    page.fill("input[name=identifiant]", identifiant)
    page.fill("input[name=motdepasse]", mdp)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")


def lire(nom):
    return (SORTIES / nom).read_text(encoding="utf-8")


with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge")
    t = nav.new_page()
    racine = f"PowerShell — {PROJET}"
    terminal(t, "01_venv_installation.png", racine, lire("venv.txt"))
    terminal(t, "02_chaine_idempotence.png", racine, lire("chaine.txt"))
    terminal(t, "03_manifeste.png", racine + r"\zone_brute\<lot>\_manifeste.json", lire("manifeste.txt"))
    terminal(t, "04_cli_comptes_tarif.png", racine, lire("cli.txt"))
    terminal(t, "05_tests_pytest.png", racine, "(.venv) > python -m pytest tests/ -v\n" + lire("tests.txt"))
    terminal(t, "20_controle_complet.png", racine,
             "(.venv) > python tests/controle_complet.py\n" + lire("controle_complet.txt"))

    vue = {"width": 1280, "height": 800}
    ctx = nav.new_context(viewport=vue)
    page = ctx.new_page()
    capture(page, "06_connexion.png", "/connexion", pleine=False)
    page.fill("input[name=identifiant]", "julie")
    page.fill("input[name=motdepasse]", "mauvais")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=CAPTURES / "07_connexion_erreur.png")
    capture(page, "17_sante.png", "/sante", pleine=False)

    connecter(page, "claire")
    page.screenshot(path=CAPTURES / "08_tableau_admin.png", full_page=True)
    capture(page, "09_tableau_admin_filtre_paris.png", "/?boutique=paris-marais")
    capture(page, "13_administration.png", "/administration")
    page.fill("form[action='/administration/boutique'] input[name=code]", "bordeaux-centre")
    page.fill("form[action='/administration/boutique'] input[name=ville]", "Bordeaux")
    page.fill("form[action='/administration/boutique'] input[name=surface_m2]", "80")
    page.fill("form[action='/administration/boutique'] input[name=objectif_mensuel]", "3000")
    page.screenshot(path=CAPTURES / "14a_formulaire_boutique.png")
    page.click("form[action='/administration/boutique'] button")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=CAPTURES / "14b_boutique_creee.png", full_page=True)
    page.fill("form[action='/administration/boutique'] input[name=code]", "Bordeaux Lac")
    page.click("form[action='/administration/boutique'] button")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=CAPTURES / "15_code_invalide.png")
    page.select_option("select[name=boutique]", "bordeaux-centre")
    page.fill("input[name=identifiant]", "marc")
    page.fill("form[action='/administration/gerant'] input[name=nom]", "Marc Durand")
    page.fill("form[action='/administration/gerant'] input[name=motdepasse]", MDP)
    page.click("form[action='/administration/gerant'] button")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=CAPTURES / "15b_gerant_nomme.png", full_page=True)
    capture(page, "18_api_boutiques_json.png", "/api/boutiques", pleine=False)
    capture(page, "19_api_qualite_json.png", "/api/qualite", pleine=False)
    capture(page, "16_documentation_docs.png", "/docs")
    page.get_by_text("/api/boutiques", exact=True).first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=CAPTURES / "16b_docs_route_boutiques.png")
    ctx.close()

    ctx = nav.new_context(viewport=vue)
    page = ctx.new_page()
    connecter(page, "julie")
    page.screenshot(path=CAPTURES / "10_tableau_gerante_lyon.png", full_page=True)
    capture(page, "11_gerante_triche_paris.png", "/?boutique=paris-marais")
    capture(page, "12_gerante_admin_403.png", "/administration", pleine=False)
    capture(page, "12b_gerante_api_qualite_403.png", "/api/qualite", pleine=False)
    ctx.close()
    nav.close()

print("\n".join(sorted(f.name for f in CAPTURES.iterdir())))
