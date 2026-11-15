# Documentation Dashboard : Mireille et Fouchi

> **Responsables :** Mireille et Fouchi  
> **Projet :** Régulation intelligente des feux de circulation  
> **Composant :** Dashboard de supervision, d'analyse, de prédiction et de régulation du trafic  
> **Technologies principales :** Python, Streamlit, Plotly, pandas  
> **Lecteurs visés :** Honoré (données), Joel (Machine Learning), Godwin (régulation et simulation), équipe projet

---

## En bref

| Élément | Description |
|---|---|
| **Application** | Dashboard web Smart Traffic |
| **Framework** | Streamlit |
| **Visualisation** | Plotly |
| **Traitement des données** | pandas |
| **Navigation** | Six pages accessibles depuis un menu latéral |
| **Données historiques** | `data/processed/` — du 1er février au 31 mai 2020 |
| **Résultats de simulation** | `results/simulation.csv` et `results/simulation_summary.csv` |
| **Période des simulations intégrées** | Du 14 au 31 mai 2020 : 18 jours et 5 184 observations de cinq minutes |
| **Style commun** | `dashboard/style.py` |
| **Point d'entrée** | `dashboard/app.py` |

Le dashboard rassemble les résultats produits par les différents volets du projet dans une interface unique. Il permet de consulter les données historiques, d'explorer les variations du trafic, d'examiner les performances des modèles, de visualiser les résultats de régulation et d'accéder à une interface de prédiction.

Notre travail porte sur la présentation des résultats, la navigation entre les pages, les filtres, les visualisations et l'intégration des fichiers produits par les autres membres de l'équipe.

---

## 1. Périmètre du travail

### 1.1 Objectifs

Le dashboard doit permettre de :

- présenter une vue générale des conditions de circulation ;
- explorer les données historiques selon plusieurs dimensions ;
- comparer les performances des modèles de prédiction ;
- examiner les résultats du modèle retenu ;
- comparer une régulation par cycle fixe à une régulation adaptative ;
- proposer une interface de prédiction du trafic ;
- présenter les résultats de manière lisible et cohérente.

### 1.2 Répartition du travail

Le développement du dashboard est réalisé conjointement par Mireille et Fouchi.

| Partie | Contribution |
|---|---|
| **Fouchi** | Participation à la conception et au développement du dashboard, notamment la vue d'ensemble et l'exploration des données |
| **Mireille** | Développement et intégration des pages de comparaison des modèles, d'analyse du modèle retenu, de régulation des feux et de prédiction |
| **Travail commun** | Organisation générale, navigation, harmonisation visuelle, intégration des données et vérification du fonctionnement des pages |

Cette répartition décrit les principales responsabilités. Les ajustements d'interface et l'intégration ont été réalisés de manière collaborative.

---

## 2. Organisation du dashboard

Le dashboard est organisé en six pages.

| Page | Fichier | Fonction |
|---|---|---|
| **1. Tableau de bord** | `dashboard/app.py` | Présentation des indicateurs principaux, de l'état du trafic, de sa répartition et de son évolution |
| **2. Exploration** | `dashboard/pages/2_Exploration.py` | Analyse du profil horaire, des jours de la semaine, de la relation débit/vitesse et de la météo |
| **3. Comparaison des modèles** | `dashboard/pages/3_Comparaison_modeles.py` | Comparaison des algorithmes à partir de leurs métriques de performance |
| **4. Meilleur modèle** | `dashboard/pages/4_Meilleur_modele.py` | Analyse détaillée des résultats du modèle retenu |
| **5. Régulation des feux** | `dashboard/pages/5_Regulation_feux.py` | Comparaison des résultats du cycle fixe et de la régulation adaptative |
| **6. Prédiction** | `dashboard/pages/6_Prediction.py` | Interface de saisie des paramètres et de consultation d'une prédiction de trafic |

### 2.1 Vue d'ensemble

La page d'accueil présente les indicateurs calculés sur la période sélectionnée :

- débit moyen ;
- vitesse moyenne ;
- heure de pointe ;
- débit maximal ;
- état général du trafic ;
- proportion des observations correspondant aux états fluide, dense et congestionné ;
- évolution temporelle du débit.

Les filtres permettent de sélectionner une période, des jours, une plage horaire et un type de jour.

### 2.2 Exploration des données

La page d'exploration propose plusieurs visualisations :

- profil horaire du trafic en semaine et le week-end ;
- carte de chaleur croisant les heures et les jours ;
- débit moyen par jour de la semaine ;
- relation entre le débit et la vitesse ;
- débit moyen selon les conditions météorologiques.

Ces analyses servent à observer les variations du trafic et les relations entre les variables disponibles dans le jeu de données.

### 2.3 Comparaison des modèles

Cette page présente les résultats de plusieurs modèles de prédiction et permet de comparer leurs performances à partir des métriques disponibles, notamment MAE, RMSE et R².

