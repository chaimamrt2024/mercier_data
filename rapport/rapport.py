"""Génère le rapport HTML puis PDF du projet Mercier Data."""
import html
import inspect
import sys
from pathlib import Path

PROJET = Path(sys.argv[1])
sys.path.insert(0, str(PROJET))

from mercier import (administration, api, entrepot, indicateurs, ingestion,  # noqa: E402
                     qualite, securite, tarif_java)

SORTIES = PROJET / "rapport" / "sorties"


def code(texte, titre=""):
    t = f'<div class="fichier">{html.escape(titre)}</div>' if titre else ""
    return f'{t}<pre class="code">{html.escape(texte.strip())}</pre>'


def src(objet, fichier):
    return code(inspect.getsource(objet), fichier)


def fichier(chemin):
    return code((PROJET / chemin).read_text(encoding="utf-8"), chemin)


def sortie(nom):
    return f'<pre class="console">{html.escape((SORTIES / nom).read_text(encoding="utf-8").strip())}</pre>'


def img(nom, legende):
    return (f'<figure><img src="../captures/{nom}"><figcaption>{html.escape(legende)}'
            f'</figcaption></figure>')


ROUTES = [
    ("GET", "/sante", "aucune", "Point de santé : état, version, nombre de faits"),
    ("GET", "/connexion", "aucune", "Formulaire de connexion"),
    ("POST", "/connexion", "aucune", "Vérifie identifiant / mot de passe, ouvre la session"),
    ("GET", "/deconnexion", "aucune", "Vide la session"),
    ("GET", "/?boutique=…", "connecté", "Tableau de bord, filtré par les droits"),
    ("GET", "/administration", "administrateur", "Page d'administration"),
    ("POST", "/administration/boutique", "administrateur", "Création d'une boutique"),
    ("POST", "/administration/gerant", "administrateur", "Nomination d'un gérant"),
    ("POST", "/administration/desactiver", "administrateur", "Désactivation d'une boutique"),
    ("GET", "/api/synthese", "connecté", "Ventes, pièces, CA, taux d'objectif (JSON)"),
    ("GET", "/api/boutiques", "connecté", "CA par boutique comparé à l'objectif (JSON)"),
    ("GET", "/api/categories", "connecté", "CA par catégorie (JSON)"),
    ("GET", "/api/qualite", "administrateur", "Dernier lot chargé et ses rejets (JSON)"),
    ("GET", "/docs", "aucune", "Documentation interactive générée par FastAPI"),
]
lignes_routes = "".join(
    f"<tr><td><b>{m}</b></td><td><code>{html.escape(r)}</code></td><td>{a}</td><td>{d}</td></tr>"
    for m, r, a, d in ROUTES)

ARBO = """mercier_data/
├── .venv/                 environnement virtuel
├── donnees_sources/       fichiers reçus (jamais modifiés)
├── java/Tarif.java        composant Java (moteur de remises)
├── mercier/
│   ├── __init__.py        version du paquet
│   ├── config.py          configuration (variables d'environnement)
│   ├── ingestion.py       étape 1
│   ├── qualite.py         étape 2
│   ├── entrepot.py        étape 3
│   ├── tarif_java.py      étape 4
│   ├── api.py             étape 5 (+ routes des étapes 6 et 7)
│   ├── indicateurs.py     requêtes de restitution
│   ├── administration.py  étape 6
│   ├── securite.py        étape 7
│   ├── cli.py             ligne de commande
│   ├── templates/         base, connexion, tableau, administration
│   └── static/style.css
├── tests/                 test_mercier.py (pytest), controle_complet.py
├── zone_brute/            lots horodatés (créé par l'ingestion)
├── entrepot.db            entrepôt SQLite (créé par la chaîne)
├── captures/              captures d'écran du rapport
├── requirements.txt, Dockerfile, .dockerignore, .env.exemple, README.md"""

CMD_VENV = r"""python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pytest httpx        # pour les tests"""

CMD_LANCER = r""".venv\Scripts\activate
python -m mercier.cli chaine      # ingestion + qualité + chargement
python -m mercier.cli comptes     # comptes de démonstration
uvicorn mercier.api:app --reload  # puis ouvrir http://127.0.0.1:8000
python -m pytest tests/ -q"""

