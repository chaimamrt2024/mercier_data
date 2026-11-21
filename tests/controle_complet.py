"""Contrôle complet de l'application (section 8.6), sur le serveur lancé."""

import httpx

URL = "http://127.0.0.1:8000"
MDP = "mercier2026"


def client():
    return httpx.Client(base_url=URL, follow_redirects=False)


anonyme = client()
r = anonyme.get("/sante")
print("1. santé sans compte     :", r.status_code, r.json())
r = anonyme.get("/")
print("2. accueil sans compte   :", r.status_code, r.headers["location"])
print("3. api sans compte       :", anonyme.get("/api/boutiques").status_code)
r = anonyme.post("/connexion", data={"identifiant": "julie", "motdepasse": "faux"})
print("4. mauvais mot de passe  :", r.headers["location"])

julie = client()
r = julie.post("/connexion", data={"identifiant": "julie", "motdepasse": MDP})
print("5. connexion gérante     :", r.status_code, r.headers["location"])
print("6. tableau de bord       :", julie.get("/").status_code)
print("7. synthèse gérante      :", julie.get("/api/synthese").json())
print("8. boutiques visibles    :", [b["code"] for b in julie.get("/api/boutiques").json()])
print("9. admin interdit à julie:", julie.get("/administration").status_code)
print("10. api qualité interdite:", julie.get("/api/qualite").status_code)
page = julie.get("/?boutique=paris-marais").text
print("    filtre interdit (julie demande paris) :", "Paris</b>" in page)

claire = client()
claire.post("/connexion", data={"identifiant": "claire", "motdepasse": MDP})
print("11. synthèse admin       :", claire.get("/api/synthese").json())
print("12. boutiques admin      :", [b["code"] for b in claire.get("/api/boutiques").json()])
print("13. page admin           :", claire.get("/administration").status_code)
r = claire.post("/administration/boutique",
                data={"code": "nantes-graslin", "ville": "Nantes",
                      "surface_m2": 70, "objectif_mensuel": 2600})
print("14. création boutique    :", dict(httpx.URL(r.headers["location"]).params))
r = claire.post("/administration/boutique",
                data={"code": "Nantes Graslin", "ville": "Nantes"})
print("15. code invalide refusé :", dict(httpx.URL(r.headers["location"]).params))
print("16. documentation        :", anonyme.get("/docs").status_code)
