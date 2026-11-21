# Mercier Data

Plateforme de données d'Atelier Mercier — projet « Notions Python avancées », Master 1 DAT.

Le rapport détaillé (captures d'écran, routes et code) est dans
[`rapport/rapport_mercier_data.pdf`](rapport/rapport_mercier_data.pdf),
les captures dans [`captures/`](captures/).

## 1. Installation

Prérequis : Python 3.11 ou plus récent. Java est facultatif (sans Java, le calcul
tarifaire utilise le repli Python, avec le même résultat).

```
git clone <adresse-du-depot>
cd mercier_data

python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # Linux / macOS

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 2. Chaîne de données

```
python -m mercier.cli chaine      # ingestion + contrôle qualité + chargement
python -m mercier.cli chaine      # 2e fois : 0 nouvelle ligne (idempotence)
python -m mercier.cli comptes     # comptes de démonstration
python -m mercier.cli tarif       # voies de calcul : JPype, sous-processus, Python
```

Résultat attendu : 122 ventes acceptées, 7 rejetées (94.57 %).

## 3. Tests unitaires

```
python -m pytest tests/ -v
```

Résultat attendu : `7 passed`.

## 4. Application web

```
uvicorn mercier.api:app --reload
```

- Tableau de bord : http://127.0.0.1:8000
- Documentation de l'API : http://127.0.0.1:8000/docs
- Point de santé : http://127.0.0.1:8000/sante

Comptes de démonstration (créés par `python -m mercier.cli comptes`),
mot de passe `mercier2026` :

| Identifiant | Rôle | Périmètre |
|---|---|---|
| `claire` | administratrice | tout le réseau, page d'administration |
| `julie` | gérante | lyon-presquile uniquement |

## 5. Contrôle complet (16 vérifications)

Le serveur étant lancé, dans un second terminal :

```
python tests/controle_complet.py
```

## 6. Docker

```
docker build -t mercier-data .
docker run -p 8000:8000 -v mercier_donnees:/donnees -e MERCIER_CLE_SECRETE=<clé> mercier-data
```

## Arborescence

```
mercier_data/
├── donnees_sources/     fichiers reçus (jamais modifiés)
├── java/Tarif.java      moteur de remises
├── mercier/             paquet Python (config, ingestion, qualite, entrepot,
│                        tarif_java, indicateurs, administration, securite, api, cli)
├── tests/               tests pytest et contrôle complet
├── captures/            captures d'écran
└── rapport/             rapport PDF / HTML
```