CSS = """
body{font-family:Segoe UI,Arial,sans-serif;color:#222;max-width:960px;margin:auto;padding:24px;line-height:1.45}
h1{color:#1f2a44;border-bottom:3px solid #1f2a44;padding-bottom:6px}
h2{color:#1f2a44;margin-top:34px;border-bottom:1px solid #ccc;padding-bottom:4px;page-break-after:avoid}
h3{margin-top:22px;page-break-after:avoid}
.garde{text-align:center;padding:120px 0 80px;page-break-after:always}
.garde h1{border:0;font-size:2.4em}
pre{white-space:pre-wrap;word-break:break-word;font:12px Consolas,monospace;border-radius:4px;padding:10px 12px}
pre.code{background:#f6f8fa;border:1px solid #e1e4e8}
pre.console{background:#0c0c0c;color:#e6e6e6}
.fichier{font:bold 12px Consolas,monospace;color:#555;margin-top:12px}
figure{margin:16px 0;text-align:center;page-break-inside:avoid}
figure img{max-width:100%;border:1px solid #ccc}
figcaption{font-size:.88em;color:#555;margin-top:4px}
table{border-collapse:collapse;width:100%;font-size:.9em;margin:10px 0}
th,td{border:1px solid #ccc;padding:5px 8px;text-align:left}
th{background:#eef0f4}
.note{background:#fff8e6;border-left:4px solid #c98a2b;padding:8px 12px}
"""