Les résultats affichés doivent provenir des fichiers produits par le volet Machine Learning. Les valeurs de démonstration éventuellement présentes dans une ancienne version de la page ne doivent pas être considérées comme des résultats expérimentaux.

### 2.4 Analyse du modèle retenu

Cette page est consacrée à l'examen du modèle retenu : métriques sur le jeu de test, comparaison avec la persistance, analyse des prédictions et importance des variables lorsque ces résultats sont disponibles.

### 2.5 Régulation des feux

Cette page exploite les fichiers générés par le module de simulation de Godwin :

- `results/simulation.csv` ;
- `results/simulation_summary.csv`.

Elle compare deux stratégies :

- **Cycle fixe :** durées de vert constantes ;
- **Régulation adaptative :** durées de vert ajustées selon le trafic prévu.

Les indicateurs présentés comprennent notamment le temps d'attente moyen, la vitesse moyenne, le nombre d'arrêts par véhicule, les émissions de CO₂ et la longueur des files d'attente.

Les filtres de date et d'heure permettent d'examiner les résultats sur une période sélectionnée. Les fichiers intégrés couvrent les journées du 14 au 31 mai 2020, soit 18 jours et 5 184 intervalles de cinq minutes, hors ligne d'en-tête.

### 2.6 Prédiction

La page de prédiction fournit une interface permettant de définir des paramètres temporels et météorologiques et de consulter le résultat associé lorsque le modèle et les composants nécessaires sont disponibles.

Les variables saisies doivent rester cohérentes avec celles attendues par la chaîne de prétraitement et le modèle entraîné. Les variables historiques décalées, lorsqu'elles sont nécessaires, doivent être obtenues depuis l'historique ou traitées selon la méthode définie avec le responsable Machine Learning.

---

## 3. Sources de données et intégration

Le dashboard réunit deux ensembles de données qui n'ont pas le même rôle.

### 3.1 Données historiques — travail d'Honoré

Les pages d'analyse et de prédiction s'appuient sur le jeu de données historique préparé par Honoré.

- **Période :** du 1er février au 31 mai 2020 ;
- **Fréquence :** une observation toutes les cinq minutes ;
- **Nombre de lignes après nettoyage :** 34 820 ;
- **Variable cible :** `traffic_flow`, correspondant au nombre de véhicules par intervalle de cinq minutes.

Les fichiers préparés se trouvent dans `data/processed/`.

### 3.2 Résultats de simulation — travail de Godwin

La page de régulation exploite les résultats de simulation SUMO fournis par Godwin.

- **Période intégrée au dashboard :** du 14 au 31 mai 2020 ;
- **Nombre d'observations :** 5 184 ;
- **Fréquence :** cinq minutes ;
- **Fichiers :** `results/simulation.csv` et `results/simulation_summary.csv`.

Ces résultats sont distincts des données historiques utilisées dans les autres pages. Il ne faut donc pas confondre la période historique de février à mai avec la période des simulations de régulation.

### 3.3 Résultats du Machine Learning — travail de Joel

Les pages consacrées à la comparaison et à l'analyse des modèles utilisent les résultats produits par le volet Machine Learning.

Les noms et formats des fichiers doivent correspondre à ceux réellement fournis par Joel. Le dashboard ne doit pas présenter des données fictives comme des résultats d'entraînement ou de test.

---

## 4. Architecture et organisation des fichiers

Les principaux fichiers du dashboard sont organisés de la manière suivante :

```text
dashboard/
├── app.py
├── style.py
├── donnees.py
├── assets/
│   └── feu-de-circulation.png
└── pages/
    ├── 2_Exploration.py
    ├── 3_Comparaison_modeles.py
    ├── 4_Meilleur_modele.py
    ├── 5_Regulation_feux.py
    └── 6_Prediction.py

results/
├── simulation.csv
└── simulation_summary.csv
```

- `app.py` constitue le point d'entrée de l'application et contient la vue d'ensemble.
- `style.py` regroupe les fonctions et les règles CSS communes.
- `donnees.py` centralise le chargement et le filtrage des données historiques ainsi que les fonctions associées à l'état du trafic.
- `pages/` contient les cinq autres pages.
- `assets/` contient les ressources graphiques communes.
- `results/` contient les résultats de simulation exploités par la page de régulation.

---

## 5. Interface et composants communs

Afin de conserver une présentation homogène, les pages utilisent les fonctions communes définies dans `dashboard/style.py`.

| Fonction | Utilisation |
|---|---|
| `appliquer_style()` | Applique les règles CSS communes |
| `afficher_menu(page_active)` | Affiche la navigation latérale et identifie la page active |
| `afficher_banniere(titre, description, surtitre)` | Affiche la bannière principale |
| `titre_section(titre, sous_titre)` | Affiche les titres et sous-titres des sections |
| `carte_kpi(label, valeur, pied, icone, couleur)` | Affiche un indicateur sous forme de carte |
| `styliser_graphique(fig, titre, titre_y, hauteur)` | Harmonise la présentation des graphiques Plotly |

### 5.1 Choix visuels

