# Image de base contenant Python et un JRE, puisque le moteur
# tarifaire est en Java.
FROM eclipse-temurin:21-jdk-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Les dépendances d'abord : cette couche reste en cache tant que
# requirements.txt ne change pas.
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
RUN javac java/Tarif.java

ENV MERCIER_ENTREPOT=/donnees/entrepot.db \
    MERCIER_ZONE_BRUTE=/donnees/zone_brute
VOLUME ["/donnees"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/sante')"

CMD ["uvicorn", "mercier.api:app", "--host", "0.0.0.0", "--port", "8000"]