R = []
w = R.append
w(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Rapport Mercier Data</title><style>{CSS}</style></head><body>
<div class="garde"><h1>Projet Mercier Data</h1>
<p style="font-size:1.2em">Notions Python avancées — Master 1 DAT</p>
<p>Rapport de réalisation : code, routes et captures d'écran</p>
<p>Année universitaire 2025 / 2026</p></div>

<h2>1. Objectif du projet</h2>
<p>Atelier Mercier reçoit chaque nuit quatre fichiers (catalogue, ventes d'octobre, configuration
des boutiques, journal de caisse). Le projet construit une chaîne complète qui répond à la question :
<i>quel est le chiffre d'affaires par boutique, et quelles boutiques ont atteint leur objectif ?</i></p>
<p>La chaîne suit les huit étapes du sujet : ingestion, contrôle qualité, entrepôt SQLite en étoile,
appel du moteur tarifaire Java, restitution web avec FastAPI, administration, sécurité et mise en production.</p>

<h2>2. Environnement virtuel et installation</h2>
<p>L'environnement virtuel est créé avant toute installation, puis les dépendances sont installées
depuis <code>requirements.txt</code> (versions figées avec <code>==</code>).</p>
{code(CMD_VENV, 'Commandes (Windows)')}
{fichier('requirements.txt')}
{img('01_venv_installation.png', "Figure 1 — Environnement virtuel créé et paquets installés")}

<h2>3. Arborescence du projet</h2>
<pre class="code">{html.escape(ARBO)}</pre>
{fichier('mercier/config.py')}

<h2>4. Étape 1 : l'ingestion</h2>
<p>Les fichiers reçus ne sont jamais modifiés : ils sont copiés dans un lot horodaté de la zone brute,
avec une empreinte SHA-256 et un manifeste.</p>
{src(ingestion.ingerer, 'mercier/ingestion.py')}
{img('03_manifeste.png', "Figure 2 — Manifeste d'un lot (empreinte de articles.csv identique à celle du sujet)")}

<h2>5. Étape 2 : la qualité</h2>
<p>Six contrôles sont appliqués à chaque vente, du moins coûteux au plus coûteux. Une ligne écartée
reçoit un seul motif (le premier rencontré) et est tracée dans un objet <code>Rejet</code>.</p>
<p>Six anomalies (une par contrôle) ont été ajoutées en fin de <code>ventes_octobre.csv</code>
(lignes 125 à 130), comme dans le sujet ; le doublon de la ligne 89 était déjà présent.</p>
{src(qualite.controler_ventes, 'mercier/qualite.py')}
{src(qualite.Rejet, 'mercier/qualite.py')}

<h2>6. Étape 3 : l'entrepôt</h2>
<p>Modèle en étoile : la table de faits <code>fait_vente</code> au centre, et les dimensions
<code>dim_article</code>, <code>dim_boutique</code>, <code>dim_date</code>. S'ajoutent les tables
<code>rejet</code>, <code>chargement</code> et <code>utilisateur</code>.</p>
{code(entrepot.SCHEMA, 'mercier/entrepot.py — SCHEMA')}
<p>Les dimensions sont mises à jour par UPSERT (<code>ON CONFLICT … DO UPDATE</code>). La contrainte
<code>UNIQUE</code> et <code>ON CONFLICT DO NOTHING</code> rendent le chargement idempotent,
et tout le lot est écrit dans une seule transaction (<code>with con:</code>).</p>
{src(entrepot.charger_ventes, 'mercier/entrepot.py')}
{src(entrepot.charger, 'mercier/entrepot.py')}
{img('02_chaine_idempotence.png', "Figure 3 — Chaîne lancée deux fois : 122 lignes puis 0 (idempotence vérifiée)")}

<h2>7. Étape 4 : Python et la JVM</h2>
<p>Le calcul du montant net est fait par la classe Java <code>Tarif</code>. Le module
<code>tarif_java.py</code> choisit automatiquement la meilleure voie : JPype, sinon sous-processus
<code>java</code>, sinon repli en Python (même règle).</p>
{fichier('java/Tarif.java')}
{src(tarif_java.moteur_disponible, 'mercier/tarif_java.py')}
{src(tarif_java.montant_ligne, 'mercier/tarif_java.py')}
<p class="note">Java (JDK) n'est pas installé sur le poste de développement : la détection retient
donc la voie <b>python</b>, et le résultat est identique (35,82 pour 2 × 19,90 € à 10 %).
Dans le conteneur Docker (JDK inclus), c'est la voie <b>jpype</b> qui doit être retenue
(non exécuté ici : Docker Desktop n'était pas démarré).</p>
{img('04_cli_comptes_tarif.png', "Figure 4 — Création des comptes de démonstration et comparaison des voies de calcul")}

<h2>8. Étape 5 : la restitution (FastAPI)</h2>
<p>Lancement du serveur :</p>
{code('uvicorn mercier.api:app --reload', '')}
<h3>8.1 Tableau des routes</h3>
<table><tr><th>Méthode</th><th>Route</th><th>Accès</th><th>Rôle</th></tr>{lignes_routes}</table>
<h3>8.2 Dépendances</h3>
<p>La connexion à la base et les droits sont des dépendances FastAPI : la sécurité est dans la
signature de la route.</p>
{src(api.base, 'mercier/api.py')}
{src(api.exige_connexion, 'mercier/api.py')}
{src(api.exige_administrateur, 'mercier/api.py')}
<h3>8.3 Le tableau de bord</h3>
{src(api.tableau_de_bord, 'mercier/api.py')}
{src(indicateurs.synthese, 'mercier/indicateurs.py')}
{img('06_connexion.png', "Figure 5 — Page de connexion (GET /connexion)")}
{img('08_tableau_admin.png', "Figure 6 — Tableau de bord de l'administratrice : 122 ventes, 11 728 €, rejets du dernier lot")}
{img('09_tableau_admin_filtre_paris.png', "Figure 7 — Filtre /?boutique=paris-marais pour l'administratrice")}
<h3>8.4 L'API JSON et sa documentation</h3>
{src(api.sante, 'mercier/api.py')}
{src(api.api_boutiques, 'mercier/api.py')}
{img('17_sante.png', "Figure 8 — GET /sante sans authentification")}
{img('18_api_boutiques_json.png', "Figure 9 — GET /api/boutiques (administratrice)")}
{img('19_api_qualite_json.png', "Figure 10 — GET /api/qualite : dernier lot et ses 7 rejets")}
{img('16_documentation_docs.png', "Figure 11 — Documentation interactive générée sur /docs")}
{img('16b_docs_route_boutiques.png', "Figure 12 — Détail d'une route dans /docs")}

<h2>9. Étape 6 : l'administration</h2>
<p>La validation se fait dans le module métier (et non dans le formulaire) : elle vaut donc aussi
pour l'API. Le code d'une boutique est contrôlé par une expression régulière.</p>
{src(administration.valider_code, 'mercier/administration.py')}
{src(administration.creer_boutique, 'mercier/administration.py')}
{src(administration.nommer_gerant, 'mercier/administration.py')}
{src(api.creation_boutique, 'mercier/api.py')}
<p>Après un envoi, la route redirige (code 303) : actualiser la page ne recrée pas la boutique.</p>
{img('13_administration.png', "Figure 13 — Page d'administration")}
{img('14a_formulaire_boutique.png', "Figure 14 — Saisie d'une nouvelle boutique (bordeaux-centre)")}
{img('14b_boutique_creee.png', "Figure 15 — Boutique créée, message de confirmation")}
{img('15_code_invalide.png', "Figure 16 — Code « Bordeaux Lac » refusé par la validation")}
{img('15b_gerant_nomme.png', "Figure 17 — Gérant nommé pour bordeaux-centre")}

<h2>10. Étape 7 : la sécurité</h2>
<h3>10.1 Mots de passe</h3>
<p>Aucun mot de passe n'est stocké : on stocke un sel aléatoire et une empreinte PBKDF2-SHA256
(200 000 itérations). La comparaison est faite en temps constant.</p>
{src(securite.hacher, 'mercier/securite.py')}
{src(securite.verifier, 'mercier/securite.py')}
{src(securite.authentifier, 'mercier/securite.py')}
{img('07_connexion_erreur.png', "Figure 18 — Mauvais mot de passe : message volontairement neutre")}
<h3>10.2 Session, rôles et cloisonnement</h3>
<p>La session est un cookie signé avec la clé secrète (<code>SessionMiddleware</code>). Le
cloisonnement est appliqué dans la requête SQL : un gérant ne voit que sa boutique.</p>
{src(securite.boutiques_visibles, 'mercier/securite.py')}
{img('10_tableau_gerante_lyon.png', "Figure 19 — Julie, gérante de Lyon : 31 ventes, 3 592 €, une seule boutique")}
{img('11_gerante_triche_paris.png', "Figure 20 — Julie saisit /?boutique=paris-marais : le filtre est ignoré, elle voit Lyon")}
{img('12_gerante_admin_403.png', "Figure 21 — /administration interdit à la gérante (403)")}
{img('12b_gerante_api_qualite_403.png', "Figure 22 — /api/qualite interdite à la gérante (403)")}
<h3>10.3 Contrôle complet (16 vérifications)</h3>
<p>Script <code>tests/controle_complet.py</code>, exécuté sur le serveur lancé :</p>
{sortie('controle_complet.txt')}
<table><tr><th></th><th>Claire, administratrice</th><th>Julie, gérante de Lyon</th></tr>
<tr><td>Chiffre d'affaires</td><td>11 728 €</td><td>3 592 €</td></tr>
<tr><td>Ventes</td><td>122</td><td>31</td></tr>
<tr><td>Page d'administration</td><td>accessible</td><td>code 403</td></tr>
<tr><td>API qualité</td><td>accessible</td><td>code 403</td></tr></table>

<h2>11. Étape 8 : la mise en production</h2>
<p>Les secrets viennent de l'environnement. <code>.env.exemple</code> est livré, <code>.env</code>
est exclu du dépôt. L'application refuse de démarrer en production avec la clé de développement.</p>
{fichier('.env.exemple')}
{fichier('Dockerfile')}
{fichier('.dockerignore')}
<p class="note">Seule différence avec le sujet : l'image de base est <code>eclipse-temurin:21-jdk-jammy</code>
au lieu de <code>-jre</code>, car la commande <code>RUN javac java/Tarif.java</code> nécessite le
compilateur, absent d'un JRE.</p>
{code('''docker build -t mercier-data .
docker run -p 8000:8000 -v mercier_donnees:/donnees -e MERCIER_CLE_SECRETE=<clé aléatoire> mercier-data''', 'Construction et lancement du conteneur')}
{code('uvicorn mercier.api:app --host 0.0.0.0 --port 8000 --workers 4', 'Serveur de production (sans --reload)')}

<h2>12. Tests</h2>
<p>Sept tests pytest, chacun sur un entrepôt temporaire (<code>tmp_path</code>) : ingestion,
contrôle qualité, idempotence, moteur tarifaire, empreintes différentes pour un même mot de passe,
code de boutique invalide, cloisonnement.</p>
{img('05_tests_pytest.png', "Figure 23 — python -m pytest tests/ -v : 7 tests réussis")}
{img('20_controle_complet.png', "Figure 24 — Contrôle complet de l'application")}

<h2>13. Lancer le projet</h2>
{code(CMD_LANCER, '')}
<p>Comptes de démonstration (développement uniquement) : <code>claire</code> (administratrice) et
<code>julie</code> (gérante de lyon-presquile), mot de passe <code>mercier2026</code>.</p>

<h2>14. Conclusion</h2>
<p>La plateforme répond à la question de départ en une seconde : le chiffre d'affaires d'octobre est de
11 728 € pour un objectif de 13 600 € (86 %). Seule la boutique de Lyon dépasse son objectif (112 %).
Les chiffres obtenus sont identiques à ceux du sujet (122 ventes acceptées, 7 rejetées, 94,57 %).</p>
</body></html>""")

sortie_html = PROJET / "rapport" / "rapport_mercier_data.html"
sortie_html.write_text("".join(R), encoding="utf-8")

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge")
    page = nav.new_page()
    page.goto(sortie_html.as_uri())
    page.wait_for_load_state("networkidle")
    page.pdf(path=str(PROJET / "rapport" / "rapport_mercier_data.pdf"), format="A4",
             margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"},
             print_background=True, display_header_footer=True,
             header_template="<span></span>",
             footer_template='<div style="font-size:9px;width:100%;text-align:center">'
                             'Mercier Data — page <span class="pageNumber"></span>/'
                             '<span class="totalPages"></span></div>')
    nav.close()
print("ok", sortie_html)