L'interface utilise :

- une barre latérale bleu marine ;
- un fond général gris très clair ;
- des cartes blanches ;
- des accents turquoise et bleus ;
- des couleurs distinctes pour les niveaux de circulation ;
- une typographie et des espacements harmonisés.

Le pied de page est commun aux pages et ne contient que l'identification du projet :

`SMART TRAFFIC · SUPERVISION ET ANALYSE DU TRAFIC ROUTIER`

Les formulations promotionnelles et les remarques génériques en fin de page sont évitées afin de conserver une interface sobre.

---

## 6. Installation et lancement

Depuis la racine du dépôt, activer l'environnement virtuel :

```bash
source venv/bin/activate
```

Si l'environnement porte le nom `.venv` :

```bash
source .venv/bin/activate
```

Installer les dépendances du projet si cela n'a pas déjà été fait :

```bash
pip install -r requirements.txt
```

Lancer le dashboard :

```bash
streamlit run dashboard/app.py
```

L'application est alors accessible depuis l'adresse locale indiquée par Streamlit, généralement `http://localhost:8501`.

---

## 7. Vérifications réalisées

Les vérifications effectuées pendant l'intégration ont porté sur :

- le lancement de l'application Streamlit ;
- l'accès aux six pages depuis le menu latéral ;
- l'affichage des données historiques ;
- le fonctionnement des filtres de période, de jours et d'heures sur les pages concernées ;
- l'affichage des graphiques et des indicateurs ;
- le chargement des fichiers de simulation ;
- la présence des colonnes attendues dans les deux fichiers de résultats ;
- la mise à jour des indicateurs de régulation lorsque la période sélectionnée change ;
- l'harmonisation du style et du pied de page.

Les fichiers de simulation ont été contrôlés : `simulation.csv` contient 5 184 observations et les dates vont du 14 au 31 mai 2020. Les colonnes nécessaires à la page de régulation sont présentes.

---

## 8. Limites et points d'attention

1. **Périodes différentes.** Les données historiques couvrent février à mai 2020, tandis que les résultats de simulation intégrés couvrent le 14 au 31 mai 2020.
2. **Données historiques.** Les résultats des analyses dépendent de la qualité, de la couverture et des transformations appliquées au jeu de données préparé.
3. **Simulation.** Les résultats de régulation proviennent d'un scénario SUMO défini par Godwin. Ils ne constituent pas une mesure réalisée sur un carrefour réel.
4. **Prédiction.** La cohérence des résultats dépend du chargement du bon modèle et de la préparation correcte des variables attendues.
5. **Évolution des fichiers.** Si les responsables des données, du Machine Learning ou de la simulation modifient les noms de colonnes ou les formats des fichiers, les fonctions de chargement du dashboard doivent être vérifiées.
6. **Filtres.** Une sélection sans observation doit être signalée à l'utilisateur plutôt que de produire des indicateurs vides ou trompeurs.

---

## 9. Notes pour l'équipe

### Pour Honoré — Données

- Les pages d'analyse utilisent les données historiques préparées dans `data/processed/`.
- La période historique affichée dans le tableau de bord est du 1er février au 31 mai 2020.
- Les noms de colonnes et les transformations de `donnees.py` doivent rester cohérents avec les fichiers préparés.

### Pour Joel — Machine Learning

- Les pages de comparaison et d'analyse doivent exploiter les métriques et prédictions réellement exportées par le pipeline.
- Toute modification du modèle, des variables d'entrée ou des fichiers de résultats doit être communiquée afin de maintenir la compatibilité de la page de prédiction.

### Pour Godwin — Régulation et simulation

- La page de régulation lit `results/simulation.csv` et `results/simulation_summary.csv`.
- Les résultats intégrés couvrent les 18 jours du 14 au 31 mai 2020.
- Si le schéma des CSV évolue, les colonnes utilisées par la page 5 doivent être vérifiées.

### Pour Mireille et Fouchi — Dashboard

- Conserver les fonctions communes dans `dashboard/style.py` afin d'éviter de dupliquer le CSS dans chaque page.
- Vérifier le rendu des six pages après toute modification du style commun.
- Ne pas modifier les calculs des pages sans vérifier leur cohérence avec les données sources.
- Garder les données historiques et les résultats de simulation clairement séparés.
- Tester les filtres, les graphiques et les indicateurs après chaque intégration.

---

## 10. Bilan

Le dashboard Smart Traffic constitue l'interface de consultation des différents résultats du projet. Il relie les données historiques préparées par Honoré, les résultats du Machine Learning produits par Joel et les résultats de simulation fournis par Godwin.

Le travail de Mireille et Fouchi consiste à rendre ces résultats accessibles dans une application organisée en six pages, avec des filtres, des indicateurs, des graphiques et une présentation visuelle cohérente.

L'interface a été conçue pour faciliter la lecture des résultats et la comparaison des différentes étapes du projet, tout en conservant une séparation claire entre analyse historique, prédiction et simulation de régulation.
